import requests
from bs4 import BeautifulSoup
from typing import List
import re
from tqdm import tqdm
from ..meta.database_connector import DatabaseConnector

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


collection = DatabaseConnector().get_collection()


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
