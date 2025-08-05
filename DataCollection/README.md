# Data Collection

채용 정보 수집 및 데이터 처리를 위한 모듈입니다.

## 구조
- `Crawler/`: 채용 사이트 크롤링 구현체
  - 원티드, 잡코리아 등의 채용 정보 수집
  - 자동화된 데이터 수집 파이프라인

- `Embedding_to_Pinecone/`: 임베딩 생성 및 저장
  - 채용 공고 텍스트의 벡터 임베딩 생성
  - Pinecone에 임베딩 데이터 저장
  - 캐시 관리 시스템

## 사용 방법
```python
from data_collection.Crawler import WantedCrawler

# 크롤러 초기화
crawler = WantedCrawler()

# 데이터 수집 실행
crawler.run()
``` 