import streamlit as st  # core package used in this project
import pandas as pd
import base64, random
import time, datetime
import pymysql
import os
import socket
import platform
import geocoder
import secrets
import io, random
import plotly.express as px  # to create visualisations at the admin session
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
# libraries used to parse the pdf files
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.svm import SVC

from streamlit_tags import st_tags
from PIL import Image
# pre stored data for prediction purposes
from Courses import ds_course, web_course, android_course, ios_course, uiux_course, resume_videos, interview_videos
import nltk

nltk.download('stopwords')


###### Preprocessing functions ######


# Generates a link allowing the data in a given panda dataframe to be downloaded in csv format 
def get_csv_download_link(df, filename, text):
    csv = df.to_csv(index=False)
    ## bytes conversions
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


# Reads Pdf file and check_extractable
def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    ## close open handles
    converter.close()
    fake_file_handle.close()
    return text


# show uploaded file path to view pdf_display
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


# course recommendations which has data already loaded from Courses.py
def course_recommender(course_list):
    st.subheader("**Courses & Certificates Recommendations 👨‍🎓**")
    c = 0
    rec_course = []
    ## slider to choose from range 1-10
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 5)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course


###### Database Stuffs ######


# sql connector
connection = pymysql.connect(host='localhost', user='root', password='', db='cv')
cursor = connection.cursor()

###### Setting Page Configuration (favicon, Logo, Title) ######


st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon='./Logo/recommend.png',
)


###### Main function run() ######

