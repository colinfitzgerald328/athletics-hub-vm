import requests
import concurrent.futures
from tqdm import tqdm
import time
from datetime import datetime
from ..meta.database_connector import DatabaseConnector

# set up logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_timestamp(date: str) -> float:
    """
    Returns a timestamp from a date string.
    """
    date_format = "%d %b %Y"
    timestamp = datetime.strptime(date, date_format).timestamp()
    return timestamp


def return_results_desc(json_list: list) -> list:
    """
    Returns a list of results sorted by date in descending order.
    """
    for item in json_list:
        date_string = item["date"]
        timestamp = get_timestamp(date_string)
        item["timestamp"] = timestamp
    return sorted(json_list, key=lambda x: x["timestamp"], reverse=True)


def get_athlete_results(athlete_id: str) -> list:
    """
    Returns a list of results for a given athlete.
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Sec-Fetch-Site": "cross-site",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Fetch-Mode": "cors",
        "Origin": "https://worldathletics.org",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
        "Referer": "https://worldathletics.org/",
        "Connection": "keep-alive",
        "Host": "wpgiegzkbrhj5mlsdxnipboepm.appsync-api.eu-west-1.amazonaws.com",
        "Sec-Fetch-Dest": "empty",
        "x-amz-user-agent": "aws-amplify/3.0.2",
        "x-api-key": "da2-juounigq4vhkvg5ac47mezxqge",
    }

    json_data = {
        "operationName": "GetSingleCompetitorResultsDate",
        "variables": {
            "resultsByYearOrderBy": "date",
            "id": int(athlete_id),
        },
        "query": "query GetSingleCompetitorResultsDate($id: Int, $resultsByYearOrderBy: String, $resultsByYear: Int) {\n  getSingleCompetitorResultsDate(id: $id, resultsByYear: $resultsByYear, resultsByYearOrderBy: $resultsByYearOrderBy) {\n    parameters {\n      resultsByYear\n      resultsByYearOrderBy\n      __typename\n    }\n    activeYears\n    resultsByDate {\n      date\n      competition\n      venue\n      indoor\n      disciplineCode\n      disciplineNameUrlSlug\n      typeNameUrlSlug\n      discipline\n      country\n      category\n      race\n      place\n      mark\n      wind\n      notLegal\n      resultScore\n      remark\n      __typename\n    }\n    __typename\n  }\n}\n",
    }

    response = requests.post(
        "https://wpgiegzkbrhj5mlsdxnipboepm.appsync-api.eu-west-1.amazonaws.com/graphql",
        headers=headers,
        json=json_data,
    )

    json_resp = response.json()["data"]["getSingleCompetitorResultsDate"][
        "resultsByDate"
    ]

    sorted_results = return_results_desc(json_resp)
    return sorted_results


collection = DatabaseConnector().get_collection()

documents = collection.find({})


def update_document(document, collection, logger):
    athlete_results = get_athlete_results(document["aaAthleteId"])
    logger.info("got athlete results, now updating DB \n\n =====")
    document["results"] = athlete_results
    collection.update_one(
        {"_id": document["_id"]}, {"$set": {"results": athlete_results}}
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
