import streamlit as st
import pandas as pd
from Home import main_db, db,supabase_url,supabase_key
from supabase import Client, create_client
import requests
from langchain_groq import ChatGroq



st.set_page_config(
    page_title="Email WorkFlow Manager",
    layout="wide",
    initial_sidebar_state="expanded",
       page_icon="📧"  
)


supabase: Client = create_client(
    supabase_url=supabase_url,
    supabase_key=supabase_key
)

if "token" not in st.session_state:
    st.write("Login again Session Token Invalid")
    st.switch_page("Home.py")
else:
    token = st.session_state.token
   
    if "page" not in st.session_state:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        resp = requests.get('https://www.googleapis.com/oauth2/v3/userinfo',headers=headers)
        main_data_oauth = resp.json()
        user_email = main_data_oauth["email"]
        if main_db.find_one({'email': user_email}):
            st.session_state.page = "process"
            st.rerun()
        else:
            st.session_state.page = "upload"
            st.rerun()

    if "processing" not in st.session_state:
        st.session_state.processing = False

    if st.session_state.page == "upload":
        left_col, right_col = st.columns(2)

        with left_col:
           
            header = {"Authorization": f"Bearer {st.session_state.token}"}
            resp = requests.get('https://www.googleapis.com/oauth2/v3/userinfo',headers=header)
            main_data_oauth = resp.json()
            st.title(f"Hey {main_data_oauth['name']} !")
            resume_file = st.file_uploader("Upload Your Resume File:", type=['PDF'], accept_multiple_files=False, label_visibility="visible")
            start_disabled = not (resume_file) or st.session_state.processing

            if st.button("Start Processing", disabled=start_disabled):
                st.session_state.processing = True
                with st.spinner("\u23f3 Processing your resume..."):
                    from compdfkit.client import CPDFClient
                    from compdfkit.enums import CPDFConversionEnum
                    import os
                    import json
                    import ast
                    import random
                    import tempfile
                    import requests
                    import urllib
                    from Home import public_key,secret_key

                    public_key = public_key
                    secret_key = secret_key

                    def pdf_to_text_api(public_key, secret_key, file_path):
                        client = CPDFClient(public_key, secret_key)
                        create_task_result = client.create_task(CPDFConversionEnum.PDF_TO_TXT)
                        task_id = create_task_result.task_id
                        client.upload_file(file_path, task_id)
                        client.execute_task(task_id)
                        task_info = client.get_task_info(task_id)
                        return task_info

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(resume_file.getvalue())
                        tmp_file_path = tmp_file.name

                    text = pdf_to_text_api(public_key, secret_key, tmp_file_path)

                    def upload_pdf(file_path, bucket_name, destination_path):
                        with open(file_path, "rb") as f:
                            pdf_bytes = f.read()
                            response = supabase.storage.from_(bucket_name).upload(destination_path, pdf_bytes, {"content-type": "application/pdf"})
                            public_url = supabase.storage.from_(bucket_name).get_public_url(destination_path)
                            return public_url

                    no = random.randint(0, 1000)
                    file_name = str(main_data_oauth['email'] + '_' + str(no))
                    public_resume_url = upload_pdf(tmp_file_path, "the-applier", f"uploads/{file_name}.pdf")

                    text = str(text)

                    def parsing_text_url(text):
                        start_index = text.find("downloadUrl='") + len("downloadUrl='")
                        end_index = text.find("'", start_index)
                        if start_index != -1 and end_index != -1:
                            url = text[start_index:end_index]
                            return url
                        else:
                            return "Not Found PTT URL"

                    text_file_url = parsing_text_url(text)

                    def get_value_from_download_url(text_file_url):
                        try:
                            response = requests.get(text_file_url)
                            if response.status_code == 200:
                                text_data = response.text.strip()
                                return text_data if text_data else None
                            else:
                                print(f" HTTP Error {response.status_code}")
                                return None
                        except requests.RequestException as e:
                            print(f" Request failed: {e}")
                            return None

                    content = get_value_from_download_url(text_file_url)
                    if content:
                        main_db.insert_one({
                            'email': main_data_oauth['email'],
                            'pdf_url_text': text_file_url,
                            'pdf_download_content': content,
                            'pdf_bucket_file_url': public_resume_url
                        })
                    else:
                        st.warning(" PDF content was empty or download failed.")

                    if main_db.find_one({'email': main_data_oauth['email']}):
                        st.session_state.page = "process"
                        st.rerun()
                    else:
                        st.warning("Parsing Error Occurred")
                        st.session_state.page = "upload"
                        st.session_state.processing = False
                        st.rerun()

        with right_col:
            st.divider()

    elif st.session_state.page == "process":
        st.toast("Resume Parsed Successfully", icon="\u2705")
        st.title("Welcome to the Job Portal")
        left_col, right_col = st.columns(2)

        search_term = st.text_input("Enter Your Desired Job Here:", value="")
        if "applying_in_progress" not in st.session_state:
                st.session_state.applying_in_progress = False
        if search_term:
            condition = f"job_title.ilike.*{search_term}*,role.ilike.*{search_term}*,responsibilities.ilike.*{search_term}*"
            get_searched_data = supabase.table("test_data").select("*").or_(condition).execute()
            get_count_data = supabase.table("test_data").select("*", count="exact", head=True).or_(condition).execute()
            header = {"Authorization": f"Bearer {st.session_state.token}"}
            resp = requests.get('https://www.googleapis.com/oauth2/v3/userinfo',headers=header)
            main_data_oauth = resp.json()
          
            
                
                # Get all sent email history for this user
            get_sent_data = (
                      supabase.table("emails_history")
                      .select("*")
                      .eq("email", main_data_oauth['email'])
                      .eq("status", "SENT")
                      .execute()
                      ).data
 

            data_get_searched = get_searched_data.data


            filtered_jobs = []
            for job in data_get_searched:
                 found_match = False
                 for sent in get_sent_data:

                      if (
                       job.get("job_title") == sent.get("job_title") and
                       job.get("company") == sent.get("company") and
                       job.get("role") == sent.get("role") and
                       main_data_oauth["email"] == sent.get("email") and
                       sent.get("status") == "SENT"
                       ):
                       found_match = True
                       break
                 if not found_match:
                    filtered_jobs.append(job)
              
              
            data_get_searched = filtered_jobs

            #st.write(filtered_jobs)
            
            count_result = len(data_get_searched)



            if data_get_searched:
                st.toast("Data Fetched Successfully")
                st.write(f"Total {count_result} jobs found!")

                get_jobs_number = len(data_get_searched)
                first_half = int(get_jobs_number / 2)
                second_half = get_jobs_number

                lf_col, rl_col = st.columns(2)
                if 'selected_jobs' not in st.session_state:
                      
                      st.session_state.selected_jobs = []
                new_selected_jobs = []


                with lf_col:
                    for i in range(first_half):
                        job = data_get_searched[i]
                        is_selected = job in st.session_state.selected_jobs
                        with st.container(border=True):
                            left_col, right_col = st.columns([1, 6])
                            with left_col:
                                checked = st.checkbox("Select Job",key=f"job_select_{i}",value=is_selected,label_visibility="collapsed")

                             
                            with right_col:
                                st.markdown(f"### {job.get('job_title', 'Unknown')}")
                                st.write(f"**Company:** {job.get('company', 'Unknown')}")
                                st.write(f"**Location:** {job.get('location', 'N/A')}")
                                st.write(f"**Description:** {job.get('responsibilities', 'No details')[:100]}...")
                            if checked:
                                new_selected_jobs.append(job)
                                st.success(f"\u2705 You selected: {job.get('title', 'Job Title')}")

                with rl_col:
                    for i in range(first_half, second_half):
                        job = data_get_searched[i]
                        is_selected = job in st.session_state.selected_jobs
                        with st.container(border=True):
                            left_col, right_col = st.columns([1, 6])
                            with left_col:
                                checked = st.checkbox("Select Job",key=f"job_select_{i}",value=is_selected,label_visibility="collapsed")

                            with right_col:
                                st.markdown(f"### {job.get('job_title', '')}")
                                st.write(f"**Company:** {job.get('company', 'Unknown')}")
                                st.write(f"**Location:** {job.get('location', 'N/A')}")
                                st.write(f"**Description:** {job.get('responsibilities', 'No details')[:100]}...")
                            if checked:
                                new_selected_jobs.append(job)
                                
                                st.success(f"\u2705 You selected: {job.get('title', 'Job Title')}")
                st.session_state.selected_jobs = new_selected_jobs
                applying_btn_disabled = len(st.session_state.selected_jobs) == 0 or st.session_state.applying_in_progress

                if st.session_state.applying_in_progress:
                      st.warning("⏳ Application process in progress... Please wait.")

                applying_btn = st.button("Start Applying" if not st.session_state.applying_in_progress else "Processing Applications...", disabled=applying_btn_disabled)
                if applying_btn:
                      st.session_state.applying_in_progress = True
                      st.session_state.page = "Applying Portal"
                      st.rerun()

    elif st.session_state.page == "Applying Portal":
        
        applying_for_jobs = st.session_state.selected_jobs
        from Home import Grooq_api
        for job in applying_for_jobs:
            def call_llm(prompt, message):
               llm = ChatGroq(
               model="llama-3.1-8b-instant",
               temperature=0,
               api_key=Grooq_api
               )
               messages = [("system", prompt["system"]), ("human", prompt["human"] + ": " + str(message))]
               return llm.invoke(messages)
            job_title = job.get('job_title', 'Unavailable')
            company = job.get('company', 'Unavailable')
            responsibilities = job.get('responsibilities', 'Unavailable')
            skills = job.get('skills', 'Unavailable')
            email = job.get('email', 'Unavailable')
            role = job.get('role', 'Unavailable')
            original_timestamp = job.get('original_timestamp','Unavailable')


            prompt = {
    "system": (
        "You are a professional career consultant specializing in crafting compelling cover letters. "
        "Your task is to write personalized, conversational, and authentic cover letters that sound "
        "like they were written by a real person who is genuinely excited about the opportunity. "
        "IMPORTANT GUIDELINES:\n"
        "- Write in a warm, conversational tone that feels natural and human\n"
        "- Show genuine enthusiasm and passion for the role and company\n"
        "- Match candidate's skills to job requirements when relevant\n"
        "- If skills don't perfectly match, focus on transferable skills and eagerness to learn\n"
        "- Keep paragraphs concise (2-3 sentences max)\n"
        "- Avoid corporate jargon, buzzwords, or overly formal language\n"
        "- No emojis, hashtags, or excessive punctuation\n"
        "- Make it feel like a personal conversation, not a template"
    ),

    "human": (
        "Create a cover letter email in JSON format with 'subject' and 'body' keys.\n\n"
        "SUBJECT LINE: Keep it professional but not overly specific (e.g., 'Application for [Job Title] Position', '[Job Title] Application - [Your Name]', or 'Interest in [Job Title] Role')\n\n"
        "BODY STRUCTURE:\n"
        "1. OPENING: Start with 'Dear Hiring Manager' or 'Dear [Company] Team'\n"
        "2. HOOK (1-2 sentences): Express genuine excitement about the role/company\n"
        "3. RELEVANT EXPERIENCE (2-3 sentences): Highlight matching skills from resume\n"
        "4. VALUE PROPOSITION (1-2 sentences): What you can bring to the role\n"
        "5. ENTHUSIASM & LEARNING (1-2 sentences): Show eagerness, especially if not perfect match\n"
        "6. CLOSING: Simple, warm closing like 'I'd love to chat more about how I can contribute' or 'Looking forward to hearing from you'\n"
        "7. SIGN-OFF: 'Best regards,' or 'Thank you,' followed by name\n\n"
        "TONE REQUIREMENTS:\n"
        "- Sound like you're talking to a friend about an opportunity you're excited about\n"
        "- Use 'I'm' instead of 'I am', 'I'd' instead of 'I would'\n"
        "- Include phrases like 'I'm really excited about...', 'I'd love to...', 'This role sounds perfect because...'\n"
        "- If skills don't match perfectly, say something like 'While I'm still building experience in X, I'm eager to learn and have strong foundation in Y'\n\n"
        "Use these job details: job_title, role, responsibilities, skills, email, company\n"
        "Reference the provided resume text naturally.\n"
        "Output only clean JSON with no extra formatting or commentary."
    )
}


            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            resp = requests.get('https://www.googleapis.com/oauth2/v3/userinfo',headers=headers)
            main_data_oauth = resp.json()
           
            user_email = main_data_oauth["email"]
            
            resume_dta = main_db.find_one({'email':user_email}) 
            resume_text = resume_dta['pdf_download_content']

            msg_prompt = f"this is my job_description {job_title},{company},{responsibilities},{skills},{role} and here is my resume text {resume_text}"
            resume_file_path = resume_dta['pdf_bucket_file_url']
            resp_resume_file = requests.get(resume_file_path)
            if resp_resume_file.status_code == 200:
                 import tempfile

                 with tempfile.NamedTemporaryFile(delete=False,suffix = ".pdf") as tmpp_file:
                     tmpp_file.write(resp_resume_file.content)
                     tempp_file_path = tmpp_file.name
                 
            import json
            import re
            import codecs
            llm_datas = call_llm(prompt,msg_prompt)
            from langchain.schema import AIMessage 
            response_text = llm_datas.content if isinstance(llm_datas, AIMessage) else llm_datas
            cleaned_text = re.sub(r'```json|```', '', response_text)
            cleaned_ll = []
            cleaned_ll.append(cleaned_text)
            print(f"maincode is {cleaned_text}")

            print(cleaned_ll)
            # The string stored in the list:
            json_str = cleaned_ll[0]

