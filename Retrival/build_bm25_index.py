import json
import pickle
from rank_bm25 import BM25Okapi

CORPUS_FILE = "../wanted.result.updated.jsonl"  # JSONL 파일 경로
PKL_OUT     = "bm25.pkl"                       # 출력될 피클 파일

docs, meta = [], []
with open(CORPUS_FILE, encoding="utf-8") as f:
    for line in f:
        job = json.loads(line)
        # 1) 필드 추출 (None 방지)
        title  = job.get("title", "") or ""
        detail = job.get("position_detail", "") or ""
        text   = (title + " " + detail).lower()
        # 2) 간단 토큰화 (공백 기준)
        tokens = text.split()
        docs.append(tokens)

        # 3) 메타데이터 통일
        _id         = job.get("url", "")
        meta.append({
            "id":          _id,
            "title":       title,
            "company":     job.get("company_name", ""),
            "description": detail,
            "location":    job.get("location", ""),
            "category":    job.get("job_name", ""),
        })

# 4) BM25 인덱스 생성
bm25 = BM25Okapi(docs)

# 5) 피클로 저장
with open(PKL_OUT, "wb") as out:
    pickle.dump({"bm25": bm25, "meta": meta}, out)
    print("샘플 meta[0]:", meta[0])
print(f"✓ BM25 index built ({len(meta)} docs) → {PKL_OUT}")