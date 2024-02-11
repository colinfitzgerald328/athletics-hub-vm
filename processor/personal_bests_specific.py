import requests
import os
import json

import os

current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the absolute path to event_mappings.json
file_path = os.path.join(current_dir, "event_mappings.json")

f = open(file_path)
event_mappings = json.load(f)


def get_mappings(profile):
    split_disciplines = profile["disciplines"].split(", ")
    augmented = [profile["gender"] + "'s " + i for i in split_disciplines]
    mappings = []
    for i in augmented:
        for e in event_mappings:
            if i == e:
                mappings.append({"event": i, "code": event_mappings.get(e)})
    return mappings


def get_pb_for_discipline(aaAthleteId, discipline):
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


def get_pbs_for_athlete(profile):
    mappings = get_mappings(profile)
    pbs = []
    for mapping in mappings:
        data = get_pb_for_discipline(profile["aaAthleteId"], mapping["code"])
        pbs.append(data)
    return pbs
