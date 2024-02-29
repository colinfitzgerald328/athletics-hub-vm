import requests
from datetime import datetime
import concurrent.futures
from typing import List, Dict, Union
from itertools import chain
import os
import time
import pandas as pd
from ..meta.database_connector import DatabaseConnector

# set up logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


import json

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the absolute path to event_mappings.json
file_path = os.path.join(current_dir, "scoring.json")
f = open(file_path)
data = json.load(f)

# scoring system credit goes to https://github.com/GlaivePro/IaafPoints
# he provides details and a json on how to reproduce World Athletics scores for events


def time_string_to_seconds(time_str: str) -> Union[float, str]:
    if not time_str:
        return "N/A"
    try:
        time_parts = time_str.split(":")

        hours = 0
        minutes = 0
        seconds = 0

        if len(time_parts) == 3:
            hours = int(time_parts[0])
            minutes = int(time_parts[1])
            seconds = float(time_parts[2])
        elif len(time_parts) == 2:
            minutes = int(time_parts[0])
            seconds = float(time_parts[1])
        elif len(time_parts) == 1:
            seconds = float(time_str)

        total_seconds = (hours * 3600) + (minutes * 60) + seconds
    except ValueError:
        return "N/A"
    except AttributeError:
        return time_str
    return total_seconds


def get_coefs(gender: str, event: str) -> Union[Dict, None]:
    if gender == "Women's":
        subsection = "f"
    else:
        subsection = "m"
    try:
        return data["outdoor"][subsection][event]
    except KeyError:
        logger.info(f"[get_coefs] a keyerror occurred on {str(gender)} {str(event)}")
        return None


def score_event(gender: str, event: str, time_seconds: float) -> Union[float, str]:
    try:
        coefs = get_coefs(gender, event)
        if not coefs:
            return "N/A"
        points = (
            coefs["conversionFactor"] * (time_seconds + coefs["resultShift"]) ** 2
            + coefs["pointShift"]
        )
    except TypeError:
        logger.info(
            f"[score_event] a type error occurred on {str(gender)} {str(event)} {str(time_seconds)}"
        )
        return "N/A"
    return points


def get_results_for_competition(
    athlete_name: str,
    gender: str,
    discipline_code: str,
    competition_id: int,
    event_id: int,
) -> Union[Dict, None]:
    found_table = None
    # if there is no competition or event id, don't send the request
    # the server will internally error (500)
    if (not competition_id) or (not event_id):
        return None
    tables = pd.read_html(
        f"https://worldathletics.org/competition/calendar-results/results/{competition_id}?eventId={event_id}"
    )
    for table in tables:
        dict_rep = table.to_dict("records")
        if athlete_name in str(dict_rep):
            found_table = dict_rep
    for item in found_table:
        # add the discipline code and gender to be used for scoring
        item["Discipline_Code"] = discipline_code
        item["Gender"] = gender
    return found_table


def get_results_with_codes(athlete_id: str) -> List[Dict[str, str]]:
    headers = {
        "Content-Type": "application/json",
        "Pragma": "no-cache",
        "Accept": "*/*",
        "Sec-Fetch-Site": "cross-site",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Sec-Fetch-Mode": "cors",
        "Origin": "https://worldathletics.org",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
        "Referer": "https://worldathletics.org/",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Host": "7e3hwayfdbdutl4bbgjnmnp5sm.appsync-api.eu-west-1.amazonaws.com",
        "x-amz-user-agent": "aws-amplify/3.0.2",
        "x-api-key": "da2-5vmxql6nfrafzc76a5n2v4vsbm",
    }

    json_data = {
        "operationName": "GetSingleCompetitorResultsDiscipline",
        "variables": {
            "resultsByYearOrderBy": "discipline",
            "id": athlete_id,
        },
        "query": "query GetSingleCompetitorResultsDiscipline($id: Int, $resultsByYearOrderBy: String, $resultsByYear: Int) {\n  getSingleCompetitorResultsDiscipline(id: $id, resultsByYear: $resultsByYear, resultsByYearOrderBy: $resultsByYearOrderBy) {\n    parameters {\n      resultsByYear\n      resultsByYearOrderBy\n      __typename\n    }\n    activeYears\n    resultsByEvent {\n      indoor\n      disciplineCode\n      disciplineNameUrlSlug\n      typeNameUrlSlug\n      discipline\n      withWind\n      results {\n        date\n        competition\n        venue\n        country\n        category\n        race\n        place\n        mark\n        wind\n        notLegal\n        resultScore\n        remark\n        competitionId\n        eventId\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",
    }

    response = requests.post(
        "https://7e3hwayfdbdutl4bbgjnmnp5sm.appsync-api.eu-west-1.amazonaws.com/graphql",
        headers=headers,
        json=json_data,
    )
    data = response.json()["data"]["getSingleCompetitorResultsDiscipline"][
        "resultsByEvent"
    ]
    return data


