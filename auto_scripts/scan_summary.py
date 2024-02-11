import requests
from tqdm import tqdm
import sys
from database_connector import get_collection
from vm_secrets import DEEPINFRA_API_KEY

# set up logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


collection = get_collection()

# Add the noCursorTimeout option to prevent cursor timeout
documents = collection.find(
    {"$expr": {"$and": [{"$ne": ["$summary", None]}, {"$not": ["$summary_scanned"]}]}}
).limit(20)

# Check if the cursor result is None
if len(list(documents)) == 0:
    logger.info("===== No documents found. Exiting the script. =====")
    sys.exit()


for document in tqdm(documents):
    try:
        prompt = (
            "Can you summarize who this athlete is? \n\nContext:\n"
            + document["summary"]
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPINFRA_API_KEY}",
        }

        json_data = {
            "model": "deepinfra/airoboros-70b",
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.2,
            "top_p": 0.2,
        }

        response = requests.post(
            "https://api.deepinfra.com/v1/openai/chat/completions",
            headers=headers,
            json=json_data,
        )
        summary = response.json()["choices"][0]["message"]["content"]

        logger.info("got summary, now updating \n\n =====")

        # Update the summary field
        collection.update_one(
            {"_id": document["_id"]},
            {"$set": {"summary": summary, "summary_scanned": True}},
        )
    except Exception as e:
        # Log the exception
        logger.error("An exception occurred: %s", str(e), exc_info=True)
