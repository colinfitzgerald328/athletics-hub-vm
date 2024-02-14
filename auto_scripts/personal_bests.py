import sys

sys.path.append("../")

from datetime import datetime
import requests
import os
from typing import Dict, List
import time
import json
import os
from Meta.database_connector import get_collection, connect_to_db
from Meta.app_secrets import DATABASE_NAME, COLLECTION_NAME

# set up logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the absolute path to event_mappings.json
file_path = os.path.join(current_dir, "event_mappings.json")

f = open(file_path)
event_mappings = json.load(f)


def get_athlete_disciplines_and_gender(aaAthleteId: str) -> Dict[str, str]:
    try:
        client = connect_to_db()
        database = client.get_database(DATABASE_NAME)
        collection = database.get_collection(COLLECTION_NAME)
        athlete = collection.find_one({"aaAthleteId": aaAthleteId})
    finally:
        client.close()
    return {"disciplines": athlete["disciplines"], "gender": athlete["gender"] + "'s"}


def get_mappings(aaAthleteID: str) -> List[str]:
    athlete_info = get_athlete_disciplines_and_gender(str(aaAthleteID))
    split_disciplines = athlete_info["disciplines"].split(", ")
    augmented = [athlete_info["gender"] + " " + i for i in split_disciplines]
    mappings = []
    for i in augmented:
        for e in event_mappings:
            if i == e:
                mappings.append({"event": i, "code": event_mappings.get(e)})
    return mappings


def get_mappings(aaAthleteID: str) -> str:
    athlete_info = get_athlete_disciplines_and_gender(str(aaAthleteID))
    split_disciplines = athlete_info["disciplines"].split(", ")
    augmented = [athlete_info["gender"] + " " + i for i in split_disciplines]
    mappings = []
    for i in augmented:
        for e in event_mappings:
            if i == e:
                mappings.append({"event": i, "code": event_mappings.get(e)})
    return mappings


def get_pb_for_discipline(aaAthleteId: str, discipline: str) -> str:
    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Sec-Fetch-Site": "cross-site",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Fetch-Mode": "cors",
        # 'Accept-Encoding': 'gzip, deflate, br',
        "Origin": "https://worldathletics.org",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
        "Referer": "https://worldathletics.org/",
        # 'Content-Length': '817',
        "Connection": "keep-alive",
        "Host": "wpgiegzkbrhj5mlsdxnipboepm.appsync-api.eu-west-1.amazonaws.com",
        "Sec-Fetch-Dest": "empty",
        "x-amz-user-agent": "aws-amplify/3.0.2",
        "x-api-key": "da2-juounigq4vhkvg5ac47mezxqge",
    }

    json_data = {
        "operationName": "GetSingleCompetitorAllTimePersonalTop10",
        "variables": {
            "allTimePersonalTop10Discipline": discipline,
            "id": aaAthleteId,
        },
        "query": "query GetSingleCompetitorAllTimePersonalTop10($id: Int, $urlSlug: String, $allTimePersonalTop10Discipline: Int) {\n  getSingleCompetitorAllTimePersonalTop10(id: $id, urlSlug: $urlSlug, allTimePersonalTop10Discipline: $allTimePersonalTop10Discipline) {\n    parameters {\n      allTimePersonalTop10Discipline\n      __typename\n    }\n    disciplines {\n      id\n      name\n      __typename\n    }\n    results {\n      discipline\n      date\n      competition\n      country\n      category\n      race\n      place\n      result\n      wind\n      drop\n      withWind\n      withDrop\n      score\n      records\n      remark\n      __typename\n    }\n    __typename\n  }\n}\n",
    }

    response = requests.post(
        "https://wpgiegzkbrhj5mlsdxnipboepm.appsync-api.eu-west-1.amazonaws.com/graphql",
        headers=headers,
        json=json_data,
    )

    results = response.json()["data"]["getSingleCompetitorAllTimePersonalTop10"][
        "results"
    ]
    if len(results) > 0:
        return results[0]
    else:
        return results


def get_pbs_for_athlete(aaAthleteID: str) -> List[str]:
    mappings = get_mappings(aaAthleteID)
    pbs = []
    for mapping in mappings:
        data = get_pb_for_discipline(aaAthleteID, mapping["code"])
        pbs.append(data)
    return pbs


collection = get_collection()

documents = collection.find({})

for document in documents:
    time.sleep(1)
    personal_bests = get_pbs_for_athlete(document["aaAthleteId"])
    logger.info("got personal bests, now updating DB \n\n =====")
    document["personal_bests"] = personal_bests
    collection.update_one(
        {"_id": document["_id"]}, {"$set": {"personal_bests": personal_bests}}
    )
