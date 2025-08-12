# 🚀 MangMangDae-AI 배포 가이드

## 📋 목차
1. [Backend 배포 (Railway)](#backend-배포-railway)
2. [Frontend 배포 (Vercel)](#frontend-배포-vercel)
3. [환경 변수 설정](#환경-변수-설정)
4. [배포 후 확인사항](#배포-후-확인사항)

---

## Backend 배포 (Railway)

### 1. Railway 프로젝트 생성
1. [Railway](https://railway.app) 로그인
2. "New Project" 클릭
3. "Deploy from GitHub repo" 선택
4. GitHub 저장소 연결 및 권한 부여

### 2. 환경 변수 설정
Railway 대시보드에서 다음 환경 변수들을 설정:

```bash
# 필수 환경 변수
RAILWAY_ENVIRONMENT=production

# Database (PostgreSQL)
DATABASE_URL=<Railway가 자동 생성>
AWS_RDS_HOST=<AWS RDS 호스트>
AWS_RDS_DB=<데이터베이스 이름>
AWS_RDS_USER=<사용자명>
AWS_RDS_PASSWORD=<비밀번호>

# Redis
REDIS_URL=<Railway가 자동 생성>

# API Keys
OPENAI_API_KEY=<OpenAI API 키>
TAVILY_API_KEY=<Tavily API 키>
PINECONE_API_KEY=<Pinecone API 키>
LANGSMITH_API_KEY=<LangSmith API 키>
HUGGINGFACE_API_KEY=<HuggingFace API 키>

# AWS
AWS_ACCESS_KEY_ID=<AWS 액세스 키>
AWS_SECRET_ACCESS_KEY=<AWS 시크릿 키>
AWS_REGION=ap-northeast-2

# OpenSearch
OPENSEARCH_HOST=<OpenSearch 호스트>
OPENSEARCH_PORT=443
OPENSEARCH_INDEX=opensearch_job

# Frontend URL (Vercel 배포 후 설정)
FRONTEND_URL=https://your-app.vercel.app
```

### 3. 배포 설정
Railway는 `railway.toml` 파일을 자동으로 감지하여 배포합니다.

### 4. 서비스 추가 (선택사항)
- PostgreSQL 추가: Railway 대시보드에서 "Add Service" → "Database" → "PostgreSQL"
- Redis 추가: Railway 대시보드에서 "Add Service" → "Database" → "Redis"

---

## Frontend 배포 (Vercel)

### 1. Vercel 프로젝트 생성
1. [Vercel](https://vercel.com) 로그인
2. "Add New" → "Project" 클릭
3. GitHub 저장소 Import
4. Root Directory를 `Frontend`로 설정

### 2. 빌드 설정
```json
{
  "Framework Preset": "Vite",
  "Root Directory": "Frontend",
  "Build Command": "npm run build",
  "Output Directory": "dist",
  "Install Command": "npm install"
}
```

### 3. 환경 변수 설정
Vercel 대시보드 → Settings → Environment Variables:

```bash
# Backend API URL (Railway 배포 URL)
VITE_API_BASE_URL=https://mangmangdae-ai-backend.railway.app
```

### 4. 도메인 설정 (선택사항)
- Vercel 대시보드 → Settings → Domains
- 커스텀 도메인 추가 가능

---

## 환경 변수 설정

### Backend (Railway)
1. Railway 대시보드 → Variables 탭
2. "RAW Editor" 모드로 전환
3. `.env.example` 참고하여 모든 변수 입력
4. "Save" 클릭 → 자동 재배포

### Frontend (Vercel)
1. Vercel 대시보드 → Settings → Environment Variables
2. 변수 추가:
   - Key: `VITE_API_BASE_URL`
   - Value: Railway 배포 URL
   - Environment: Production, Preview, Development
3. "Save" 클릭

---

## 배포 후 확인사항

### ✅ Backend 체크리스트
- [ ] Railway 배포 상태 확인 (초록색 체크)
- [ ] Health check 엔드포인트 응답 확인: `https://your-backend.railway.app/`
- [ ] API 문서 접근 확인: `https://your-backend.railway.app/docs`
- [ ] 로그 확인: Railway 대시보드 → Logs

### ✅ Frontend 체크리스트
- [ ] Vercel 배포 상태 확인
- [ ] 메인 페이지 로딩 확인
- [ ] API 연결 테스트 (채팅 기능)
- [ ] 콘솔 에러 확인 (F12 → Console)

### ✅ 통합 테스트
- [ ] Frontend에서 Backend API 호출 확인
- [ ] CORS 에러 없는지 확인
- [ ] 세션 쿠키 정상 작동 확인
- [ ] 채팅 기능 정상 작동 확인

---

## 🔧 트러블슈팅

### Railway 배포 실패
1. 로그 확인: Railway 대시보드 → Logs
2. 환경 변수 누락 확인
3. Python 버전 확인 (3.11+ 권장)
4. requirements.txt 의존성 확인

### Vercel 배포 실패
1. 빌드 로그 확인
2. Node.js 버전 확인 (18+ 권장)
3. TypeScript 에러 확인
4. 환경 변수 설정 확인

### CORS 에러
1. Backend `config.py`의 `cors_origins` 확인
2. Frontend URL이 허용 목록에 있는지 확인
3. Railway 환경 변수 `FRONTEND_URL` 설정 확인

### API 연결 실패
1. `vercel.json`의 rewrites 설정 확인
2. Backend URL이 올바른지 확인
3. Railway 서비스가 실행 중인지 확인

---

## 📝 참고사항

### 비용 관리
- **Railway**: 월 $5 크레딧 무료 (Hobby 플랜)
- **Vercel**: 무료 플랜으로 충분 (개인 프로젝트)

### 성능 최적화
- Railway: 자동 스케일링 설정
- Vercel: Edge Functions 활용
- CDN 캐싱 활용

### 보안
- 환경 변수에 민감한 정보 저장
- HTTPS 강제 사용
- API 키 정기적 갱신

---

## 📞 지원

문제가 발생하면:
1. 각 플랫폼의 공식 문서 참조
   - [Railway Docs](https://docs.railway.app)
   - [Vercel Docs](https://vercel.com/docs)
2. GitHub Issues에 문제 제기
3. 커뮤니티 포럼 활용
