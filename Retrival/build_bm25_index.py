#!/usr/bin/env python3
# build_bm25_index.py

import json
import pickle
from konlpy.tag import Okt
from rank_bm25 import BM25Okapi

CORPUS_FILE = "/Users/chanwoo/MangMangDae-AI/wanted.result.updated.jsonl"
PKL_OUT     = "bm25.pkl"

okt = Okt()
seen_urls = set()

def tokenize(text: str):
    return okt.morphs(text, stem=True)

docs, meta = [], []
with open(CORPUS_FILE, encoding="utf-8") as f:
    for line in f:
        job = json.loads(line)
        url = job.get("url")
        if not url or url in seen_urls:
            continue         # 중복이거나 URL이 없으면 skip
        seen_urls.add(url)

        # 텍스트 결합 & 토큰화
        title  = job.get("title", "") or ""
        detail = job.get("position_detail", "") or ""
        desc   = job.get("description", "") or ""
        text   = f"{title} {detail} {desc}"
        tokens = tokenize(text)
        docs.append(tokens)

        # 메타에 URL을 id로 저장
        job["id"] = url
        meta.append(job)

bm25 = BM25Okapi(docs)
with open(PKL_OUT, "wb") as out:
    pickle.dump({"bm25": bm25, "meta": meta}, out)

print(f"✓ BM25 index built ({len(meta)} docs) → {PKL_OUT}")