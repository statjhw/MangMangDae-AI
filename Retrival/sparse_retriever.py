#!/usr/bin/env python3
# sparse_retriever.py

"""
Fake 유저 JSON + BM25.pkl 을 이용해 Sparse 검색(BM25)만 수행하는 스크립트

사용법:
  1. build_bm25_index.py 로 생성된 bm25.pkl 이
     /Users/chanwoo/MangMangDae-AI/Retrival/bm25.pkl 에 존재
  2. pip install konlpy rank_bm25 numpy python-dotenv
    2-1. 이건 만들어 놓은거랑 토큰화 같아야함
  3. python sparse_retriever.py ../fake/fake_user/user_01.json --top_k 5
"""

import os
import re
import json
import argparse
import pickle
import numpy as np
from konlpy.tag import Okt

OKT = Okt()

def tokenize(text: str):
    # 형태소 단위로 토큰화
    return OKT.morphs(text, stem=True)

def build_full_query(user: dict) -> str:
    conv   = user.get("conversation", "").strip()
    edu    = user.get("education", {})
    level  = edu.get("level")
    major  = edu.get("major")
    car    = user.get("career", {})
    years  = car.get("years")
    cat    = car.get("job_category")
    skills = user.get("skills", {}).get("tech_stack", [])
    salary = user.get("preferences", {}).get("desired_salary")

    parts = [conv]
    if level or major:
        parts.append(f"학력:{level or ''}({major or ''})".strip("():"))
    if years is not None or cat:
        parts.append(f"{years or ''}년차 {cat or ''}".strip())
    if skills:
        parts.append("기술:" + ", ".join(skills))
    if salary:
        parts.append(f"희망연봉:{salary}")
    return " | ".join(parts)

def main():
    parser = argparse.ArgumentParser(description="Sparse(BM25) Retriever")
    parser.add_argument("user_json", help="fake_user JSON 경로")
    parser.add_argument("--top_k", type=int, default=5, help="상위 k개 리턴")
    args = parser.parse_args()

    # 1) 사용자 파일 로드
    with open(args.user_json, encoding="utf-8") as f:
        user = json.load(f)

    full_query = build_full_query(user)
    if not full_query:
        print("Error: conversation 필드가 비어 있습니다.")
        return

    # 2) BM25 피클 로드
    PKL_PATH = "/Users/chanwoo/MangMangDae-AI/Retrival/bm25.pkl"
    with open(PKL_PATH, "rb") as f:
        data = pickle.load(f)
    bm25, meta = data["bm25"], data["meta"]

    # 3) 토큰화 및 점수 계산
    tokens = tokenize(full_query)
    scores = bm25.get_scores(tokens)
    idxs   = np.argsort(scores)[::-1][: args.top_k]

    print(f"\n=== TOP-{args.top_k} SPARSE RESULTS for Query: '{full_query}' ===\n")
    for rank, i in enumerate(idxs, start=1):
        sc = float(scores[i])
        if sc <= 0:
            continue
        doc = meta[i]
        text_full = doc.get("text") or doc.get("description","") or ""
        # 직무/회사 뽑기
        m = re.search(r"직무:\s*([^\n]+?)\s+회사:\s*([^\n]+)", text_full)
        role = m.group(1).strip() if m else "(Unknown)"
        comp = m.group(2).strip() if m else "(Unknown)"
        # URL 추출
        u = re.search(r"채용공고 URL:\s*(https?://\S+)", text_full)
        url = u.group(1) if u else doc.get("id","(No URL)")
        # 스니펫
        snippet = text_full.replace("\n"," ")
        snippet = re.sub(r"\[document\]\s*","", snippet)
        snippet = re.sub(r"직무:[^\n]+","", snippet)
        snippet = re.sub(r"회사:[^\n]+","", snippet).strip()
        if len(snippet)>200:
            snippet = snippet[:200] + "..."

        print(f"{rank}. {url} | 직무:{role} | 회사:{comp} | Score:{sc:.4f}")
        print(f"   {snippet}\n")

if __name__ == "__main__":
    main()