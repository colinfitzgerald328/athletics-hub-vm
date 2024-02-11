from vm_secrets import DATABASE_PASSWORD
import pymongo


def connect_to_db() -> pymongo.MongoClient:
    client = pymongo.MongoClient(
        "mongodb+srv://colinfitzgerald:"
        + DATABASE_PASSWORD
        + "@trackathletes.tqfgaze.mongodb.net/?retryWrites=true&w=majority"
    )
    return client


def get_collection():
    client = connect_to_db()
    database = client.get_database("track_athletes")
    collection = database.get_collection("athlete_profile_data")
    return collection
