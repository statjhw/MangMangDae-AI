import os
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from .logger import setup_logger

# 로거 설정
logger = setup_logger(__name__)

load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")


class Pinecone:
    def __init__(self, embedding_model=None):
        self.api_key = PINECONE_API_KEY
        self.index_name = "mmdindex"
        self.embedding = embedding_model
        logger.info(f"Pinecone class initialized. Index name: {self.index_name}")
        self.index = self.get_index()

    def get_index(self):
        logger.info(f"Accessing Pinecone index: {self.index_name}")
        return PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embedding
        ) 