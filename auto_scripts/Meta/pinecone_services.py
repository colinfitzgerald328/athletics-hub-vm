import pinecone
from langchain.embeddings import CohereEmbeddings
import os

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)


class PineconeIndexConnector:
    """Pinecone Index Connector"""

    def get_embedding_client(self):
        embedding_client = CohereEmbeddings(cohere_api_key=COHERE_API_KEY)
        return embedding_client

    def get_index(self):
        index = pinecone.GRPCIndex(PINECONE_INDEX_NAME)
        return index

    def get_max_id(self):
        index = self.get_index()
        current_max_id = index.describe_index_stats()["total_vector_count"]
        return current_max_id

    def get_embeddings(self, query):
        embedding_client = self.get_embedding_client()
        return embedding_client.embed_query(query)
