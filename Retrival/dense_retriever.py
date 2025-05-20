import os
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

MODEL = SentenceTransformer("intfloat/multilingual-e5-large")

def embed_e5(text: str):
    return MODEL.encode("query: " + text, normalize_embeddings=True).tolist()

# Pinecone 클라이언트
pc = Pinecone(
    api_key=os.getenv("PINECONE_API_KEY"),
    environment=os.getenv("PINECONE_ENV"),
)
INDEX = pc.Index(os.getenv("PINECONE_INDEX", "jobs-index"))

def dense_search(text: str, top_k: int = 20):
    vec = embed_e5(text)
    res = INDEX.query(vector=vec, top_k=top_k, include_metadata=False)
    # 메타는 로컬에서 보강하니, id+score만 반환
    return [{"id": m["id"], "score": m["score"]} for m in res["matches"]]