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


def get_accomplishments(url_slug):
    accomplishments = []
    resp_text = requests.get(
      f"https://worldathletics.org/athletes/{url_slug}").text
    page_soup = BeautifulSoup(resp_text, 'html.parser')
    accolades = page_soup.find_all(
      "div", class_="profileStatistics_honourSummaryBlock__1qOBV")
    for accolade in accolades:
        accomplishments.append(accolade.get_text())
    return accomplishments


client = connect_to_db()

database = client.get_database('track_athletes')
collection = database.get_collection('athlete_profile_data')

documents = collection.find({})

for document in tqdm(documents): 
    url_slug = document["urlSlug"]
    time.sleep(2)
    accomplishments = get_accomplishments(url_slug)
    document["accomplishments"] = accomplishments
    collection.update_one({"_id": document["_id"]}, {"$set": {"accomplishments": accomplishments}})
