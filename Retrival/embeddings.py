from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from config import get_pinecone

# 지연 로딩을 위한 함수
def get_embeddings():
    return OpenAIEmbeddings(model="text-embedding-3-small")  # Note. dim is 1536 in job-offer index

def get_vector_store():
    embeddings = get_embeddings()
    index = get_pinecone()
    return PineconeVectorStore(index=index, embedding=embeddings)

# 테스트 시 mock 용도로 미리 선언
vector_store = None