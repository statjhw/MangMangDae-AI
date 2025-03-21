# 📦 Feature: Store Job Postings to Document DB

이 브랜치는 웹 또는 API를 통해 수집한 **채용 공고 데이터**를  
**Document DB (예: AWS DynamoDB)**에 저장하는 기능을 개발합니다. 

**AWS DynamoDB를 고려한 이유**
 - 여러 사용자가 로컬 db가 아닌 클라우드 db를 이용하고 공유 및 통합 가능
 - 프리티어로 무료 사용 가능하다.

---

## ✅ 목표

- [x] API 또는 웹 크롤링 방식으로 채용 공고 데이터 수집
- [x] 수집된 데이터를 문서형 구조로 가공
- [x] DynamoDB에 저장하는 함수 또는 모듈 구현
- [ ] 데이터 중복 방지 처리
- [ ] 벡터화 여부를 구분할 수 있는 플래그(`is_vectorized`) 추가

---

## ✅ 규칙 사항 
 - 의존성을 위해 requirements.txt 작성
 - 동시 작업 시 merge 충돌이 일어날 수 있으므로 각각의 브랜치 생성 ex> feature/store-jobposts-to-docdb/jhw


**이 브랜치는 소스 코드만 개발하는 브랜치로 airflow 및 배포를 위한 자동화는 다른 브랜치에서 진행**