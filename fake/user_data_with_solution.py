import os, sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import openai
from dotenv import load_dotenv
from db import DynamoDB
import random
load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

def fetch_dynamodb_data():
    """
    DynamoDB에서 랜덤으로 30개의 데이터를 가져오는 함수입니다.
    
    Returns:
        list: 30개의 랜덤 데이터가 포함된 리스트
    """
    db = DynamoDB()
    all_items = []
    
    # 모든 아이템을 리스트에 저장
    for item in db.scan_items_generator("wanted_jobs"):
        all_items.append(item)
    
    # 전체 데이터가 30개 미만인 경우 전체 데이터 반환
    if len(all_items) <= 30:
        return all_items
        
    # 랜덤으로 30개 선택
    import random
    return random.sample(all_items, 30)

def generate_user_data_with_solution(job_data: dict) -> dict:
    """
    job_data에 있는 데이터에 적합한 데이터를 생성하고 job_data를 기반으로
    정답을 생성하는 함수
    
    Args:
        job_data (dict): 데이터베이스에서 가져온 하나의 데이터
        
    Returns:
        dict: 생성된 데이터와 정답. 다음과 같은 형식:
        {
            "user_data": 생성된 사용자 데이터,
            "solution": job_data에서 사용자에게 적합한 추천 직무 목록
        }
    """
    # OpenAI 클라이언트 초기화
    client = openai.OpenAI(api_key=openai_api_key)    

    # 사용자 데이터 생성을 위한 프롬프트 작성
    user_prompt = f"""
    주어진 채용공고를 분석하여 해당 포지션에 적합한 가상의 구직자 프로필을 생성해주세요.
    
    채용공고 정보: {job_data}
    
    다음 JSON 형식으로 응답해주세요. 모든 필드는 채용공고의 요구사항과 일관성이 있어야 합니다:
    
    {{
        "education": {{
            "level": "채용공고의 최소 학력 요건을 충족하는 학력 수준",
            "major": "직무 연관성 높은 전공",
            "school": "구체적인 학교명"
        }},
        "career": {{
            "years": "채용공고 요구경력에 부합하는 연차",
            "current_status": "현재 구직/재직 상태",
            "job_category": "채용공고와 일치하는 직무 카테고리"
        }},
        "skills": {{
            "tech_stack": ["채용공고에서 요구하는 핵심 기술스택 3-5개"],
            "level": "경력에 맞는 기술 숙련도(초급/중급/고급)"
        }},
        "preferences": {{
            "desired_job": "채용공고의 직무명과 일치",
            "desired_location": ["채용공고 근무지와 동일/인접 지역"],
            "desired_salary": "채용공고 제시 연봉의 ±10% 범위",
            "work_type": "채용공고의 근무형태와 일치"
        }},
        "conversation": "위 정보를 자연스럽게 포함한 실제 구직자의 질문 내용"
    }}
    
    주의사항:
    1. 모든 데이터는 채용공고의 요구사항과 정확히 매칭되어야 함
    2. 기술스택은 해당 직무에서 실제 많이 사용되는 것으로 선택
    3. 대화문은 자연스러운 한국어로 작성
    4. 데이터 간 논리적 일관성 유지(예: 경력과 기술 레벨의 연관성)
    """
    
    # 사용자 데이터 생성
    user_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 채용 전문가입니다. 반드시 유효한 JSON 형식으로만 응답해주세요. 다른 텍스트는 포함하지 마세요."},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    user_data_raw = user_response.choices[0].message.content
    
    # JSON 응답을 파싱
    try:
        user_data = json.loads(user_data_raw)
    except json.JSONDecodeError:
        # JSON 파싱 실패 시 원본 텍스트 반환
        print(f"JSON 파싱 실패: {user_data_raw}")
        user_data = {"raw_response": user_data_raw}
    
    return {
        "job_data": job_data,
        "user_data": user_data
    }   

if __name__ == "__main__":
    job_datas = fetch_dynamodb_data()
    print("채용 정보 데이터 가져오기 완료!")
    
    user_data_with_solutions = {}
    data_count = 0
    for job_data in job_datas:
        print(f"데이터 {data_count + 1}번째 생성 중...")
        user_data_with_solution = generate_user_data_with_solution(job_data)
        user_data_with_solutions[data_count] = user_data_with_solution
        print(f"데이터 {data_count + 1}번째 생성 완료!")
        data_count += 1

    with open("fake/user_data_with_solutions.json", "w", encoding="utf-8") as f:
        json.dump(user_data_with_solutions, f, ensure_ascii=False, indent=4)