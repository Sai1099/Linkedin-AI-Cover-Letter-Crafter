import pandas as pd
from pymongo import MongoClient
from pandasql import sqldf


client = MongoClient('mongodb+srv://sai:sai1099@cluster0.l9c5xyp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')

db = client['Scrapper']
main_db = db['posts']

data = main_db.find({"job_title":"hiring interns"})

df = pd.DataFrame(data)
"""
query = "SELECT timestamp,job_title,mode,mode_tag,results FROM df GROUP BY timestamp;"
queryed_df = sqldf(query)
queryed_df.to_csv("data.csv")
print(queryed_df.head(5))
"""

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

top_new_match = sqldf(Query)


print("Top new latest posts")
print(top_new_latest)


print("Top new matchs posts")
print(top_new_match)



#print(new_df)