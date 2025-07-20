from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import workflow
import uvicorn

app = FastAPI(
    title="개인화 컨설팅 API",
    description="AI 기반의 커리어 분석 서비스",
    version="1.0.0"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # 기본 React 포트
        "http://localhost:3001",  # Vite 설정 포트
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(workflow.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "개인화 컨설팅 API 서버가 실행 중입니다."}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 