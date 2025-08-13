from typing import Dict, Any, Union, List, Annotated, TypedDict
import logging
import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from datetime import datetime
from langsmith import Client, traceable
from WorkFlow.SLD.tools import (
    search_company_info_tool, get_preparation_advice_tool, 
    record_history_tool, generate_final_answer_tool, analyze_intent_tool, contextual_qa_tool,
    present_candidates_tool, load_selected_job_tool, recommend_jobs_tool, reformulate_query_tool,
    research_for_advice_tool, formulate_retrieval_query_tool
)
import re

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LangSmith 환경 변수 로드
load_dotenv()
langsmith_api_key = os.getenv("LANGSMITH_API_KEY", "")
langsmith_project = os.getenv("LANGSMITH_PROJECT", "job_advisor")

# LangSmith 클라이언트 초기화
client = Client(api_key=langsmith_api_key)

# 상태 타입 정의
class GraphState(TypedDict, total=False):
    # --- 핵심 입력 및 사용자 정보 ---
    user_input: Dict[str, Any]
    user_id: int
    company_name_filter: List[str] # 유저 질문에 회사명이 포함되어 있다면, 회사명 필터링을 위한 리스트
    
    # --- 대화 흐름 및 맥락 관리 ---
    intent: str
    chat_history: list
    conversation_turn: int
    summary: str # 장기 기억을 위한 대화 요약

    # --- 채용 공고 관련 상태 ---
    job_list: List[Dict[str, Any]] # 추천된 공고 목록
    selected_job: Any     
    selected_job_data: Dict[str, Any] # 사용자가 선택한 특정 공고

    # --- 심층 분석 정보 ---
    search_result: str       # 웹 검색을 통해 얻은 회사 정보
    interview_questions_context: str
    company_culture_context: str
    preparation_advice: str # 면접 및 준비 조언

    # --- 최종 결과 ---
    final_answer: str       # 사용자에게 보여줄 최종 답변

# 노드 함수 정의 - 각 도구를 래핑
@traceable(name="parse_input_node")
def parse_input(state: GraphState) -> GraphState:
    """
    입력 파싱 및 상태 업데이트를 직접 수행하는 노드.
    """
    user_input = state.get("user_input", {})
    if not isinstance(user_input, dict):
        raise ValueError("user_input must be a dictionary within the state.")

    user_id = user_input.get("user_id")
    if not user_id:
        raise ValueError("'user_id' must be provided in the user_input.")

    # --- chat_history 업데이트 ---
    chat_history = state.get("chat_history", [])
    conversation_turn = len(chat_history) + 1
    
    chat_history.append({
        "user": user_input.get("candidate_question"),
        "assistant": "",
        "timestamp": datetime.now().isoformat()
    })

    # --- 변경된 부분만 포함된 딕셔너리 생성 ---
    updates = {
        "chat_history": chat_history,
        "conversation_turn": conversation_turn,
    }
    
    # 기존 state에 업데이트 사항을 병합하여 반환
    return {**state, **updates}

@traceable(name="analyze_intent_node")
def analyze_intent(state: GraphState) -> GraphState:
    """사용자 의도 분석 노드"""
    result = analyze_intent_tool.func(state)
    return {**state, **result}

@traceable(name="contextual_qa_node")
def contextual_qa(state: GraphState) -> GraphState:
    """문맥 기반 후속 질문 답변 노드"""
    result = contextual_qa_tool.func(state)
    return {**state, **result}

@traceable(name="explain_term_node")
def explain_term(state: GraphState) -> GraphState:
    """직전 답변에 대한 설명 제공 노드"""
    result = explain_term_tool.func(state)
    return {**state, **result}

@traceable(name="present_candidates_node")
def present_candidates(state: GraphState) -> GraphState:
    """추천된 후보 목록을 사용자에게 제시하는 노드"""
    result = present_candidates_tool.func(state)
    return {**state, **result}

@traceable(name="load_selected_job_node")
def load_selected_job(state: GraphState) -> GraphState:
    """사용자가 선택한 직무를 state에 로드하는 노드"""
    result = load_selected_job_tool.func(state)
    return {**state, **result}

