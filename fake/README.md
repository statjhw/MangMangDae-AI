# Fake Data Generator

테스트 및 개발용 가상 데이터 생성 모듈입니다.

## 생성 데이터
1. 사용자 프로필
   - 교육 정보 (학력, 전공)
   - 경력 사항
   - 기술 스택
   - 선호 사항 (희망 직무, 지역, 연봉)
   - 사용자 대화 예시

2. 회사 정보
   - 회사명, 위치
   - 산업 분야
   - 채용 공고
   - 기업 문화

## 사용 방법
```python
from fake.user_data_generator import generate_user

# 단일 사용자 데이터 생성
user = generate_user()

# 여러 사용자 데이터 생성
users = [generate_user() for _ in range(10)]
```

## 특징
- 실제와 유사한 데이터 패턴
- 다양한 시나리오 커버
- 일관된 데이터 구조
- 랜덤하지만 의미 있는 조합 