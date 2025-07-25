import sys
import os
from fastapi import APIRouter, Request
from fastapi.exceptions import HTTPException

# 프로젝트 루트 경로를 sys.path에 추가하여 다른 모듈을 임포트할 수 있도록 합니다.
# 이 코드는 uvicorn으로 실행될 때를 대비한 것입니다.
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.schemas.schemas import ChatRequest, ChatResponse
from db.redis_connect import RedisConnect
from WorkFlow.SLD.agents import run_job_advisor_workflow

router = APIRouter()

# RedisConnect 인스턴스를 생성합니다.
# 실제 프로덕션에서는 Depends를 사용한 의존성 주입을 고려할 수 있습니다.
try:
    redis_connect = RedisConnect()
except Exception as e:
    # Redis 연결 실패는 심각한 문제이므로, 서버 시작 시 확인합니다.
    print(f"CRITICAL: Redis 연결에 실패하여 서버를 시작할 수 없습니다. {e}")
    # 실제 운영 환경에서는 여기서 서버를 종료시키는 로직이 필요할 수 있습니다.
    redis_connect = None

@router.post("/chat", response_model=ChatResponse)
async def handle_chat(request: Request, chat_request: ChatRequest):
    if not redis_connect:
        raise HTTPException(status_code=503, detail="Redis 서버에 연결할 수 없습니다.")

    # 미들웨어에서 설정한 session_id를 가져옵니다.
    session_id = request.state.session_id
    
    # 1. Redis에서 이전 대화 상태를 불러옵니다.
    previous_state = redis_connect.load_state(session_id)
    if previous_state is None:
        previous_state = {}

    # 2. WorkFlow에 전달할 입력을 구성합니다.
    # 요청 본문에 user_profile이 없으면 빈 딕셔너리를 사용합니다.
    user_profile = chat_request.user_profile or {}
    
    current_input = {
        **user_profile, 
        "user_id": session_id,  # session_id를 워크플로우의 user_id로 사용
        "candidate_question": chat_request.question # 사용자 질문 추가
    }

    try:
        # 3. WorkFlow를 실행합니다.
        # 워크플로우 실행은 동기 함수이므로, 그대로 호출합니다.
        final_state = run_job_advisor_workflow(current_input, previous_state)

        # 4. 업데이트된 상태를 Redis에 저장합니다.
        redis_connect.save_state(session_id, final_state)

        # 5. 최종 답변을 준비하고 응답합니다.
        final_answer = final_state.get("final_answer", "죄송합니다. 답변을 생성하는 데 실패했습니다.")

        return ChatResponse(session_id=session_id, answer=final_answer)

    except Exception as e:
        # 실제 운영에서는 로깅 라이브러리(e.g., loguru, logging)를 사용하세요.
        print(f"워크플로우 실행 중 오류 발생 (세션 ID: {session_id}): {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다. 다시 시도해주세요.") 