import sys
import os
import json
import logging
import pickle
from dotenv import load_dotenv
from WorkFlow.SLD.agents import run_job_advisor_workflow

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

def save_state(user_id: int, state: dict):
    """대화 상태를 pickle 파일로 저장합니다."""
    state_file = os.path.join(STATE_PKL_DIR, f"state_{user_id}.pkl")
    try:
        with open(state_file, "wb") as f:
            pickle.dump(state, f)
        logger.info(f"State for user {user_id} saved to {state_file}")
    except Exception as e:
        logger.error(f"Failed to save state for user {user_id}: {e}")

def save_chat_history_json(user_id: int, chat_history: list):
    """대화 기록(list)을 JSON 파일로 저장합니다."""
    history_file = os.path.join(CHAT_JSON_DIR, f"history_{user_id}.json")
    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(chat_history, f, ensure_ascii=False, indent=2)
        logger.info(f"Chat history for user {user_id} saved to {history_file}")
    except Exception as e:
        logger.error(f"Failed to save JSON chat history for user {user_id}: {e}")



def load_state(user_id: int) -> dict:
    """pickle 파일에서 대화 상태를 불러옵니다."""
    state_file = f"state_{user_id}.pkl"
    if os.path.exists(state_file):
        try:
            with open(state_file, "rb") as f:
                state = pickle.load(f)
            logger.info(f"State for user {user_id} loaded from {state_file}")
            return state
        except Exception as e:
            logger.error(f"Failed to load or read state file for user {user_id}: {e}")
            return {}
    return {}


def start_chat_session():
    """
    사용자와의 대화 세션을 시작하고 상태를 관리합니다.
    """
    # 사용자 ID는 실제 앱에서는 로그인 등을 통해 동적으로 할당됩니다.
    user_id = 1
    
    # 기본 사용자 프로필 정보
    base_user_info = {
        "user_id": user_id,
        "candidate_major": "경영학",
        "candidate_interest": "**서비스 기획자**",
        "candidate_career": "5년",
        "candidate_tech_stack": [
            "UX/UI 설계", "데이터 분석", "A/B 테스트", "프로젝트 관리"
        ],
        "candidate_location": "**서울 강남**",
    }

    # 프로그램 시작 시, 저장된 이전 대화 상태를 불러옵니다.
    conversation_state = load_state(user_id)
    
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
            save_state(user_id, conversation_state)

            # 대화 기록만 JSON 파일로 저장
            chat_history = conversation_state.get("chat_history", [])
            if chat_history:
                save_chat_history_json(user_id, chat_history)

            # 사용자에게 최종 답변 출력
            final_answer = conversation_state.get("final_answer", "답변을 생성하지 못했습니다.")
            print(f"Assistant: {final_answer}")

        except KeyboardInterrupt:
            print("\nAssistant: 대화를 종료합니다.")
            break
        except Exception as e:
            logger.error("An unexpected error occurred in the chat loop: %s", str(e), exc_info=True)
            print("Assistant: 죄송합니다. 예상치 못한 오류가 발생했습니다. 다시 시도해주세요.")


if __name__ == "__main__":
    start_chat_session()