def get_athlete_results(athlete_id: str) -> List[Dict[str, str]]:
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

    return json_resp


def get_complete_results(athlete_id: str) -> List:
    athlete_results = get_athlete_results(athlete_id)
    results_with_codes = get_results_with_codes(athlete_id)
    for index, result in enumerate(results_with_codes):
        result["disciplineCode"] = athlete_results[index]["disciplineCode"]
    return results_with_codes


def get_compiled_results(athlete_id: str) -> List:
    compiled_results = []
    collection = DatabaseConnector().get_collection()
    athlete = collection.find_one({"aaAthleteId": athlete_id})
    complete_results = get_complete_results(athlete_id)
    capitalized_name = athlete["givenName"] + " " + athlete["familyName"]
    gender = athlete["gender"]
    for item in complete_results:
        competition_results = get_results_for_competition(
            capitalized_name,
            gender,
            item["disciplineCode"],
            item["results"][0]["competitionId"],
            item["results"][0]["eventId"],
        )
        if competition_results:
            compiled_results.append(competition_results)
    return compiled_results


def return_results_dict(compiled_results):
    results_dict = []
    flattened_list = list(chain(*compiled_results))
    for item in flattened_list:
        # don't include relays
        if "," not in item["Name"]:
            results_dict.append(
                {
                    "Name": item["Name"],
                    "Time_Seconds": time_string_to_seconds(item["Mark"]),
                    "Discipline_Code": item["Discipline_Code"],
                    "Score": score_event(
                        item["Gender"],
                        item["Discipline_Code"],
                        time_string_to_seconds(item["Mark"]),
                    ),
                }
            )
    return results_dict


def get_top_competitors(capitalized_name: str, athlete_id: str) -> List[str]:

    compiled_results = get_compiled_results(athlete_id)

    results_dict = return_results_dict(compiled_results)

    df = pd.DataFrame.from_dict(results_dict)

    actual_results = df[df["Time_Seconds"] != "N/A"]
    actual_results = actual_results[actual_results["Score"] != "N/A"]

    avg_score = (
        actual_results.groupby("Name")["Score"]
        .mean()
        .reset_index()
        .sort_values(by="Score", ascending=False)
        .set_index("Name")
    )

    sum_runs = (
        actual_results.groupby("Name")
        .count()
        .sort_values(by="Time_Seconds", ascending=False)
        .reset_index()[["Name", "Time_Seconds"]]
        .rename(columns={"Time_Seconds": "Count"})
        .set_index("Name")
    )

    # join the average score and total times the athlete appears in the results together
    joined = avg_score.join(sum_runs)
    plus_one = joined[joined["Count"] > 1]

    # calculate the weighted average score for each athlete
    plus_one["Weighted_Average"] = joined["Score"] + 5 * joined["Count"]

    if len(plus_one) <= 3:
        joined["Weighted_Average"] = joined["Score"] + 5 * joined["Count"]
        sorted_results = joined.sort_values(by="Weighted_Average", ascending=False)
        sorted_results = sorted_results[sorted_results.index != capitalized_name]
    else:
        # sort by weighted average and filter out athlete
        sorted_results = plus_one.sort_values(by="Weighted_Average", ascending=False)
        sorted_results = sorted_results[sorted_results.index != capitalized_name]
    top_competitors = list(sorted_results.index)[:3]
    return top_competitors


collection = DatabaseConnector().get_collection()

documents = collection.find({})


def update_document(document, collection, logger):
    logger.info("Starting to get top competitors for " + document["full_name"])
    capitalized_name = document["givenName"] + " " + document["familyName"]
    try:
        top_competitors = get_top_competitors(capitalized_name, document["aaAthleteId"])
        logger.info("got top competitors \n\n =====")
        document["top_competitors"] = top_competitors
        collection.update_one(
            {"_id": document["_id"]}, {"$set": {"top_competitors": top_competitors}}
        )
    except Exception as e:
        # Move to the next iteration if an exception occurs
        logger.exception(
            f"[top_competitors] caught exception {str(e)} for athlete {str(capitalized_name)}"
        )
        pass


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
