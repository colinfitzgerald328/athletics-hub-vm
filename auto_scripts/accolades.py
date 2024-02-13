import sys
sys.path.append("../")

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
from database_connector import get_collection

# set up logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_accomplishments(url_slug):
    accomplishments = []
    resp_text = requests.get(f"https://worldathletics.org/athletes/{url_slug}").text
    page_soup = BeautifulSoup(resp_text, "html.parser")
    accolades = page_soup.find_all(
        "div", class_="profileStatistics_honourSummaryBlock__1qOBV"
    )
    for accolade in accolades:
        accomplishments.append(accolade.get_text())
    return accomplishments


collection = get_collection()

documents = collection.find({})

for document in tqdm(documents):
    url_slug = document["urlSlug"]
    time.sleep(2)
    accomplishments = get_accomplishments(url_slug)
    logger.info("got accomplishments, now updating DB \n\n ======")
    document["accomplishments"] = accomplishments
    collection.update_one(
        {"_id": document["_id"]}, {"$set": {"accomplishments": accomplishments}}
    )
