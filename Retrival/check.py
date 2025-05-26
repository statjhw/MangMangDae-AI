# peek_pinecone.py
import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

# 1) Pinecone 클라이언트 & 인덱스 오픈
pc    = Pinecone(api_key=os.getenv("PINECONE_API_KEY"),
                 environment=os.getenv("PINECONE_ENV"))
index = pc.Index(os.getenv("PINECONE_INDEX", "jobs-index"))

# 2) 인덱스 차원 확인 → 0벡터 생성
stats    = index.describe_index_stats().to_dict()
dim      = stats["dimension"]
zero_vec = [0.0] * dim

# 3) 0벡터로 top-5 조회 (include_metadata=True 로 메타도 가져옴)
res = index.query(vector=zero_vec, top_k=5, include_metadata=True)

# 4) id와 메타 출력
print("=== Pinecone head 5 ===")
for m in res["matches"]:
    print(f"id: {m['id']}")
    print(" metadata:", m["metadata"])
    print(" score:", m["score"])
    print("---")