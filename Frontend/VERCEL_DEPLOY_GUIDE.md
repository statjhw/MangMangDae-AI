# Vercel 배포 가이드

## 배포 전 체크리스트

### 1. 로컬 테스트
```bash
# 의존성 설치 테스트
npm ci --legacy-peer-deps

# 빌드 테스트
npm run build

# 빌드된 파일 확인
ls -la dist/
```

### 2. Vercel 프로젝트 설정

#### Vercel 대시보드에서 설정할 항목:

1. **Framework Preset**: Vite
2. **Node.js Version**: 18.x
3. **Build & Output Settings**:
   - Build Command: `npm ci --legacy-peer-deps && npm run build`
   - Output Directory: `dist`
   - Install Command: `npm ci --legacy-peer-deps`

4. **Environment Variables** (필요시):
   ```
   VITE_API_URL=https://your-backend-api.com/api
   ```

### 3. 배포 명령어

#### CLI를 통한 배포:
```bash
# Vercel CLI 설치 (전역)
npm i -g vercel

# 프로젝트 연결 및 배포
vercel

# 프로덕션 배포
vercel --prod
```

#### Git 통합 배포:
1. GitHub/GitLab/Bitbucket 저장소 연결
2. main/master 브랜치에 push 시 자동 배포

### 4. 트러블슈팅

#### 의존성 문제 발생 시:
1. `node_modules` 및 `package-lock.json` 삭제
2. 다시 설치:
   ```bash
   rm -rf node_modules package-lock.json
   npm install --legacy-peer-deps
   npm run build
   ```

#### 빌드 실패 시:
1. TypeScript 에러 확인:
   ```bash
   npx tsc --noEmit
   ```

2. Vite 설정 확인:
   ```bash
   npx vite build --debug
   ```

#### 메모리 부족 에러:
Vercel 대시보드에서 Functions 설정:
- Memory: 1024 MB
- Max Duration: 10s

### 5. 배포 후 확인사항

1. **빌드 로그 확인**
   - Vercel 대시보드 > Functions > Logs

2. **성능 확인**
   - Lighthouse 점수 확인
   - 번들 사이즈 확인

3. **기능 테스트**
   - 라우팅 동작 확인
   - API 연결 확인
   - 정적 자산 로딩 확인

### 6. 최적화 팁

1. **이미지 최적화**
   - WebP 포맷 사용
   - Vercel Image Optimization 활용

2. **캐싱 설정**
   - 정적 자산에 대한 캐시 헤더 설정 (vercel.json에 포함됨)

3. **환경별 설정**
   - Preview 환경과 Production 환경 변수 분리

## 현재 설정 요약

- **Node.js**: 18.18.0
- **Package Manager**: npm (with legacy-peer-deps)
- **Framework**: Vite + React + TypeScript
- **Build Output**: /dist
- **SPA Routing**: 모든 경로를 index.html로 리다이렉트

## 문의사항

배포 관련 문제 발생 시 다음 정보와 함께 문의:
1. 빌드 로그 전체
2. package.json 내용
3. vercel.json 설정
4. 에러 메시지 스크린샷