def run():
    st.sidebar.markdown("# Choose Something...")
    activities = ["User", "Feedback", "About", "Job Role Predictor"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    link = '<b><a href="https://dnoobnerd.netlify.app/" style="text-decoration: none; color: #021659;"></a></b>'
    st.sidebar.markdown(link, unsafe_allow_html=True)
    st.sidebar.markdown('''
        <!-- site visitors -->

        <div id="sfct2xghr8ak6lfqt3kgru233378jya38dy" hidden></div>

        <noscript>
            <a href="https://www.freecounterstat.com" title="hit counter">
                <img src="https://counter9.stat.ovh/private/freecounterstat.php?c=t2xghr8ak6lfqt3kgru233378jya38dy" border="0" title="hit counter" alt="hit counter"> -->
            </a>
        </noscript>
    
        <p>Visitors <img src="https://counter9.stat.ovh/private/freecounterstat.php?c=t2xghr8ak6lfqt3kgru233378jya38dy" title="Free Counter" Alt="web counter" width="60px"  border="0" /></p>
    
    ''', unsafe_allow_html=True)

    ###### Creating Database and Table ######

    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS CV;"""
    cursor.execute(db_sql)

    DBf_table_name = 'user_feedback'
    tablef_sql = "CREATE TABLE IF NOT EXISTS " + DBf_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                        feed_name varchar(50) NOT NULL,
                        feed_email VARCHAR(50) NOT NULL,
                        feed_score VARCHAR(5) NOT NULL,
                        comments VARCHAR(100) NULL,
                        Timestamp VARCHAR(50) NOT NULL,
                        PRIMARY KEY (ID)
                    );
                """
    cursor.execute(tablef_sql)

    ###### CODE FOR CLIENT SIDE (USER) ######

    if choice == 'User':
        st.title("ResuProb"
                 "")
        st.image('Logo\ResuProb.png', caption='', width=300)
        # Collecting Miscellaneous Information
        # act_name = st.text_input('Name*')
        # act_mail = st.text_input('Mail*')
        # act_mob = st.text_input('Mobile Number*')
        sec_token = secrets.token_urlsafe(12)
        host_name = socket.gethostname()
        ip_add = socket.gethostbyname(host_name)
        dev_user = os.getlogin()
        os_name_ver = platform.system() + " " + platform.release()
        g = geocoder.ip('me')
        latlong = g.latlng
        geolocator = Nominatim(user_agent="geoapiExercises")
        location = geolocator.reverse(latlong, language='en')
        address = location.raw['address']
        cityy = address.get('city', '')
        statee = address.get('state', '')
        countryy = address.get('country', '')
        city = cityy
        state = statee
        country = countryy

        # Upload Resume
        st.markdown(
            '''<h5 style='text-align: left; color: #021659;'> Upload Your Resume, And Get Smart Recommendations</h5>''',
            unsafe_allow_html=True)

        ## file upload in pdf format
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            with st.spinner('Hang On While We Cook Magic For You...'):
                time.sleep(4)

            ### saving the uploaded resume to folder
            save_image_path = './Uploaded_Resumes/' + pdf_file.name
            pdf_name = pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)

            ### parsing and extracting whole resume 
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:

                ## Get the whole resume data into resume_text
                resume_text = pdf_reader(save_image_path)

                ## Showing Analyzed data from (resume_data)
                st.header("**Resume Analysis **")
                st.success("Hello " + resume_data['name'])
                st.subheader("**Your Basic info **")
                try:
                    st.text('Name: ' + resume_data['name'])
                    st.text('Email: ' + resume_data['email'])
                    st.text('Contact: ' + resume_data['mobile_number'])
                    st.text('Degree: ' + str(resume_data['degree']))
                    st.text('Resume pages: ' + str(resume_data['no_of_pages']))

                except:
                    pass
                ## Predicting Candidate Experience Level 

                ### Trying with different possibilities
                cand_level = ''
                if resume_data['no_of_pages'] < 1:
                    cand_level = "NA"
                    st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>You are at Fresher level!</h4>''',
                                unsafe_allow_html=True)

                #### if internship then intermediate level
                elif 'INTERNSHIP' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',
                                unsafe_allow_html=True)
                elif 'INTERNSHIPS' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',
                                unsafe_allow_html=True)
                elif 'Internship' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',
                                unsafe_allow_html=True)
                elif 'Internships' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',
                                unsafe_allow_html=True)

                #### if Work Experience/Experience then Experience level
                elif 'EXPERIENCE' in resume_text:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',
                                unsafe_allow_html=True)
                elif 'WORK EXPERIENCE' in resume_text:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',
                                unsafe_allow_html=True)
                elif 'Experience' in resume_text:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',
                                unsafe_allow_html=True)
                elif 'Work Experience' in resume_text:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',
                                unsafe_allow_html=True)
                else:
                    cand_level = "Fresher"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at Fresher level!!''',
                                unsafe_allow_html=True)
                # st.markdown("Skills"+str(resume_data['skills']))
                st.subheader("Here Are The Interview Questions Based On Your Skills")

                skills_dict = {index: skill for index, skill in enumerate(resume_data['skills'])}

                skill_faq_dictionary = {
                    "java": [
                        "What is Java?",
                        "What are the features of Java?",
                        "How do I write a basic Java program?",
                        "What are Java data types?",
                        "What is the difference between JDK and JRE?"
                    ],
                    "c": [
                        "What is C?",
                        "What are the basic data types in C?",
                        "How do I declare and initialize variables in C?",
                        "What are control statements in C?",
                        "How do I use functions in C?"
                    ],
                    "cpp": [
                        "What is C++?",
                        "What are the differences between C and C++?",
                        "How do I write a C++ class?",
                        "What is operator overloading in C++?",
                        "How do I handle exceptions in C++?"
                    ],
                    "c++": [
                        "What is C++?",
                        "What are the differences between C and C++?",
                        "How do I write a C++ class?",
                        "What is operator overloading in C++?",
                        "How do I handle exceptions in C++?"
                    ],
                    "python": [
                        "What is Python?",
                        "What are the benefits of using Python?",
                        "How do I install Python?",
                        "What are some popular Python libraries?",
                        "What is the difference between Python 2 and Python 3?"
                    ],
                    "html": [
                        "What is HTML?",
                        "What are the basic tags in HTML?",
                        "How do I create links in HTML?",
                        "What is the purpose of the <div> tag in HTML?",
                        "What are the different input types in HTML forms?"
                    ],
                    "css": [
                        "What is CSS?",
                        "How do I apply CSS styles to HTML elements?",
                        "What are CSS selectors?",
                        "What is the box model in CSS?",
                        "How do I create responsive layouts with CSS?"
                    ],
                    "javascript": [
                        "What is JavaScript?",
                        "What are the advantages of using JavaScript?",
                        "How do I include JavaScript code in an HTML page?",
                        "What is the DOM (Document Object Model) in JavaScript?",
                        "What are some common JavaScript frameworks?"
                    ],
                    "php": [
                        "What is PHP?",
                        "How do I write PHP code?",
                        "What are PHP variables and data types?",
                        "How do I handle form data in PHP?",
                        "What are PHP sessions and cookies?"
                    ],
                    "mysql": [
                        "What is MySQL?",
                        "How do I create a MySQL database?",
                        "What are SQL queries?",
                        "How do I perform data manipulation in MySQL?",
                        "What is the difference between MySQL and PostgreSQL?"
                    ],
                    "aws": [
                        "What is AWS (Amazon Web Services)?",
                        "How do I create an AWS account?",
                        "What are some common AWS services?",
                        "How do I deploy an application on AWS?",
                        "What is the AWS Lambda function?"
                    ],
                    "mern stack": [
                        "What is the MERN stack?",
                        "How do I set up a MERN stack project?",
                        "What are the components of the MERN stack?",
                        "How do I connect MongoDB with a Node.js application?",
                        "What is the role of React in the MERN stack?"
                    ],
                    "mean stack": [
                        "What is the MEAN stack?",
                        "How do I set up a MEAN stack project?",
                        "What are the components of the MEAN stack?",
                        "How do I perform CRUD operations with MongoDB in a MEAN stack application?",
                        "What is the role of Angular in the MEAN stack?"
                    ],
                    "Flutter": [
                        "What is Flutter?",
                        "How do I set up Flutter?",
                        "What are Flutter widgets?",
                        "How do I handle state in Flutter?",
                        "What is Flutter's hot reload feature?"
                    ],
                    "Android development": [
                        "What is Android development?",
                        "How do I set up an Android development environment?",
                        "What are activities and intents in Android?",
                        "How do I interact with APIs in Android?",
                        "What is the Android App Bundle (AAB) format?"
                    ],
                    "full stack": [
                        "What is full stack development?",
                        "What are the front-end and back-end components in a full stack?",
                        "What technologies are commonly used in full stack development?",
                        "How do I handle data storage and retrieval in a full stack application?",
                        "What are some popular full stack frameworks?"
                    ],
                    "frontend": [
                        "What is front-end development?",
                        "What are HTML, CSS, and JavaScript?",
                        "How do I create responsive web designs?",
                        "What are some popular front-end frameworks?",
                        "How do I optimize front-end performance?"
                    ],
                    "backend": [
                        "What is back-end development?",
                        "What are server-side programming languages?",
                        "How do I handle database operations in the back end?",
                        "What are some common back-end frameworks?",
                        "How do I secure a back-end application?"
                    ],
                    "google cloud": [
                        "What is Google Cloud Platform (GCP)?",
                        "How do I create a project on GCP?",
                        "What are some popular GCP services?",
                        "How do I deploy an application on GCP?",
                        "What is Google Cloud Functions?"
                    ],
                    "salesforce": [
                        "What is Salesforce?",
                        "How do I set up a Salesforce account?",
                        "What are Salesforce objects and fields?",
                        "How do I create custom workflows in Salesforce?",
                        "What is the Apex programming language in Salesforce?"
                    ],
                    "cloud developer": [
                        "What is cloud development?",
                        "What are the benefits of cloud computing?",
                        "How do I deploy applications on the cloud?",
                        "What are some common cloud platforms?",
                        "What are microservices in cloud development?"
                    ],
                    "cyber security": [
                        "What is cyber security?",
                        "What are common types of cyber attacks?",
                        "How do I secure networks and systems?",
                        "What are best practices for protecting data?",
                        "How do I respond to a security breach?"
                    ],
                    "ethical hacking": [
                        "What is ethical hacking?",
                        "How do I become an ethical hacker?",
                        "What are common hacking techniques?",
                        "How do I perform vulnerability assessments?",
                        "What are the legal and ethical considerations in ethical hacking?"
                    ],
                    "Figma": [
                        "What is Figma?",
                        "How do I create designs in Figma?",
                        "What are Figma components?",
                        "How do I collaborate with others in Figma?",
                        "What are some useful shortcuts in Figma?"
                    ],
                    "Git": [
                        "What is Git?",
                        "How do I initialize a Git repository?",
                        "What are the basic Git commands?",
                        "How do I create and switch between Git branches?",
                        "How do I resolve merge conflicts in Git?"
                    ],
                    "React": [
                        "What is React?",
                        "How do I create a React component?",
                        "What is JSX in React?",
                        "How do I handle state in React?",
                        "What are React hooks?"
                    ],
                    "Angular": [
                        "What is Angular?",
                        "How do I set up an Angular project?",
                        "What are Angular directives?",
                        "How do I handle data binding in Angular?",
                        "What is Angular CLI?"
                    ],
                    "Node.js": [
                        "What is Node.js?",
                        "How do I run a Node.js application?",
                        "What is npm (Node Package Manager)?",
                        "How do I handle asynchronous operations in Node.js?",
                        "What are some popular Node.js frameworks?"
                    ],
                    "WordPress": [
                        "What is WordPress?",
                        "How do I install WordPress?",
                        "How do I create a custom WordPress theme?",
                        "What are WordPress plugins?",
                        "How do I optimize WordPress for performance?"
                    ]
                }
                for key1, value1 in skills_dict.items():
                    for key2, value2 in skill_faq_dictionary.items():
                        if value1.lower() == key2.lower():
                            st.write(value2)
                resume_score = 0
                ### Predicting Whether these key points are added to the resume
                if 'Objective' or 'Summary' in resume_text:
                    resume_score = resume_score + 6
                else:
                    st.text('Resume pages: ' + str(resume_data['no_of_pages']))

                if 'Education' or 'School' or 'College' in resume_text:
                    resume_score = resume_score + 12
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'></h4>''', unsafe_allow_html=True)

                if 'EXPERIENCE' in resume_text:
                    resume_score = resume_score + 16
                elif 'Experience' in resume_text:
                    resume_score = resume_score + 16

                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'></h4>''', unsafe_allow_html=True)

                if 'INTERNSHIPS' in resume_text:
                    resume_score = resume_score + 6

                elif 'INTERNSHIP' in resume_text:
                    resume_score = resume_score + 6
                elif 'Internships' in resume_text:
                    resume_score = resume_score + 6

                elif 'Internship' in resume_text:
                    resume_score = resume_score + 6
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'></h4>''', unsafe_allow_html=True)

                if 'SKILLS' in resume_text:
                    resume_score = resume_score + 7

                elif 'SKILL' in resume_text:
                    resume_score = resume_score + 7

                elif 'Skills' in resume_text:
                    resume_score = resume_score + 7

                elif 'Skill' in resume_text:
                    resume_score = resume_score + 7

                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'></h4>''', unsafe_allow_html=True)

                if 'HOBBIES' in resume_text:
                    resume_score = resume_score + 4

                elif 'Hobbies' in resume_text:
                    resume_score = resume_score + 4
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>.</h4>''', unsafe_allow_html=True)

                if 'INTERESTS' in resume_text:
                    resume_score = resume_score + 5

                elif 'Interests' in resume_text:
                    resume_score = resume_score + 5
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'></h4>''', unsafe_allow_html=True)

                if 'ACHIEVEMENTS' in resume_text:
                    resume_score = resume_score + 13

                elif 'Achievements' in resume_text:
                    resume_score = resume_score + 13

                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'></h4>''', unsafe_allow_html=True)

                if 'CERTIFICATIONS' in resume_text:
                    resume_score = resume_score + 12
                elif 'Certifications' in resume_text:
                    resume_score = resume_score + 12

                elif 'Certification' in resume_text:
                    resume_score = resume_score + 12

                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'></h4>''', unsafe_allow_html=True)

                if 'PROJECTS' in resume_text:
                    resume_score = resume_score + 19

                elif 'PROJECT' in resume_text:
                    resume_score = resume_score + 19

                elif 'Projects' in resume_text:
                    resume_score = resume_score + 19

                elif 'Project' in resume_text:
                    resume_score = resume_score + 19

                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'></h4>''', unsafe_allow_html=True)

                st.subheader("Resume Score ")

                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #d73b5c;
                        }
                    </style>""",
                    unsafe_allow_html=True,
                )

                ### Score Bar
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(resume_score):
                    score += 1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)

                ### Score
                st.success('** Your Resume Writing Score: ' + str(score) + '**')
                st.warning("** Note: This score is calculated based on the content that you have in your Resume. **")

                # print(str(sec_token), str(ip_add), (host_name), (dev_user), (os_name_ver), (latlong), (city), (state), (country), (act_name), (act_mail), (act_mob), resume_data['name'], resume_data['email'], str(resume_score), timestamp, str(resume_data['no_of_pages']), reco_field, cand_level, str(resume_data['skills']), str(recommended_skills), str(rec_course), pdf_name)

                ### Getting Current Date and Time
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date + '_' + cur_time)

                ## Calling insert_data to add all the data into user_data
                # insert_data(str(sec_token), str(ip_add), (host_name), (dev_user), (os_name_ver), (latlong), (city), (state), (country), (act_name), (act_mail), (act_mob), resume_data['name'], resume_data['email'], str(resume_score), timestamp, str(resume_data['no_of_pages']), cand_level)

                ## Recommending Resume Writing Video
                st.header("Bonus Video for Resume Writing Tips")
                resume_vid = random.choice(resume_videos)
                st.video(resume_vid)

                ## Recommending Interview Preparation Video
                st.header("Bonus Video for Interview Tips")
                interview_vid = random.choice(interview_videos)
                st.video(interview_vid)

                ## On Successful Result 
                st.balloons()

            else:
                st.error('Something went wrong..')

                ###### CODE FOR FEEDBACK SIDE ######
    elif choice == 'Feedback':

        # timestamp 
        ts = time.time()
        cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        timestamp = str(cur_date + '_' + cur_time)

        # Feedback Form
        with st.form("my_form"):
            st.write("Feedback form")
            feed_name = st.text_input('Name')
            feed_email = st.text_input('Email')
            feed_score = st.slider('Rate Us From 1 - 5', 1, 5)
            comments = st.text_input('Comments')
            Timestamp = timestamp
            submitted = st.form_submit_button("Submit")
            if submitted:
                ## Calling insertf_data to add dat into user feedback
                # insertf_data(feed_name,feed_email,feed_score,comments,Timestamp)
                ## Success Message 
                st.success("Thanks! Your Feedback was recorded.")
                ## On Successful Submit
                st.balloons()

                # query to fetch data from user feedback table
        query = 'select * from user_feedback'
        plotfeed_data = pd.read_sql(query, connection)

        # fetching feed_score from the query and getting the unique values and total value count 
        labels = plotfeed_data.feed_score.unique()
        values = plotfeed_data.feed_score.value_counts()

        # plotting pie chart for user ratings
        st.subheader("**Past User Rating's**")
        fig = px.pie(values=values, names=labels, title="Chart of User Rating Score From 1 - 5",
                     color_discrete_sequence=px.colors.sequential.Aggrnyl)
        st.plotly_chart(fig)

        #  Fetching Comment History
        cursor.execute('select feed_name, comments from user_feedback')
        plfeed_cmt_data = cursor.fetchall()

        st.subheader("**User Comment's**")
        dff = pd.DataFrame(plfeed_cmt_data, columns=['User', 'Comment'])
        st.dataframe(dff, width=1000)


    ###### CODE FOR ABOUT PAGE ######
    elif choice == 'About':

        st.subheader("**About The Tool - ResuProb**")

        st.markdown('''

        <p align='justify'>
            A tool which parses information from a resume using natural language processing and finds the keywords, cluster them onto sectors based on their keywords. And lastly show recommendations, predictions, analytics to the applicant based on keyword matching.
        </p>

        <p align="justify">
            <b>How to use it: -</b> <br/><br/>
            <b>User -</b> <br/>
            In the Side Bar choose yourself as user and fill the required fields and upload your resume in pdf format.<br/>
            Just sit back and relax our tool will do the magic on it's own.<br/><br/>
            <b>Feedback -</b> <br/>
            A place where user can suggest some feedback about the tool.<br/><br/>
            
        </p><br/><br/>

        

        ''', unsafe_allow_html=True)
        st.subheader("Our Team ")
        col1, col2, col3, col4,col5 = st.columns(5)

        # Display an image in each column
        with col1:
            st.image('Asets\shambhu.png', caption='Shambhuraje Deshmukh', width=200)

        with col2:
            st.image('Asets\Akshay.png', caption='Akshay Patil', width=200)

        with col3:
            st.image('Asets\sujay.png' ,caption='Sujay Gaikwad', width=200)

        with col4:
            st.image('Asets\malhar.png',caption='Malhar Gadade', width=200)

        with col5:
            st.image('Asets\Shreyash.png',caption='Shreyash Dhulrao', width=200)
        ###### CODE FOR ADMIN SIDE (ADMIN) ######
    else:
        st.title("ResuProbe")

        # Training data
        skills = ['python', 'java', 'c++', 'html', 'css', 'AWS', 'JavaScript', 'SQL', 'Ruby', 'PHP', 'React', 'Node.js',
                  'Data Science', 'Machine Learning', 'UI/UX Design', 'Mobile App Development', 'Blockchain', 'DevOps',
                  'Big Data', 'Networking', 'Cybersecurity', 'Artificial Intelligence', 'Data Analysis', 'Cloud Computing',
                  'Frontend Frameworks', 'Backend Development', 'Statistical Modeling', 'Natural Language Processing',
                  'Database Management', 'Web Scraping']

        job_posts = ['Python Developer', 'Java Developer', 'C++ Developer', 'Web Designer', 'Frontend Developer',
                     'Cloud Engineer', 'Full Stack Developer', 'Database Administrator', 'Ruby Developer', 'PHP Developer',
                     'React Developer', 'Node.js Developer', 'Data Scientist', 'Machine Learning Engineer', 'UI/UX Designer',
                     'Mobile App Developer', 'Blockchain Developer', 'DevOps Engineer', 'Big Data Engineer', 'Network Engineer',
                     'Cybersecurity Analyst', 'AI Specialist', 'Data Analyst', 'Cloud Architect', 'Frontend Engineer',
                     'Backend Developer', 'Statistical Analyst', 'NLP Engineer', 'Database Administrator', 'Web Scraping Specialist']

        # Training the classifier
        vectorizer = CountVectorizer()
        X = vectorizer.fit_transform(skills)
        y = job_posts
        classifier = SVC()
        classifier.fit(X, y)

        # Streamlit app
        def predict_job(skill):
            X_test = vectorizer.transform([skill])
            prediction = classifier.predict(X_test)
            return prediction[0]

        def main():
            st.subheader("Job Post Prediction Chatbot")
            skill_input = st.text_input("Enter your skill:")

            if st.button("Predict"):
                job_prediction = predict_job(skill_input)
                st.write(f"Predicted job post: {job_prediction}")

        main()


# Calling the main (run()) function to make the whole process run
run()
