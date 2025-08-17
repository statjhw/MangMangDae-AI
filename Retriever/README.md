# Retrieval System

하이브리드 검색 시스템 구현 모듈입니다.

## 주요 기능
- Dense 검색 (임베딩 기반)
- Sparse 검색 (BM25)
- 하이브리드 검색 (Dense + Sparse)
- 검색 결과 재순위화

## 구성 요소
- `dense_retriever.py`: 임베딩 기반 검색
- `sparse_retriever.py`: BM25 기반 키워드 검색
- `hybrid_retriever.py`: 하이브리드 검색 구현
- `reranker.py`: Cross-Encoder 기반 재순위화

## 사용 예시
```python
from Retrival.hybrid_retriever import ensemble_retriever
python run_test.py ../fake/fake_user/user_01.json
# 검색 실행
results = ensemble_retriever(
    query="서울 지역 프론트엔드 개발자 채용",
    top_k=5
)
```

## 특징
- Dense와 Sparse 검색 결과의 앙상블
- 검색 결과 캐싱으로 성능 최적화
- Cross-Encoder 기반 정확한 순위 조정 


# python build_bm25_index.py
# → bm25.pkl 생성