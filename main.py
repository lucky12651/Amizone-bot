import requests
import bs4
import json
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext


class AMIZONE:
    def __init__(self, session_cookie=None):
        self.URL_BASE = "https://s.amizone.net"
        self.URL_LOGIN = "https://s.amizone.net"
        self.URL_HOME = "https://s.amizone.net/Home"
        self.session = requests.Session()
        self.session.headers.update({"Referer": self.URL_BASE})
        if session_cookie:
            try:
                self.session.cookies.update(json.loads(session_cookie))
            except:
                raise ValueError("Invalid or Expired cookie")

    def saveCookie(self):
        with open('cookie.json', 'w') as f:
            json.dump(requests.utils.dict_from_cookiejar(self.session.cookies), f)

    def loadCookie(self):
        with open('cookie.json', 'r') as f:
            cookiejar = requests.utils.cookiejar_from_dict(json.load(f))
            self.session.cookies.update(cookiejar)

    def login(self, user, pwd):
        defaultPage = self.session.get(self.URL_BASE)
        htmlObject = bs4.BeautifulSoup(defaultPage.content, 'html.parser')
        rvt = htmlObject.find(id="loginform").input['value']
        data = {
            "_UserName": user,
            "_Password": pwd,
            "__RequestVerificationToken": rvt
        }
        response = self.session.post(self.URL_LOGIN, data=data)
        response.raise_for_status()
        return response.cookies

    def my_courses(self, sem=None):
        try:
            if sem:
                a = self.session.post("https://s.amizone.net/Academics/MyCourses/CourseListSemWise", data={'sem': sem})
            else:
                a = self.session.get("https://s.amizone.net/Academics/MyCourses")
            b = bs4.BeautifulSoup(a.content, 'html.parser')
            courseCode = [c.text.strip() for c in b.find_all(attrs={'data-title': "Course Code"})]
            courseName = [c.text.strip() for c in b.find_all(attrs={'data-title': "Course Name"})]
            attendance = [c.text.strip() for c in b.find_all(attrs={'data-title': "Attendance"})]
            syllabus = [c.decode_contents() for c in b.find_all(attrs={'data-title': "Course Syllabus"})]
            # Extract href from anchor tags
            syllabus = [i[i.find('"') + 1:i.find('"', i.find('"') + 1)] for i in syllabus]
            percentage = []
            for i in attendance:
                try:
                    x = float(i[i.find("(") + 1:i.find(")")])
                    percentage.append(x)
                except:
                    percentage.append(100.0)
        except:
            raise ValueError("Invalid or Expired cookie")
        else:
            return {
                'course_code': courseCode,
                'course_name': courseName,
                'attendance': attendance,
                'attendance_pct': percentage,
                'syllabus': syllabus,
            }

    def start_telegram_bot(self):
        bot = Bot(token=self.TELEGRAM_TOKEN)
        updater = Updater(bot=bot, use_context=True)
        dispatcher = updater.dispatcher

        def start(update: Update, context: CallbackContext):
            context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to AMIZONE Bot! Send /login to enter your AMIZONE credentials.")

        def login_command(update: Update, context: CallbackContext):
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Please enter your AMIZONE username: /username")

        def username(update: Update, context: CallbackContext):
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Please enter your AMIZONE password: /password")

            # Save the entered username in the user's context
            context.user_data['username'] = context.args[0]

        def password(update: Update, context: CallbackContext):
            # Retrieve the previously entered username from the user's context
            username = context.user_data.get('username')

            if not username:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text="Please enter your AMIZONE username first: /username")
                return

            password = context.args[0]

            try:
                amizone.login(username, password)
                amizone.saveCookie()
                context.bot.send_message(chat_id=update.effective_chat.id, text="Login successful.")
                # Fetch attendance information after successful login
                attendance(update, context)
            except Exception as e:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text="Login failed. Please check your username and password.")

            # Clear the stored username from the user's context
            del context.user_data['username']

        def attendance(update: Update, context: CallbackContext):
            try:
                attendance_data = amizone.my_courses()
                message = "Attendance Information:\n"
                for i in range(len(attendance_data['course_code'])):
                    message += f"Course: {attendance_data['course_code'][i]} - {attendance_data['course_name'][i]}\n"
                    message += f"Attendance: {attendance_data['attendance'][i]} ({attendance_data['attendance_pct'][i]}%)\n"
                    message += f"Syllabus Link: {attendance_data['syllabus'][i]}\n\n"
                context.bot.send_message(chat_id=update.effective_chat.id, text=message)
            except Exception as e:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text="Failed to fetch attendance information.")

        start_handler = CommandHandler('start', start)
        login_command_handler = CommandHandler('login', login_command)
        username_handler = CommandHandler('username', username)
        password_handler = CommandHandler('password', password)
        attendance_handler = CommandHandler('attendance', attendance)

        dispatcher.add_handler(start_handler)
        dispatcher.add_handler(login_command_handler)
        dispatcher.add_handler(username_handler)
        dispatcher.add_handler(password_handler)
        dispatcher.add_handler(attendance_handler)

        updater.start_polling()
        updater.idle()


# Usage example:
amizone = AMIZONE()

# Set the Telegram Bot token
amizone.TELEGRAM_TOKEN = "6213929149:AAH1-xxns-W97lqVzeFWXJsiOQHjt8ryCbw"

# Start the Telegram bot
amizone.start_telegram_bot()
