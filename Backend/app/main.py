import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# uvicorn으로 실행 시 프로젝트 루트를 인식할 수 있도록 경로를 추가합니다.
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from Backend.app.middleware.middleware import EnhancedSessionMiddleware
from Backend.app.routers import chat as chat_router
from Backend.app.routers import user_stat as user_stat_router
from Backend.app.config import settings

app = FastAPI(
    title="MangMangDae AI API",
    description="AI 기반 직무 추천 어드바이저 API입니다.",
    version="1.0.0"
)

# CORS (Cross-Origin Resource Sharing) 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True, # 쿠키를 포함한 요청을 허용합니다.
    allow_methods=["*"],    # 모든 HTTP 메소드를 허용합니다.
    allow_headers=["*"],    # 모든 HTTP 헤더를 허용합니다.
)

# 향상된 세션 미들웨어를 앱에 추가합니다.
app.add_middleware(EnhancedSessionMiddleware)

# 채팅 라우터를 앱에 포함시킵니다.
app.include_router(chat_router.router, prefix="/api/v1", tags=["Chat"])
app.include_router(user_stat_router.router, prefix="/api/v1", tags=["User Stat"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "MangMangDae AI API에 오신 것을 환영합니다."} 