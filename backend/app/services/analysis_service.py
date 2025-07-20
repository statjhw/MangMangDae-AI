from app.schemas.workflow_schema import UserInfo, WorkflowResponse
import asyncio
from typing import Dict, Any
import json

class AnalysisService:
    def __init__(self):
        # 더미 데이터 - 실제 구현에서는 AI 모델이나 데이터베이스 연결
        self.job_database = {
            "백엔드 개발": {
                "required_skills": ["Python", "Java", "Node.js", "데이터베이스"],
                "salary_range": "3500-5000만원",
                "companies": ["네이버", "카카오", "쿠팡", "토스"]
            },
            "프론트엔드 개발": {
                "required_skills": ["JavaScript", "React", "Vue.js", "TypeScript"],
                "salary_range": "3000-4500만원",
                "companies": ["네이버", "카카오", "배달의민족", "당근마켓"]
            },
            "데이터 분석": {
                "required_skills": ["Python", "SQL", "R", "머신러닝"],
                "salary_range": "4000-6000만원",
                "companies": ["네이버", "카카오", "쿠팡", "데이터 전문 회사"]
            }
        }
    
    async def analyze_user_info(self, user_info: UserInfo) -> WorkflowResponse:
        """사용자 정보를 분석하여 커리어 조언을 생성"""
        
        # 기본 분석 수행
        job_analysis = self._analyze_job_fit(user_info)
        company_analysis = self._analyze_company_fit(user_info)
        salary_analysis = self._analyze_salary_expectations(user_info)
        preparation_analysis = self._analyze_preparation_needs(user_info)
        
        # 최종 답변 생성
        final_answer = self._generate_final_answer(user_info, job_analysis, preparation_analysis)
        
        return WorkflowResponse(
            job_recommendations=job_analysis,
            company_info=company_analysis,
            salary_info=salary_analysis,
            preparation_advice=preparation_analysis,
            final_answer=final_answer
        )
    
    def _analyze_job_fit(self, user_info: UserInfo) -> str:
        """직업 적합성 분석"""
        interest = user_info.candidate_interest
        tech_stack = user_info.candidate_tech_stack
        career = user_info.candidate_career
        
        recommendations = []
        
        # 관심분야 기반 추천
        if "백엔드" in interest or "서버" in interest:
            recommendations.append("백엔드 개발자")
        if "프론트엔드" in interest or "UI" in interest or "UX" in interest:
            recommendations.append("프론트엔드 개발자")
        if "데이터" in interest or "분석" in interest:
            recommendations.append("데이터 분석가")
        if "풀스택" in interest:
            recommendations.append("풀스택 개발자")
        
        # 기술 스택 기반 추천
        if any(tech in ["Python", "Django", "Flask", "FastAPI"] for tech in tech_stack):
            if "백엔드 개발자" not in recommendations:
                recommendations.append("백엔드 개발자")
        if any(tech in ["JavaScript", "React", "Vue", "Angular"] for tech in tech_stack):
            if "프론트엔드 개발자" not in recommendations:
                recommendations.append("프론트엔드 개발자")
        
        if not recommendations:
            recommendations = ["소프트웨어 개발자", "IT 전문가"]
        
        return f"귀하의 전공({user_info.candidate_major}), 관심분야({interest}), 기술 스택({', '.join(tech_stack)})을 고려할 때, 다음 직업들을 추천드립니다: {', '.join(recommendations)}. 특히 {'신입' if '신입' in career else '경력직'}으로서 좋은 기회가 있을 것으로 예상됩니다."
    
    def _analyze_company_fit(self, user_info: UserInfo) -> str:
        """회사 정보 분석"""
        location = user_info.candidate_location
        interest = user_info.candidate_interest
        
        company_suggestions = []
        
        if "서울" in location:
            company_suggestions.extend(["네이버", "카카오", "쿠팡", "토스", "배달의민족"])
        elif "판교" in location:
            company_suggestions.extend(["네이버", "카카오", "NHN", "네이버웹툰"])
        elif "강남" in location:
            company_suggestions.extend(["라인", "야놀자", "마이리얼트립"])
        
        if "스타트업" in interest:
            company_suggestions.extend(["토스", "당근마켓", "직방", "야놀자"])
        
        if not company_suggestions:
            company_suggestions = ["대기업", "중견기업", "스타트업"]
        
        return f"{location} 지역에서 {interest} 분야의 경우, 다음 회사들을 고려해보실 수 있습니다: {', '.join(company_suggestions[:5])}. 각 회사마다 고유한 기업문화와 성장 기회가 있으니 본인의 가치관과 맞는 곳을 선택하시기 바랍니다."
    
    def _analyze_salary_expectations(self, user_info: UserInfo) -> str:
        """연봉 정보 분석"""
        expected_salary = user_info.candidate_salary
        career = user_info.candidate_career
        interest = user_info.candidate_interest
        
        # 시장 연봉 정보
        if "신입" in career:
            if "백엔드" in interest:
                market_range = "3500-4500만원"
            elif "프론트엔드" in interest:
                market_range = "3000-4000만원"
            elif "데이터" in interest:
                market_range = "4000-5000만원"
            else:
                market_range = "3000-4500만원"
        else:
            market_range = "4000-7000만원"
        
        return f"희망 연봉 {expected_salary}에 대해 분석한 결과, 현재 시장에서 {interest} 분야 {'신입' if '신입' in career else '경력직'}의 평균 연봉은 {market_range} 수준입니다. 기술 스택과 경험에 따라 차이가 있을 수 있으며, 지속적인 성장을 통해 연봉 상승이 가능합니다."
    
    def _analyze_preparation_needs(self, user_info: UserInfo) -> str:
        """준비 조언 분석"""
        interest = user_info.candidate_interest
        tech_stack = user_info.candidate_tech_stack
        career = user_info.candidate_career
        
        advice = []
        
        # 기술 스택 기반 조언
        if "백엔드" in interest:
            if not any(tech in ["Python", "Java", "Node.js"] for tech in tech_stack):
                advice.append("백엔드 개발 언어(Python, Java, Node.js 중 하나) 학습")
            advice.append("데이터베이스 설계 및 최적화 경험")
            advice.append("RESTful API 설계 및 구현")
        
        if "프론트엔드" in interest:
            if not any(tech in ["JavaScript", "React", "Vue"] for tech in tech_stack):
                advice.append("프론트엔드 프레임워크(React, Vue 등) 학습")
            advice.append("반응형 웹 디자인 경험")
        
        # 공통 조언
        if "신입" in career:
            advice.extend([
                "개인 프로젝트 포트폴리오 구축",
                "알고리즘 문제 해결 능력 향상",
                "협업 도구 사용 경험(Git, Slack 등)"
            ])
        
        advice.append("최신 기술 트렌드 지속적 학습")
        
        return f"성공적인 취업을 위해 다음 사항들을 준비하시기 바랍니다: {', '.join(advice[:5])}. 특히 실무 경험을 쌓을 수 있는 프로젝트 참여를 추천드립니다."
    
    def _generate_final_answer(self, user_info: UserInfo, job_analysis: str, preparation_analysis: str) -> str:
        """최종 답변 생성"""
        question = user_info.candidate_question
        
        return f"""
질문: {question}

종합적인 분석 결과를 바탕으로 답변드리겠습니다.

{job_analysis}

{preparation_analysis}

성공적인 커리어를 위해서는 지속적인 학습과 실무 경험 축적이 중요합니다. 
귀하의 목표를 달성하기 위해 단계별로 계획을 세우고 실행하시기 바랍니다.
추가 질문이 있으시면 언제든지 문의해 주세요.
        """.strip()

# 싱글톤 인스턴스
analysis_service = AnalysisService() 