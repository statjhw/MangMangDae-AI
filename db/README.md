# Database Modules

MangMangDae-AI 프로젝트의 데이터베이스 연결 및 작업을 위한 모듈 패키지입니다.

## 구조

```
db/
├── __init__.py          # 패키지 초기화 및 클래스 export
├── dynamodb.py          # AWS DynamoDB 연결 및 작업
├── pinecone_db.py       # Pinecone 벡터 데이터베이스 연결 및 작업
├── postgres.py          # PostgreSQL 데이터베이스 연결 및 작업
├── logger.py            # 로깅 설정 모듈
├── test_db.py           # 테스트 스크립트
└── README.md            # 이 파일
```

## 사용법

### 기본 import

```python
from db import DynamoDB, Pinecone, Postgres
```

### DynamoDB 사용

```python
from db import DynamoDB

# 초기화
dynamodb = DynamoDB()

# 아이템 가져오기
item = dynamodb.get_item({'id': 'some_id'})

# 테이블 스캔 (제너레이터)
for item in dynamodb.scan_items_generator("wanted_jobs"):
    print(item)
```

### Pinecone 사용

```python
from db import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings

# 임베딩 모델 초기화
embedding_model = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")

# Pinecone 초기화
pinecone = Pinecone(embedding_model=embedding_model)

# 인덱스 사용
index = pinecone.get_index()
```

### PostgreSQL 사용

```python
from db import Postgres

# 초기화
postgres = Postgres()

# 연결
if postgres.connect():
    # 데이터 삽입
    success = postgres.insert_job_url("job_123", "https://example.com/job/123")
    
    # 데이터 업데이트
    success = postgres.update_job_url("job_123", "https://example.com/job/123-updated")
    
    # 연결 종료
    postgres.disconnect()
```

## 환경 변수

다음 환경 변수들이 필요합니다:

### AWS (DynamoDB)
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

### Pinecone
- `PINECONE_API_KEY`

### PostgreSQL
- `AWS_RDS_HOST`
- `AWS_RDS_DB`
- `AWS_RDS_USER`
- `AWS_RDS_PASSWORD`
- `AWS_RDS_PORT` (기본값: 5432)

## 테스트

프로젝트 루트에서 다음 명령어로 테스트를 실행할 수 있습니다:

```bash
python -m db.test_db
```

또는 개별 테스트:

```bash
python -c "from db.test_db import test_dynamodb_scan; test_dynamodb_scan()"
```

## 로깅

모든 클래스는 내장된 `logger.py` 모듈을 사용하여 로깅을 수행합니다. 로그 레벨과 출력 형식은 `db/logger.py`에서 설정할 수 있습니다.

### 로그 레벨 변경

```python
from db.logger import setup_logger
import logging

# DEBUG 레벨로 로거 설정
logger = setup_logger(__name__, log_level=logging.DEBUG)
``` 