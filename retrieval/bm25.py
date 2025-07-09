import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.opensearch import OpenSearchDB


def build_query(user_input: dict) -> str:
    major = user_input.get("candidate_major")
    interest = user_input.get("candidate_interest")
    career = user_input.get("candidate_career")
    tech_stack = " ".join(user_input.get("candidate_tech_stack"))
    location = user_input.get("candidate_location")
    question = user_input.get("candidate_question")
    
    search_query = {
        "query": {
            "bool": {
                "should": [
                    {
                        "multi_match": {
                            "query": interest,
                            "fields": ["job_category^3", "title^2", "position_detail", "main_tasks"],
                            "boost": 5
                        }
                    },
                    {
                        "multi_match": {
                            "query": tech_stack,
                            "fields": ["tech_stack^2", "preferred_qualifications", "qualifications"],
                            "boost": 2
                        }
                    },
                    {
                        "multi_match": {
                            "query": " ".join([major, career]),
                            "fields": ["qualifications^2", "preferred_qualifications", "tech_stack"],
                            "boost": 1.5
                        }
                    },
                    {
                        "terms": {
                            "location": [location],
                            "boost": 0.2
                        }
                    }
                ],
                "minimum_should_match": "1"
            }
        },
        "size": 10,
        "_source": True,
        "sort": [
            {"_score": {"order": "desc"}},
            {"_id": {"order": "asc"}}
        ]
    }
    return search_query

def bm25_search(query: str) -> tuple[list[float], list[str], list[dict]]:
    opensearch = OpenSearchDB()
    search_query = build_query(query)
    response = opensearch.search(search_query)
    
    # (점수쌍, id쌍, 원본 문서 쌍) 형태로 변환
    scores = []
    doc_ids = []
    documents = []
    
    for hit in response["hits"]["hits"]:
        scores.append(hit["_score"])
        doc_ids.append(hit["_id"])
        documents.append(hit["_source"])
    
    return (scores, doc_ids, documents)

if __name__ == "__main__":
    user_input = {
        "candidate_major": "통계학과, 컴퓨터공학과",
        "candidate_interest": "데이터 엔지니어",
        "candidate_career": "인하대 학사 졸업",
        "candidate_tech_stack": ["python", "kafka", "aws"],
        "candidate_location": "서울",
        "candidate_question": "현재 수학과 박사 졸업했고, 수학과 박사를 원하는 회사가 있을까?"
    }
    
    print("\n=== 검색 결과 ===")
    scores, doc_ids, documents = bm25_search(user_input)
    
    if not scores:
        print("검색 결과가 없습니다.")
    else:
        for i, (score, doc_id, document) in enumerate(zip(scores, doc_ids, documents), 1):
            print(f"\n[검색결과 {i}] 점수: {score:.2f}, 문서 ID: {doc_id}")
            print(f"제목: {document.get('title', '정보 없음')}")
            print(f"회사명: {document.get('company_name', '정보 없음')}")
            print(f"직무: {document.get('title', '정보 없음')}")
            print(f"상세 내용: {document.get('position_detail', '정보 없음')}")
            print(f"주요 업무: {document.get('main_tasks', '정보 없음')}")
            print(f"자격요건: {document.get('qualifications', '정보 없음')}")
            print(f"우대사항: {document.get('preferred_qualifications', '정보 없음')}")
            print(f"혜택 및 복지: {document.get('benefits', '정보 없음')}")
            print(f"채용 전형: {document.get('hiring_process', '정보 없음')}")
            print(f"기술 스택 • 툴: {document.get('tech_stack', '정보 없음')}")
            print(f"직무 카테고리: {document.get('job_category', '정보 없음')}")
            print(f"지역: {document.get('location', '정보 없음')}")
            print(f"기술스택: {', '.join(document.get('tech_stack', ['정보 없음']))}")
            print("-" * 50)








