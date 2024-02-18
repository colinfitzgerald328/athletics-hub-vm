import os

DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD")
DATABASE_NAME = os.environ.get("DATABASE_NAME")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME")
DATABASE_USERNAME = os.environ.get("DATABASE_USERNAME")


import pymongo


class DatabaseConnector:

    def get_client(self) -> pymongo.MongoClient:
        client = pymongo.MongoClient(
            f"mongodb+srv://{DATABASE_USERNAME}:"
            + DATABASE_PASSWORD
            + f"@{DATABASE_NAME}.tqfgaze.mongodb.net/?retryWrites=true&w=majority"
        )
        return client

    def get_collection(
        self,
        collection_name: str = COLLECTION_NAME,
    ) -> pymongo.collection.Collection:
        client = self.get_client()
        database = client.get_database(DATABASE_NAME)
        collection = database.get_collection(collection_name)
        return collection
