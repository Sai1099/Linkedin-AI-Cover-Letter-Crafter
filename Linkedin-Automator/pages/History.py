import streamlit as st
from supabase import Client,create_client
import requests


st.set_page_config(page_title="History",layout="wide",initial_sidebar_state="expanded", page_icon="📁")

# Restrict access if user is not logged in
if "token" not in st.session_state:
    st.warning("🔒 You must log in first to access this page.")
    st.switch_page("home.py")  
else:
    
    st.title("History")
    supabase : Client = create_client(supabase_url="https://zfmhkdgxtqakljhwoblk.supabase.co",supabase_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpmbWhrZGd4dHFha2xqaHdvYmxrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0ODUwOTQyOSwiZXhwIjoyMDY0MDg1NDI5fQ.DxYqlrrD3RIW1-g-MdjQ_5nMCentVGb1WT_c4AUyY5E")
    
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    resp = requests.get('https://www.googleapis.com/oauth2/v3/userinfo',headers=headers)
    data = resp.json()

    user_email = data["email"]

    get_sent_emails = supabase.table("emails_history").select("*").eq("email",user_email).execute()
    get_sent_data = get_sent_emails.data
    
    if get_sent_data:
     for data in get_sent_data:
       with st.container(border=True):
        lef_col, rig_col = st.columns([3, 1])  # Define columns inside the loop

        with lef_col:
            st.subheader(data["job_title"])
            st.write(data["msg_subject"])
            st.write(data["company"])
            st.write(f"Status: **{data['status']}**")

        with rig_col:
            if data["status"] == "SENT":
                st.markdown("**Status**  \n:green[●]")
            else:
               st.markdown("**Status**  \n:red[●]")
    else:
       st.write("No Email Job History Found.")