@traceable(name="reformulate_query_node")
def reformulate_query(state: GraphState) -> GraphState:
    """검색어 재생성 노드"""
    result = reformulate_query_tool.func(state)
    return {**state, **result}

@traceable(name="formulate_retrieval_query_node")
def formulate_retrieval_query(state: GraphState) -> GraphState:
    """리트리버 친화적 쿼리로 변환하는 노드"""
    result = formulate_retrieval_query_tool.func(state)
    return {**state, **result}

# 조건부 분기 함수 수정
@traceable(name="should_route_edge")
def should_route(state: GraphState) -> str:
    """사용자 의도와 현재 state를 바탕으로 경로를 결정합니다."""
    intent = state.get("intent", "chit_chat")
    job_list_exists = bool(state.get("job_list")) # 이전 턴에 추천 목록이 있었는지 확인
    job_is_selected = bool(state.get("selected_job"))
    user_question = state.get("user_input", {}).get("candidate_question", "")

    if job_list_exists and not job_is_selected and re.search(r'\d+', user_question):
        logger.info("Override: Detected a number selection. Forcing route to 'analyze_selection'.")
        state['intent'] = 'select_job' 
        return "analyze_selection"
    
    if intent == "chit_chat":
        return "dismiss"

    if intent == "select_job":
        return "analyze_selection"
    
    if intent == "initial_search":
        return "recommend_and_present"
    
    if intent == "new_search":
        return "reformulate"

    if intent == "explanation_request":
        return "explain"

    # 특정 직무가 선택된 상태에서만 후속 질문(qa) 경로로 안내합니다.
    if intent == "follow_up_qa" and job_is_selected:
        return "qa"
    
    # 그 외의 경우 (예: 직무 선택 없이 후속 질문)는 부적절한 요청으로 간주
    return "dismiss"

@traceable(name="recommend_jobs_node")
def recommend_jobs(state: GraphState) -> GraphState:
    """직무 추천 노드"""
    # 원래 함수는 state_or_params 파라미터를 받음
    result = recommend_jobs_tool.func(state)  # .func를 사용하여 원본 함수에 직접 접근
    return {**state, **result}

@traceable(name="get_company_info_node")
def get_company_info(state: GraphState) -> GraphState:
    """회사 정보 검색 노드 (웹 검색)"""
    result = search_company_info_tool.func(state)
    return {**state, **result}

@traceable(name="research_for_advice_node")
def research_for_advice(state: GraphState) -> GraphState:
    """면접 조언 생성을 위해, 선택된 회사/직무에 대한 웹 검색"""
    result = research_for_advice_tool.func(state)
    return {**state, **result}

@traceable(name="get_preparation_advice_node")
def get_preparation_advice(state: GraphState) -> GraphState:
    """준비 조언 제공 노드"""
    result = get_preparation_advice_tool.func(state)
    return {**state, **result}

@traceable(name="generate_final_answer_node")
def generate_final_answer(state: GraphState) -> GraphState: # 함수 이름을 final_answer -> generate_final_answer로 변경
    """최종 답변 생성 노드"""
    result = generate_final_answer_tool.func(state)
    return {**state, **result}

@traceable(name="record_history_node")
def record_history(state: GraphState) -> GraphState:
    """대화 기록 및 저장 노드"""
    # 이 도구는 state 전체를 수정하고 반환하므로, 병합 없이 그대로 반환
    return record_history_tool.func(state)

