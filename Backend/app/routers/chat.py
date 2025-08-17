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

def should_start_new_conversation(state: Dict[str, Any], new_question: str) -> bool:
    """새로운 대화 컨텍스트를 시작해야 하는지 판단합니다."""
    chat_history = state.get("chat_history", [])
    
    # 1. 대화가 너무 길어진 경우 (더 관대하게 설정)
    if len(chat_history) > 25:
        return True
    
    # 2. 명시적 대화 리셋 구문만 처리 (더 명확한 구문들)
    reset_phrases = ["새로운 대화", "대화 초기화", "처음부터 다시", "새로 시작하자", "리셋해줘"]
    if any(phrase in new_question for phrase in reset_phrases):
        return True
    
    # 3. 주제 변경 감지를 더 보수적으로 처리 (숫자 입력 등은 제외)
    if is_significant_topic_change(chat_history, new_question):
        return True
        
    return False

def is_significant_topic_change(chat_history: List[Dict], new_question: str) -> bool:
    """중요한 주제 변경만 감지 (더 보수적인 접근)"""
    if not chat_history or len(chat_history) < 3:
        return False
    
    # 숫자만 입력된 경우 (공고 선택 등) 주제 변경 아님
    if new_question.strip().isdigit():
        return False
    
    # 매우 짧은 응답 (3글자 이하)는 주제 변경 아님
    if len(new_question.strip()) <= 3:
        return False
    
    # 명확한 주제 전환 키워드가 있는 경우만 주제 변경으로 인식
    topic_change_indicators = [
        "이제 다른 얘기",
        "전혀 다른 주제",
        "다른 분야",
        "완전히 다른",
        "바꿔서",
        "대신에",
        "말고"
    ]
    
    new_question_lower = new_question.lower()
    for indicator in topic_change_indicators:
        if indicator in new_question_lower:
            return True
    
    return False

def reset_conversation_context(state: Dict[str, Any]) -> Dict[str, Any]:
    """대화 컨텍스트를 리셋하면서 사용자 프로필은 유지합니다."""
    user_profile = state.get("user_input", {})
    summary = state.get("summary", "")
    
    return {
        "user_input": user_profile,
        "summary": summary,  # 이전 대화 요약은 유지
        "chat_history": [],
        "session_started": datetime.now().isoformat(),
        "conversation_reset_count": state.get("conversation_reset_count", 0) + 1
    }

def initialize_conversation_state(session_id: str, chat_request: ChatRequest) -> Dict[str, Any]:
    """새로운 대화 상태를 초기화합니다."""
    user_profile = chat_request.user_profile or {}
    
    return {
        "user_input": user_profile,
        "chat_history": [],
        "session_started": datetime.now().isoformat(),
        "conversation_reset_count": 0
    }

@router.post("/chat", response_model=ChatResponse)
async def handle_chat(request: Request, chat_request: ChatRequest):
    if not redis_connect:
        raise HTTPException(status_code=503, detail="Redis 서버에 연결할 수 없습니다.")

    session_id = request.state.session_id
    is_new_session = getattr(request.state, 'is_new_session', False)
    
    # 1. 대화 상태 초기화 또는 로드
    if is_new_session:
        previous_state = initialize_conversation_state(session_id, chat_request)
        print(f"✨ 새로운 세션 시작: {session_id}")
    else:
        previous_state = redis_connect.load_state(session_id) or {}
        
        # 새로운 대화 컨텍스트 시작 여부 확인
        if should_start_new_conversation(previous_state, chat_request.question):
            chat_length = len(previous_state.get("chat_history", []))
            previous_state = reset_conversation_context(previous_state)
            print(f"🔄 대화 컨텍스트 리셋: {session_id} (이유: 대화 길이 {chat_length} 또는 명시적 리셋 요청)")
        else:
            print(f"📝 기존 세션 계속: {session_id} (대화 길이: {len(previous_state.get('chat_history', []))})")

    # 2. WorkFlow 입력 구성
    user_profile = chat_request.user_profile or {}
    
    current_input = {
        **user_profile, 
        "user_id": session_id,
        "candidate_question": chat_request.question
    }

    try:
        # 3. WorkFlow 실행
        final_state = run_job_advisor_workflow(current_input, previous_state)

        # 4. 세션 상태 저장 (짧은 TTL 사용)
        redis_connect.save_session_state(session_id, final_state, "short")

        # 5. 응답 생성
        final_answer = final_state.get("final_answer", "죄송합니다. 답변을 생성하는 데 실패했습니다.")

        # 6. 대화 통계 로깅
        chat_history_length = len(final_state.get("chat_history", []))
        reset_count = final_state.get("conversation_reset_count", 0)
        
        if chat_history_length > 10:
            print(f"긴 대화 감지 - 세션: {session_id}, 대화 수: {chat_history_length}, 리셋 횟수: {reset_count}")

        return ChatResponse(session_id=session_id, answer=final_answer)

    except Exception as e:
        print(f"워크플로우 실행 중 오류 발생 (세션 ID: {session_id}): {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다. 다시 시도해주세요.")

