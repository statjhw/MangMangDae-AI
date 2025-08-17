import uuid
import sys
import os
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from DB.redis_connect import RedisSessionManager

SESSION_COOKIE_NAME = "session_id"

class EnhancedSessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        try:
            self.redis_manager = RedisSessionManager()
            print(f"✅ Redis SessionManager initialized successfully")
        except Exception as e:
            print(f"❌ Redis 연결 실패 - 세션 관리가 제한됩니다: {e}")
            self.redis_manager = None
    
    def _create_empty_session(self, session_id: str):
        """새 세션에 대한 기본 빈 데이터를 생성합니다."""
        try:
            empty_session_data = {
                "chat_history": [],
                "session_started": datetime.now().isoformat(),
                "conversation_reset_count": 0
            }
            self.redis_manager.save_session_state(session_id, empty_session_data, "short")
            print(f"📦 Created empty session data for {session_id[:8]}...")
        except Exception as e:
            print(f"❌ Failed to create empty session: {e}")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        session_id = request.cookies.get(SESSION_COOKIE_NAME)
        new_session = False
        should_renew = False
        
        print(f"🔍 Middleware: Processing request to {request.url.path}")
        print(f"🍪 Session cookie received: {session_id[:8] if session_id else 'None'}...")
        print(f"📋 All cookies: {request.cookies}")
        
        if not session_id:
            session_id = str(uuid.uuid4())
            new_session = True
            print(f"🆕 Creating new session: {session_id[:8]}...")
            # 새 세션에 대한 기본 세션 데이터 저장
            if self.redis_manager:
                self._create_empty_session(session_id)
        elif self.redis_manager:
            # Check if session exists and is valid
            session_data = self.redis_manager.load_state(session_id)
            session_exists = session_data is not None
            print(f"📦 Session exists in Redis: {session_exists}")
            if session_exists:
                print(f"💾 Session data size: {len(str(session_data))} chars")
            else:
                # 디버깅: Redis에서 세션 키가 실제로 존재하는지 확인
                redis_key_exists = self.redis_manager.redis_client.exists(f"session:{session_id}")
                print(f"🔑 Redis key exists: {redis_key_exists}")
            
            if not session_exists:
                # Only create new session if current one doesn't exist
                old_session = session_id[:8]
                session_id = str(uuid.uuid4())
                new_session = True
                print(f"📋 Session {old_session}... not found, creating new: {session_id[:8]}...")
                # 새 세션에 대한 기본 세션 데이터 저장
                self._create_empty_session(session_id)
            elif self.redis_manager.should_renew_session(session_id):
                # Mark for renewal but don't create new session yet
                should_renew = True
                print(f"🔄 Session {session_id[:8]}... marked for renewal")
        
        # 요청 상태에 세션 정보 저장
        request.state.session_id = session_id
        request.state.is_new_session = new_session
        
        # 세션 활동 업데이트
        if self.redis_manager and not new_session:
            self.redis_manager.update_session_activity(session_id)
        
        response = await call_next(request)
        
        # Add session renewal header if needed
        if should_renew:
            response.headers["x-session-renewed"] = "true"
            print(f"📤 Added session renewal header for {session_id[:8]}...")
        
        # 새 세션이거나 갱신된 세션인 경우 쿠키 설정
        if new_session or not request.cookies.get(SESSION_COOKIE_NAME):
            response.set_cookie(
                key=SESSION_COOKIE_NAME,
                value=session_id,
                max_age=1800,  # 30분
                path="/",  # 모든 경로에서 쿠키 사용 가능
                httponly=True,
                samesite='lax',
                secure=False  # 개발환경에서는 False, 프로덕션에서는 True
            )
            print(f"🍪 Set session cookie: {session_id[:8]}... (max_age=1800s) with path=/")
        
        print(f"✅ Middleware completed for {session_id[:8]}...")
            
        return response

# 하위 호환성을 위한 기존 클래스 유지
class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        session_id = request.cookies.get(SESSION_COOKIE_NAME)

        if not session_id:
            session_id = str(uuid.uuid4())
        
        request.state.session_id = session_id
        
        response = await call_next(request)
        
        if not request.cookies.get(SESSION_COOKIE_NAME):
            response.set_cookie(
                key=SESSION_COOKIE_NAME,
                value=session_id,
                path="/",
                httponly=True,
                samesite='lax',
                secure=False
            )
            
        return response 