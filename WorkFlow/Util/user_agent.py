import random
from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from WorkFlow.Util.utils import get_llm, RunInvokeAdapter

# --- 1. 페르소나 생성기 ---
MAJORS = ["컴퓨터공학", "소프트웨어공학", "통계학", "산업공학", "전자공학", "경영학"]
INTERESTS = ["데이터 엔지니어", "백엔드 개발자", "서비스 기획자", "프로덕트 매니저", "QA 엔지니어"]
CAREERS = ["신입", "1년차", "3년", "5년", "주니어"]
LOCATIONS = ["서울", "판교", "성남", "경기"]
TECH_STACKS = {
    "데이터 엔지니어": ["Python", "AWS", "Kafka", "Spark", "SQL"],
    "백엔드 개발자": ["Java", "Spring", "Kotlin", "Node.js", "Python", "Go"],
    "서비스 기획자": ["Figma", "Jira", "SQL", "A/B 테스트"],
    "프로덕트 매니저": ["Jira", "Confluence", "Amplitude", "SQL"],
    "QA 엔지니어": ["Jira", "Selenium", "Appium", "Postman"]
}

def generate_random_persona(user_id: int) -> Dict[str, Any]:
    """지정된 형식에 맞춰 랜덤한 사용자 페르소나를 생성합니다."""
    interest = random.choice(INTERESTS)
    tech_stack = random.sample(TECH_STACKS[interest], k=random.randint(2, 4))
    
    return {
        "user_id": user_id,
        "candidate_major": random.choice(MAJORS),
        "candidate_interest": interest,
        "candidate_career": random.choice(CAREERS),
        "candidate_tech_stack": tech_stack,
        "candidate_location": random.choice(LOCATIONS),
    }

# --- 2. 다음 질문 생성을 위한 LLM 프롬프트 및 체인 ---
USER_AGENT_PROMPT = PromptTemplate(
    input_variables=["persona", "chat_history", "turn_count"],
    template="""당신은 [페르소나]를 가진 취업 준비생 역할을 수행하는 AI 에이전트입니다. '취업 어드바이저 챗봇'과의 대화 기록을 바탕으로, 다음에 할 가장 자연스러운 질문을 생성해야 합니다.

[당신의 페르소나]
{persona}

[이전 대화 기록]
{chat_history}

[현재 대화 턴 수]
{turn_count} / 7

[지시사항 - 턴별 질문 유형 (엄격히 준수)]
턴 1: 첫 질문 - 당신의 페르소나를 바탕으로 직무 추천을 요청하는 질문 (예: "백엔드 개발자 직무를 찾고 있는데, Java와 Spring 경험이 있는 3년차 개발자에게 적합한 공고가 있을까요?")
턴 2: 추천 목록이 나온 후 - 목록 중 하나를 선택하는 질문 (예: "1번 회사에 대해 더 자세히 알려주세요")
턴 3: 특정 회사 분석 후 - 그 회사에 대한 추가 질문 (예: "연봉은 어느 정도인가요?", "재택근무가 가능한가요?")
턴 4: 새로운 검색 요청 - 조건을 바꿔 다른 공고 찾기 (예: "혹시 판교 지역도 있나요?", "신입도 지원 가능한가요?")
턴 5: 면접/준비 관련 질문 - 구체적인 준비 방법 (예: "기술 면접은 어떤 질문이 나올까요?", "어떤 준비를 하면 좋을까요?")
턴 6: 마무리 질문 - 마지막으로 궁금한 점
턴 7: 대화 종료 - "종료"

[질문 작성 규칙 - 엄격히 준수]
- 현재 턴에 맞는 질문 유형을 정확히 파악하고 질문하세요
- **턴 1에서는 절대 "추천해주신 목록 중에서" 같은 표현을 사용하지 마세요**
- 아직 나오지 않은 정보에 대해 질문하지 마세요
- **중복 방지**: 이전 대화에서 이미 다룬 주제나 질문을 반복하지 마세요
- **대화 맥락 파악**: 이전 질문과 답변을 정확히 이해하고, 그에 이어지는 새로운 질문을 하세요
- 실제 취업준비생이 할 법한 자연스럽고 구체적인 질문으로 작성
- "~에 대해 더 자세히 알려주세요", "~이 궁금해요" 같은 간단하고 직접적인 표현 사용

[중복 방지 체크리스트]
- 이전 턴에서 이미 질문한 내용인지 확인
- 비슷한 주제의 질문을 반복하지 않음
- 각 턴마다 새로운 관점이나 다른 측면의 질문을 함

[턴 1 특별 규칙]
- 첫 질문이므로 "추천해주신 목록", "1번 회사" 같은 표현 절대 금지
- 당신의 페르소나(전공, 경력, 기술스택, 희망지역)를 바탕으로 직무 추천을 요청하는 질문만 생성

[당신이 다음에 할 질문]:
"""
)

user_agent_chain = RunInvokeAdapter(USER_AGENT_PROMPT | get_llm())

def generate_next_question(persona: dict, chat_history: list, turn_count: int) -> str:
    """페르소나와 대화 기록을 바탕으로 다음 질문을 생성합니다."""
    
    persona_str = ", ".join([f"{k}: {v}" for k, v in persona.items()])
    history_str = "\n".join([f"User: {turn['user']}\nAssistant: {turn.get('assistant', '')}" for turn in chat_history])
    
    next_question = user_agent_chain.invoke({
        "persona": persona_str,
        "chat_history": history_str,
        "turn_count": turn_count
    }).content.strip()
    
    return next_question