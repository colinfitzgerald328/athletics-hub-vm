import requests
from bs4 import BeautifulSoup
from datetime import datetime
from itertools import chain
from tqdm import tqdm
import os
import time 
import pandas as pd
import pymongo

os.environ["DB_PWD"] = "N6BnA4O5nmvEATsl"

def connect_to_db():
    client = pymongo.MongoClient('mongodb+srv://colinfitzgerald:' + os.environ["DB_PWD"] + '@trackathletes.tqfgaze.mongodb.net/?retryWrites=true&w=majority')
    return client

client = connect_to_db()
database = client.get_database('track_athletes')
collection = database.get_collection('athlete_profile_data')

# Add the noCursorTimeout option to prevent cursor timeout
documents = collection.find({"$expr": {"$and": [{"$ne": ["$summary", None]}, {"$not": ["$summary_scanned"]}]}}).limit(20)

for document in tqdm(documents):
    try: 
        prompt = "Can you summarize who this athlete is? \n\nContext:\n" + document["summary"]

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer fra0CxJkQ8wVn6N8bWmDLlQFaNWos0JD',
        }

        json_data = {
            'model': 'deepinfra/airoboros-70b',
            'messages': [
                {
                    'role': 'user',
                    'content': prompt,
                },
            ],
            'temperature': 0.2, 
            'top_p': 0.2
        }

        response = requests.post('https://api.deepinfra.com/v1/openai/chat/completions', headers=headers, json=json_data)
        summary = response.json()["choices"][0]["message"]["content"]

        print("got summary, now updating")
    
        # Update the summary field
        collection.update_one({"_id": document["_id"]}, {"$set": {"summary": summary, "summary_scanned": True}})
    except: 
        print("likely key error on summary for document so passing")
