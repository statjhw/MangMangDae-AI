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

