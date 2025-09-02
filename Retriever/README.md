# Retrieval System

하이브리드 검색 시스템 구현 모듈입니다. AWS Lambda를 활용한 서버리스 검색 서비스를 제공합니다.

## 주요 기능
- Dense 검색 (임베딩 기반)
- Sparse 검색 (BM25)
- 하이브리드 검색 (Dense + Sparse)
- 검색 결과 재순위화 (Cross-Encoder)
- AWS Lambda 서버리스 배포

## 구성 요소
- `hybrid_retriever.py`: 하이브리드 검색 구현 (기존 로컬 버전)
- `lambda_function.py`: AWS Lambda용 하이브리드 검색 구현
- `eval_retriever.py`: 검색 성능 평가 도구

## AWS Lambda 배포

### 환경 변수 설정
```bash
OPENSEARCH_HOST=your-opensearch-domain
OPENSEARCH_INDEX=opensearch_job
AWS_REGION=ap-northeast-2
```

### Lambda 함수 사용 예시
```python
import json
import boto3

# Lambda 클라이언트 생성
lambda_client = boto3.client('lambda')

# 요청 데이터
payload = {
    "user_profile": {
        "candidate_major": "컴퓨터공학",
        "candidate_interest": "프론트엔드 개발",
        "candidate_career": "3년",
        "candidate_tech_stack": ["React", "JavaScript", "TypeScript"],
        "candidate_location": "서울",
        "candidate_question": "React를 사용하는 프론트엔드 개발자 채용공고를 찾아주세요"
    },
    "top_k": 5,
    "exclude_ids": []
}

# Lambda 함수 호출
response = lambda_client.invoke(
    FunctionName='hybrid-retriever',
    Payload=json.dumps(payload)
)

# 결과 파싱
result = json.loads(response['Payload'].read())
```

### HTTP API 사용 예시
```bash
curl -X POST https://your-api-gateway-url/search \
  -H "Content-Type: application/json" \
  -d '{
    "user_profile": {
      "candidate_major": "컴퓨터공학",
      "candidate_interest": "백엔드 개발",
      "candidate_career": "신입",
      "candidate_tech_stack": ["Python", "FastAPI"],
      "candidate_location": "서울",
      "candidate_question": "Python 백엔드 신입 개발자 채용공고"
    },
    "top_k": 5
  }'
```

## 특징
- **하이브리드 검색**: OpenSearch의 키워드 검색(BM25)과 벡터 검색(Dense) 결합
- **지능적 경력 필터링**: 신입/경력 구분 및 경력 년차 매칭
- **Cross-Encoder 재순위화**: 검색 정확도 향상을 위한 2단계 랭킹
- **서버리스 아키텍처**: AWS Lambda를 통한 확장 가능한 배포
- **콜드 스타트 최적화**: 모델 로딩 캐싱으로 성능 향상
- **메모리 효율성**: 배치 처리 및 캐시 관리 최적화

## 성능 최적화
- 모델 캐싱: SentenceTransformer, CrossEncoder 모델 재사용
- 배치 처리: 리랭킹 시 배치 크기 4로 메모리 효율성 확보
- 캐시 디렉토리: Lambda `/tmp` 디렉토리 활용
- 2단계 검색: 초기 검색 후 리랭킹으로 정확도 향상