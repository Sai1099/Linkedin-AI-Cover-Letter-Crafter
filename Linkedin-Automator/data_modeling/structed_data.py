from pymongo import MongoClient
import pandas as pd
from pandasql import sqldf
from dotenv import load_dotenv
import os
import torch
from transformers import BertTokenizer, BertForSequenceClassification

# Load env variables
load_dotenv()

# MongoDB setup
mongo = os.getenv('MONGO')
client = MongoClient(mongo)
db = client['Scrapper']
main_db = db['posts']


# Load data
data = main_db.find({"job_title": "hiring interns"})
df = pd.DataFrame(data)
print(df)

# Explode and clean the data
def main_data(df):
    df_exploded = df.explode('results').reset_index(drop=True)
    df_exploded = df_exploded.rename(columns={'results': 'post_with_time'})
    columns = ['post_with_time', 'timestamp', 'mode_tag', 'count', 'mode', 'url', 'job_title']
    df_final = df_exploded[columns]
    df_final.columns = ['post_with_time', 'TIMESTAMP', 'MODE_TAG', 'Count', 'MODE', 'URL', 'JOB_TITLE']
    return df_final

new_df = main_data(df)

# Filter using SQL
Query = "SELECT DISTINCT * FROM new_df WHERE MODE_TAG == 'top_match';"
Query1 = "SELECT DISTINCT * FROM new_df WHERE MODE_TAG == 'latest';"
top_new_latest = sqldf(Query1)
top_new_match = sqldf(Query)

# Save CSVs
top_new_latest.to_csv("latest.csv", index=False)
top_new_match.to_csv("top.csv", index=False)

# -------------------------------
# Load pre-trained BERT classifier
# -------------------------------
model_name = "bhadresh-savani/bert-base-uncased-emotion"  # Placeholder model
tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertForSequenceClassification.from_pretrained(model_name)

label_map = {
    0: "job_title",
    1: "role_responsibilities",
    2: "skills",
    3: "location",
    4: "email",
    5: "company",
    6: "time",
    7: "apply_link"
}

def classify_text(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
    predicted_class_id = torch.argmax(logits, dim=1).item()
    return label_map.get(predicted_class_id, "unavailable")

def extract_structured_data(posts_df):
    structured_data = []
    for _, row in posts_df.iterrows():
        entry = {
            "timestamp": row["TIMESTAMP"],
            "source_url": row["URL"],
            "classified_data": {
                "job_title": "unavailable",
                "role_responsibilities": "unavailable",
                "skills": "unavailable",
                "location": "unavailable",
                "email": "unavailable",
                "company": "unavailable",
                "time": row["TIMESTAMP"] if row["TIMESTAMP"] else "unavailable",
                "apply_link": row["URL"] if row["URL"] else "unavailable"
            }
        }
        sentences = row["post_with_time"].split('\n')
        for sentence in sentences:
            label = classify_text(sentence)
            if entry["classified_data"].get(label) == "unavailable":
                entry["classified_data"][label] = sentence.strip()
            else:
                entry["classified_data"][label] += " " + sentence.strip()
        structured_data.append(entry)
    return structured_data

# Extract and save JSON
classified_output = extract_structured_data(top_new_match)
import json
with open("classified_output.json", "w") as f:
    json.dump(classified_output, f, indent=4)

print("✅ Structured classification complete. Saved to classified_output.json.")
