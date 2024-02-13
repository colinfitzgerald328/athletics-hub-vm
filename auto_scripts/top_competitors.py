import sys

sys.path.append("../")

import requests
from datetime import datetime
from itertools import chain
import os
import time
import pandas as pd
from database_connector import get_collection

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


event_mappings = {
    "Women's 100": 10229509,
    "Women's 200": 10229510,
    "Women's 400": 10229511,
    "Women's 800": 10229512,
    "Women's 1500": 10229513,
    "Women's Road Mile": 10229753,
    "Women's 5000": 10229514,
    "Women's 5K Road": 204598,
    "Women's 10K": 10229521,
    "Women's 10RR": 10229537,
    "Women's 100H": 10229522,
    "Women's 400H": 10229523,
    "Women's 3KSC": 10229524,
    "Women's HJ": 10229526,
    "Women's PV": 10229527,
    "Women's LJ": 10229528,
    "Women's TJ": 10229529,
    "Women's SP": 10229530,
    "Women's DT": 10229531,
    "Women's HT": 10229532,
    "Women's JT": 10229533,
    "Women's HMAR": 10229541,
    "Women's MAR": 10229534,
    "Women's 20KR": 10229535,
    "Women's 35KR": 10229989,
    "Women's Heptathlon": 10229536,
    "Women's 4x100": 204594,
    "Women's 4x400": 204596,
    "Men's 100": 10229630,
    "Men's 200": 10229605,
    "Men's 400": 10229631,
    "Men's 800": 10229501,
    "Men's 1500": 10229502,
    "Men's 2000": 10229632,
    "Men's 3000": 10229607,
    "Men's MILE": 10229503,
    "Men's Road Mile": 10229752,
    "Men's 5000": 10229609,
    "Men's 5RR": 204597,
    "Men's 10K": 10229610,
    "Men's 10RR": 10229507,
    "Men's 110H": 10229611,
    "Men's 400H": 10229612,
    "Men's 3KSC": 10229614,
    "Men's HJ": 10229615,
    "Men's PV": 10229616,
    "Men's LJ": 10229617,
    "Men's TJ": 10229618,
    "Men's SP": 10229619,
    "Men's DT": 10229620,
    "Men's HT": 10229621,
    "Men's JT": 10229636,
    "Men's HMAR": 10229633,
    "Men's MAR": 10229634,
    "Men's 20KR": 10229508,
    "Men's 35KR": 10229627,
    "Men's Decathlon": 10229629,
    "Men's 4x1": 204593,
    "Men's 4x4": 204595,
    "Mixed 4x4": 10229988,
}


def get_event_id(gender, discipline_code):
    found_item = None
    formatted_str = gender + " " + discipline_code

    for item in event_mappings:
        if item == formatted_str:
            found_item = event_mappings.get(item)
    return found_item


def convert_date(input_date):
    try:
        date_obj = datetime.strptime(input_date, "%d %b %Y")
        formatted_date = date_obj.strftime("%Y-%m-%d")
        return formatted_date
    except ValueError:
        return "Invalid date format"


def time_string_to_seconds(time_str):
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
    return total_seconds


def get_coefs(gender, event):
    if gender == "Women's":
        subsection = "f"
    else:
        subsection = "m"
    return data["outdoor"][subsection][event]


def score_event(gender, event, time_seconds):
    try:
        coefs = get_coefs(gender, event)
        points = (
            coefs["conversionFactor"] * (time_seconds + coefs["resultShift"]) ** 2
            + coefs["pointShift"]
        )
    except TypeError:
        return "N/A"
    return points


def is_date_between(date_to_check, start_date, end_date):
    try:
        date_to_check = datetime.strptime(date_to_check, "%Y-%m-%d")
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

        return start_date <= date_to_check <= end_date
    except ValueError:
        # Handle invalid date format
        return False


