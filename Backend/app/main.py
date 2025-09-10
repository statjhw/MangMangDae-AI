import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# uvicorn으로 실행 시 프로젝트 루트를 인식할 수 있도록 경로를 추가합니다.
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from Backend.app.middleware.middleware import EnhancedSessionMiddleware
from Backend.app.routers import chat as chat_router
from Backend.app.routers import user_stat as user_stat_router

app = FastAPI(
    title="MangMangDae AI API",
    description="AI 기반 직무 추천 어드바이저 API입니다.",
    version="1.0.0"
)

# CORS (Cross-Origin Resource Sharing) 설정
# 환경변수 FRONTEND_ORIGINS 에서 허용할 오리진을 읽습니다(쉼표 구분).
# 예: FRONTEND_ORIGINS="https://mmd-rose.vercel.app,https://mmd-statjhws-projects.vercel.app"
_default_origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "https://mmd-rose.vercel.app",
    "https://mmd-oof1vrst8-statjhws-projects.vercel.app",
]

_origins_env = os.getenv("FRONTEND_ORIGINS", "").strip()
origins = [o.strip() for o in _origins_env.split(",") if o.strip()] if _origins_env else _default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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