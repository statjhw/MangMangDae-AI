from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from config import index

embeddings = OpenAIEmbeddings(model="text-embedding-3-small") # Note. dim is 1536 in job-offer index
vector_store = PineconeVectorStore(index=index, embedding=embeddings)