@router.post("/chat/reset")
async def reset_conversation(request: Request):
    """현재 세션의 대화 컨텍스트를 명시적으로 리셋합니다."""
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
        
        return {
            "session_id": session_id,
            "message": "대화가 초기화되었습니다.",
            "reset_count": reset_state.get("conversation_reset_count", 0)
        }
        
    except Exception as e:
        print(f"대화 리셋 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="대화 초기화에 실패했습니다.")

@router.get("/chat/thread/{thread_id}")
async def get_conversation_thread(request: Request, thread_id: str):
    """특정 대화 스레드의 정보를 가져옵니다."""
    if not redis_connect:
        raise HTTPException(status_code=503, detail="Redis 서버에 연결할 수 없습니다.")
    
    session_id = request.state.session_id
    
    try:
        thread_key = f"session:{session_id}:thread:{thread_id}"
        thread_metadata = redis_connect.redis_client.get(f"{thread_key}:meta")
        
        if not thread_metadata:
            raise HTTPException(status_code=404, detail="대화 스레드를 찾을 수 없습니다.")
        
        import json
        metadata = json.loads(thread_metadata)
        
        return {
            "session_id": session_id,
            "thread_id": thread_id,
            "metadata": metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"스레드 조회 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="스레드 정보를 가져올 수 없습니다.")

@router.post("/chat/thread/new")
async def create_new_thread(request: Request):
    """새로운 대화 스레드를 생성합니다."""
    if not redis_connect:
        raise HTTPException(status_code=503, detail="Redis 서버에 연결할 수 없습니다.")
    
    session_id = request.state.session_id
    
    try:
        thread_id = redis_connect.create_conversation_thread(session_id)
        
        return {
            "session_id": session_id,
            "thread_id": thread_id,
            "message": "새로운 대화 스레드가 생성되었습니다."
        }
        
    except Exception as e:
        print(f"스레드 생성 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="새로운 스레드를 생성할 수 없습니다.")

@router.get("/session/info")
async def get_session_info(request: Request):
    """현재 세션의 상세 정보를 반환합니다."""
    if not redis_connect:
        raise HTTPException(status_code=503, detail="Redis 서버에 연결할 수 없습니다.")
    
    session_id = request.state.session_id
    
    try:
        # 세션 메타데이터 조회
        metadata = redis_connect.get_session_metadata(session_id)
        state_size = redis_connect.get_state_size(session_id)
        
        # 현재 상태 조회
        current_state = redis_connect.load_state(session_id)
        chat_history_length = len(current_state.get("chat_history", [])) if current_state else 0
        
        # TTL 정보
        session_ttl = redis_connect.redis_client.ttl(f"session:{session_id}")
        
        # 프론트엔드 호환성을 위한 추가 필드
        from datetime import datetime
        
        # is_active 계산: TTL이 0보다 크고 세션 데이터가 존재하면 활성
        is_active = session_ttl > 0 and current_state is not None
        
        # 프론트엔드 SessionInfo 타입에 맞는 응답 구조
        response_data = {
            "session_id": session_id,
            "created_at": metadata.get("session_started", datetime.now().isoformat()) if metadata else datetime.now().isoformat(),
            "last_activity": metadata.get("last_activity", datetime.now().isoformat()) if metadata else datetime.now().isoformat(),
            "expires_at": datetime.now().isoformat(),  # 실제 만료 시간 계산은 복잡하므로 현재 시간으로 대체
            "message_count": chat_history_length,
            "is_active": is_active,
            "time_until_expiry": max(0, session_ttl),  # 0보다 작으면 0으로 설정
            # 백엔드 전용 필드들 (프론트엔드에서 무시됨)
            "metadata": metadata,
            "state_size_bytes": state_size,
            "ttl_remaining_seconds": session_ttl,
            "is_new_session": getattr(request.state, 'is_new_session', False),
            "reset_count": current_state.get("conversation_reset_count", 0) if current_state else 0
        }
        
        return response_data
        
    except Exception as e:
        print(f"세션 정보 조회 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="세션 정보를 가져올 수 없습니다.")

@router.post("/session/cleanup")
async def cleanup_expired_sessions():
    """만료된 세션들을 정리합니다."""
    if not redis_connect:
        raise HTTPException(status_code=503, detail="Redis 서버에 연결할 수 없습니다.")
    
    try:
        # 관리자 권한 체크 (실제 환경에서는 인증 로직 추가 필요)
        redis_connect.cleanup_expired_sessions()
        
        return {
            "message": "만료된 세션 정리가 완료되었습니다.",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"세션 정리 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="세션 정리에 실패했습니다.")

@router.get("/session/stats")
async def get_session_statistics(request: Request):
    """현재 Redis 세션 통계를 반환합니다."""
    if not redis_connect:
        raise HTTPException(status_code=503, detail="Redis 서버에 연결할 수 없습니다.")
    
    try:
        # Redis 키 통계
        session_keys = list(redis_connect.redis_client.scan_iter(match="session:*"))
        meta_keys = list(redis_connect.redis_client.scan_iter(match="session:meta:*"))
        activity_keys = list(redis_connect.redis_client.scan_iter(match="session:activity:*"))
        thread_keys = list(redis_connect.redis_client.scan_iter(match="session:*:thread:*"))
        
        # 현재 세션 정보
        current_session_id = request.state.session_id
        current_state = redis_connect.load_state(current_session_id)
        
        stats = {
            "total_sessions": len(session_keys),
            "total_metadata_entries": len(meta_keys),
            "total_activity_entries": len(activity_keys),
            "total_thread_entries": len(thread_keys),
            "current_session": {
                "session_id": current_session_id,
                "has_state": current_state is not None,
                "chat_history_length": len(current_state.get("chat_history", [])) if current_state else 0
            },
            "redis_info": {
                "used_memory": redis_connect.redis_client.info().get("used_memory_human", "N/A"),
                "connected_clients": redis_connect.redis_client.info().get("connected_clients", 0)
            }
        }
        
        return stats
        
    except Exception as e:
        print(f"세션 통계 조회 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="세션 통계를 가져올 수 없습니다.")

@router.delete("/session/clear")
async def clear_current_session(request: Request):
    """현재 세션의 모든 데이터를 삭제합니다."""
    if not redis_connect:
        raise HTTPException(status_code=503, detail="Redis 서버에 연결할 수 없습니다.")
    
    session_id = request.state.session_id
    
    try:
        # 세션 관련 모든 키 삭제
        keys_to_delete = [
            f"session:{session_id}",
            f"session:meta:{session_id}",
            f"session:activity:{session_id}",
            f"session:{session_id}:active_thread"
        ]
        
        # 스레드 키들도 찾아서 삭제
        thread_pattern = f"session:{session_id}:thread:*"
        thread_keys = list(redis_connect.redis_client.scan_iter(match=thread_pattern))
        keys_to_delete.extend([key.decode() if isinstance(key, bytes) else key for key in thread_keys])
        
        # 실제 삭제
        deleted_count = 0
        for key in keys_to_delete:
            if redis_connect.redis_client.delete(key):
                deleted_count += 1
        
        return {
            "session_id": session_id,
            "message": f"세션 데이터가 삭제되었습니다.",
            "deleted_keys": deleted_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"세션 삭제 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="세션 삭제에 실패했습니다.") 