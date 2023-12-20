import pymongo
import os 
import requests
import json
import subprocess
from bs4 import BeautifulSoup

# set up logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.environ["DB_PWD"] = "N6BnA4O5nmvEATsl"

# Connect to the MongoDB database
client = pymongo.MongoClient('mongodb+srv://colinfitzgerald:' + os.environ["DB_PWD"] + '@trackathletes.tqfgaze.mongodb.net/?retryWrites=true&w=majority')
database = client.get_database('track_athletes')
collection = database.get_collection('athlete_profile_data')



def get_wiki_profile(url):
    resp = requests.get(url).text
    soup = BeautifulSoup(resp, "html.parser")
    p_tags = soup.find_all("p")
    cleaned_p_tags = [item for item in p_tags if not item.get("class")]
    text = " ".join([item.get_text() for item in cleaned_p_tags])
    return text


def summarize_athlete_wikipedia(wiki_url):
    wiki_text = get_wiki_profile(wiki_url)
    request_data = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": """Summarize the following text. Make sure the summary is pretty long and retains important detail: \n\n""" + wiki_text
                    }
                ]
            }
        ],
        "generation_config": {
            "maxOutputTokens": 2048,
            "temperature": 0.9,
            "topP": 1
        }
    }

    api_endpoint = "us-central1-aiplatform.googleapis.com"
    project_id = "athletics-hub"
    model_id = "gemini-pro"
    location_id = "us-central1"

    # Authenticate and get the access token using gcloud (assuming gcloud is installed and configured)
    access_token = subprocess.run(['gcloud', 'auth', 'print-access-token'], capture_output=True, text=True).stdout.strip()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    url = f"https://{api_endpoint}/v1/projects/{project_id}/locations/{location_id}/publishers/google/models/{model_id}:streamGenerateContent"

    response = requests.post(url, headers=headers, data=json.dumps(request_data))

    data = response.json()
    summary = "".join(item["candidates"][0]["content"]["parts"][0]["text"] for item in data)
    return summary 



# find all documents that have wikipedia URLs
wikipedia_documents = collection.find({"wikipedia_url": {"$ne": None}})
for document in wikipedia_documents: 
    try: 
        new_summary = summarize_athlete_wikipedia(document["wikipedia_url"])
        logger.info("got summary, now updating \n\n =====")
        document["summary"] = new_summary 
        collection.update_one({"_id": document["_id"]}, {"$set": {"summary": document["summary"]}})
    except Exception as e: 
        # Log the exception
        logger.error("An exception occurred: %s", str(e), exc_info=True)
