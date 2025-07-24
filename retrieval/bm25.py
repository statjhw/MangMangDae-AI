import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.opensearch import OpenSearchDB

def build_query(user_input: dict, top_k: int = 5, exclude_ids: list = None) -> dict:
    if exclude_ids is None:
        exclude_ids = []

    major = user_input.get("candidate_major", "")
    interest = user_input.get("candidate_interest", "")
    career = user_input.get("candidate_career", "")
    tech_stack = " ".join(user_input.get("candidate_tech_stack", []))
    location = user_input.get("candidate_location", "")
    
    # 제외할 ID가 있을 경우 must_not 절 구성
    must_not_clauses = []
    if exclude_ids:
        must_not_clauses.append({"ids": {"values": exclude_ids}})

    search_query = {
        "query": {
            "bool": {
                "should": [
                    {"multi_match": {"query": interest, "fields": ["job_name^3", "title^2", "position_detail"], "boost": 5}},
                    {"multi_match": {"query": tech_stack, "fields": ["tech_stack^2", "preferred_qualifications", "qualifications"], "boost": 3}},
                    {"multi_match": {"query": f"{major} {career}", "fields": ["qualifications", "preferred_qualifications"], "boost": 1.5}},
                    {"match": {"location": {"query": location, "boost": 1.2}}} if location else None
                ],
                "must_not": must_not_clauses,
                "minimum_should_match": 1
            }
        },
        "size": 5,
        "_source": True
    }
    
    search_query["query"]["bool"]["should"] = [q for q in search_query["query"]["bool"]["should"] if q is not None]

    return search_query

def bm25_search(user_profile: dict, top_k: int = 5, exclude_ids: list = None) -> tuple[list[float], list[dict], list[str]]:
    opensearch = OpenSearchDB()
    search_query = build_query(user_profile, top_k, exclude_ids)
    
    try:
        response = opensearch.search(search_query, size=top_k)
    except Exception as e:
        print(f"OpenSearch search failed: {e}")
        return [], [], []
    
    scores = []
    documents = []
    doc_ids = []
    
    for hit in response.get("hits", {}).get("hits", []):
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
        ('tag_name', '태그'),
        ('location', '위치'),
        ('dead_line', '마감일'),
        ('position_detail', '포지션 상세'),
        ('main_tasks', '주요 업무'),
        ('qualifications', '자격 요건'),
        ('preferred_qualifications', '우대 사항'),
        ('benefits', '혜택 및 복지'),
        ('hiring_process', '채용 과정'),
        ('tech_stack', '기술 스택 • 툴'),
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
    
    print("\n=== 검색 결과 ===")
    scores, doc_ids, documents = bm25_search(base_user_info, top_k=5)
    
    if not scores:
        print("검색 결과가 없습니다.")
    else:
        for i, (score, doc_id, document) in enumerate(zip(scores, doc_ids, documents), 1):
            print(f"\n[검색결과 {i}] 점수: {score:.2f}, 문서 ID: {doc_id}")
            print(f"제목: {document.get('title', '정보 없음')}")
            print(f"회사명: {document.get('company_name', '정보 없음')}")
            print(f"지역: {document.get('location', '정보 없음')}")
            print(f"직무: {document.get('title', '정보 없음')}")
            print(f"기술 스택 • 툴: {document.get('tech_stack', '정보 없음')}")
            print(f"자격요건: {document.get('qualifications', '정보 없음')}")

            print(f"주요 업무: {document.get('main_tasks', '정보 없음')}")

            #print(f"상세 내용: {document.get('position_detail', '정보 없음')}")
            #print(f"우대사항: {document.get('preferred_qualifications', '정보 없음')}")
            #print(f"혜택 및 복지: {document.get('benefits', '정보 없음')}")
            #print(f"채용 전형: {document.get('hiring_process', '정보 없음')}")

            #print(f"직무 카테고리: {document.get('job_category', '정보 없음')}")

            print("-" * 50)
