# 개인화 컨설팅 API 서버

AI 기반의 커리어 분석 결과를 반환하는 FastAPI 백엔드 서버입니다.

## 기술 스택

- **Python 3.8+**
- **FastAPI**: 고성능 웹 프레임워크
- **Uvicorn**: ASGI 서버
- **Pydantic**: 데이터 검증 및 설정 관리

## 프로젝트 구조

```
backend/
├── app/
│   ├── routers/
│   │   └── workflow.py        # 워크플로우 API 라우터
│   ├── schemas/
│   │   └── workflow_schema.py # Pydantic 모델
│   ├── services/
│   │   └── analysis_service.py # 분석 서비스
│   └── main.py               # FastAPI 애플리케이션
├── requirements.txt          # 의존성 패키지
├── .env                     # 환경 변수
└── README.md               # 프로젝트 문서
```

## 설치 및 실행

### 1. 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 가상환경 활성화 (macOS/Linux)
source venv/bin/activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 서버 실행

```bash
# 개발 모드로 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는 Python으로 직접 실행
python -m app.main
```

서버가 성공적으로 실행되면 http://localhost:8000 에서 접근할 수 있습니다.

## API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API 엔드포인트

### POST /api/workflow

사용자 정보를 받아 AI 기반 커리어 분석을 실행하고 결과를 반환합니다.

**요청 Body:**
```json
{
  "candidate_major": "컴퓨터공학",
  "candidate_career": "신입",
  "candidate_interest": "백엔드 개발",
  "candidate_location": "서울",
  "candidate_tech_stack": ["Python", "Django", "PostgreSQL"],
  "candidate_question": "백엔드 개발자로 취업하기 위해 어떤 준비를 해야 하나요?",
  "candidate_salary": "4000만원"
}
```

**응답 Body:**
```json
{
  "job_recommendations": "직업 추천 내용",
  "company_info": "회사 정보",
  "salary_info": "연봉 정보",
  "preparation_advice": "준비 조언",
  "final_answer": "최종 답변"
}
```

## 프론트엔드 연동

이 API는 프론트엔드 애플리케이션과 연동되도록 설계되었습니다:

1. **CORS 설정**: 프론트엔드 포트(3000)에서의 요청 허용
2. **API 경로**: 프론트엔드의 프록시 설정에 맞춰 `/api` 접두사 사용
3. **데이터 모델**: 프론트엔드의 TypeScript 인터페이스와 정확히 일치

## 개발 정보

- **포트**: 8000
- **호스트**: 0.0.0.0 (모든 인터페이스)
- **리로드**: 개발 모드에서 코드 변경 시 자동 재시작
- **로깅**: INFO 레벨로 설정

## 환경 변수

`.env` 파일에서 다음 설정을 변경할 수 있습니다:

- `API_HOST`: 서버 호스트 (기본값: 0.0.0.0)
- `API_PORT`: 서버 포트 (기본값: 8000)
- `API_DEBUG`: 디버그 모드 (기본값: True)
- `CORS_ORIGINS`: CORS 허용 도메인
- `LOG_LEVEL`: 로깅 레벨 (기본값: INFO) 