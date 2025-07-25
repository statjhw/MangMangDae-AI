import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Starlette의 특정 타입 힌트 대신, 표준 라이브러리인 Callable을 사용합니다.

SESSION_COOKIE_NAME = "session_id"

class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. 요청에서 'session_id' 쿠키를 확인합니다.
        session_id = request.cookies.get(SESSION_COOKIE_NAME)

        # 2. 쿠키가 없으면, 새로운 UUID를 생성합니다.
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # 3. 요청 객체의 state에 session_id를 저장하여 API 엔드포인트에서 접근할 수 있도록 합니다.
        request.state.session_id = session_id
        
        # 요청을 처리하고 응답을 받습니다.
        response = await call_next(request)
        
        # 4. 쿠키가 원래 없었다면, 응답에 Set-Cookie 헤더를 추가하여 브라우저에 쿠키를 설정합니다.
        if not request.cookies.get(SESSION_COOKIE_NAME):
            response.set_cookie(
                key=SESSION_COOKIE_NAME,
                value=session_id,
                httponly=True,  # 보안 강화: JavaScript에서 쿠키에 접근하는 것을 막습니다.
                # secure=True,  # 실제 배포 시 HTTPS에서만 쿠키를 전송하도록 이 옵션을 활성화하세요.
                samesite='lax'
            )
            
        return response 