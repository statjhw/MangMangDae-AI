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
    research_for_advice_tool, formulate_retrieval_query_tool, request_selection_tool, reset_selection_tool,
    resolve_company_context_tool, show_full_posting_and_confirm_tool, expert_research_tool, confirmation_router_tool, request_further_action_tool
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

def last_write_reducer(left: Any, right: Any) -> Any:
    """어떤 키에 대한 업데이트가 충돌하더라도, 항상 최신 값(right)으로 덮어씁니다."""
    return right

# 상태 타입 정의
class GraphState(TypedDict, total=False):
    # --- 핵심 입력 및 사용자 정보 ---
    user_input: Annotated[Dict[str, Any], last_write_reducer]
    user_id: Annotated[int, last_write_reducer]
    company_name_filter: Annotated[List[str], last_write_reducer]

    # --- 대화 흐름 및 맥락 관리 ---
    intent: Annotated[str, last_write_reducer]
    chat_history: Annotated[list, last_write_reducer]
    conversation_turn: Annotated[int, last_write_reducer]
    summary: Annotated[str, last_write_reducer]
    awaiting_selection: Annotated[bool, last_write_reducer]
    current_company: Annotated[str, last_write_reducer]
    company_contexts: Annotated[Dict[str, Any], last_write_reducer]

    # --- 채용 공고 관련 상태 ---
    job_list: Annotated[List[Dict[str, Any]], last_write_reducer]
    selected_job: Annotated[Any, last_write_reducer]
    selected_job_data: Annotated[Dict[str, Any], last_write_reducer]

    # --- 심층 분석 정보 ---
    awaiting_analysis_confirmation: Annotated[bool, last_write_reducer]
    search_result: Annotated[str, last_write_reducer]
    interview_questions_context: Annotated[str, last_write_reducer]
    company_culture_context: Annotated[str, last_write_reducer]
    preparation_advice: Annotated[str, last_write_reducer]

    # --- 최종 결과 ---
    final_answer: Annotated[str, last_write_reducer]
    next_action: Annotated[str, last_write_reducer]

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

@traceable(name="request_selection_node")
def request_selection(state: GraphState) -> GraphState:
    result = request_selection_tool.func(state)
    return {**state, **result}

@traceable(name="reset_selection_node")
def reset_selection(state: GraphState) -> GraphState:
    result = reset_selection_tool.func(state)
    return {**state, **result}

@traceable(name="resolve_company_context_node")
def resolve_company_context(state: GraphState) -> GraphState:
    result = resolve_company_context_tool.func(state)
    return {**state, **result}


@traceable(name="confirmation_router_node")
def confirmation_router(state: GraphState) -> GraphState:
    """LLM을 사용하여 사용자의 확인 의도를 라우팅하는 노드"""
    result = confirmation_router_tool.func(state)
    return {**state, **result}

# 조건부 분기 함수 수정
@traceable(name="should_route_edge")
def should_route(state: GraphState) -> str:
    """사용자 의도와 현재 state를 바탕으로 경로를 결정합니다."""
    intent = state.get("intent", "chit_chat")
    job_list_exists = bool(state.get("job_list")) # 이전 턴에 추천 목록이 있었는지 확인
    job_is_selected = bool(state.get("selected_job"))
    user_question = state.get("user_input", {}).get("candidate_question", "")
    awaiting_selection = state.get("awaiting_selection", False)

    # 심층분석 여부 확인 상태일 때의 분기 로직
    if state.get("awaiting_analysis_confirmation"):
        return "route_confirmation"

    # 강제 선택 모드: 추천 목록 이후에는 선택만 허용
    if job_list_exists and awaiting_selection and not job_is_selected:
        if re.search(r"\d+", user_question):
            state['intent'] = 'select_job'
            return "analyze_selection"
        if any(
            job.get('source_data', {}).get('company_name') and job.get('source_data', {}).get('company_name') in user_question
            for job in state.get('job_list', [])
        ):
            state['intent'] = 'select_job'
            return "analyze_selection"
        
        elif any(keyword in user_question for keyword in ["다른", "새로운", "new", "다른거", "목록"]):
            state['intent'] = 'new_search'
            logger.info("User requested a new search while in selection mode. Routing to reformulate.")
            return "reformulate" # 'new_search' 의도와 동일한 경로로 분기

        # 3. 위 두 경우에 해당하지 않으면, 선택을 다시 요청
        else:
            logger.info("User input is not a valid selection or new search request. Re-prompting.")
            return "request_selection"
    
    if intent == "chit_chat":
        return "dismiss"

    if intent == "select_job":
        return "analyze_selection"
    
    if intent == "initial_search":
        return "recommend_and_present"
    
    if intent == "new_search":
        return "reformulate"

    if intent == "follow_up_qa" and job_is_selected:
        return "qa"
    
    return "dismiss"


@traceable(name="recommend_jobs_node")
def recommend_jobs(state: GraphState) -> GraphState:
    """직무 추천 노드"""
    # 원래 함수는 state_or_params 파라미터를 받음
    result = recommend_jobs_tool.func(state)  # .func를 사용하여 원본 함수에 직접 접근
    return {**state, **result}


