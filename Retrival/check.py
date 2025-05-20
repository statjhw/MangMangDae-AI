# inspect_ids.py
import os, json, random
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

load_dotenv()

# 1) Pinecone 클라이언트 & 인덱스
pc = Pinecone(
    api_key=os.getenv("PINECONE_API_KEY"),
    environment=os.getenv("PINECONE_ENV"),
)
index = pc.Index(os.getenv("PINECONE_INDEX", "jobs-index"))

# 2) 인덱스 dimension 확인 → 0벡터 생성 (아무거나 OK)
dim = index.describe_index_stats().to_dict()["dimension"]
dummy_vec = [0.0] * dim


# 3) 샘플 query 로 id 10개 확인
res = index.query(vector=dummy_vec, top_k=10, include_metadata=True)
print("\n=== 샘플 id 및 메타 ===")
for m in res["matches"]:
    print(json.dumps({
        "id":        m["id"],
        "title":     m["metadata"].get("title"),
        "source":    m["metadata"].get("source"),
        "text_snip": m["metadata"].get("text","")[:50] + "..."
    }, ensure_ascii=False))

# 4) 특정 URL 이 존재하는지 fetch 로 확인 (원하는 URL 넣기)
URL_TO_CHECK = "https://www.wanted.co.kr/wd/27612"
print("\n=== fetch test ===")
f = index.fetch(ids=[URL_TO_CHECK])
print("found?" , URL_TO_CHECK in f["vectors"])
