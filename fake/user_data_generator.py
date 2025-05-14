import json
from typing import List, Dict
import random

# 기본 데이터 정의
EDUCATION_LEVELS = [
    "고등학교 졸업",
    "전문대학 졸업",
    "대학교 재학",
    "대학교 졸업",
    "석사 과정",
    "석사 졸업",
    "박사 과정",
    "박사 졸업"
]

MAJORS = [
    "컴퓨터공학",
    "소프트웨어공학",
    "정보통신공학",
    "데이터사이언스",
    "인공지능",
    "전자공학",
    "산업공학",
    "경영학",
    "통계학",
    "수학"
]

CAREER_YEARS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

JOB_CATEGORIES = [
    "프론트엔드 개발자",
    "백엔드 개발자",
    "풀스택 개발자",
    "모바일 앱 개발자",
    "데이터 엔지니어",
    "데이터 사이언티스트",
    "머신러닝 엔지니어",
    "DevOps 엔지니어",
    "시스템 엔지니어",
    "보안 엔지니어"
]

TECH_STACKS = {
    "프론트엔드": ["JavaScript", "TypeScript", "React", "Vue.js", "Angular", "HTML", "CSS", "Webpack", "Redux", "Next.js"],
    "백엔드": ["Python", "Java", "Node.js", "Spring", "Django", "FastAPI", "MySQL", "PostgreSQL", "MongoDB", "Redis"],
    "모바일": ["Swift", "Kotlin", "React Native", "Flutter", "Android SDK", "iOS SDK"],
    "데이터": ["Python", "R", "SQL", "Spark", "Hadoop", "TensorFlow", "PyTorch", "scikit-learn", "Pandas", "NumPy"],
    "DevOps": ["Docker", "Kubernetes", "AWS", "GCP", "Azure", "Jenkins", "Git", "Linux", "Terraform", "Ansible"]
}

LOCATIONS = ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종", "제주"]

# 사용자 대화 템플릿 정의
CONVERSATION_TEMPLATES = [
    "안녕하세요, {desired_salary}의 연봉을 받을 수 있는 {desired_location} 지역의 {desired_job} 직무를 찾고 있어요.",
    "{tech_stack} 기술을 가진 {career_years}년차 {job_category}입니다. {desired_location} 지역에서 이직하고 싶은데 조언해주세요.",
    "{education_level} {major} 전공자입니다. {desired_job}로 커리어 전환하고 싶은데 어떤 준비를 해야 할까요?",
    "{desired_location} 근처에서 {work_type}으로 일할 수 있는 회사 추천해주세요. {tech_stack} 기술을 주로 사용합니다.",
    "{job_category} {level} 개발자입니다. 연봉 {desired_salary} 정도 받을 수 있는 회사들이 어디가 있을까요?",
    "{education_level} 졸업하고 {tech_stack}을 공부했는데, {desired_job}로 취업하고 싶습니다. 어떤 회사가 좋을까요?",
    "{desired_location}에 있는 {desired_job} 포지션 중에서 {work_type} 근무가 가능한 곳 추천해주세요.",
    "{career_years}년 동안 {job_category}로 일했고, {tech_stack} 기술을 다뤄봤습니다. 연봉 {desired_salary} 정도면 어느 회사가 좋을까요?",
    "현재 {current_status}이고 {tech_stack} 기술을 사용하는 {desired_job} 직무를 찾고 있어요. {desired_location} 지역 추천해주세요.",
    "{major} 전공이고 {tech_stack}을 다룰 줄 아는데, {desired_job}로 일하고 싶어요. 어떤 회사들이 있나요?"
]

def generate_tech_stack(job_category: str) -> List[str]:
    """직무 카테고리에 맞는 기술 스택 생성"""
    if "프론트엔드" in job_category:
        base_stack = TECH_STACKS["프론트엔드"]
    elif "백엔드" in job_category:
        base_stack = TECH_STACKS["백엔드"]
    elif "모바일" in job_category:
        base_stack = TECH_STACKS["모바일"]
    elif "데이터" in job_category:
        base_stack = TECH_STACKS["데이터"]
    elif "DevOps" in job_category:
        base_stack = TECH_STACKS["DevOps"]
    else:
        # 풀스택의 경우 프론트엔드와 백엔드 조합
        base_stack = TECH_STACKS["프론트엔드"] + TECH_STACKS["백엔드"]
    
    return random.sample(base_stack, random.randint(3, 6))

def generate_conversation(user_data: Dict) -> str:
    """사용자 데이터를 기반으로 대화 생성"""
    template = random.choice(CONVERSATION_TEMPLATES)
    
    # 템플릿에 들어갈 데이터 준비
    format_data = {
        "education_level": user_data["education"]["level"],
        "major": user_data["education"]["major"],
        "career_years": user_data["career"]["years"],
        "current_status": user_data["career"]["current_status"],
        "job_category": user_data["career"]["job_category"],
        "tech_stack": ", ".join(random.sample(user_data["skills"]["tech_stack"], 2)),
        "level": user_data["skills"]["level"],
        "desired_job": user_data["preferences"]["desired_job"],
        "desired_location": random.choice(user_data["preferences"]["desired_location"]),
        "desired_salary": user_data["preferences"]["desired_salary"],
        "work_type": user_data["preferences"]["work_type"]
    }
    
    return template.format(**format_data)

def generate_user() -> Dict:
    """가상의 사용자 데이터 생성"""
    job_category = random.choice(JOB_CATEGORIES)
    career_years = random.choice(CAREER_YEARS)
    
    user = {
        "education": {
            "level": random.choice(EDUCATION_LEVELS),
            "major": random.choice(MAJORS),
            "school": f"{'ABC'} {'대학교' if '대학' in EDUCATION_LEVELS else '고등학교'}"
        },
        "career": {
            "years": career_years,
            "current_status": "재직중" if random.random() > 0.3 else "구직중",
            "job_category": job_category
        },
        "skills": {
            "tech_stack": generate_tech_stack(job_category),
            "level": "초급" if career_years < 3 else "중급" if career_years < 7 else "고급"
        },
        "preferences": {
            "desired_job": job_category,
            "desired_location": random.sample(LOCATIONS, random.randint(1, 3)),
            "desired_salary": f"{random.randint(3000, 12000):,}만원",
            "work_type": random.choice(["상주", "리모트", "하이브리드"])
        }
    }
    
    # 사용자 대화 추가
    user["conversation"] = generate_conversation(user)
    
    return user

# 10명의 가상 사용자 데이터 생성
if __name__ == "__main__":
    users = generate_user()
    print(users)