# 워크플로우 그래프 빌드
@traceable(name="build_workflow_graph")
def build_workflow_graph() -> StateGraph:
    """워크플로우 그래프 생성"""
    # 그래프 초기화
    workflow = StateGraph(GraphState)
    
    # 노드 추가
    workflow.add_node("parse_input", parse_input)
    workflow.add_node("analyze_intent", analyze_intent)
    workflow.add_node("present_candidates", present_candidates) 
    workflow.add_node("load_selected_job", load_selected_job) 
    workflow.add_node("recommend_jobs", recommend_jobs)
    workflow.add_node("reformulate_query", reformulate_query)
    workflow.add_node("formulate_retrieval_query", formulate_retrieval_query)
    #workflow.add_node("verify_job_relevance", verify_job_relevance)
    workflow.add_node("get_company_info", get_company_info)
    workflow.add_node("research_for_advice", research_for_advice)
    workflow.add_node("get_preparation_advice", get_preparation_advice)
    workflow.add_node("contextual_qa", contextual_qa)
    workflow.add_node("explain_term", explain_term)
    workflow.add_node("generate_final_answer", generate_final_answer) 
    workflow.add_node("record_history", record_history) 
    
    # 시작 노드 설정
    workflow.set_entry_point("parse_input")
    
    # 엣지 연결
    workflow.add_edge("parse_input", "analyze_intent")

    workflow.add_conditional_edges(
        "analyze_intent",
        should_route,
        {
            "recommend_and_present": "formulate_retrieval_query",
            "reformulate": "reformulate_query",
            "analyze_selection": "load_selected_job",
            "qa": "contextual_qa",
            "explain": "explain_term",
            "dismiss": "generate_final_answer"  # chit_chat은 바로 답변 생성으로
        }
    )
    
    # 1. 추천 경로: recommend -> present -> generate_final_answer -> record_history -> END
    workflow.add_edge("formulate_retrieval_query", "recommend_jobs")
    workflow.add_edge("recommend_jobs", "present_candidates")
    workflow.add_edge("present_candidates", "generate_final_answer")
    
    # 2. 선택 후 심층 분석 경로: load -> get_company_info -> ... -> generate_final_answer 
    workflow.add_edge("load_selected_job", "get_company_info")
    workflow.add_edge("get_company_info", "research_for_advice") # get_company_info 다음에 research 추가
    workflow.add_edge("research_for_advice", "get_preparation_advice") # research 결과를 advice 생성에 사용
    workflow.add_edge("get_preparation_advice", "generate_final_answer") # 최종적으로 종합

    # 2.1 다른 회사를 찾고 심층분석
    workflow.add_edge("reformulate_query", "formulate_retrieval_query")


    # 4. 후속 질문 경로: contextual_qa -> generate_final_answer
    workflow.add_edge("contextual_qa", "generate_final_answer")

    # 5. 설명 요청 경로: explain_term -> generate_final_answer
    workflow.add_edge("explain_term", "generate_final_answer")
    
    # 모든 경로는 최종적으로 답변 생성 및 기록 후 종료
    workflow.add_edge("generate_final_answer", "record_history")
    workflow.add_edge("record_history", END)
    # 그래프 컴파일
    return workflow.compile()

# 그래프 인스턴스 생성
workflow_graph = build_workflow_graph()

# 워크플로우 실행 함수
@traceable(name="job_advisor_workflow")
def run_job_advisor_workflow(current_input: Dict[str, Any], previous_state: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    워크플로우 실행 함수.
    이전 대화 상태를 받아 현재 입력을 추가하여 그래프를 실행하고,
    다음 턴을 위해 최종 상태 전체를 반환합니다.
    """
    try:
        # 첫 대화인 경우, 이전 상태를 빈 딕셔너리로 초기화
        if previous_state is None:
            previous_state = {}
        
        # 이전 상태에 현재 사용자 입력을 합쳐서 이번에 실행할 상태를 구성
        # 이렇게 해야 이전 대화의 'job_list' 같은 정보가 유지됩니다.
        state_to_run = {**previous_state, "user_input": current_input}

        logger.info(f"Starting workflow with combined state: {state_to_run}")
        
        # LangSmith 프로젝트 설정
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = langsmith_project
        
        # 준비된 상태로 그래프 실행
        final_state = workflow_graph.invoke(state_to_run)
        logger.info("Workflow completed successfully")

        return final_state
    except Exception as e:
        logger.error(f"Workflow execution error: {e}", exc_info=True)
        return {"error": str(e)}