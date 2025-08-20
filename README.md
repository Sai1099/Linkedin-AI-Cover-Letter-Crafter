# Linkedin-AI-Cover-Letter-Crafter
A lightweight AI-powered tool that generates personalized cover letters for LinkedIn job postings. Simply provide a job description and your profile/resume, and the tool crafts a professional, tailored cover letter in seconds.

# 🚀 LinkedIn AI Cover Letter & Job Automator

## 📌 Problem Statement
Nowadays, many graduates and students are actively seeking internships and jobs. On average, they spend **1–2 hours per day** applying to multiple jobs in order to secure interview calls.  
This project was born to **automate job applications**, **generate AI-powered cover letters**, and **save time for job seekers**.

---

## 🛠️ Tech Stack
- **Frontend:** Streamlit  
- **Backend:** Python FastAPI  
- **Web Scraping:** Selenium, BeautifulSoup  
- **Databases:** MongoDB, Supabase SQL, Supabase S3  
- **AI & NLP:** Google Gemini, NLTK  
- **Authentication:** Google OAuth  
- **Containerization:** Docker  

---

## ⚙️ Workflow Overview
The project is divided into **4 main modules**:

1. **Scraping & Organizing Data**  
   - Scrapes LinkedIn job posts using **Selenium + BeautifulSoup**.  
   - Two categories scraped:
     - 🔹 *Top Matches*  
     - 🔹 *Latest Jobs*  
   - Scraper runs every **5 minutes** inside Docker to avoid API rate limits.  
   - Raw data is stored in **MongoDB**, then structured using **Gemini + NLTK**, and finally stored in **Supabase SQL** (batch-wise).

---

2. **User Details Upload**  
   - Users upload their **resume (PDF)**.  
   - **PDFPlumber** extracts text → stored in **MongoDB Users DB**.  
   - Original PDF is stored in **Supabase S3**.  
   - Resume data is later used for:
     - Job recommendations  
     - AI-powered cover letter generation  

---

3. **Homepage, OAuth & Dashboard**  
   - Homepage explains project workflow.  
   - Users can preview a **sample cover letter** (with blurred company details).  
   - To send real emails:
     - User logs in via **Google OAuth**.  
     - Authentication is handled using **JWT tokens** + **private key decryption**.  
     - Email is then sent via Gmail API.  
   - **Search Bar**:  
     - Acts like SQL query on **Supabase DB**.  
     - Non-logged-in users → top 3 results only.  
     - Logged-in users → full matching job list.  
   - Selected jobs are stored in a **multi-select list** on the dashboard.  

---

4. **Job Selection, Cover Letter Generation & Emailing**  
   - For each selected job:  
     - Resume text + Job description → sent to **Gemini** with a system prompt.  
     - Gemini generates a **personalized AI cover letter**.  
   - Cover letter + Resume → sent via email in a **for-loop** process.  
   - **History DB** logs all sent emails, allowing users to review past applications.  

---

## 📬 Email Workflow
The email workflow has **3 states**:

1. **Upload** → User uploads resume (PDF).  
2. **Process** → User selects jobs from recommendations/search.  
3. **Generate & Send** → AI creates cover letters and emails recruiters.  

---

## 🏗️ Architecture Summary
1. Scraping jobs → MongoDB → Processed by AI → Supabase SQL  
2. Resume Upload → Extracted Text → MongoDB + PDF → Supabase S3  
3. User Auth → OAuth (JWT + Private Key Decryption) → Gmail Integration  
4. Search & Multi-select Jobs → AI Cover Letter → Email → History DB  

---

## ✅ Features
- 🔹 Automated LinkedIn job scraping  
- 🔹 Resume parsing & structured storage  
- 🔹 AI-powered cover letter generation  
- 🔹 Gmail OAuth integration for secure mail delivery  
- 🔹 Dashboard with job search & history tracking  
- 🔹 Runs on Docker for continuous scraping  

---
