import sys
import os
import logging
from dotenv import load_dotenv
from WorkFlow.SLD.agents import run_job_advisor_workflow
from langsmith import Client
from langchain.callbacks.tracers import LangChainTracer

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LangSmith 환경 변수 설정
load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "job_advisor")
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

def invoke_workflow():
    """LangGraph 기반으로 워크플로우 실행."""
    user_input = {
        "candidate_major": "통계학과 및 수학과",
        "candidate_interest": "수학과 교수",
        "candidate_career": "수학과 박사 졸업",
        "candidate_tech_stack": ["Latex", "위상수학", "대수학", "해석학", "미적분학", "확률론"],
        "candidate_location": "서울",
        "candidate_question": "현재 수학과 박사 졸업했고, 수학과 박사를 원하는 회사가 있을까?"
    }
    
    try:
        # LangSmith 트레이서 초기화
        tracer = LangChainTracer(
            project_name=os.getenv("LANGSMITH_PROJECT", "job_advisor")
        )
        
        # LangGraph 워크플로우 실행
        logger.info("Starting workflow with LangSmith tracing enabled")
        result = run_job_advisor_workflow(user_input)
        logger.info("Workflow completed with LangSmith tracing")
        
        # 최종 결과 출력
        print("\n\n=== 최종 답변 ===")
        print(result.get("final_answer", "결과 없음"))
        print("\n=== 추가 정보 ===")
        print(f"검색 재시도 횟수: {result.get('retry_count', 0)}")
        print("\n=== LangSmith 추적 정보 ===")
        print(f"프로젝트: {os.getenv('LANGSMITH_PROJECT', 'job_advisor')}")
        print("자세한 실행 로그는 LangSmith 대시보드에서 확인하세요: https://smith.langchain.com")

        return result.get("final_answer", "결과 없음")
        
    except Exception as e:
        logger.error("Workflow error: %s", str(e))
        print("Error:", str(e))

if __name__ == "__main__":
    # LangGraph 워크플로우 실행 (LangSmith 추적 활성화)
    invoke_workflow()
    