from pymongo import MongoClient
import pandas as pd
from pandasql import sqldf
from dotenv import load_dotenv
import os

load_dotenv()

mongo = os.getenv('MONGO')
client = MongoClient(mongo)
db = client['Email']
main_db = db['Sample_csv']



data = main_db.find({"job_title":"hiring interns"})

df = pd.DataFrame(data)


def main_data(df):
   df_exploded = df.explode('results').reset_index(drop=True)
   df_exploded   = df_exploded.rename(columns={'results':'post_with_time'})
   columns = ['post_with_time', 'timestamp', 'mode_tag', 'count', 'mode', 'url', 'job_title']
   df_final = df_exploded[columns]
   df_final.columns = ['post_with_time', 'TIMESTAMP', 'MODE_TAG', 'Count', 'MODE', 'URL', 'JOB_TITLE']
   return df_final
           
           #new_df = pd.DataFrame({'post_time':r,'TIMESTAMP': df['timestamp'],'Mode':df['mode_tag']})
new_df =main_data(df)


Query = "SELECT DISTINCT * FROM new_df WHERE MODE_TAG == 'top_match';"

Query1 = "SELECT DISTINCT * FROM new_df WHERE MODE_TAG == 'latest';"



top_new_latest = sqldf(Query1)
top_new_latest.to_csv("latest.csv")

top_new_match = sqldf(Query)

top_new_match.to_csv("top.csv")
