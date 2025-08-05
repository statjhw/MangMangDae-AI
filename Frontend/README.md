# MMD Frontend

MMD(망망대 AI)의 프론트엔드 애플리케이션입니다. React, TypeScript, Vite를 기반으로 구축된 최신 웹 애플리케이션입니다.

## 🚀 주요 기능

- **사용자 정보 입력**: 단계별 폼을 통한 사용자 정보 수집
- **실시간 통계 분석**: 입력된 정보 기반 맞춤형 통계 시각화
- **AI 기반 상담**: RAG 기술을 활용한 지능형 채팅 상담
- **반응형 디자인**: 모든 디바이스에서 최적화된 사용자 경험
- **동적 애니메이션**: Framer Motion을 활용한 부드러운 UI 애니메이션

## 🛠 기술 스택

### Core
- **React 18** - 사용자 인터페이스 라이브러리
- **TypeScript** - 타입 안정성
- **Vite** - 빠른 개발 서버 및 빌드 도구

### UI/UX
- **Tailwind CSS** - 유틸리티 기반 CSS 프레임워크
- **Framer Motion** - 애니메이션 라이브러리
- **Lucide React** - 아이콘 라이브러리
- **React Hook Form** - 폼 상태 관리

### 차트 및 시각화
- **Recharts** - React 차트 라이브러리

### 통신
- **Axios** - HTTP 클라이언트
- **React Hot Toast** - 토스트 알림

## 📁 프로젝트 구조

```
frontend/
├── public/                 # 정적 파일
├── src/
│   ├── components/         # 재사용 가능한 컴포넌트
│   │   ├── common/        # 공통 컴포넌트 (Button, Input, Select)
│   │   ├── charts/        # 차트 컴포넌트 (BarChart, PieChart)
│   │   ├── features/      # 기능별 컴포넌트
│   │   └── layout/        # 레이아웃 컴포넌트 (Header)
│   ├── pages/             # 페이지 컴포넌트
│   ├── types/             # TypeScript 타입 정의
│   ├── utils/             # 유틸리티 함수
│   ├── App.tsx            # 메인 앱 컴포넌트
│   └── main.tsx           # 앱 진입점
├── package.json
├── vite.config.ts         # Vite 설정
├── tailwind.config.js     # Tailwind CSS 설정
└── tsconfig.json          # TypeScript 설정
```

## 🚀 시작하기

### 필수 요구사항
- Node.js 18.0.0 이상
- npm 또는 yarn

### 설치 및 실행

1. **의존성 설치**
   ```bash
   cd frontend
   npm install
   ```

2. **개발 서버 실행**
   ```bash
   npm run dev
   ```
   애플리케이션이 `http://localhost:3000`에서 실행됩니다.

3. **빌드**
   ```bash
   npm run build
   ```

4. **프리뷰**
   ```bash
   npm run preview
   ```

## 🔧 개발 가이드

### 컴포넌트 작성 규칙
- 모든 컴포넌트는 TypeScript로 작성
- Props 인터페이스 정의 필수
- 재사용 가능한 컴포넌트는 `components/common/`에 배치
- 기능별 컴포넌트는 `components/features/`에 배치

### 스타일링 가이드
- Tailwind CSS 클래스 우선 사용
- 커스텀 CSS는 최소화
- 반응형 디자인 고려
- 접근성(Accessibility) 준수

### 애니메이션 가이드
- Framer Motion을 활용한 부드러운 애니메이션
- 성능을 고려한 애니메이션 최적화
- 사용자 경험 향상을 위한 적절한 애니메이션 적용

## 🌐 API 연동

### 백엔드 서버
- 개발 환경: `http://localhost:8000`
- Vite 프록시 설정으로 `/api` 경로를 백엔드로 전달

### 주요 API 엔드포인트
- `POST /api/statistics` - 통계 데이터 조회
- `POST /api/workflow` - 워크플로우 실행
- `GET /api/jobs/search` - 직업 자동완성
- `GET /api/universities/search` - 대학 자동완성

## 📱 반응형 디자인

- **모바일**: 320px ~ 768px
- **태블릿**: 768px ~ 1024px
- **데스크톱**: 1024px 이상

## 🎨 디자인 시스템

### 색상 팔레트
- **Primary**: 파란색 계열 (#3B82F6 ~ #1E3A8A)
- **Secondary**: 회색 계열 (#F8FAFC ~ #0F172A)
- **Success**: 초록색 (#10B981)
- **Warning**: 노란색 (#F59E0B)
- **Error**: 빨간색 (#EF4444)

### 타이포그래피
- **제목**: Inter, 굵은 글씨
- **본문**: Inter, 일반 글씨
- **코드**: 시스템 폰트

## 🔍 성능 최적화

- **코드 스플리팅**: React.lazy를 활용한 지연 로딩
- **이미지 최적화**: WebP 포맷 사용
- **번들 최적화**: Vite의 자동 최적화 활용
- **캐싱**: 적절한 캐싱 전략 적용

## 🧪 테스트

```bash
# 린트 검사
npm run lint

# 타입 체크
npm run type-check
```

## 📦 배포

### 빌드
```bash
npm run build
```

### 배포 파일
빌드 후 `dist/` 폴더에 배포 가능한 파일들이 생성됩니다.

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해주세요. 