@traceable(name="show_and_confirm_node")
def show_and_confirm(state: GraphState) -> GraphState:
    """선택된 공고 전체 내용과 함께 심층 분석 여부를 묻는 노드"""
    result = show_full_posting_and_confirm_tool.func(state)
    return {**state, **result}

@traceable(name="request_further_action_node")
def request_further_action(state: GraphState) -> GraphState:
    """쓸모없는 질문에 대해 행동을 다시 요청하는 노드"""
    # 이 노드는 플래그를 변경하지 않고 메시지만 생성합니다.
    result = request_further_action_tool.func(state)
    return {**state, **result}

def route_after_confirmation(state: GraphState) -> str:
    """`confirmation_router_node`의 결과를 바탕으로 다음 경로를 결정합니다."""
    next_action = state.get("next_action", "request_further_action")
    logger.info(f"Routing to '{next_action}' after LLM confirmation.")
    return next_action

@traceable(name="expert_research_node")
def expert_research(state: GraphState) -> GraphState:
    """Perplexity를 사용한 전문가 리서치 노드"""
    result = expert_research_tool.func(state)
    return {**state, **result}

@traceable(name="get_company_info_node")
def get_company_info(state: GraphState) -> GraphState:
    """회사 정보 검색 노드 (웹 검색)"""
    state["awaiting_analysis_confirmation"] = False # 심층 분석이 시작되므로 플래그를 초기화
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
def generate_final_answer(state: GraphState) -> GraphState: 
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
    workflow.add_node("show_and_confirm", show_and_confirm)
    workflow.add_node("confirmation_router", confirmation_router)  
    workflow.add_node("expert_research", expert_research) # Perplexity 에이전트 노드
    workflow.add_node("request_further_action", request_further_action)
    workflow.add_node("reformulate_query", reformulate_query)
    workflow.add_node("formulate_retrieval_query", formulate_retrieval_query)
    workflow.add_node("request_selection", request_selection)
    workflow.add_node("reset_selection", reset_selection)
    workflow.add_node("resolve_company_context", resolve_company_context)
    workflow.add_node("get_company_info", get_company_info)
    workflow.add_node("research_for_advice", research_for_advice)
    workflow.add_node("get_preparation_advice", get_preparation_advice)
    workflow.add_node("contextual_qa", contextual_qa)
    workflow.add_node("generate_final_answer", generate_final_answer) 
    workflow.add_node("record_history", record_history) 
    
    # 시작 노드 설정
    workflow.set_entry_point("parse_input")
    
    # 엣지 연결
    workflow.add_edge("parse_input", "analyze_intent")
    # 의도 분석 후 현재 회사/비교 대상 해석
    workflow.add_edge("analyze_intent", "resolve_company_context")

    workflow.add_conditional_edges(
        "resolve_company_context",
        should_route,
        {
            "recommend_and_present": "reset_selection",
            "reformulate": "reset_selection",
            "analyze_selection": "load_selected_job",
            "route_confirmation": "confirmation_router",
            "qa": "contextual_qa",
            "dismiss": "generate_final_answer",
            "request_selection": "request_selection"
        }
    )
    
    
    # reset 이후 흐름 연결
    workflow.add_edge("reset_selection", "formulate_retrieval_query")

    # 1. 추천 경로: recommend -> present -> generate_final_answer -> record_history -> END
    workflow.add_edge("formulate_retrieval_query", "recommend_jobs")
    workflow.add_edge("recommend_jobs", "present_candidates")
    workflow.add_edge("present_candidates", "generate_final_answer")
    
    # 2. 선택 후 심층 분석 경로: load -> get_company_info -> ... -> generate_final_answer 
    workflow.add_edge("load_selected_job", "show_and_confirm")
    workflow.add_edge("show_and_confirm", "generate_final_answer")
    
    
    workflow.add_conditional_edges(
        "confirmation_router",
        route_after_confirmation,
        {
            "start_deep_analysis": "get_company_info",      # 동의 -> 심층 분석 시작
            "reset_and_reformulate": "reset_selection",     # 다른 회사 -> 새 검색 시작
            "expert_research": "expert_research",           # 추가 질문 -> 전문가 검색
            "request_further_action": "request_further_action" # 잡담 -> 재요청
        }
    )

    workflow.add_edge("request_further_action", "generate_final_answer")

    workflow.add_edge("get_company_info", "research_for_advice") # get_company_info 다음에 research 추가
    workflow.add_edge("research_for_advice", "get_preparation_advice") # research 결과를 advice 생성에 사용
    workflow.add_edge("get_preparation_advice", "generate_final_answer") # 최종적으로 종합

    # 2.1 다른 회사를 찾고 심층분석
    workflow.add_edge("reformulate_query", "formulate_retrieval_query")


    # 4. 후속 질문 경로: contextual_qa -> generate_final_answer
    workflow.add_edge("contextual_qa", "generate_final_answer")
    workflow.add_edge("expert_research", "generate_final_answer")
    
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
        
        # 중요: 특정 값만 추출하지 않고, 다음 턴을 위해 'final_state' 전체를 반환합니다.
        return final_state

    except Exception as e:
        logger.error(f"워크플로우 실행 오류: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # 오류 발생 시, 다음 턴에 영향을 주지 않도록 이전 상태를 그대로 반환할 수 있습니다.
        return {**previous_state, "error": str(e), "final_answer": "오류가 발생했습니다. 다시 시도해주세요."}