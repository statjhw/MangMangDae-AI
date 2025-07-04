from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from config import get_pinecone

import torch

# 지연 로딩을 위한 함수
def get_embeddings():
    return HuggingFaceEmbeddings(
                model_name="intfloat/multilingual-e5-large",
                model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            ) ############ 모델 이름 변경

def get_vector_store():
    embeddings = get_embeddings()
    index = get_pinecone()
    return PineconeVectorStore(index=index, embedding=embeddings)

def retrieve(query: str, top_k: int = 5):
    embeddings = get_embeddings()
    query_vector = embeddings.embed_query(query)

    index = get_pinecone()
    results = index.query(vector=query_vector, top_k=top_k, include_values=False, include_metadata=True)

    distances = [x['score'] for x in results['matches']]
    meta_data_li = [x['metadata'] for x in results['matches']]
    text_data_li = [x['text'] for x in meta_data_li]
    return distances, text_data_li