# Extract subject
            subject_match = re.search(r'"subject"\s*:\s*"([^"]*)"', json_str)
            subject = subject_match.group(1) if subject_match else ""

# Extract body (including escaped newlines)
            body_match = re.search(r'"body"\s*:\s*"((?:[^"\\]|\\.)*)"', json_str, re.DOTALL)
            body_escaped = body_match.group(1) if body_match else ""

            body = codecs.decode(body_escaped, 'unicode_escape')
         
            
            subject = subject
            body = body
            to = email

            
            def send_email(to, subject, body, file_path, access_token):
                 from email.mime.multipart import MIMEMultipart
                 from email.mime.text import MIMEText
                 from email.mime.application import MIMEApplication
                 import base64
                 import requests
                     # Split text by newline and wrap each line in <p> tags

                    
                 msg = MIMEMultipart()
                 msg['to'] = to
                 msg['Subject'] = subject
                 msg.attach(MIMEText(body.replace('\n', '<br>'), 'html', _charset='utf-8'))


                 with open(file_path, "rb") as file:
                    part = MIMEApplication(file.read(), name="resume.pdf")
                    part['Content-Disposition'] = 'attachment; filename="resume.pdf"'
                    msg.attach(part)

                    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
                    r = requests.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"raw": raw}
    )
                    return r
            import datetime
            import time
            current_time = datetime.datetime.now()
            timestamp = current_time.isoformat()  
            if 'sent_jobs' not in st.session_state:
               st.session_state.sent_jobs = set()

