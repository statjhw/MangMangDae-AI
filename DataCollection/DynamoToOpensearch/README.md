# 🚀 AI 기반 하이브리드 검색 데이터 파이프라인

이 프로젝트는 AWS DynamoDB에 저장된 채용 공고 데이터를 **AI 임베딩**과 **전처리**를 통해 OpenSearch에 **하이브리드 검색 인덱스**로 변환하는 지능형 데이터 파이프라인입니다.

## 🎯 프로젝트 개요

### 핵심 기능
- **🤖 AI 임베딩**: `intfloat/multilingual-e5-large` 모델을 활용한 1024차원 벡터 임베딩 생성
- **🔍 하이브리드 검색**: BM25(키워드 검색) + KNN(벡터 검색)을 OpenSearch에서 통합 구현
- **⚡ 실시간 처리**: Airflow를 통한 자동화된 데이터 파이프라인
- **📊 데이터 품질**: 전처리 및 정제를 통한 고품질 검색 인덱스 구축

### 왜 OpenSearch 하이브리드인가?

1. **통합 관리**: 키워드 검색과 벡터 검색을 단일 시스템에서 관리
2. **성능 최적화**: 별도 벡터 DB 없이 OpenSearch의 HNSW 알고리즘 활용
3. **비용 효율성**: Pinecone 등 외부 벡터 DB 비용 절약
4. **검색 정확도**: BM25와 Semantic Search의 점수 정규화 및 재정렬로 최적의 결과 제공

## 🔧 기술 스택

### AI/ML 모델
- **임베딩 모델**: `intfloat/multilingual-e5-large`
  - 다국어 지원 (한국어 최적화)
  - 1024차원 고밀도 벡터
  - CUDA/CPU 자동 선택
  - 정규화된 임베딩 (코사인 유사도 최적화)

### 데이터베이스
- **소스**: AWS DynamoDB (`wanted_jobs` 테이블)
- **타겟**: OpenSearch with KNN plugin
- **벡터 알고리즘**: HNSW (Hierarchical Navigable Small World)

## 📋 사전 요구사항

### 1. 환경 변수 설정

`.env` 파일에 다음 설정을 추가하세요:

```bash
# AWS 설정
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-northeast-2

# OpenSearch 설정
OPENSEARCH_HOST=your_opensearch_endpoint
OPENSEARCH_PORT=443
OPENSEARCH_INDEX=your_index
OPENSEARCH_USE_SSL=true
OPENSEARCH_VERIFY_CERTS=true
```

### 2. Python 패키지 설치

```bash
# 핵심 의존성
pip install opensearch-py requests-aws4auth boto3 python-dotenv

# AI/ML 의존성
pip install langchain-huggingface sentence-transformers torch

# 데이터 처리
pip install beautifulsoup4 pandas numpy
```

## 🚀 사용 방법

### 1. AI 임베딩 마이그레이션 실행

```bash
cd DataCollection/DynamoToOpensearch
python migrate.py
```

### 2. 고급 설정 (환경 변수)

```bash
# 배치 크기 설정 (메모리 사용량 조절)
export MIGRATION_BATCH_SIZE=50

# GPU 사용 강제 설정
export CUDA_VISIBLE_DEVICES=0

# 임베딩 모델 캐싱 경로
export TRANSFORMERS_CACHE=/path/to/cache

# 마이그레이션 실행
python migrate.py
```

### 3. Python 코드에서 사용

```python
from migrate import DynamoToOpenSearchMigrator

# AI 임베딩 마이그레이션 실행
migrator = DynamoToOpenSearchMigrator(batch_size=50)
stats = migrator.migrate_all_with_embedding()

# 결과 확인
print(f"🎯 마이그레이션된 문서: {stats['total_migrated']}")
print(f"❌ 오류 수: {stats['total_errors']}")
print(f"⏱️ 총 소요 시간: {stats['total_time']:.2f}초")

# 하이브리드 검색 테스트
search_results = migrator.test_hybrid_search("Python 개발자 채용")
print(f"🔍 검색 결과: {len(search_results)} 건")
```

### 4. Airflow를 통한 자동화

```python
# DataCollection/airflow/crawler_dag.py 에서 자동 실행
# 1. 크롤링 완료 후
# 2. 자동으로 임베딩 생성 및 OpenSearch 인덱싱
# 3. 하이브리드 검색 인덱스 업데이트
```

## ⚡ 주요 기능

### 1. 🤖 AI 임베딩 생성
- **모델**: `intfloat/multilingual-e5-large` (1024차원)
- **전처리**: HTML 태그 제거, 텍스트 정규화, 구조화
- **최적화**: `[document]` 프리픽스로 문서 임베딩 품질 향상
- **성능**: GPU/CPU 자동 선택, 배치 처리로 메모리 효율성

