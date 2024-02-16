from tqdm import tqdm
import sys
from Meta.database_connector import DatabaseConnector
from Meta.ai_services import DeepInfraAIAdaptor

# set up logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


collection = DatabaseConnector().get_collection()

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
        summary = DeepInfraAIAdaptor().generate(
            "Can you summarize who this athlete is? \n\nContext:\n"
            + document["summary"]
        )

        logger.info("got summary, now updating \n\n =====")

        # Update the summary field
        collection.update_one(
            {"_id": document["_id"]},
            {"$set": {"summary": summary, "summary_scanned": True}},
        )
    except Exception as e:
        # Log the exception
        logger.error("An exception occurred: %s", str(e), exc_info=True)
