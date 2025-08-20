from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore



app = FastAPI()

jobstores = {
    'default':MemoryJobStore
}

#implement the schedulers 


@app.get("/", response_class=HTMLResponse)
def form():
    return """
    <form action="/update" method="post">
        <label for="job_title">Job Title:</label>
        <input type="text" id="job_title" name="job_title"><br><br>
        <label for="mode">Mode:</label>
        <select id="mode" name="mode">
            <option value="date_posted">Date Posted</option>
            <option value="relevance">Relevance</option>
        </select><br><br>
        <input type="submit" value="Update and Start Scraper">
    </form>
    """

@app.post("/update")
def update(job_title: str = Form(...), mode: str = Form(...)):
    with open("config.env", "w") as f:
        f.write(f"JOB_TITLE={job_title}\nMODE={mode}")
    os.system("pkill -f main.py")
    os.system("nohup python main.py &")
    return {"message": f"Scraper started with {job_title} and mode {mode}"}