from pymongo import MongoClient
import pandas as pd
from pandasql import sqldf
from dotenv import load_dotenv
import os
import json
import time
from bson import ObjectId
from langchain_groq import ChatGroq
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# MongoDB connection
client = MongoClient(os.getenv('MONGO'))
db = client['Scrapper']
main_db = db['posts']

# Supabase client setup
supabase: Client = create_client(
    supabase_url=os.getenv('SUPABASE_URL'),
    supabase_key=os.getenv('SUPABASE_API_KEY')
)

# Load prompt
base_dir = os.path.dirname(__file__)
file_path_json_prompts = os.path.join(base_dir, "prompts.json")
with open(file_path_json_prompts, "r", encoding="utf-8") as f:
    prompt_data = json.load(f)
prompt = prompt_data["Prompt 1"]

# Custom JSON encoder for ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

# Query and prepare data from MongoDB
data = main_db.find({"job_title": "hiring"})
df = pd.DataFrame(list(data))
df = df.explode('results').rename(columns={'results': 'post_with_time'}).drop_duplicates()
df = df[['post_with_time', 'timestamp', 'mode_tag', 'count', 'mode', 'url', 'job_title']]
df.columns = ['post_with_time', 'TIMESTAMP', 'MODE_TAG', 'Count', 'MODE', 'URL', 'JOB_TITLE']

# Filter relevant posts
filtered_df = sqldf("""
SELECT DISTINCT * FROM df
WHERE TIMESTAMP LIKE '%May 30%'
GROUP BY post_with_time
""")

# Call LLM using Langchain Groq
def call_llm(prompt, message):
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY")
    )
    messages = [("system", prompt["system"]), ("human", prompt["human"] + ": " + str(message))]
    return llm.invoke(messages)

# Parse the LLM response using string ops
def parse_response(response):
    content = str(getattr(response, "content", response)).strip()
    
    # Remove wrapping quotes if present
    if content.startswith("'") and content.endswith("'"):
        content = content[1:-1]
    
    # If it's multiple JSON objects, convert to list
    content = content.strip()
    if content.startswith('{') and content.count('{') > 1:
        content = "[" + content.replace("}\n{", "},\n{") + "]"
    
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, list) else [parsed]
    except json.JSONDecodeError as e:
        print("❌ JSON decoding error:", e)
        print("--- Raw content ---")
        print(content)
        return []

# Main job processing function
def process_job_data():
    entries = filtered_df[['post_with_time', 'TIMESTAMP', 'MODE']].to_dict('records')
    results = []
    
    for i in range(0, len(entries), 3):
        batch = entries[i:i + 3]
        posts = "\n---\n".join([e['post_with_time'] for e in batch])

        response = call_llm(prompt, posts)
        print("\n--- RAW LLM RESPONSE START ---\n")
        print(response)
        print("\n--- RAW LLM RESPONSE END ---\n")

        jobs = parse_response(response)

        for j, job_data in enumerate(jobs):
            if j < len(batch):
                meta = batch[j]
                job_data.update({
                    'original_timestamp': meta['TIMESTAMP'],
                    'mode': meta['MODE'],
                    'processed_timestamp': pd.Timestamp.now().isoformat()
                })

                # Clean and limit keys
                keys = {
                    "job_title", "role", "responsibilities", "skills", "location",
                    "email", "company", "time", "google_form_link", "original_timestamp",
                    "mode", "processed_timestamp"
                }
                cleaned = {k: job_data.get(k, "unavailable") for k in keys}
                supabase.table("all_database").insert(cleaned).execute()
                results.append(cleaned)

        time.sleep(5)
    return results


final_results = process_job_data()
prompt_data["structured_output"] = final_results


with open(file_path_json_prompts, "w", encoding="utf-8") as f:
    json.dump(prompt_data, f, indent=2, ensure_ascii=False, cls=JSONEncoder)

print(f"Done! {len(final_results)} jobs processed.")