# You can use job index or job_title+company as unique key
            job_key = f"{job_title}_{company}"

            if job_key not in st.session_state.sent_jobs:
               fn = send_email(to, subject, body, tempp_file_path, st.session_state.token)
           
               if fn.status_code == 200:
                  tre = fn.json()
                  status = tre.get("labelIds", ["SENT"])[0]
               else:
                tre = fn.json()
                status = tre.get("labelIds", ["FAILED"])[0]

               data = {
        "email": user_email,
        "msg_subject": subject,
        "job_title": job_title,
        "role": role,
        "company": company,
        "status": status,
        "timestamp_sent": timestamp,
        "original_timestamp": original_timestamp,
        "responsibilities": responsibilities
    }
               data_res = supabase.table("emails_history").insert(data).execute()

               st.session_state.sent_jobs.add(job_key)

    
               with st.container(border=True):
                col1, col2 = st.columns([3, 1])  
                if status == "SENT":
                 with col1:
                   st.subheader(f"Email triggered successfully to {company}")
                   st.subheader(f"Email Send Status: {status}")

                 with col2:
                  st.markdown("**Status**  \n:green[●]")
                else:
                 with col1:
                   st.subheader(f"Email triggered successfully to {company}")
                   st.subheader(f"Email Send Status: {status}")

                 with col2:
                  st.markdown("**Status**  \n:green[●]")
            st.session_state.applying_in_progress = False
        btn = st.button("Back to Job Portal", key="back_button_final")
        if btn:
                st.session_state.sent_jobs = set()
                st.session_state.page = "process"
                st.rerun()