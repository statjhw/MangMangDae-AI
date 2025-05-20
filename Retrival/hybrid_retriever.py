from functools import lru_cache
from typing import List, Dict
from openai import OpenAI
from sentence_transformers import CrossEncoder
from dense_retriever import dense_search
from sparse_retriever import sparse_search
from job_store import get_meta_by_id

client   = OpenAI()
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device="cpu")

@lru_cache(maxsize=512)
def cache_hyde_document(prompt: str) -> str:
    msg = [{"role":"user","content":f"Write a detailed job post that matches:\n{prompt}"}]
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=msg,
        temperature=0.2
    ).choices[0].message.content

def ensemble_retriever(query: str, top_k: int = 5) -> List[Dict]:
    fake_doc = cache_hyde_document(query)
    dense   = dense_search(fake_doc, 20)
    sparse  = sparse_search(query,   20)

    pool = {}
    for d in dense:
        pool[d["id"]] = {"id":d["id"], "dense":d["score"], "bm25":0}
    for s in sparse:
        itm = pool.get(s["id"], {"id":s["id"], "dense":0})
        itm["bm25"] = s["score"]
        pool[s["id"]] = itm

    max_d = max(v["dense"] for v in pool.values()) or 1
    max_s = max(v["bm25"] for v in pool.values()) or 1
    for v in pool.values():
        v["combo"] = 0.7*(v["dense"]/max_d) + 0.3*(v["bm25"]/max_s)

    prelim = sorted(pool.values(), key=lambda x: x["combo"], reverse=True)[:20]
    # HyDE 文 + 실제 description을 로컬에서 꺼내서 리랭킹
    pairs = [(query, get_meta_by_id(p["id"])["description"]) for p in prelim]
    ranks = reranker.predict(pairs)
    for p, r in zip(prelim, ranks):
        p["rerank"] = r

    final = sorted(prelim, key=lambda x: x["rerank"], reverse=True)[:top_k]
    # 최종엔 로컬 메타데이터 통째로 붙여서 반환
    return [
        {
            **get_meta_by_id(item["id"]),
            "dense":  item["dense"],
            "bm25":   item["bm25"],
            "combo":  item["combo"],
            "rerank": item["rerank"]
        }
        for item in final
    ]