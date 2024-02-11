from vm_secrets import DATABASE_PASSWORD, DATABASE_NAME, COLLECTION_NAME, DATABASE_USERNAME
import pymongo


def connect_to_db() -> pymongo.MongoClient:
    client = pymongo.MongoClient(
        f"mongodb+srv://{DATABASE_USERNAME}:"
        + DATABASE_PASSWORD
        + f"@{DATABASE_NAME}.tqfgaze.mongodb.net/?retryWrites=true&w=majority"
    )
    return client


def get_collection():
    client = connect_to_db()
    database = client.get_database(DATABASE_NAME)
    collection = database.get_collection(COLLECTION_NAME)
    return collection
