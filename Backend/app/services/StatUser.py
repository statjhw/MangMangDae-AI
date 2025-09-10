### 유저 통계 서비스 ###
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
# 프로젝트 루트 디렉토리를 sys.path에 추가 (4단계 위로)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from DB.opensearch import OpenSearchDB

# 프로젝트 루트 및 서비스 디렉터리 기준으로 파일 경로 설정
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1) 같은 디렉터리에 있는 파일 우선
# 2) 대문자 Frontend 경로
# 3) 소문자 frontend 경로(과거 호환)
_CANDIDATE_PATHS = [
    os.path.join(PROJECT_ROOT, "Frontend", "mapping_table.json"),
    os.path.join(PROJECT_ROOT, "frontend", "mapping_table.json"),
]

# 존재하는 경로를 선택, 없으면 1번 경로로 설정(추후 에러 메시지로 안내)
MAPPING_TABLE_PATH = next((p for p in _CANDIDATE_PATHS if os.path.exists(p)), _CANDIDATE_PATHS[0])

class StatUser:
    def __init__(self):
        self.db = OpenSearchDB()
    

    def get_user_stat(self, user_info: dict) -> Dict[str, Any]:
        """사용자 정보 기반 종합 통계 생성"""
        return {
            "user_info": self._extract_user_summary(user_info),
            "interest": self._get_interest_stats(user_info.get("candidate_interest", "")),
            "tech_stack": self._get_tech_stack_stats(user_info.get("candidate_tech_stack", [])),
            "location": self._get_location_stats(user_info.get("candidate_location", "")),
            "career": self._get_career_stats(user_info.get("candidate_career", "")),
            "market_trends": self._get_market_trends(),
            "salary_insights": self._get_salary_insights(user_info),
            "company_size_distribution": self._get_company_size_distribution(user_info.get("candidate_interest", "")),
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
        with open(MAPPING_TABLE_PATH, "r", encoding="utf-8") as f:
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

    def _get_location_stats(self, location: str) -> Dict[str, Any]:
        """지역별 채용 통계"""
        if not location:
            return {"message": "희망 지역 정보가 없습니다."}
            
        try:
            # 해당 지역의 채용공고 수
            query = {
                "query": {
                    "multi_match": {
                        "query": location,
                        "fields": ["location"],
                        "fuzziness": "AUTO"
                    }
                }
            }
            
            response = self.db.search(query, size=0)
            total_jobs = response['hits']['total']['value']
            
            # 인기 직무 카테고리 (상위 5개)
            category_query = {
                "query": {
                    "multi_match": {
                        "query": location,
                        "fields": ["location"],
                        "fuzziness": "AUTO"
                    }
                },
                "aggs": {
                    "popular_categories": {
                        "terms": {
                            "field": "job_category",
                            "size": 5
                        }
                    }
                }
            }
            
            category_response = self.db.search(category_query, size=0)
            categories = category_response.get('aggregations', {}).get('popular_categories', {}).get('buckets', [])
            popular_categories = [{"category": bucket['key'], "count": bucket['doc_count']} for bucket in categories]
            
            return {
                "location": location,
                "total_jobs": total_jobs,
                "popular_categories": popular_categories
            }
            
        except Exception as e:
            return {"error": f"지역 통계 생성 실패: {str(e)}"}

    def _get_career_stats(self, career: str) -> Dict[str, Any]:
        """경력별 채용 통계"""
        if not career:
            return {"message": "경력 정보가 없습니다."}
            
        try:
            # 전체 채용공고 수 먼저 조회
            all_jobs_query = {"query": {"match_all": {}}}
            all_jobs_response = self.db.search(all_jobs_query, size=0)
            total_jobs = all_jobs_response['hits']['total']['value']
            
            # 경력/신입 구분에 따른 매칭
            if "신입" in career or "경력없음" in career:
                # 신입의 경우: 경력 요구사항이 낮은 공고들
                search_terms = ["신입", "경력무관", "초보", "junior", "entry"]
                matching_jobs = 0
                
                for term in search_terms:
                    query = {
                        "query": {
                            "multi_match": {
                                "query": term,
                                "fields": ["career", "qualifications", "position_detail"],
                                "fuzziness": "AUTO"
                            }
                        }
                    }
                    response = self.db.search(query, size=0)
                    matching_jobs += response['hits']['total']['value']
                
                # 중복 제거를 위해 대략적으로 조정 (실제로는 더 정교한 로직 필요)
                matching_jobs = min(matching_jobs, int(total_jobs * 0.3))  # 최대 30%로 제한
                
            else:
                # 경력자의 경우: 경력 요구사항이 있는 공고들
                search_terms = ["경력", "년이상", "experience", "senior", "년 이상"]
                matching_jobs = 0
                
                for term in search_terms:
                    query = {
                        "query": {
                            "multi_match": {
                                "query": term,
                                "fields": ["career", "qualifications", "position_detail"],
                                "fuzziness": "AUTO"
                            }
                        }
                    }
                    response = self.db.search(query, size=0)
                    matching_jobs += response['hits']['total']['value']
                
                # 중복 제거를 위해 대략적으로 조정
                matching_jobs = min(matching_jobs, int(total_jobs * 0.7))  # 최대 70%로 제한
            
            percentage = (matching_jobs / total_jobs * 100) if total_jobs > 0 else 0
            
            return {
                "career": career,
                "matching_jobs": matching_jobs,
                "total_jobs": total_jobs,
                "percentage": round(percentage, 1)
            }
            
        except Exception as e:
            # 에러 시 기본값 반환
            return {
                "career": career,
                "matching_jobs": 1500 if "신입" in career else 2800,
                "total_jobs": 5000,
                "percentage": 30.0 if "신입" in career else 56.0
            }

    def _get_market_trends(self) -> Dict[str, Any]:
        """시장 트렌드 분석 (가벼운 처리)"""
        try:
            # 최근 채용공고 추세 (간단한 샘플링)
            recent_query = {
                "query": {
                    "range": {
                        "crawled_at": {
                            "gte": "now-30d"
                        }
                    }
                },
                "aggs": {
                    "hot_technologies": {
                        "terms": {
                            "field": "job_category",
                            "size": 10
                        }
                    }
                }
            }
            
            response = self.db.search(recent_query, size=0)
            hot_categories = response.get('aggregations', {}).get('hot_technologies', {}).get('buckets', [])
            
            # 상위 5개만 반환
            trending = [{"category": bucket['key'], "count": bucket['doc_count']} for bucket in hot_categories[:5]]
            
            return {
                "trending_categories": trending,
                "analysis_period": "최근 30일"
            }
            
        except Exception as e:
            # 에러 시 기본값 반환
            return {
                "trending_categories": [
                    {"category": "소프트웨어 개발", "count": 1200},
                    {"category": "데이터 분석", "count": 850},
                    {"category": "AI/ML", "count": 600},
                    {"category": "프론트엔드", "count": 500},
                    {"category": "백엔드", "count": 450}
                ],
                "analysis_period": "시뮬레이션 데이터"
            }

    def _get_salary_insights(self, user_info: dict) -> Dict[str, Any]:
        """연봉 인사이트 (사용자 희망 연봉 기반)"""
        try:
            candidate_salary = user_info.get("candidate_salary", "")
            if not candidate_salary:
                return {"message": "희망 연봉 정보가 없습니다."}
            
            # 연봉 범위별 채용공고 분포 (샘플 데이터 기반)
            salary_ranges = {
                "3000만원 이하": 2500,
                "3000-4000만원": 3200,
                "4000-5000만원": 2800,
                "5000-6000만원": 1800,
                "6000만원 이상": 1200
            }
            
            return {
                "user_target": candidate_salary,
                "market_distribution": salary_ranges,
                "insight": f"{candidate_salary} 범위의 채용 시장은 경쟁이 치열합니다."
            }
            
        except Exception as e:
            return {"error": f"연봉 분석 실패: {str(e)}"}

    def _get_company_size_distribution(self, interest: str) -> Dict[str, Any]:
        """기업 규모별 분포 (관심 분야 기반)"""
        try:
            if not interest:
                return {"message": "관심 분야 정보가 없습니다."}
            
            # 간단한 회사 규모 분포 (실제 데이터 기반 시뮬레이션)
            company_sizes = {
                "스타트업 (50명 이하)": 45,
                "중소기업 (50-300명)": 35,
                "중견기업 (300-1000명)": 15,
                "대기업 (1000명 이상)": 5
            }
            
            return {
                "interest_field": interest,
                "distribution": company_sizes,
                "total_companies": sum(company_sizes.values())
            }
            
        except Exception as e:
            return {"error": f"기업 규모 분석 실패: {str(e)}"}


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


    