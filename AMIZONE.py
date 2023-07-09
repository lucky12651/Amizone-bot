from http.client import HTTPException
import requests
import bs4
import json
import telegram
from telegram import Update, Bot, replymarkup
from telegram.ext import Updater, CommandHandler, CallbackContext
from requests.exceptions import HTTPError
from datetime import datetime
import re
import firebase_admin
from firebase_admin import credentials, db


class InvalidCredentialsError(Exception):
    pass

class ExpiredCredentialsError(Exception):
    pass

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


        # Initialize Firebase Admin SDK
        cred = credentials.Certificate('/Users/vaibhav/Desktop/new/assistant-b35bd-firebase-adminsdk-7ntnq-7c96808bc5.json')
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://assistant-b35bd-default-rtdb.firebaseio.com/'
        })

    def saveCookie(self):
        pass

    def loadCookie(self):
        pass



    def validate_credentials(self, username, password):
        default_page = self.session.get(self.URL_BASE)
        html_object = bs4.BeautifulSoup(default_page.content, 'html.parser')
        rvt = html_object.find(id="loginform").input['value']
        data = {
            "_UserName": username,
            "_Password": password,
            "__RequestVerificationToken": rvt
        }
        response = self.session.post(self.URL_LOGIN, data=data)
        response.raise_for_status()

        if "Please check your credential !!" in response.text:
            return False
        elif "Expired credentials" in response.text:
            return False

        # If the response doesn't contain "Invalid credentials" or "Expired credentials",
        # assume the credentials are valid
        return True


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

    def faculty(self):
        try:
            a = self.session.get("https://s.amizone.net/FacultyFeeback/FacultyFeedback")
            b = bs4.BeautifulSoup(a.content, 'html.parser')
            faculties=[x.text.strip() for x in b.find_all(attrs={"class":"faculty-name"})]
            subjects=[x.text.strip() for x in b.find_all(attrs={"class":"subject"})]
            images=[x["src"] for x in b.find_all(attrs={"class":"img-responsive"})]
        except:
            raise HTTPException(status_code=401, detail="Invalid or Expired cookie")
        else:
            return {
                'faculties':faculties,
                'subjects':subjects,
                'images':images
            }
        

    def timetable(self, date=datetime.now().strftime("%Y-%m-%d")):
        timestamp = round(datetime.now().timestamp()*1000)
        start = datetime.strptime(date, "%Y-%m-%d")
        end = start
        try:
            res = self.session.get("https://s.amizone.net/Calendar/home/GetDiaryEvents?start={0}&end={1}&_={2}".format(date, end, timestamp))
            res_json = json.loads(res.content)
            courseCode = [i['CourseCode'].strip() for i in res_json]
            courseTitle = [i['title'].strip() for i in res_json]
            courseTeacher = [re.sub('&lt;/?[a-z]+&gt;', '', i['FacultyName'].split('[')[0]).strip() for i in res_json]
            classLocation = [i['RoomNo'].strip() for i in res_json]
            Time = [datetime.strptime(i['start'],'%Y/%m/%d %I:%M:%S %p').strftime('%H:%M') + ' - ' + datetime.strptime(i['end'],'%Y/%m/%d %I:%M:%S %p').strftime('%H:%M') for i in res_json]
            Attendance = []
            for i in res_json:
                if i['AttndColor'] == '#4FCC4F':
                    Attendance.append("✅")
                elif i['AttndColor'] == '#f00':
                    Attendance.append("❌")
                elif i['AttndColor'] == '#3a87ad':
                    Attendance.append(0)
        except:
            raise HTTPException(status_code=401, detail="Invalid or Expired cookie")
        else:
            timeTableData = {'course_code':courseCode,'course_title':courseTitle,'course_teacher':courseTeacher,'class_location':classLocation,'class_time':Time,'attendance':Attendance}
            sortedTimeTableData = {
                'course_code':[timeTableData['course_code'][timeTableData['class_time'].index(i)] for i in sorted(timeTableData['class_time'])],
                'course_title':[timeTableData['course_title'][timeTableData['class_time'].index(i)] for i in sorted(timeTableData['class_time'])],
                'course_teacher':[timeTableData['course_teacher'][timeTableData['class_time'].index(i)] for i in sorted(timeTableData['class_time'])],
                'class_location':[timeTableData['class_location'][timeTableData['class_time'].index(i)] for i in sorted(timeTableData['class_time'])],
                'class_time':sorted(timeTableData['class_time']),
                'attendance':[timeTableData['attendance'][timeTableData['class_time'].index(i)] for i in sorted(timeTableData['class_time'])]
            }
            return sortedTimeTableData


    def exam_schedule(self):
        try:
            a = self.session.get('https://s.amizone.net/Examination/ExamSchedule')
            b = bs4.BeautifulSoup(a.content, 'html.parser')
            courseCode = [c.text.strip() for c in b.find_all(attrs={'data-title': "Course Code"})]
            courseTitle = [c.text.strip() for c in b.find_all(attrs={'data-title': "Course Title"})]
            ExamDate = [c.text.strip() for c in b.find_all(attrs={'data-title': "Exam Date"})]
            Time = [c.text.strip() for c in b.find_all(attrs={'data-title': "Time"})]
        except:
            raise HTTPException(status_code=401, detail="Invalid or Expired cookie")
        else:
            return {
                'course_code':courseCode,
                'course_title':courseTitle,
                'exam_date':ExamDate,
                'exam_time':Time
            }


    def my_profile(self):
        try:
            a = self.session.get("https://s.amizone.net/Electives/NewCourseCoding")
            b = bs4.BeautifulSoup(a.content, 'html.parser')
            row1=[x.text for x in b.find_all("div",attrs={"class":"col-md-3"})]
            row2 = [x.text for x in b.find_all("div", attrs={"class": "col-md-2"})]
            name=row1[0].split(': ')[1].strip()
            Enrollment=row1[1].split(': ')[1].strip()
            programme=row2[0].split(': ')[1].strip()
            sem=row2[1].split(': ')[1].strip()
            passyear=row2[2].split(': ')[1].strip()
        except:
            raise HTTPException(status_code=401, detail="Invalid or Expired cookie")
        else:
            return {
                'name':name,
                'enrollment':Enrollment,
                'programme':programme,
                'sem':sem,
                'passyear':passyear
            }
        

    def results(self, sem=None):
        try:
            if sem:
                a = self.session.post("https://s.amizone.net/Examination/Examination/ExaminationListSemWise", data= {'sem':sem})
            else:
                a = self.session.get("https://s.amizone.net/Examination/Examination")
            b = bs4.BeautifulSoup(a.content, 'html.parser')
            courseCode = [c.text.strip() for c in b.find_all(attrs={'data-title': "Course Code"})]
            courseTitle = [c.text.strip() for c in b.find_all(attrs={'data-title': "Course Title"})]
            GradeObtained = [c.text.strip() for c in b.find_all(attrs={'data-title': "Go"})]
            GradePoint=[c.text.strip() for c in b.find_all(attrs={'data-title': "GP"})]
            sgpa=[float(x.text.strip()) for x in b.find_all(attrs={'data-title': "SGPA"})]
            cgpa=[x.text.strip() for x in b.find_all(attrs={'data-title': "CGPA"})]
            if len(sgpa):
                cgpa[0] = sgpa[0]
                cgpa=[float(x) for x in cgpa]
        except:
            raise HTTPError("Invalid or Expired cookie")
        else:
            return {
                "sem_result":{
                    "course_code":courseCode,
                    "course_title":courseTitle,
                    "grade_obtained":GradeObtained,
                    "grade_point":GradePoint,
                },
                "combined":{
                    "sgpa":sgpa,
                    "cgpa":cgpa
                }
            }

    def start_telegram_bot(self):
        bot = Bot(token=self.TELEGRAM_TOKEN)
        updater = Updater(bot=bot, use_context=True)
        dispatcher = updater.dispatcher

        def start(update: Update, context: CallbackContext):
            context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to AMIZONE Bot! Send /login to enter your AMIZONE credentials.")

        def login_command(update: Update, context: CallbackContext):
            context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter your AMIZONE username:For Example-  /username 8098099")

        def username(update: Update, context: CallbackContext):
            context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter your AMIZONE password:For Example-  /password hello@123")
            # Save the entered username in the user's context
            context.user_data['username'] = context.args[0]

        def password(update: Update, context: CallbackContext):
            # Retrieve the previously entered username from the user's context
            username = context.user_data.get('username')

            if not username:
               context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter your AMIZONE username first: /username")
               return

            password = context.args[0]

            # Check if the credentials are valid
            if not self.validate_credentials(username, password):
                context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid username or password. Please try again.")
                return

            # If the credentials are valid, perform the login
            self.login(username, password)

            context.bot.send_message(chat_id=update.effective_chat.id, text="Login successful.\nPlease select commands from the menu.")

             # Store user credentials in Firebase database
            user_data = {
                'username': username,
                'password': password
            }
            user_ref = db.reference('users').child(str(update.effective_chat.id))
            user_ref.set(user_data)

    
                
            # Fetch attendance information after successful login
        def attendance(update: Update, context: CallbackContext):
            try:
                chat_id = update.effective_chat.id
                if check_user_exist(chat_id):
                    username, password = fetch_user_credentials(chat_id)
                    if username and password:
                        self.login(username, password)
                        self.loadCookie()
                        attendance_data = self.my_courses()
                        attendance_message = ""
                        for i in range(len(attendance_data['course_code'])):
                            attendance_message += f"Course Code: {attendance_data['course_code'][i]}\n"
                            attendance_message += f"Course Name: {attendance_data['course_name'][i]}\n"
                            attendance_message += f"Attendance: {attendance_data['attendance'][i]}\n"
                            attendance_message += f"Attendance Percentage: {attendance_data['attendance_pct'][i]}%\n"
                            attendance_message += f"Syllabus: {attendance_data['syllabus'][i]}\n\n"
                        context.bot.send_message(chat_id=chat_id, text=attendance_message)
                    else:
                        context.bot.send_message(chat_id=chat_id, text="User credentials not found. Please log in again.")
                else:
                    context.bot.send_message(chat_id=chat_id, text="User not found. Please log in using /login command.")
            except:
                context.bot.send_message(chat_id=chat_id, text="An error occurred while fetching attendance information.")
        def my_profile_command(update: Update, context: CallbackContext):
            try:
                chat_id = update.effective_chat.id
                if check_user_exist(chat_id):
                    username, password = fetch_user_credentials(chat_id)
                    if username and password:
                        self.login(username, password)
                        self.loadCookie()
                        profile_data = self.my_profile()
                        profile_message = ""
                        profile_message += f"Name: {profile_data['name']}\n"
                        profile_message += f"Enrollment: {profile_data['enrollment']}\n"
                        profile_message += f"Programme: {profile_data['programme']}\n"
                        profile_message += f"Semester: {profile_data['sem']}\n"
                        profile_message += f"Passing Year: {profile_data['passyear']}\n"
                        context.bot.send_message(chat_id=update.effective_chat.id, text=profile_message)
                    else:
                        context.bot.send_message(chat_id=chat_id, text="User credentials not found. Please log in again.")
                else:
                    context.bot.send_message(chat_id=chat_id, text="User not found. Please log in using /login command.")
    
            except:
                context.bot.send_message(chat_id=update.effective_chat.id, text="An error occurred while fetching profile information.")     

        def exam_schedule_command(update: Update, context: CallbackContext):
                    try:
                        chat_id = update.effective_chat.id
                        if check_user_exist(chat_id):
                            username, password = fetch_user_credentials(chat_id)
                            if username and password:
                               self.login(username, password)
                               self.loadCookie()
                               exam_schedule_data = self.exam_schedule()
                               exam_schedule_message = ""
                               for i in range(len(exam_schedule_data['course_code'])):
                                   exam_schedule_message += f"Course Code: {exam_schedule_data['course_code'][i]}\n"
                                   exam_schedule_message += f"Course Title: {exam_schedule_data['course_title'][i]}\n"
                                   exam_schedule_message += f"Exam Date: {exam_schedule_data['exam_date'][i]}\n"
                                   exam_schedule_message += f"Exam Time: {exam_schedule_data['exam_time'][i]}\n\n"
                               context.bot.send_message(chat_id=update.effective_chat.id, text=exam_schedule_message)
                            else:
                              context.bot.send_message(chat_id=chat_id, text="User credentials not found. Please log in again.")
                        else:
                           context.bot.send_message(chat_id=chat_id, text="User not found. Please log in using /login command.")
                    except:
                      context.bot.send_message(chat_id=update.effective_chat.id, text="An error occurred while fetching exam information.")     

        def my_courses_command(update: Update, context: CallbackContext):
            try:
                chat_id = update.effective_chat.id
                if check_user_exist(chat_id):
                    username, password = fetch_user_credentials(chat_id)
                    if username and password:
                        self.login(username, password)
                        self.loadCookie()
                        my_courses_data = self.my_courses()
                        my_courses_message = ""
                        for i in range(len(my_courses_data['course_code'])):
                            my_courses_message += f"Course Code: {my_courses_data['course_code'][i]}\n"
                            my_courses_message += f"Course Name: {my_courses_data['course_name'][i]}\n"
                        context.bot.send_message(chat_id=update.effective_chat.id, text=my_courses_message)
                    else:
                        context.bot.send_message(chat_id=chat_id, text="User credentials not found. Please log in again.")
                else:
                    context.bot.send_message(chat_id=chat_id, text="User not found. Please log in using /login command.")
            except:
                context.bot.send_message(chat_id=chat_id, text="An error occurred while fetching my course information.")

        def timetable_command(update: Update, context: CallbackContext):
            try:
                chat_id = update.effective_chat.id
                if check_user_exist(chat_id):
                    username, password = fetch_user_credentials(chat_id)
                    if username and password:
                        self.login(username, password)
                        self.loadCookie()
                        timetable_data = self.timetable()
                        timetable_message = ""
                        for i in range(len(timetable_data['course_code'])):
                            timetable_message += f"Course Code: {timetable_data['course_code'][i]}\n"
                            timetable_message += f"Course Title: {timetable_data['course_title'][i]}\n"
                            timetable_message += f"Course Teacher: {timetable_data['course_teacher'][i]}\n"
                            timetable_message += f"Class Location: {timetable_data['class_location'][i]}\n"
                            timetable_message += f"Class Time: {timetable_data['class_time'][i]}\n"
                            timetable_message += f"Attendance: {timetable_data['attendance'][i]}\n\n"
                        context.bot.send_message(chat_id=update.effective_chat.id, text=timetable_message)
                    else:
                        context.bot.send_message(chat_id=chat_id, text="User credentials not found. Please log in again.")
                else:
                    context.bot.send_message(chat_id=chat_id, text="User not found. Please log in using /login command.")
            except:
                context.bot.send_message(chat_id=chat_id, text="Your Time-Table is not set yet")


        def faculty(update: Update, context: CallbackContext):
            try:
                chat_id = update.effective_chat.id
                if check_user_exist(chat_id):
                    username, password = fetch_user_credentials(chat_id)
                    if username and password:
                        self.login(username, password)
                        self.loadCookie()
                        faculty_data = self.faculty()
                        faculty_message = ""
                        for i, faculty in enumerate(faculty_data['faculties']):
                           faculty_message += f"Name: {faculty}\n"
                           faculty_message += f"Subject: {faculty_data['subjects'][i]}\n"
                           faculty_message += f"Image: {faculty_data['images'][i]}\n\n"
                        context.bot.send_message(chat_id=update.effective_chat.id, text=faculty_message)
                    else:
                        context.bot.send_message(chat_id=chat_id, text="User credentials not found. Please log in again.")
                else:
                    context.bot.send_message(chat_id=chat_id, text="User not found. Please log in using /login command.")
            except:
                context.bot.send_message(chat_id=chat_id, text="An error occurred while fetching faculty information.")

              
        def results(update: Update, context: CallbackContext):
            try:
                chat_id = update.effective_chat.id
                if check_user_exist(chat_id):
                    username, password = fetch_user_credentials(chat_id)
                    if username and password:
                        self.login(username, password)
                        self.loadCookie()
                        results_data = self.results()
                        results_message = ""
                        sem_result = results_data['sem_result']
                        combined = results_data['combined']
                        for i in range(len(sem_result['course_code'])):
                            results_message += f"Course Code: {sem_result['course_code'][i]}\n"
                            results_message += f"Course Title: {sem_result['course_title'][i]}\n"
                            results_message += f"Grade Obtained: {sem_result['grade_obtained'][i]}\n"
                            results_message += f"Grade Point: {sem_result['grade_point'][i]}\n\n"
                            results_message += f"SGPA: {combined['sgpa'][0]}\n"
                            results_message += f"CGPA: {combined['cgpa'][0]}\n"
                        context.bot.send_message(chat_id=chat_id, text=results_message)
                    else:
                        context.bot.send_message(chat_id=chat_id, text="User credentials not found. Please log in again.")
                else:
                    context.bot.send_message(chat_id=chat_id, text="User not found. Please log in using /login command.")
            except:
                context.bot.send_message(chat_id=chat_id, text="An error occurred while fetching results information.")

        # Define command handlers
        start_handler = CommandHandler('start', start)
        login_command_handler = CommandHandler('login', login_command)
        username_handler = CommandHandler('username', username)
        password_handler = CommandHandler('password', password)
        attendance_handler = CommandHandler('attendance', attendance)
        timetable_handler = CommandHandler('timetable', timetable_command)
        my_profile_handler = CommandHandler('my_profile', my_profile_command)
        my_courses_handler = CommandHandler('my_course', my_courses_command)
        results_handler = CommandHandler('results', results)
        faculty_handler = CommandHandler('faculty', faculty)
        exam_schedule_handler = CommandHandler('exam_schedule', exam_schedule_command)

        # Add command handlers to the dispatcher
        dispatcher.add_handler(start_handler)
        dispatcher.add_handler(login_command_handler)
        dispatcher.add_handler(username_handler)
        dispatcher.add_handler(password_handler)
        dispatcher.add_handler(attendance_handler)
        dispatcher.add_handler(faculty_handler)
        dispatcher.add_handler(my_profile_handler)
        dispatcher.add_handler(results_handler)
        dispatcher.add_handler(my_courses_handler)
        dispatcher.add_handler(exam_schedule_handler)
        dispatcher.add_handler(timetable_handler)

        updater.start_polling()

    def run_telegram_bot(self, telegram_token):
        self.TELEGRAM_TOKEN = telegram_token
        self.start_telegram_bot()

def check_user_exist(chat_id):
    ref = db.reference('users')
    user_ref = ref.child(str(chat_id))
    return user_ref.get() is not None

def fetch_user_credentials(chat_id):
    ref = db.reference('users')
    user_ref = ref.child(str(chat_id))
    user_data = user_ref.get()
    if user_data:
        username = user_data.get('username')
        password = user_data.get('password')
        return username, password
    return None, None

if __name__ == '__main__':
    bot = AMIZONE()
    bot.run_telegram_bot("")
    
