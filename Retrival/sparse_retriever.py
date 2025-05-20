import pickle
import numpy as np

with open("bm25.pkl", "rb") as f:
    data = pickle.load(f)
BM25, META = data["bm25"], data["meta"]

def sparse_search(text: str, top_k: int = 20):
    tokens = text.lower().split()
    scores = BM25.get_scores(tokens)
    idx = np.argsort(scores)[::-1][:top_k]
    # id+score만 반환
    return [{"id": META[i]["id"], "score": float(scores[i])}
            for i in idx if scores[i] > 0]