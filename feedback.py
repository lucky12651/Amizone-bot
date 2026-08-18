import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

# Check if the correct number of arguments are provided
if len(sys.argv) != 3:
    print("Usage: python script.py <Username> <Password>")
    sys.exit(1)

Username = sys.argv[1]
Password = sys.argv[2]

try:
    with requests.session() as s:

        # Step 1: Get the initial page to retrieve the token
        r = s.get("https://s.amizone.net/")
        bs = BeautifulSoup(r.content, 'html.parser')
        token = bs.find('input', attrs={'name': '__RequestVerificationToken'})["value"]

        # Step 2: Log in
        login_data = {
            "__RequestVerificationToken": token,
            "_UserName": Username,
            "_QString": "",
            "_Password": Password
        }
        headers = {
            "Referer": "https://s.amizone.net/FacultyFeeback/FacultyFeedback",
        }
        s.headers.update(headers)
        resp = s.post("https://s.amizone.net/", data=login_data)

        if resp.headers.get('Set-Cookie'):
            # Step 3: Get the faculty feedback page
            resp = s.get("https://s.amizone.net/FacultyFeeback/FacultyFeedback")
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Step 4: Iterate over each visible faculty
            for teacher in soup.find_all("li", class_="open"):
                try:
                    link = teacher.find("a", {"class": "btn btn-primary btn-minier"})['href']
                    if link:
                        # Extract URL and parameters
                        url = "https://s.amizone.net" + link
                        resp = s.get(url)
                        faculty_soup = BeautifulSoup(resp.text, 'html.parser')

                        # Extract required values
                        iDetId = faculty_soup.find('input', {'name': 'clsCourseFaculty.iDetId'})['value']
                        iFacultyStaffId = faculty_soup.find('input', {'name': 'clsCourseFaculty.iFacultyStaffId'})['value']
                        iSRNO = faculty_soup.find('input', {'name': 'clsCourseFaculty.iSRNO'})['value']

                        # Get the CSRF token from the new page
                        csrf_token = faculty_soup.find('input', {'name': '__RequestVerificationToken'})['value']

                        # Prepare feedback data
                        feedback = {
                            '__RequestVerificationToken': csrf_token,
                            'CourseType': '1',  # Example value
                            'clsCourseFaculty.iDetId': iDetId,
                            'clsCourseFaculty.iFacultyStaffId': iFacultyStaffId,
                            'clsCourseFaculty.iSRNO': iSRNO,
                            'FeedbackRating_Q1Rating': '1',
                            'FeedbackRating_Q2Rating': '1',
                            'FeedbackRating_Q3Rating': '1',
                            'FeedbackRating_Q5Rating': '1',
                            'FeedbackRating_Comments': 'Good',
                            'X-Requested-With': 'XMLHttpRequest'
                        }

                        # List of aspect IDs
                        aspect_ids = [
                            "1", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14",
                            "15", "18", "28", "22", "23", "24", "25"
                        ]
                        for index, aspect_id in enumerate(aspect_ids):
                            feedback[f'FeedbackRating[{index}].iAspectId'] = aspect_id
                            feedback[f'FeedbackRating[{index}].Rating'] = '5'  # Assigning a rating of 5 to all aspects

                        # Submit feedback
                        feedback_response = s.post("https://s.amizone.net/FacultyFeeback/FacultyFeedback/SaveFeedbackRating", data=feedback)
                        if feedback_response.status_code == 200:
                            print(f"Successfully submitted feedback for {iFacultyStaffId}")
                        else:
                            print(f"Failed to submit feedback for {iFacultyStaffId}")

                except Exception as e:
                    print(f"Error processing faculty: {e}")

            print("success")
except Exception as e:
    print(f"error: {e}")
