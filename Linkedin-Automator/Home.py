import streamlit as st
import os
import pandas as pd 
from pymongo import MongoClient
from langchain_groq import ChatGroq
import json
from dotenv import load_dotenv
from streamlit_oauth import OAuth2Component
import base64, requests
from email.mime.text import MIMEText
import jwt
from urllib.parse import unquote


st.set_page_config(layout="wide", page_title="Applier", initial_sidebar_state="expanded")

load_dotenv() 

mongo = os.getenv('MONGO')
client = MongoClient(mongo)

base_dir = os.path.dirname(__file__)
#file_path_json_prompts = os.path.join(base_dir, "prompts.json")

#prompt = json.load(open(file_path_json_prompts, "r"))

#print(prompt)

#Configuration

AUTHORIZATION_URL = os.getenv("AUTHORIZATION_URL")
TOKEN_URL = os.getenv("TOKEN_URL")
REVOKE_URL = os.getenv("REVOKE_URL")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPE = os.getenv("SCOPE")

supabase_url= os.getenv('supabase_url')
supabase_key= os.getenv("supabase_key")
Grooq_api = os.getenv("GROQ_API_KEY")
public_key = os.getenv("public_key")
secret_key = os.getenv("secret_key")
oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZATION_URL, TOKEN_URL, REVOKE_URL)


jwt_secret_token = os.getenv("JWT_SECRET_KEY")
jwt_algo = "HS256"


query_params = st.query_params
raw_token = query_params.get("token", "")


if isinstance(raw_token, list):
    raw_token = raw_token[0]

decoded_token = unquote(raw_token)
# ---- Streamlit UI ----
if 'token' in query_params:
     token = query_params['token'][0]  # Get first value
     jwt_decode = jwt.decode(decoded_token,jwt_secret_token,algorithms=jwt_algo)
     resume = jwt_decode.get("resume")
     job_data = jwt_decode.get("job")
     token_1 = jwt_decode.get("token")
     token = token_1['access_token']
     st.session_state["token"] = token
     st.write(resume)

if "token" not in st.session_state:
      st.switch_page("Server.py")
        
        
      st.rerun()
else:
    st.toast("✅ Logged in with Gmail")
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    resp = requests.get('https://www.googleapis.com/oauth2/v3/userinfo',headers=headers)
    oauth_data = resp.json()
    st.title(f"Welcome {oauth_data['name']}")
    query_params = st.experimental_get_query_params()

    resume_text = query_params.get('resume', [''])[0]
    job_data = query_params.get('job', [''])[0]

    st.write("Resume Text:", resume_text)
    st.write("Job Data:", job_data)
    #st.write(st.session_state.token)


# No imports needed - Streamlit automatically handles pages in the pages/ folder

    def jobs():
      st.switch_page("pages/Job.py")

    def history():
       st.switch_page("pages/History.py")

    def gmail_automator():
       st.switch_page("pages/Email Work Flow Manager.py")


    file_path_sample = os.path.join(base_dir, "templates", "sample.csv")

    df_sample = pd.read_csv(file_path_sample)

    db = client['The_applier']
    main_db = db['users']




#main_db.insert_many(df_sample.to_dict(orient="records"))







    left_col, right_col = st.columns(2)
    with left_col:

      st.progress(value=0)
      st.divider()