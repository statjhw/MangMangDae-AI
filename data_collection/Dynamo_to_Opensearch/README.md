# DynamoDB to OpenSearch 마이그레이션

이 프로젝트는 AWS DynamoDB에 저장된 데이터를 OpenSearch로 마이그레이션하는 도구입니다.

## 개요

- **목적**: DynamoDB의 `wanted_jobs` 테이블 데이터를 OpenSearch 인덱스로 마이그레이션
- **특징**: 배치 처리, 오류 처리, 진행 상황 모니터링, 검증 기능 포함
- **성능**: 대용량 데이터 처리에 최적화된 벌크 인덱싱

## 사전 요구사항

### 1. 환경 설정

`.env` 파일에 다음 환경 변수들을 설정해야 합니다:

```bash
# AWS 설정
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-northeast-2

# OpenSearch 설정
OPENSEARCH_HOST=your_opensearch_endpoint
OPENSEARCH_PORT=443
OPENSEARCH_INDEX=wanted_jobs
```

### 2. Python 패키지 설치

```bash
pip install opensearch-py requests-aws4auth boto3 python-dotenv
```

## 사용 방법

### 1. 기본 마이그레이션 실행

```bash
cd data_collection/Dynamo_to_Opensearch
python migrate.py
```

### 2. 환경 변수를 통한 설정 커스터마이징

```bash
# 배치 크기 설정
export MIGRATION_BATCH_SIZE=200

# 재시도 횟수 설정
export MIGRATION_MAX_RETRIES=5

# 로그 레벨 설정
export MIGRATION_LOG_LEVEL=DEBUG

# 마이그레이션 실행
python migrate.py
```

### 3. Python 코드에서 사용

```python
from migrate import DynamoToOpenSearchMigrator

# 마이그레이션 실행
migrator = DynamoToOpenSearchMigrator(batch_size=100)
stats = migrator.migrate_all()

# 결과 확인
print(f"마이그레이션된 문서: {stats['total_migrated']}")
print(f"오류 수: {stats['total_errors']}")

# 검증
if migrator.verify_migration():
    print("마이그레이션 성공!")
```

## 주요 기능

### 1. 배치 처리
- 메모리 효율적인 배치 단위 처리
- 기본 배치 크기: 100개 문서
- 환경 변수로 배치 크기 조정 가능

### 2. 오류 처리 및 재시도
- 개별 문서 변환 오류 처리
- 벌크 인덱싱 실패 시 재시도 로직
- 상세한 오류 로깅

### 3. 진행 상황 모니터링
- 실시간 진행 상황 표시
- 처리된 문서 수, 오류 수, 소요 시간 표시
- 마이그레이션 속도 계산

### 4. 데이터 검증
- 마이그레이션 완료 후 자동 검증
- OpenSearch 인덱스 문서 수 확인
- 샘플 데이터 검색 테스트

### 5. 데이터 변환
- DynamoDB 스키마를 OpenSearch 스키마로 자동 변환
- 날짜 필드 자동 처리
- 누락된 필드에 대한 기본값 설정

## 파일 구조

```
Dynamo_to_Opensearch/
├── migrate.py          # 메인 마이그레이션 스크립트
├── config.py           # 설정 관리
└── README.md          # 이 파일
```

## 설정 옵션

### 환경 변수

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `MIGRATION_BATCH_SIZE` | 100 | 한 번에 처리할 문서 수 |
| `MIGRATION_MAX_RETRIES` | 3 | 최대 재시도 횟수 |
| `MIGRATION_RETRY_DELAY` | 1 | 재시도 간격 (초) |
| `MIGRATION_LOG_LEVEL` | INFO | 로그 레벨 |

### OpenSearch 매핑

기본적으로 다음 필드들이 매핑됩니다:

- `url`: keyword 타입 (정확한 매칭)
- `title`: text 타입 (전문 검색)
- `company`: text 타입
- `location`: text 타입
- `description`: text 타입
- `requirements`: text 타입
- `salary`: text 타입
- `job_type`: keyword 타입
- `experience_level`: keyword 타입
- `skills`: text 타입
- `created_at`: date 타입
- `updated_at`: date 타입

## 성능 최적화

### 1. 배치 크기 조정
- 메모리 사용량과 처리 속도의 균형
- 권장 배치 크기: 100-500

### 2. OpenSearch 설정
- 샤드 수: 1 (단일 노드)
- 레플리카 수: 0 (개발 환경)
- refresh_interval: 1s (실시간 검색)

### 3. 네트워크 최적화
- 타임아웃 설정
- 재시도 로직
- 연결 풀링

## 문제 해결

### 1. 연결 오류
```bash
# OpenSearch 엔드포인트 확인
curl -X GET "https://your-opensearch-endpoint/_cluster/health"

# AWS 인증 확인
aws sts get-caller-identity
```

### 2. 권한 오류
- DynamoDB 읽기 권한 확인
- OpenSearch 쓰기 권한 확인
- IAM 역할 및 정책 확인

### 3. 메모리 부족
- 배치 크기 줄이기
- 시스템 메모리 확인
- 가비지 컬렉션 강제 실행

### 4. 타임아웃 오류
- 네트워크 연결 확인
- 타임아웃 설정 증가
- 재시도 횟수 증가

## 로그 분석

마이그레이션 과정에서 다음과 같은 로그를 확인할 수 있습니다:

```
INFO - Starting migration from DynamoDB to OpenSearch
INFO - OpenSearch index created/verified
INFO - Progress: 100 documents migrated, 0 errors, elapsed: 5.23s
INFO - Successfully migrated 100 documents
INFO - Migration completed. Stats: {...}
INFO - Migration verification successful
```

## 예상 출력

마이그레이션이 성공적으로 완료되면 다음과 같은 출력을 볼 수 있습니다:

```
==================================================
마이그레이션 완료!
==================================================
총 마이그레이션된 문서: 1500
총 오류 수: 0
총 소요 시간: 45.67초
마이그레이션 속도: 32.85 문서/초
==================================================
✅ 마이그레이션 검증 성공
```

## 주의사항

1. **데이터 백업**: 마이그레이션 전 DynamoDB 데이터 백업 권장
2. **인덱스 중복**: 기존 OpenSearch 인덱스가 있다면 삭제 후 재생성
3. **네트워크 안정성**: 대용량 데이터 마이그레이션 시 안정적인 네트워크 환경 필요
4. **리소스 모니터링**: CPU, 메모리, 네트워크 사용량 모니터링 권장

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
