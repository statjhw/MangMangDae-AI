import sys
import os
from fastapi import APIRouter, Request
from fastapi.exceptions import HTTPException
from datetime import datetime
from typing import Dict, List, Any

# 프로젝트 루트 경로를 sys.path에 추가하여 다른 모듈을 임포트할 수 있도록 합니다.
# 이 코드는 uvicorn으로 실행될 때를 대비한 것입니다.
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from Backend.app.schemas.schemas import ChatRequest, ChatResponse
from DB.redis_connect import RedisSessionManager
from WorkFlow.SLD.agents import run_job_advisor_workflow

router = APIRouter()

# RedisSessionManager 인스턴스를 생성합니다.
try:
    redis_connect = RedisSessionManager()
except Exception as e:
    print(f"CRITICAL: Redis 연결에 실패하여 서버를 시작할 수 없습니다. {e}")
    redis_connect = None

# 단순화된 세션 관리 - 복잡한 자동 리셋 로직 제거
def reset_conversation_context(state: Dict[str, Any]) -> Dict[str, Any]:
    """대화 컨텍스트를 완전히 초기화합니다 (사용자가 명시적으로 요청할 때만)"""
    user_profile = state.get("user_input", {})
    
    return {
        "user_input": user_profile,
        "chat_history": [],
        "session_started": datetime.now().isoformat(),
        "reset_count": state.get("reset_count", 0) + 1
    }

def initialize_conversation_state(session_id: str, chat_request: ChatRequest) -> Dict[str, Any]:
    """새로운 대화 상태를 초기화합니다."""
    user_profile = chat_request.user_profile or {}
    
    return {
        "user_input": user_profile,
        "chat_history": [],
        "session_started": datetime.now().isoformat(),
        "reset_count": 0
    }

@router.post("/chat", response_model=ChatResponse)
async def handle_chat(request: Request, chat_request: ChatRequest):
    if not redis_connect:
        raise HTTPException(status_code=503, detail="Redis 서버에 연결할 수 없습니다.")

    session_id = request.state.session_id
    is_new_session = getattr(request.state, 'is_new_session', False)
    
    # 단순화된 세션 로직: 새 세션이면 초기화, 아니면 기존 상태 로드
    if is_new_session:
        previous_state = initialize_conversation_state(session_id, chat_request)
        print(f"✨ 새로운 세션 시작: {session_id[:8]}...")
    else:
        previous_state = redis_connect.load_state(session_id) or initialize_conversation_state(session_id, chat_request)
        print(f"📝 기존 세션 계속: {session_id[:8]}... (대화 길이: {len(previous_state.get('chat_history', []))})")

    # WorkFlow 입력 구성
    user_profile = chat_request.user_profile or {}
    current_input = {
        **user_profile, 
        "user_id": session_id,
        "candidate_question": chat_request.question
    }

    try:
        # WorkFlow 실행
        final_state = run_job_advisor_workflow(current_input, previous_state)

        # 세션 상태 저장
        redis_connect.save_session_state(session_id, final_state, "short")

        # 응답 생성
        final_answer = final_state.get("final_answer", "죄송합니다. 답변을 생성하는 데 실패했습니다.")

        return ChatResponse(session_id=session_id, answer=final_answer)

    except Exception as e:
        print(f"워크플로우 실행 중 오류 발생 (세션 ID: {session_id[:8]}...): {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다. 다시 시도해주세요.")

@router.post("/chat/reset")
async def reset_conversation(request: Request):
    """현재 세션의 대화를 초기화합니다."""
    if not redis_connect:
        raise HTTPException(status_code=503, detail="Redis 서버에 연결할 수 없습니다.")
    
    session_id = request.state.session_id
    
    try:
        # 기존 상태 로드
        current_state = redis_connect.load_state(session_id) or {}
        
        # 대화 컨텍스트 리셋
        reset_state = reset_conversation_context(current_state)
        
        # 상태 저장
        redis_connect.save_session_state(session_id, reset_state, "short")
        
        print(f"🔄 대화 리셋 완료: {session_id[:8]}...")
        
        return {
            "session_id": session_id,
            "message": "대화가 초기화되었습니다.",
            "reset_count": reset_state.get("reset_count", 0)
        }
        
    except Exception as e:
        print(f"대화 리셋 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="대화 초기화에 실패했습니다.")

# 복잡한 스레드 관리 기능 제거됨

@router.get("/session/info")
async def get_session_info(request: Request):
    """현재 세션의 기본 정보를 반환합니다."""
    if not redis_connect:
        raise HTTPException(status_code=503, detail="Redis 서버에 연결할 수 없습니다.")
    
    session_id = request.state.session_id
    
    try:
        current_state = redis_connect.load_state(session_id)
        chat_history_length = len(current_state.get("chat_history", [])) if current_state else 0
        session_ttl = redis_connect.redis_client.ttl(f"session:{session_id}")
        
        from datetime import datetime
        
        return {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "expires_at": datetime.now().isoformat(),
            "message_count": chat_history_length,
            "is_active": session_ttl > 0 and current_state is not None,
            "time_until_expiry": max(0, session_ttl),
            "is_new_session": getattr(request.state, 'is_new_session', False)
        }
        
    except Exception as e:
        print(f"세션 정보 조회 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="세션 정보를 가져올 수 없습니다.")

# 세션 정리 기능 제거됨 (Redis TTL에 의해 자동 관리됨)

@router.get("/session/stats")
async def get_session_statistics(request: Request):
    """간단한 세션 통계를 반환합니다."""
    if not redis_connect:
        raise HTTPException(status_code=503, detail="Redis 서버에 연결할 수 없습니다.")
    
    try:
        current_session_id = request.state.session_id
        current_state = redis_connect.load_state(current_session_id)
        
        return {
            "current_session": {
                "session_id": current_session_id[:8] + "...",
                "has_state": current_state is not None,
                "chat_history_length": len(current_state.get("chat_history", [])) if current_state else 0
            },
            "status": "active"
        }
        
    except Exception as e:
        print(f"세션 통계 조회 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="세션 통계를 가져올 수 없습니다.")

@router.delete("/session/clear")
async def clear_current_session(request: Request):
    """현재 세션 데이터를 삭제합니다."""
    if not redis_connect:
        raise HTTPException(status_code=503, detail="Redis 서버에 연결할 수 없습니다.")
    
    session_id = request.state.session_id
    is_force_clear = request.headers.get("X-Force-Clear") == "true"
    
    try:
        # 세션 데이터 삭제
        deleted = redis_connect.redis_client.delete(f"session:{session_id}")
        
        # 강제 클리어인 경우 추가 작업 수행
        if is_force_clear:
            print(f"🧹 Force clear requested for session: {session_id[:8]}...")
            
            # 관련된 모든 키 패턴 삭제 시도
            try:
                keys_to_delete = redis_connect.redis_client.keys(f"*{session_id}*")
                if keys_to_delete:
                    redis_connect.redis_client.delete(*keys_to_delete)
                    print(f"🗑️ Deleted {len(keys_to_delete)} related keys")
            except Exception as e:
                print(f"❌ Failed to delete related keys: {e}")
        
        response_data = {
            "session_id": session_id[:8] + "...",
            "message": "세션 데이터가 삭제되었습니다." if not is_force_clear else "세션이 강제로 완전히 삭제되었습니다.",
            "deleted": deleted > 0,
            "force_clear": is_force_clear,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"✅ Session clear completed: {response_data}")
        return response_data
        
    except Exception as e:
        print(f"세션 삭제 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="세션 삭제에 실패했습니다.") 