import requests
from bs4 import BeautifulSoup
from ..meta.database_connector import DatabaseConnector
from ..meta.ai_services import GoogleGenAIAdaptor

# set up logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_wiki_profile(url: str) -> str:
    resp = requests.get(url).text
    soup = BeautifulSoup(resp, "html.parser")
    p_tags = soup.find_all("p")
    cleaned_p_tags = [item for item in p_tags if not item.get("class")]
    text = " ".join([item.get_text() for item in cleaned_p_tags])
    return text


def summarize_athlete_wikipedia(wiki_url: str) -> str:
    wiki_text = get_wiki_profile(wiki_url)
    prompt = (
        """Summarize the following text. Make sure the summary is pretty long and retains important detail:\n\n """
        + wiki_text
    )

    response = GoogleGenAIAdaptor().generate(prompt)
    return response


collection = DatabaseConnector().get_collection()
# find all documents that have wikipedia URLs
wikipedia_documents = collection.find(
    {
        "$expr": {
            "$and": [
                {"$ne": ["$google_scanned", True]},  # Use $ne instead of $not
                {"$ne": ["$wikipedia_url", None]},
            ]
        }
    }
).limit(20)
for document in wikipedia_documents:
    try:
        new_summary = summarize_athlete_wikipedia(document["wikipedia_url"])
        logger.info("got summary, now updating \n\n =====")
        document["summary"] = new_summary
        collection.update_one(
            {"_id": document["_id"]},
            {"$set": {"summary": document["summary"], "google_scanned": True}},
        )
    except Exception as e:
        # Log the exception
        logger.error("An exception occurred: %s", str(e), exc_info=True)
