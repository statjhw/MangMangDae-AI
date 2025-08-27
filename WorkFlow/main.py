import sys
import os
import json
import logging
import pickle
from dotenv import load_dotenv
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from WorkFlow.SLD.agents import run_job_advisor_workflow
from WorkFlow.Util.user_agent import generate_random_persona, generate_next_question
from DB.redis_connect import RedisConnect
import multiprocessing as mp

redis_connect = RedisConnect()


# --- 기본 설정 ---
# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LangSmith 환경 변수 설정
load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "job_advisor")
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"


STATE_PKL_DIR = "memory/chat_states_pkl"
CHAT_JSON_DIR = "memory/chat_histories_json"
os.makedirs(STATE_PKL_DIR, exist_ok=True)
os.makedirs(CHAT_JSON_DIR, exist_ok=True)



def start_chat_session():
    """
    사용자와의 대화 세션을 시작하고 상태를 관리합니다.
    """
    # 사용자 ID는 실제 앱에서는 로그인 등을 통해 동적으로 할당됩니다.
    user_id = 18
    
    # 기본 사용자 프로필 정보
    base_user_info = {
        "user_id": user_id,
        "candidate_major": "통계학",
        "candidate_interest": "데이터 엔지니어",
        "candidate_career": "5년",
        "candidate_tech_stack": [
            "파이썬", "aws", "정보처리기사", "sql", "kafka", "spark"
        ],
        "candidate_location": "서울, 경기",
    }

    # 프로그램 시작 시, 저장된 이전 대화 상태를 불러옵니다.
    conversation_state = redis_connect.load_state(user_id)
    
    print("\nAssistant: 안녕하세요! 저는 당신의 커리어 어드바이저입니다.")
    if conversation_state:
        print("Assistant: 이전 대화 기록을 불러왔습니다. 이어서 진행할 수 있습니다.")
    print("Assistant: 무엇을 도와드릴까요? (종료하시려면 '종료'를 입력하세요)")

    # 대화 루프 시작
    while True:
        try:
            user_question = input("User: ")
            if user_question.lower() in ["exit", "quit", "종료"]:
                print("Assistant: 이용해주셔서 감사합니다.")
                break

            # 현재 질문과 사용자 프로필을 합쳐서 워크플로우에 전달할 입력값 생성
            current_input = {**base_user_info, "candidate_question": user_question}

            # 워크플로우 실행: 이전 상태를 전달하고, 새로운 상태를 반환받음
            logger.info("Invoking workflow...")
            conversation_state = run_job_advisor_workflow(current_input, conversation_state)
            
            # 워크플로우 실행 후, 최신 상태를 파일에 저장
            redis_connect.save_state(user_id, conversation_state)

            # 대화 기록만 JSON 파일로 저장
            chat_history = conversation_state.get("chat_history", [])
            # if chat_history:
            #     redis_connect.save_chat_history_json(user_id, chat_history)

            # 사용자에게 최종 답변 출력
            final_answer = conversation_state.get("final_answer", "답변을 생성하지 못했습니다.")
            print(f"Assistant: {final_answer}")

        except KeyboardInterrupt:
            print("\nAssistant: 대화를 종료합니다.")
            break
        except Exception as e:
            logger.error("An unexpected error occurred in the chat loop: %s", str(e), exc_info=True)
            print("Assistant: 죄송합니다. 예상치 못한 오류가 발생했습니다. 다시 시도해주세요.")


def run_simulation(user_id: int, num_turns: int = 7):
    """
    '가상 사용자 에이전트'와 '취업 어드바이저' 간의 자동 대화 시뮬레이션을 실행합니다.
    """
    print(f"\n===== 대화 시뮬레이션 시작 (User ID: {user_id}) =====")
    
    # 1. 가상 사용자 페르소나 생성
    persona = generate_random_persona(user_id)
    print("--- User Agent Persona ---")
    print(json.dumps(persona, indent=2, ensure_ascii=False))
    print("-" * 26)

    # 2. 상태 초기화
    job_advisor_state = {}
    simulation_log = []

    # 3. 대화 루프 시작
    for i in range(1, num_turns + 1):
        print(f"\n--- Turn {i} ---")
        
        # 3-1. 사용자 에이전트가 다음 질문 생성
        user_question = generate_next_question(persona, simulation_log, i)
        print(f"User Agent: {user_question}")

        # 3-2. 챗봇 워크플로우에 전달할 입력값 생성
        current_input = {**persona, "candidate_question": user_question}

        # 3-3. 챗봇 워크플로우 실행
        job_advisor_state = run_job_advisor_workflow(current_input, job_advisor_state)

        # 3-4. 챗봇의 최종 답변 가져오기
        assistant_answer = job_advisor_state.get("final_answer", "답변을 생성하지 못했습니다.")
        print(f"Job Advisor: {assistant_answer}")
        
        # 3-5. 시뮬레이션 로그에 대화 기록 추가
        simulation_log.append({
            "user": user_question,
            "assistant": assistant_answer,
            "timestamp": datetime.now().isoformat()
        })
        
        # 챗봇이 대화를 종료하려 하거나, 사용자가 감사를 표하면 루프 중단
        if "감사합니다" in user_question or "이용해주셔서 감사합니다" in assistant_answer:
            print("\n대화가 자연스럽게 종료되었습니다.")
            break
            
    # 4. 최종 대화 로그를 JSON 파일로 저장
    log_file_name = f"simulation_log_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_file_path = os.path.join(CHAT_JSON_DIR, log_file_name)
    try:
        with open(log_file_path, "w", encoding="utf-8") as f:
            json.dump(simulation_log, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 시뮬레이션 대화 로그가 '{log_file_path}'에 저장되었습니다.")
    except Exception as e:
        print(f"\n❌ 로그 저장 실패: {e}")

    print("===== 시뮬레이션 종료 =====")

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    start_chat_session()
    #run_simulation(user_id=411)