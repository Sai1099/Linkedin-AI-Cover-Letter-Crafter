from scrape import data,login_status
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
import threading



app = FastAPI()


@app.get("/")
def login():
    if login_status:
        return jobs()
    return {"status": False, "message": "Login failed"}

@app.get("/jobs_data")
def jobs():
    return {"status": True, "jobs": data}