def get_competition_id(competition_name, competition_date):
    formatted_date = convert_date(competition_date)
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
        # 'Content-Length': '3250',
        "Connection": "keep-alive",
        "Host": "wpgiegzkbrhj5mlsdxnipboepm.appsync-api.eu-west-1.amazonaws.com",
        "Sec-Fetch-Dest": "empty",
        "x-amz-user-agent": "aws-amplify/3.0.2",
        "x-api-key": "da2-juounigq4vhkvg5ac47mezxqge",
    }

    json_data = {
        "operationName": "getCalendarEvents",
        "variables": {
            "startDate": None,
            "endDate": None,
            "query": competition_name,
            "regionType": "world",
            "regionId": None,
            "disciplineId": None,
            "rankingCategoryId": None,
            "permitLevelId": None,
            "competitionGroupId": None,
            "competitionSubgroupId": None,
            "limit": 100,
            "offset": 0,
            "showOptionsWithNoHits": False,
            "hideCompetitionsWithNoResults": False,
            "orderDirection": "Ascending",
        },
        "query": "query getCalendarEvents($startDate: String, $endDate: String, $query: String, $regionType: String, $regionId: Int, $currentSeason: Boolean, $disciplineId: Int, $rankingCategoryId: Int, $permitLevelId: Int, $competitionGroupId: Int, $competitionSubgroupId: Int, $competitionGroupSlug: String, $limit: Int, $offset: Int, $showOptionsWithNoHits: Boolean, $hideCompetitionsWithNoResults: Boolean, $orderDirection: OrderDirectionEnum) {\n  getCalendarEvents(startDate: $startDate, endDate: $endDate, query: $query, regionType: $regionType, regionId: $regionId, currentSeason: $currentSeason, disciplineId: $disciplineId, rankingCategoryId: $rankingCategoryId, permitLevelId: $permitLevelId, competitionGroupId: $competitionGroupId, competitionSubgroupId: $competitionSubgroupId, competitionGroupSlug: $competitionGroupSlug, limit: $limit, offset: $offset, showOptionsWithNoHits: $showOptionsWithNoHits, hideCompetitionsWithNoResults: $hideCompetitionsWithNoResults, orderDirection: $orderDirection) {\n    hits\n    paginationPage\n    defaultOffset\n    options {\n      regions {\n        world {\n          id\n          name\n          count\n          __typename\n        }\n        area {\n          id\n          name\n          count\n          __typename\n        }\n        country {\n          id\n          name\n          count\n          __typename\n        }\n        __typename\n      }\n      disciplines {\n        id\n        name\n        count\n        __typename\n      }\n      rankingCategories {\n        id\n        name\n        count\n        __typename\n      }\n      disciplines {\n        id\n        name\n        count\n        __typename\n      }\n      permitLevels {\n        id\n        name\n        count\n        __typename\n      }\n      competitionGroups {\n        id\n        name\n        count\n        __typename\n      }\n      competitionSubgroups {\n        id\n        name\n        count\n        __typename\n      }\n      __typename\n    }\n    parameters {\n      startDate\n      endDate\n      query\n      regionType\n      regionId\n      disciplineId\n      rankingCategoryId\n      permitLevelId\n      competitionGroupId\n      competitionSubgroupId\n      limit\n      offset\n      showOptionsWithNoHits\n      hideCompetitionsWithNoResults\n      __typename\n    }\n    results {\n      id\n      iaafId\n      hasResults\n      hasApiResults\n      hasStartlist\n      name\n      venue\n      area\n      rankingCategory\n      disciplines\n      competitionGroup\n      competitionSubgroup\n      startDate\n      endDate\n      dateRange\n      hasCompetitionInformation\n      undeterminedCompetitionPeriod {\n        status\n        label\n        remark\n        __typename\n      }\n      season\n      wasUrl\n      __typename\n    }\n    __typename\n  }\n}\n",
    }

    response = requests.post(
        "https://wpgiegzkbrhj5mlsdxnipboepm.appsync-api.eu-west-1.amazonaws.com/graphql",
        headers=headers,
        json=json_data,
    )
    found_item = None
    possible_results = response.json()["data"]["getCalendarEvents"]["results"]
    for item in possible_results:
        if is_date_between(formatted_date, item["startDate"], item["endDate"]):
            found_item = item
            break
    return found_item["id"]


