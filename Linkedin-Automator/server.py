from flask import Flask,render_template,redirect,request,jsonify,session
import supabase
from supabase import create_client,Client
from pdfminer.high_level import extract_text
from io import BytesIO
from langchain_groq import ChatGroq
import os
from requests_oauthlib import OAuth2Session
from urllib.parse import urlencode,quote
import json
import base64
import jwt 
import datetime
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.urandom(24) 


#main
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
AUTHORIZATION_URL = os.getenv("AUTHORIZATION_URL")
TOKEN_URL = os.getenv("TOKEN_URL")
REVOKE_URL = os.getenv("REVOKE_URL")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPE = os.getenv("SCOPE")

supabase: Client = create_client(
    supabase_url= os.getenv('supabase_url'),
    supabase_key= os.getenv("supabase_key")
)
@app.route("/",methods=['GET','POST'])
def home():
 
    if request.method == 'POST':
      search_query = request.form.get("search_job_filed")
      items = supabase.table("test_data").select("*").or_(f"job_title.ilike.%{search_query}%,role.ilike.%{search_query}%,responsibilities.ilike.%{search_query}%").limit(3).execute().data

      
      return render_template("index.html",items=items)
    
    return render_template("index.html")

@app.route("/selected_data",methods=['POST'])
def get_data():
    data = request.get_json()
    session['job_data'] = {
        "title": data.get("title"),
        "role": data.get("role"),
        "location": data.get("location"),
        "responsibilities": data.get("responsibilities")
    }

    return jsonify({"status": "received"})

@app.route("/get_current_company", methods=['GET'])
def get_current_company():
    try:
        job_data = session['job_data']
        responsibili = job_data["responsibilities"]
        company_result = supabase.table("test_data").select("company").eq("responsibilities", responsibili).execute()
        
        if company_result.data and len(company_result.data) > 0:
            company_name = company_result.data[0]['company']
            return jsonify({"company": company_name})
        else:
            return jsonify({"company": None})
    except Exception as e:
        print("Error getting company:", str(e))
        return jsonify({"company": None})
@app.route("/upload", methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return "No File Part", 400
    file = request.files['file']
    if file.filename == '':
        return "No file is selected", 400
    if file and file.filename.endswith('.pdf'):
        main_f = BytesIO(file.read())
        extracted_text = extract_text(main_f)
                # Store in session for later use
        from flask import session
        session['extracted_text'] = extracted_text
        # Return JSON response instead of rendering template
        return jsonify({"status": "success", "extracted_text": extracted_text})
    else:
        return jsonify({"status": "error", "message": "Invalid file type. Please upload a PDF."})

@app.route("/generate_cover", methods=['POST'])
def generate_coverletteer():
    print("Generate cover route called!") 
    try:
        from flask import session
        print("Inside try block") 

        if 'extracted_text' not in session:
            return jsonify({"status": "error", "message": "No resume data found. Please upload resume first."}), 400

        if 'job_data' not in session:
            return jsonify({"status": "error", "message": "No job data found. Please apply to a job first."}), 400

        resume_text = session['extracted_text']
        job_data = session['job_data']

        title = job_data["title"]
        responsibilities = job_data["responsibilities"]

        # Get company name based on responsibilities
        main_company = supabase.table("test_data").select("company").eq("responsibilities", responsibilities).execute()

        # Prepare prompt
        jd = f"{title} {responsibilities} {main_company.data}"
        main_message = resume_text + " " + jd

        prompts = {
            "system": "Ensure you are the good writer in writing the emails for jobs based on the description and the resume data so please craft a nice cover letter based on the job and please ensure you please write the cover letter in a humanerized format and makesure use the basic vocubulary so just give me the only cover letter email",
            "human": "please give me the short and simple make sure give me the cover letter data based on the responsibilities and if the resume matches with the responsibilities then combine give in that format if not don't exagerate the resume details"
        }

        llm = ChatGroq(
            model="llama-3.1-8b-instant", 
            temperature=0, 
            api_key=os.getenv("GROQ_API_KEY")
        )

        messages = [
            ("system", prompts["system"]),
            ("human", prompts["human"] + ": " + main_message)
        ]

        response = llm.invoke(messages)
        cover_letter = response.content if hasattr(response, 'content') else str(response)

        return jsonify({"status": "success", "cover_letter": cover_letter})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/login")
def login():
    google = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE)
    authorization_url, state = google.authorization_url(AUTHORIZATION_URL, access_type="offline", prompt="select_account")

    session['oauth_state'] = state

    return redirect(authorization_url)

@app.route("/callback")
def callback():
    state = session.get('oauth_state')  

    if not state:
        return "Missing state. Please start login again.", 400

    google = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, state=state)

    token = google.fetch_token(
        TOKEN_URL,
        client_secret=CLIENT_SECRET,
        authorization_response=request.url
    )

    session['token'] = token

    resume_text = session.get('extracted_text', '')
    job_data = session.get('job_data', '')
    JWT_ALGORITHM = "HS256"
    jwt_payload = {
        'resume': resume_text,
        'job': job_data,
        'token': token,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }

    jwt_token = jwt.encode(jwt_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    fined_jwt_token = quote(jwt_token)

    

    # Now redirect with Base64-encoded data
    return redirect(f"http://localhost:8501/?token={fined_jwt_token}")

