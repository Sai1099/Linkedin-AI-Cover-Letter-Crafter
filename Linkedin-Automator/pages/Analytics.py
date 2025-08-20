import streamlit as st
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import pandas as pd
from pymongo import MongoClient
from pandasql import sqldf
from supabase import create_client,Client

st.set_page_config(page_title="Jobs",layout="wide",initial_sidebar_state="expanded",page_icon="🧑‍💻")




if "token" not in st.session_state:
    st.warning("Please Login")
    st.switch_page("home.py")
else:
    st.title("Page is under Construction")