### 2. 🔍 하이브리드 검색 인덱스
- **BM25**: 키워드 기반 전문 검색 (제목, 회사명, 직무 내용)
- **KNN**: 벡터 유사도 검색 (의미적 유사성)
- **HNSW 알고리즘**: ef_construction=108, m=16으로 최적화
- **점수 정규화**: BM25와 KNN 점수를 정규화하여 재정렬

### 3. 📊 데이터 전처리 파이프라인
```python
# 전처리 과정
DynamoDB Raw Data → HTML 정제 → 구조화 → 토큰화 → 임베딩 → OpenSearch
```

### 4. ⚡ 성능 최적화
- **배치 처리**: 기본 50개 문서 (메모리 효율성)
- **병렬 처리**: 임베딩 생성과 인덱싱 병렬화
- **재시도 로직**: 네트워크 오류 시 자동 재시도
- **진행률 모니터링**: 실시간 처리 상태 확인

### 5. 🔧 자동화 및 검증
- **Airflow 통합**: 크롤링 → 임베딩 → 인덱싱 자동화
- **품질 검증**: 마이그레이션 후 자동 검색 테스트
- **오류 처리**: 개별 문서 실패 시에도 전체 프로세스 지속

## 📁 파일 구조

```
DynamoToOpensearch/
├── migrate.py              # 🚀 메인 AI 임베딩 마이그레이션 스크립트
├── data_preprocessing.py   # 🔧 데이터 전처리 및 정제 클래스
├── config.py              # ⚙️ 설정 관리
├── logger.py              # 📝 로깅 설정
├── test_connection.py     # 🔍 연결 테스트 유틸리티
└── README.md             # 📚 이 문서
```

## 🗄️ OpenSearch 데이터 구조

### 인덱스 매핑 (Index Mapping)

```json
{
  "mappings": {
    "properties": {
      // 🔑 기본 채용 정보
      "url": {"type": "keyword"},
      "title": {"type": "text", "analyzer": "standard"},
      "company_name": {"type": "text", "analyzer": "standard"},
      "company_id": {"type": "keyword"},
      "location": {"type": "text", "analyzer": "standard"},
      "job_name": {"type": "text", "analyzer": "standard"},
      "job_category": {"type": "keyword"},
      
      // 📄 상세 정보
      "position_detail": {"type": "text", "analyzer": "standard"},
      "main_tasks": {"type": "text", "analyzer": "standard"},
      "qualifications": {"type": "text", "analyzer": "standard"},
      "preferred_qualifications": {"type": "text", "analyzer": "standard"},
      "benefits": {"type": "text", "analyzer": "standard"},
      "hiring_process": {"type": "text", "analyzer": "standard"},
      
      // 🤖 AI 임베딩 필드 (핵심!)
      "content_embedding": {
        "type": "knn_vector",
        "dimension": 1024,
        "method": {
          "name": "hnsw",
          "engine": "lucene",
          "parameters": {
            "ef_construction": 108,
            "m": 16
          }
        }
      },
      "preprocessed_content": {"type": "text", "analyzer": "standard"},
      
      // 📅 메타데이터
      "crawled_at": {"type": "date"},
      "created_at": {"type": "date"},
      "updated_at": {"type": "date"}
    }
  }
}
```

### 저장되는 문서 예시

```json
{
  // 🔑 기본 정보
  "url": "https://example.com/job/123",
  "title": "Python 백엔드 개발자",
  "company_name": "테크 컴퍼니",
  "company_id": "1234567",
  "location": "서울특별시 강남구",
  "job_name": "백엔드 개발자",
  "job_category": "개발",
  "dead_line": "2024-02-15",
  "crawled_at": "2024-01-15T10:30:00Z",
  
  // 📄 상세 정보 (DynamoDB에 있는 경우만)
  "position_detail": "Python, Django를 활용한 백엔드 개발 업무를 담당합니다...",
  "main_tasks": "• RESTful API 개발 및 유지보수\n• 데이터베이스 설계 및 최적화...",
  "qualifications": "• Python 3년 이상 개발 경험\n• Django/FastAPI 프레임워크 경험...",
  "preferred_qualifications": "• AWS 클라우드 서비스 경험\n• Docker 컨테이너 경험...",
  "benefits": "• 4대보험 완비\n• 연봉 상한 없음\n• 자유로운 휴가제도...",
  "hiring_process": "• 서류전형 → 1차 기술면접 → 2차 임원면접 → 최종합격",
  
  // 🤖 AI 처리 결과
  "preprocessed_content": "직무: Python 백엔드 개발자 회사: 테크 컴퍼니 위치: 서울특별시 강남구 직무 상세: Python, Django를 활용한 백엔드 개발...",
  "content_embedding": [0.1234, -0.5678, 0.9012, ...], // 1024차원 벡터
  
  // 📅 메타데이터
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
