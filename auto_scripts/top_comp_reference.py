import requests
from bs4 import BeautifulSoup
from datetime import datetime
from itertools import chain
from tqdm import tqdm
import os
import time
import pymongo

os.environ["DB_PWD"] = "N6BnA4O5nmvEATsl"


def connect_to_db():
    client = pymongo.MongoClient(
        "mongodb+srv://colinfitzgerald:"
        + os.environ["DB_PWD"]
        + "@trackathletes.tqfgaze.mongodb.net/?retryWrites=true&w=majority"
    )
    return client


client = connect_to_db()

database = client.get_database("track_athletes")
collection = database.get_collection("athlete_profile_data")

documents = collection.find({"$expr": {"$not": ["$top_competitors_with_reference"]}})

for document in tqdm(documents):
    top_competitors_with_reference = []
    top_competitors = document["top_competitors"]
    if top_competitors:
        if len(top_competitors) > 0:
            for competitor in top_competitors:
                found_reference = None
                projection = {"_id": 0}
                cur = collection.find(
                    {
                        "$expr": {
                            "$eq": [
                                {"$concat": ["$givenName", " ", "$familyName"]},
                                competitor,
                            ]
                        }
                    },
                    projection,
                )
                cursor_results = list(cur)

                if cursor_results:
                    found_reference = cursor_results[0]["aaAthleteId"]

                    top_competitors_with_reference.append(
                        {"athlete_name": competitor, "athlete_id": found_reference}
                    )

    collection.update_one(
        {"_id": document["_id"]},
        {"$set": {"top_competitors_with_reference": top_competitors_with_reference}},
    )
