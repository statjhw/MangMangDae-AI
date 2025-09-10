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
        
        print(f"🔍 Middleware: Processing request to {request.url.path}")
        print(f"🍪 Session cookie: {session_id[:8] if session_id else 'None'}...")
        
        # 페이지 로드 헤더들 체크
        is_page_load_header = request.headers.get("X-Page-Load") == "true"
        is_force_new_session = request.headers.get("X-Force-New-Session") == "true"
        page_load_timestamp = request.headers.get("X-Page-Load-Timestamp")
        user_agent = request.headers.get("user-agent", "")
        referer = request.headers.get("referer", "")
        
        print(f"🌐 Referer: {referer}")
        print(f"👤 User-Agent: {user_agent[:50]}..." if user_agent else "👤 No User-Agent")
        print(f"🔄 X-Page-Load header: {is_page_load_header}")
        print(f"🆕 X-Force-New-Session header: {is_force_new_session}")
        print(f"⏰ X-Page-Load-Timestamp: {page_load_timestamp}")
        
        # 강제 새 세션 헤더가 있으면 무조건 새 세션 생성
        if is_force_new_session or is_page_load_header:
            if session_id:
                print(f"🔄 FORCED session reset - ignoring existing session: {session_id[:8]}...")
                # 기존 세션 데이터 삭제 (선택적)
                if self.redis_manager:
                    try:
                        self.redis_manager.redis_client.delete(f"session:{session_id}")
                        print(f"🗑️ Deleted old session data: {session_id[:8]}...")
                    except Exception as e:
                        print(f"❌ Failed to delete old session: {e}")
            
            session_id = str(uuid.uuid4())
            new_session = True
            print(f"🆕 FORCED new session created: {session_id[:8]}...")
            if self.redis_manager:
                self._create_empty_session(session_id)
        
        # 기존 로직들 (fallback)
        elif not session_id:
            session_id = str(uuid.uuid4())
            new_session = True
            print(f"🆕 Creating new session (no cookie): {session_id[:8]}...")
            if self.redis_manager:
                self._create_empty_session(session_id)
        elif self.redis_manager:
            # 세션이 존재하는지만 확인
            session_data = self.redis_manager.load_state(session_id)
            if session_data is None:
                # 세션 데이터가 없으면 새 세션으로 처리
                old_session = session_id[:8]
                session_id = str(uuid.uuid4())
                new_session = True
                print(f"📋 Session {old_session}... expired, creating new: {session_id[:8]}...")
                self._create_empty_session(session_id)
            else:
                print(f"✅ Using existing session: {session_id[:8]}...")
        
        # 요청 상태에 세션 정보 저장
        request.state.session_id = session_id
        request.state.is_new_session = new_session
        
        response = await call_next(request)
        
        # 새 세션인 경우 쿠키 설정 (강제 만료 옵션 추가)
        if new_session:
            # 프로덕션 환경에서는 secure=True, 개발에서는 False
            is_production = os.getenv("DEBUG", "True").lower() == "false"
            response.set_cookie(
                key=SESSION_COOKIE_NAME,
                value=session_id,
                max_age=1800,  # 30분
                path="/",
                httponly=True,
                samesite='none' if is_production else 'lax',  # 크로스 사이트 허용
                secure=is_production  # HTTPS에서만 secure=True
            )
            print(f"🍪 Set new session cookie: {session_id[:8]}...")
            
            # 강제 세션 리셋인 경우 추가 헤더 설정
            if is_force_new_session:
                response.headers["X-Session-Reset"] = "true"
                response.headers["X-New-Session-Id"] = session_id[:8] + "..."
                print(f"📤 Added session reset response headers")
        
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
            # 프로덕션 환경에서는 secure=True, 개발에서는 False
            is_production = os.getenv("DEBUG", "True").lower() == "false"
            response.set_cookie(
                key=SESSION_COOKIE_NAME,
                value=session_id,
                path="/",
                httponly=True,
                samesite='none' if is_production else 'lax',  # 크로스 사이트 허용
                secure=is_production  # HTTPS에서만 secure=True
            )
            
        return response 