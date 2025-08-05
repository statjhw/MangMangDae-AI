### 유저 통계 서비스 ###
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
# 프로젝트 루트 디렉토리를 sys.path에 추가 (4단계 위로)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from DB.opensearch import OpenSearchDB

# 프로젝트 루트 경로를 기준으로 파일 경로 설정
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MAPPING_TABLE_PATH = os.path.join(PROJECT_ROOT, "frontend", "mapping_table.json")

class StatUser:
    def __init__(self):
        self.db = OpenSearchDB()
    

    def get_user_stat(self, user_info: dict) -> Dict[str, Any]:
        """사용자 정보 기반 종합 통계 생성"""
        return {
            "user_info": self._extract_user_summary(user_info),
            "interest": self._get_interest_stats(user_info.get("candidate_interest", "")),
            "tech_stack": self._get_tech_stack_stats(user_info.get("candidate_tech_stack", [])),
        }

    def _extract_user_summary(self, user_info: dict) -> Dict[str, str]:
        """사용자 기본 정보 요약"""
        return {
            "전공": user_info.get("candidate_major", "정보 없음"),
            "경력": user_info.get("candidate_career", "정보 없음"),
            "관심분야": user_info.get("candidate_interest", "정보 없음"),
            "희망지역": user_info.get("candidate_location", "정보 없음"),
            "기술스택": user_info.get("candidate_tech_stack", [])
        }

    def _get_interest_stats(self, interest: str) -> Dict[str, Any]:
        """관심 분야 기반 통계"""
        if not interest:
            return {"message": "관심 분야 정보가 없습니다."}
        ## 역 인덱스 생성해서 하는 것이 더 효과적
        with open(MAPPING_TABLE_PATH, "r") as f:
            mapping_table = json.load(f)
            for parent_key, child_dict in mapping_table.items():
                for child_key, child_value in child_dict.items():
                    if child_value == interest:
                        interest_category = child_key
                        break
        try:
            # 관심 분야와 관련된 채용공고 검색
            query = {
                "query": {
                    "bool": {
                        "should": [
                            {"match": {"job_category": interest_category}},
                        ],
                        "minimum_should_match": 1
                    }
                }
            }
            
            response = self.db.search(query, size=9662)
            total_job = response['hits']['total']['value']
            
            return {"interest": interest, "total_job": total_job}
            
        except Exception as e:
            return {"error": f"관심 분야 통계 생성 실패: {str(e)}"}
        
    def _get_tech_stack_stats(self, tech_stacks: List[str]) -> Dict[str, Any]:
        """기술 스택별 채용 회사 수 반환"""
        if not tech_stacks:
            return {"message": "기술 스택 정보가 없습니다."}
            
        try:
            tech_company_count = {}
            
            # 각 기술별 회사 수 조사 (aggregation 사용)
            for tech in tech_stacks:
                query = {
                    "query": {
                        "multi_match": {
                            "query": tech,
                            "fields": ["tech_stack", "qualifications", "preferred_qualifications", "position_detail"],
                            "type": "phrase"
                        }
                    },
                    "aggs": {
                        "unique_companies": {
                            "terms": {
                                "field": "company_id",
                                "size": 10000
                            }
                        }
                    }
                }
            
                response = self.db.search(query, size=0)
                buckets = response.get('aggregations', {}).get('unique_companies', {}).get('buckets', [])
                company_count = len(buckets)
                tech_company_count[tech] = company_count
            
            return tech_company_count
            
        except Exception as e:
            return {"error": f"기술 스택 통계 생성 실패: {str(e)}"}


if __name__ == "__main__":
    # 테스트 데이터
    interest = "소프트웨어 엔지니어"
    tech_stacks = ["Python", "React", "Java", "Docker", "AWS"]
    
    stat_user = StatUser()
    
    print("=== 관심분야 통계 ===")
    print(stat_user._get_interest_stats(interest))
    
    print("\n=== 기술스택별 회사 수 ===")
    tech_stats = stat_user._get_tech_stack_stats(tech_stacks)
    print(tech_stats)
    
    # 예시 출력: {"Python": 150, "React": 98, "Java": 200, "Docker": 75, "AWS": 180}


    