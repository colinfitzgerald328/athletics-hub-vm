import os
from pymongo.mongo_client import MongoClient

DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD")
DATABASE_STRING_NAME = os.environ.get("DATABASE_STRING_NAME")
DATABASE_NAME = os.environ.get("DATABASE_NAME")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME")
DATABASE_USERNAME = os.environ.get("DATABASE_USERNAME")


class DatabaseConnector:

    def get_client(self):
        uri = f"mongodb+srv://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_STRING_NAME}.tqfgaze.mongodb.net/?retryWrites=true&w=majority"
        print(uri)
        client = MongoClient(uri)
        return client

    def get_collection(
        self,
        collection_name: str = COLLECTION_NAME,
    ):
        client = self.get_client()
        database = client.get_database(DATABASE_NAME)
        collection = database.get_collection(collection_name)
        return collection
