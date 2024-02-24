from tqdm import tqdm
import concurrent.futures
from ..meta.database_connector import DatabaseConnector

collection = DatabaseConnector().get_collection()

documents = collection.find({"$expr": "$top_competitors"})

# set up logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_document(document, collection, logger):
    top_competitors_with_reference = []
    top_competitors = document["top_competitors"]
    if top_competitors and len(top_competitors) > 0:
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
    logger.info("now updating")
    collection.update_one(
        {"_id": document["_id"]},
        {"$set": {"top_competitors_with_reference": top_competitors_with_reference}},
    )


def process_documents(documents, collection, logger):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for document in documents:
            futures.append(
                executor.submit(update_document, document, collection, logger)
            )

        # Wait for all futures to complete
        for future in concurrent.futures.as_completed(futures):
            pass


process_documents(documents, collection, logger)
