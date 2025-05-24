from typing import Dict, Any, Union, Annotated, TypedDict
import logging
import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnablePassthrough
from langsmith import Client, traceable
from langsmith.run_helpers import get_run_tree_context
from config import get_llm
from WorkFlow.SLD.tools import (
    parse_input_tool, recommend_jobs_tool, verify_job_relevance_tool, 
    get_company_info_tool, get_salary_info_tool, get_preparation_advice_tool, 
    summarize_results_tool
)

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
    user_input: Dict[str, Any]
    parsed_input: Dict[str, Any]
    chat_history: list
    conversation_turn: int
    job_recommendations: str
    selected_job: Any
    company_info: str
    salary_info: str
    preparation_advice: str
    final_answer: str
    retry_count: int
    revised_query: str

# 노드 함수 정의 - 각 도구를 래핑
@traceable(name="parse_input_node")
def parse_input(state: GraphState) -> GraphState:
    """입력 파싱 노드"""
    # state에서 user_input을 추출하여 도구에 전달
    user_input = state.get("user_input", {})
    # parse_input_tool에 필요한 파라미터 이름으로 정확히 전달
    result = parse_input_tool.func(user_input)  # .func를 사용하여 원본 함수에 직접 접근
    # 결과를 state에 병합
    return {**state, **result}

@traceable(name="recommend_jobs_node")
def recommend_jobs(state: GraphState) -> GraphState:
    """직무 추천 노드"""
    # 원래 함수는 state_or_params 파라미터를 받음
    result = recommend_jobs_tool.func(state)  # .func를 사용하여 원본 함수에 직접 접근
    return result

@traceable(name="verify_job_relevance_node")
def verify_job_relevance(state: GraphState) -> GraphState:
    """직무 적합성 검증 노드"""
    result = verify_job_relevance_tool.func(state)
    return result

@traceable(name="get_company_info_node")
def get_company_info(state: GraphState) -> GraphState:
    """회사 정보 조회 노드"""
    result = get_company_info_tool.func(state)
    return result

@traceable(name="get_salary_info_node")
def get_salary_info(state: GraphState) -> GraphState:
    """급여 정보 조회 노드"""
    result = get_salary_info_tool.func(state)
    return result

@traceable(name="get_preparation_advice_node")
def get_preparation_advice(state: GraphState) -> GraphState:
    """준비 조언 제공 노드"""
    result = get_preparation_advice_tool.func(state)
    return result

@traceable(name="summarize_results_node")
def summarize_results(state: GraphState) -> GraphState:
    """결과 요약 노드"""
    result = summarize_results_tool.func(state)
    return result

# 에지 함수 - 조건에 따라 다음 노드 결정
@traceable(name="should_retry_edge")
def should_retry(state: GraphState) -> str:
    """재검색 필요 여부 결정"""
    if state.get("retry_count", 0) > 0 and state.get("retry_count", 0) < 3 and state.get("revised_query"):
        logger.info(f"Retrying with revised query: {state.get('revised_query')}")
        return "recommend_jobs"
    return "get_company_info"

# 워크플로우 그래프 빌드
@traceable(name="build_workflow_graph")
def build_workflow_graph() -> StateGraph:
    """워크플로우 그래프 생성"""
    # 그래프 초기화
    workflow = StateGraph(GraphState)
    
    # 노드 추가
    workflow.add_node("parse_input", parse_input)
    workflow.add_node("recommend_jobs", recommend_jobs)
    workflow.add_node("verify_job_relevance", verify_job_relevance)
    workflow.add_node("get_company_info", get_company_info)
    workflow.add_node("get_salary_info", get_salary_info)
    workflow.add_node("get_preparation_advice", get_preparation_advice)
    workflow.add_node("summarize_results", summarize_results)
    
    # 시작 노드 설정 - START에서 parse_input으로 연결
    workflow.set_entry_point("parse_input")
    
    # 에지 연결 - 기본 실행 경로
    workflow.add_edge("parse_input", "recommend_jobs")
    workflow.add_edge("recommend_jobs", "verify_job_relevance")
    workflow.add_conditional_edges(
        "verify_job_relevance",
        should_retry,
        {
            "recommend_jobs": "recommend_jobs",
            "get_company_info": "get_company_info"
        }
    )
    workflow.add_edge("get_company_info", "get_salary_info")
    workflow.add_edge("get_salary_info", "get_preparation_advice")
    workflow.add_edge("get_preparation_advice", "summarize_results")
    workflow.add_edge("summarize_results", END)
    
    # 그래프 컴파일
    return workflow.compile()

# 그래프 인스턴스 생성
workflow_graph = build_workflow_graph()

# 워크플로우 실행 함수
@traceable(name="job_advisor_workflow")
def run_job_advisor_workflow(user_input: Dict[str, Any]) -> Dict[str, Any]:
    """워크플로우 실행 함수"""
    try:
        # 초기 상태 설정
        initial_state = {"user_input": user_input}
        logger.info(f"Starting workflow with user input: {user_input}")
        
        # LangSmith 프로젝트 설정
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = langsmith_project
        
        # 그래프 실행
        final_state = workflow_graph.invoke(initial_state)
        logger.info("Workflow completed successfully")
        
        # 결과 반환
        return {
            "final_answer": final_state.get("final_answer", "결과를 찾을 수 없습니다."),
            "retry_count": final_state.get("retry_count", 0),
            "job_recommendations": final_state.get("job_recommendations", ""),
            "company_info": final_state.get("company_info", ""),
            "salary_info": final_state.get("salary_info", ""),
            "preparation_advice": final_state.get("preparation_advice", "")
        }
    except Exception as e:
        logger.error(f"워크플로우 실행 오류: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": str(e)}