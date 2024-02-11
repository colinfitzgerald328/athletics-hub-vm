import requests
from bs4 import BeautifulSoup
from typing import List
import re
import pymongo
from tqdm import tqdm
import os
import time
from database_connector import get_collection

# set up logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_subject(string: str) -> str:
    try:
        results = re.findall("\w+-\w+", string)
        if len(results) >= 2:
            return results[1]
        else:
            return None
    except:
        return None


def get_hq_images_for_athlete(query: str, last_name: str) -> List[str]:
    results = []
    candidates = []

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Sec-Fetch-Site": "none",
        # 'Cookie': '_fbp=fb.1.1698026678111.1952040698; _ga=GA1.2.2132144913.1698026678; _ga_DMJJ3WT1SM=GS1.1.1698026677.1.1.1698026761.47.0.0; _gid=GA1.2.1309145392.1698026678; gtm_ppn=category_browse; sp=rps=closed&mf=&ci=av%2Ct%2Crf&es=best&ei=; unisess=bVdrMHpJSFZQczNrbGgrM1p0bEU5TDBnMDZ3b0haWUp5VjJKcVAvYWh6bkxzaDAvMTVYWnZTUlZBUFE4VWI2TDJLN293VTJoWTV5a0dTUjRNUDh3UHc9PS0tbWdFMUFMUGhoam9JMlZPNlBRT2VwQT09--7c432c7cc48f189014a4c7f33978bff4b4cd4192; IR_4202=1698026748113%7C0%7C1698026748113%7C%7C; _gcl_au=1.1.1311169312.1698026678; ELOQUA=GUID=F9CE87CA12D74638990D74DC0F0619F0; IR_gbd=gettyimages.com; giu=nv=8&lv=2023-10-23T02%3A04%3A35Z; uac=t=EXim5%2F6cRRQ9NKLvRaGslqzbZvOGv9dSFpGj%2F0aPQ7yqRfb028x0QCfQNyPyrmUe9Nu7H9h0130gNyTkl9BVigi%2FTBU%2BMIJJtxdub3W6uoLHVxZ%2F66dNFB8LpdW%2BnzBkD6F3MHOOpfEG8g1KAIbtQxIXMcec6oGiIe4kRk3g4Ww%3D%7C77u%2FR2pjWUxiYVJqSTV5MWpvRlJ5TDUKMTAwCgpOR1lYR0E9PQpQRzBYR0E9PQowCgoKMAoxMDAKNTg3NklBPT0KMTAwCjAKM2E1OGE4NDItODE2OS00OGZlLTkzMDMtMzcwMTYyZmQ5ZDM4Cgo%3D%7C3%7C4%7C1&d; vis=vid=3a58a842-8169-48fe-9303-370162fd9d38; csrf=t=A2I%2BYvHyWi2x0PwNaTpbFaiMv%2BNusXkW4femP3HxO7A%3D; mc=3',
        # 'Accept-Encoding': 'gzip, deflate, br',
        "Sec-Fetch-Mode": "navigate",
        "Host": "www.gettyimages.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Fetch-Dest": "document",
        "Connection": "keep-alive",
    }

    params = {
        "family": "editorial",
        "assettype": "image",
        "sort": "best",
    }

    response = requests.get(
        f"https://www.gettyimages.com/photos/{query}", params=params, headers=headers
    )
    response_text = response.text
    soup = BeautifulSoup(response_text, "html.parser")
    imgs = soup.find_all("img")
    for img in imgs:
        if "https" in img["src"]:
            results.append(img["src"])
    if results:
        for result in results:
            subject = extract_subject(result)
            if last_name in subject and "medical" not in result:
                candidates.append(result)
    if not candidates:
        return None
    return candidates


collection = get_collection()


documents = collection.find(
    {"$expr": {"$and": [{"$not": ["$hq_images"]}, {"$ne": ["$wikipedia_url", None]}]}}
)

for document in tqdm(documents):
    full_name = document["givenName"] + " " + document["familyName"]
    last_name = document["familyName"].lower()
    images_list = get_hq_images_for_athlete(full_name + " track and field", last_name)
    if images_list:
        document["hq_images"] = images_list

        # Update the document in the MongoDB collection
        collection.update_one(
            {"_id": document["_id"]}, {"$set": {"hq_images": images_list}}
        )
        print("image list update successful")
