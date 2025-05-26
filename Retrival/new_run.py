# new_run.py
#!/usr/bin/env python3
"""
가짜 유저 프로필 + 질문 JSON 파일을 읽어 Pinecone에서 Dense 검색을 수행 후
상위 N개 결과의 ID, 직무, 회사, 유사도, 원문 스니펫을 출력

사용법:
  1. .env 파일에 PINECONE_API_KEY, PINECONE_ENV, PINECONE_INDEX 설정
  2. pip install pinecone-client sentence-transformers python-dotenv
  3. python new_run.py path/to/user_01.json [--top_k N]
  현재는 ../fake/fake_user/user_01.json으로 뽑으면 됨
  Top-k 기본값은 5
"""
import os
import re
import json
import argparse
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer


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
    load_dotenv()
    api_key    = os.getenv("PINECONE_API_KEY")
    env        = os.getenv("PINECONE_ENV")
    index_name = os.getenv("PINECONE_INDEX")

    parser = argparse.ArgumentParser(description="Dense Retriever for job recommendations")
    parser.add_argument("user_json", help="Path to fake user JSON file")
    parser.add_argument("--top_k", type=int, default=5, help="Number of top results to return")
    args = parser.parse_args()

    # Pinecone init
    pc    = Pinecone(api_key=api_key, environment=env)
    index = pc.Index(index_name)

    # Embedding model
    model = SentenceTransformer("intfloat/multilingual-e5-large-instruct")

    # Load user data
    with open(args.user_json, encoding="utf-8") as f:
        user = json.load(f)

    full_query = build_full_query(user)
    if not full_query:
        print("Error: conversation and profile fields are empty.")
        return
    prefix_query = f"[Query] {full_query}"

    # Embed and retrieve
    query_vec = model.encode(prefix_query, normalize_embeddings=True).tolist()
    res = index.query(
        vector=query_vec,
        top_k=args.top_k,
        include_metadata=True,
        metric="cosine"
    )

    # Print results: ID | 직무 | 회사 | Score | 스니펫
    print(f"\n=== TOP-{args.top_k} DENSE RESULTS for Query: '{full_query}' ===\n")
    for idx, match in enumerate(res.get("matches", []), start=1):
        job_id = match.get("id")
        text_full = match.get("metadata", {}).get("text", "")
        # extract 직무, 회사
        m = re.search(r"직무:\s*([^\n]+?)\s+회사:\s*([^\n]+)", text_full)
        role = m.group(1).strip() if m else "(Unknown)"
        comp = m.group(2).strip() if m else "(Unknown)"
        score = match.get("score", 0)
        # extract URL from the end of the document text
        u = re.search(r"채용공고 URL:\s*(https?://\S+)", text_full)
        job_url = u.group(1) if u else "(No URL)"
        # prepare snippet: remove prefix lines
        snippet = text_full
        snippet = re.sub(r"\[document\]\s*", "", snippet)
        snippet = re.sub(r"직무:[^\n]+", "", snippet)
        snippet = re.sub(r"회사:[^\n]+", "", snippet)
        snippet = snippet.replace("\n", " ").strip()
        if len(snippet) > 200:
            snippet = snippet[:200] + "..."

        print(f"{idx}. {job_id} | URL: {job_url} | 직무: {role} | 회사: {comp} | Score:{score:.4f}")
        print(f"   {snippet}\n")

if __name__ == "__main__":
    main()
