from pydantic import BaseModel, Field
from typing import List, Optional

class UserInfo(BaseModel):
    candidate_major: str = Field(..., description="지원자 전공")
    candidate_career: str = Field(..., description="지원자 경력")
    candidate_interest: str = Field(..., description="지원자 관심분야")
    candidate_location: str = Field(..., description="지원자 희망 근무지")
    candidate_tech_stack: List[str] = Field(default=[], description="지원자 기술 스택")
    candidate_question: str = Field(..., description="지원자 질문")
    candidate_salary: str = Field(..., description="지원자 희망 연봉")

    class Config:
        schema_extra = {
            "example": {
                "candidate_major": "컴퓨터공학",
                "candidate_career": "신입",
                "candidate_interest": "백엔드 개발",
                "candidate_location": "서울",
                "candidate_tech_stack": ["Python", "Django", "PostgreSQL"],
                "candidate_question": "백엔드 개발자로 취업하기 위해 어떤 준비를 해야 하나요?",
                "candidate_salary": "4000만원"
            }
        }

class WorkflowResponse(BaseModel):
    job_recommendations: str = Field(..., description="직업 추천")
    company_info: str = Field(..., description="회사 정보")
    salary_info: str = Field(..., description="연봉 정보")
    preparation_advice: str = Field(..., description="준비 조언")
    final_answer: str = Field(..., description="최종 답변")
    retry_count: int = Field(default=0, description="워크플로우 재시도 횟수")

    class Config:
        schema_extra = {
            "example": {
                "job_recommendations": "귀하의 전공과 관심사를 고려할 때, 백엔드 개발자, 풀스택 개발자, 데이터 엔지니어 등의 직업을 추천드립니다.",
                "company_info": "네이버, 카카오, 쿠팡 등 대기업부터 다양한 스타트업까지 기회가 많습니다.",
                "salary_info": "신입 백엔드 개발자의 평균 연봉은 3500-4500만원 수준입니다.",
                "preparation_advice": "프로젝트 경험을 쌓고, 알고리즘 문제 해결 능력을 기르는 것이 중요합니다.",
                "final_answer": "백엔드 개발자로의 성공적인 취업을 위해 체계적인 준비를 하시기 바랍니다.",
                "retry_count": 0
            }
        } 