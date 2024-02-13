import sys

sys.path.append("../")

import requests
from bs4 import BeautifulSoup
from database_connector import get_collection

# set up logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

collection = get_collection()

import google.generativeai as genai

genai.configure(api_key="AIzaSyDG_j0Cf-71Xf6Uy6RyWaC4ufufaiel7rg")

# Set up the model
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
]


def get_wiki_profile(url: str) -> str:
    resp = requests.get(url).text
    soup = BeautifulSoup(resp, "html.parser")
    p_tags = soup.find_all("p")
    cleaned_p_tags = [item for item in p_tags if not item.get("class")]
    text = " ".join([item.get_text() for item in cleaned_p_tags])
    return text


def summarize_athlete_wikipedia(wiki_url: str) -> str:
    wiki_text = get_wiki_profile(wiki_url)
    model = genai.GenerativeModel(
        model_name="gemini-pro",
        generation_config=generation_config,
        safety_settings=safety_settings,
    )

    prompt_parts = [
        """Summarize the following text. Make sure the summary is pretty long and retains important detail:\n\n """
        + wiki_text
    ]

    response = model.generate_content(prompt_parts)
    return response.text


# find all documents that have wikipedia URLs
documents = wikipedia_documents = collection.find(
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
