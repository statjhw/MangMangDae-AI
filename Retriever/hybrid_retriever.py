import os
import sys
import torch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from DB.opensearch import OpenSearchDB
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

    #사용자의 프로필 정보
    major = user_input.get("candidate_major", "")
    interest = user_input.get("candidate_interest", "")
    career = user_input.get("candidate_career", "")
    tech_stack = " ".join(user_input.get("candidate_tech_stack", []))
    location = user_input.get("candidate_location", "")
    
    #chat에서 활용되는 사용자의 질문
    query = user_input.get("candidate_question", "")
    
    # 임베딩 모델로 쿼리 벡터 생성
    embedding_model = get_embedding_model()
    query_vector = embedding_model.embed_query(f"[Query] {query}")
    
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
                            "fields": ["position_detail", "preferred_qualifications", "qualifications"], 
                            "boost": 2.5
                        }
                    },
                    {
                        "multi_match": {
                            "query": f"{major}", 
                            "fields": ["qualifications", "preferred_qualifications"], 
                            "boost": 1.5
                        }
                    },
                    {"match": {"career": {"query": career, "boost": 1.5}}},
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

def _format_hit_to_text(hit_source: dict) -> str:
    """
    OpenSearch의 _source 딕셔너리를 원본 문서와 동일한 텍스트 형식으로 재구성합니다.
    """
    if not hit_source:
        return ""

    # 문서에 포함될 필드와 표시될 이름, 그리고 순서를 정의합니다.
    field_order_map = [
        ('title', '직무'),
        ('company_name', '회사'),
        ('job_category', '직무 카테고리'),
        ('location', '위치'),
        ('career', '경력'),
        ('dead_line', '마감일'),
        ('position_detail', '포지션 상세'),
        ('main_tasks', '주요 업무'),
        ('qualifications', '자격 요건'),
        ('preferred_qualifications', '우대 사항'),
        ('benefits', '혜택 및 복지'),
        ('hiring_process', '채용 과정'),
        ('url', '채용공고 URL')
    ]

    lines = ["[document]"]

    for field_key, display_name in field_order_map:
        value = hit_source.get(field_key)

        # 값이 존재하고, 비어있지 않은 경우에만 추가합니다.
        if value:
            # '주요 업무', '자격 요건' 등 여러 줄로 나열되어야 하는 필드 처리
            if field_key in ['main_tasks', 'qualifications', 'preferred_qualifications', 'benefits'] and isinstance(value, list):
                # 각 항목 앞에 '- '를 붙여서 줄바꿈으로 연결
                formatted_value = '\n'.join([f"- {item}" for item in value])
                lines.append(f"{display_name}:\n{formatted_value}")
            # '태그'와 같이 쉼표로 구분된 리스트 처리
            elif isinstance(value, list):
                lines.append(f"{display_name}: {', '.join(value)}")
            # 나머지 일반 텍스트 필드
            else:
                lines.append(f"{display_name}: {value}")

    # 각 섹션을 두 번의 줄바꿈으로 연결하여 최종 텍스트 생성
    return "\n\n".join(lines)



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
