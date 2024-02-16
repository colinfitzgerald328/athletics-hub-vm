from tqdm import tqdm
from Meta.database_connector import DatabaseConnector

collection = DatabaseConnector().get_collection()

documents = collection.find({"$expr": {"$not": ["$top_competitors_with_reference"]}})

for document in tqdm(documents):
    top_competitors_with_reference = []
    top_competitors = document["top_competitors"]
    if top_competitors:
        if len(top_competitors) > 0:
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

    collection.update_one(
        {"_id": document["_id"]},
        {"$set": {"top_competitors_with_reference": top_competitors_with_reference}},
    )
