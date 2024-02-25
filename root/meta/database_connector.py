import os
from pymongo.mongo_client import MongoClient

DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_STRING_NAME = os.getenv("DATABASE_STRING_NAME")
DATABASE_NAME = os.getenv("DATABASE_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")


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