def get_results(competition, date, gender, discipline_code):
    time.sleep(1)
    competition_id = get_competition_id(competition, date)
    event_id = get_event_id(gender, discipline_code)

    if not event_id:
        return {"operation": "error", "description": "event not yet supported"}

    else:
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
            # 'Content-Length': '2936',
            "Connection": "keep-alive",
            "Host": "wpgiegzkbrhj5mlsdxnipboepm.appsync-api.eu-west-1.amazonaws.com",
            "Sec-Fetch-Dest": "empty",
            "x-amz-user-agent": "aws-amplify/3.0.2",
            "x-api-key": "da2-juounigq4vhkvg5ac47mezxqge",
        }

        json_data = {
            "operationName": "getCalendarCompetitionResults",
            "variables": {
                "competitionId": competition_id,
                "day": None,
                "eventId": event_id,
            },
            "query": "query getCalendarCompetitionResults($competitionId: Int, $day: Int, $eventId: Int) {\n  getCalendarCompetitionResults(competitionId: $competitionId, day: $day, eventId: $eventId) {\n    competition {\n      dateRange\n      endDate\n      name\n      rankingCategory\n      startDate\n      venue\n      __typename\n    }\n    eventTitles {\n      rankingCategory\n      eventTitle\n      events {\n        event\n        eventId\n        gender\n        isRelay\n        perResultWind\n        withWind\n        summary {\n          competitor {\n            teamMembers {\n              id\n              name\n              iaafId\n              urlSlug\n              __typename\n            }\n            id\n            name\n            iaafId\n            urlSlug\n            birthDate\n            __typename\n          }\n          mark\n          nationality\n          placeInRace\n          placeInRound\n          points\n          raceNumber\n          records\n          wind\n          __typename\n        }\n        races {\n          date\n          day\n          race\n          raceId\n          raceNumber\n          results {\n            competitor {\n              teamMembers {\n                id\n                name\n                iaafId\n                urlSlug\n                __typename\n              }\n              id\n              name\n              iaafId\n              urlSlug\n              birthDate\n              hasProfile\n              __typename\n            }\n            mark\n            nationality\n            place\n            points\n            qualified\n            records\n            wind\n            remark\n            details {\n              event\n              eventId\n              raceNumber\n              mark\n              wind\n              placeInRound\n              placeInRace\n              points\n              overallPoints\n              placeInRoundByPoints\n              overallPlaceByPoints\n              __typename\n            }\n            __typename\n          }\n          startList {\n            competitor {\n              birthDate\n              country\n              id\n              name\n              urlSlug\n              __typename\n            }\n            order\n            pb\n            sb\n            bib\n            __typename\n          }\n          wind\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    options {\n      days {\n        date\n        day\n        __typename\n      }\n      events {\n        gender\n        id\n        name\n        combined\n        __typename\n      }\n      __typename\n    }\n    parameters {\n      competitionId\n      day\n      eventId\n      __typename\n    }\n    __typename\n  }\n}\n",
        }

        response = requests.post(
            "https://wpgiegzkbrhj5mlsdxnipboepm.appsync-api.eu-west-1.amazonaws.com/graphql",
            headers=headers,
            json=json_data,
        )
        race_results = response.json()["data"]["getCalendarCompetitionResults"]
        if race_results is None:
            return {"operation": "error", "description": "failed to get results"}
        else:
            list_results = race_results["eventTitles"][0]["events"][0]["races"][0][
                "results"
            ]
            for result in list_results:
                result["discipline_code"] = discipline_code
                result["gender"] = gender
            return {"operation": "success", "results": list_results}


def get_compiled_results(gender, competitor_results):
    compiled_results = []
    for item in competitor_results:
        try:
            event_results = get_results(
                item["competition"], item["date"], gender, item["disciplineCode"]
            )
        except Exception as e:
            logger.error("An exception occurred: %s", str(e), exc_info=True)
            pass
        if event_results["operation"] == "success":
            compiled_results.append(event_results["results"])
    return compiled_results


def return_results_dict(compiled_results):
    results_dict = []
    flattened_list = list(chain(*compiled_results))
    for item in flattened_list:
        results_dict.append(
            {
                "name": item["competitor"]["name"],
                "time_seconds": time_string_to_seconds(item["mark"]),
                "discipline_code": item["discipline_code"],
                "score": score_event(
                    item["gender"],
                    item["discipline_code"],
                    time_string_to_seconds(item["mark"]),
                ),
            }
        )
    return results_dict


def get_top_competitors(athlete_id):
    time.sleep(1)
    response_data = requests.get(
        f"https://athletics-hub.uc.r.appspot.com/athletes/results?athlete_id={athlete_id}"
    ).json()
    results = response_data["athlete_data"]
    gender = response_data["athlete_gender"]
    name = response_data["athlete_name"]

    compiled_results = get_compiled_results(gender + "'s", results)

    results_dict = return_results_dict(compiled_results)

    df = pd.DataFrame.from_dict(results_dict)

    actual_results = df[df["time_seconds"] != "N/A"]

    avg_score = (
        actual_results.groupby("name")["score"]
        .mean()
        .reset_index()
        .sort_values(by="score", ascending=False)
        .set_index("name")
    )

    sum_runs = (
        actual_results.groupby("name")
        .count()
        .sort_values(by="time_seconds", ascending=False)
        .reset_index()[["name", "time_seconds"]]
        .rename(columns={"time_seconds": "count"})
        .set_index("name")
    )

    # join the average score and total times the athlete appears in the results together
    joined = avg_score.join(sum_runs)
    plus_one = joined[joined["count"] > 1]

    # calculate the weighted average score for each athlete
    plus_one["weighted_average"] = joined["score"] + 5 * joined["count"]

    # sort by weighted average and filter out athlete
    sorted_results = plus_one.sort_values(by="weighted_average", ascending=False)
    sorted_results = sorted_results[sorted_results.index != name]
    top_competitors = list(sorted_results.index)[:3]
    return top_competitors


collection = get_collection()

documents = collection.find({})

for document in documents:
    time.sleep(1)
    top_competitors = get_top_competitors(document["aaAthleteId"])
    logger.info("got top competitors \n\n =====")
    document["top_competitors"] = top_competitors
    collection.update_one(
        {"_id": document["_id"]}, {"$set": {"top_competitors": top_competitors}}
    )
