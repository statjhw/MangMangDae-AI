import os
import sys
import torch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.opensearch import OpenSearchDB
from langchain_huggingface import HuggingFaceEmbeddings

# 전역 임베딩 모델 (한 번만 초기화)
_embedding_model = None

def get_embedding_model():
    """임베딩 모델을 초기화하고 반환합니다 (싱글톤 패턴)"""
    global _embedding_model
    if _embedding_model is None:
        print("Initializing embedding model for hybrid search...")
        _embedding_model = HuggingFaceEmbeddings(
            model_name="intfloat/multilingual-e5-large",
            model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print(f"✅ Embedding model initialized on {'cuda' if torch.cuda.is_available() else 'cpu'}")
    return _embedding_model

def build_hybrid_query(user_input: dict, top_k: int = 5, exclude_ids: list = None) -> dict:
    """
    BM25와 KNN을 결합한 하이브리드 검색 쿼리를 생성합니다.
    """
    if exclude_ids is None:
        exclude_ids = []

    major = user_input.get("candidate_major", "")
    interest = user_input.get("candidate_interest", "")
    career = user_input.get("candidate_career", "")
    tech_stack = " ".join(user_input.get("candidate_tech_stack", []))
    location = user_input.get("candidate_location", "")
    
    # 검색 텍스트 구성 (의미적 검색용)
    search_text = f"{interest} {tech_stack} {major} {career}".strip()
    
    # 임베딩 모델로 쿼리 벡터 생성
    embedding_model = get_embedding_model()
    query_vector = embedding_model.embed_query(f"[Query] {search_text}")
    
    # 제외할 ID가 있을 경우 must_not 절 구성
    must_not_clauses = []
    if exclude_ids:
        must_not_clauses.append({"ids": {"values": exclude_ids}})

    # 하이브리드 검색 쿼리 구성
    search_query = {
        "query": {
            "bool": {
                "should": [
                    # BM25 기반 검색 (기존 로직)
                    {
                        "multi_match": {
                            "query": interest, 
                            "fields": ["job_name^3", "title^2", "position_detail"], 
                            "boost": 3.0  # BM25 boost
                        }
                    },
                    {
                        "multi_match": {
                            "query": tech_stack, 
                            "fields": ["tech_stack^2", "preferred_qualifications", "qualifications"], 
                            "boost": 2.5
                        }
                    },
                    {
                        "multi_match": {
                            "query": f"{major} {career}", 
                            "fields": ["qualifications", "preferred_qualifications"], 
                            "boost": 1.5
                        }
                    },
                    # 위치 매칭
                    {"match": {"location": {"query": location, "boost": 1.2}}} if location else None,
                    
                    # KNN 의미적 검색 추가
                    {
                        "knn": {
                            "content_embedding": {
                                "vector": query_vector,
                                "k": top_k * 2,  # 더 많은 후보를 가져온 후 재랭킹
                                "boost": 2.0  # 의미적 검색 boost
                            }
                        }
                    }
                ],
                "must_not": must_not_clauses,
                "minimum_should_match": 1
            }
        },
        "size": top_k,
        "_source": {
            "excludes": ["content_embedding"]  # 응답에서 큰 벡터 필드 제외
        }
    }

    # None인 쿼리 제거
    search_query["query"]["bool"]["should"] = [q for q in search_query["query"]["bool"]["should"] if q is not None]

    return search_query

def hybrid_search(user_profile: dict, top_k: int = 5, exclude_ids: list = None) -> tuple[list[float], list[str], list[dict]]:
    """
    BM25 + 의미적 검색을 결합한 하이브리드 검색을 수행합니다.
    
    Args:
        user_profile (dict): 사용자 프로필 정보
        top_k (int): 반환할 결과 개수
        exclude_ids (list): 제외할 문서 ID 목록
        
    Returns:
        tuple: (점수 리스트, 문서 ID 리스트, 문서 리스트)
    """
    opensearch = OpenSearchDB()

    try:
        # 하이브리드 쿼리 생성
        search_query = build_hybrid_query(user_profile, top_k, exclude_ids)
        
        print(f"🔍 하이브리드 검색 수행: BM25 + KNN")
        print(f"📝 검색어: {user_profile.get('candidate_interest', '')} {' '.join(user_profile.get('candidate_tech_stack', []))}")
        
        # 검색 실행
        response = opensearch.search(search_query, size=top_k)
        
    except Exception as e:
        print(f"❌ 하이브리드 검색 실패: {e}")
        return [], [], []
    
    scores = []
    documents = []
    doc_ids = []
    
    hits = response.get("hits", {}).get("hits", [])
    print(f"✅ 하이브리드 검색 완료: {len(hits)}개 결과 반환")
    
    for hit in hits:
        scores.append(hit.get("_score", 0.0))
        documents.append(hit.get("_source", {}))
        doc_ids.append(hit.get("_id", ""))
    
    return scores, doc_ids, documents


if __name__ == "__main__":
    base_user_info = {
        "user_id": 10,
        "candidate_major": "경영학",
        "candidate_interest": "서비스 기획자",
        "candidate_career": "5년",
        "candidate_tech_stack": [
            "UX/UI 설계", "데이터 분석", "A/B 테스트", "프로젝트 관리"
        ],
        "candidate_location": "서울 강남",
        "candidate_question": "안녕하세요, 서비스 기획자 직무에 적합한 포지션이 있을까요?"
    }
    
    print("\n=== 하이브리드 검색 결과 ===")
    scores, doc_ids, documents = hybrid_search(base_user_info, top_k=5)
    
    if not scores:
        print("검색 결과가 없습니다.")
    else:
        for i, (score, doc_id, document) in enumerate(zip(scores, doc_ids, documents), 1):
            print(f"\n[하이브리드 검색결과 {i}] 점수: {score:.2f}, 문서 ID: {doc_id}")
            print(document)
            print(f"제목: {document.get('title', '정보 없음')}")
            print(f"회사명: {document.get('company_name', '정보 없음')}")
            print(f"지역: {document.get('location', '정보 없음')}")
            print(f"직무: {document.get('title', '정보 없음')}")
            print(f"기술 스택 • 툴: {document.get('tech_stack', '정보 없음')}")
            print(f"자격요건: {document.get('qualifications', '정보 없음')}")
            print(f"주요 업무: {document.get('main_tasks', '정보 없음')}")
            print("-" * 50)
