# WorkFlow

LangGraph 기반 워크플로우 관리 모듈입니다.

## 구조
### Util/
- `graph_state.py`: LangGraph 상태 정의
  - 사용자 입력
  - 파싱된 정보
  - 추천 결과
  - 대화 기록
  
### SLD/ (Short-Long-Division)
각 단계별 처리 로직 구현
1. `input_processor.py`: 입력 처리
   - 사용자 입력 파싱
   - 의도 분석
   
2. `job_recommender.py`: 직무 추천
   - 검색 실행
   - 결과 필터링
   
3. `company_info.py`: 회사 정보
   - 회사 데이터 조회
   - 정보 포맷팅
   
4. `salary_info.py`: 급여 정보
   - 급여 데이터 검색
   - 시장 평균 계산
   
5. `advice_generator.py`: 조언 생성
   - 맞춤형 조언 생성
   - 응답 포맷팅

## 워크플로우 예시
```python
from WorkFlow.Util.graph_state import GraphState
from WorkFlow.SLD.input_processor import parse_input
from WorkFlow.SLD.job_recommender import recommend_jobs

# 워크플로우 설정
workflow = StateGraph(GraphState)
workflow.add_node("parse_input", parse_input)
workflow.add_node("recommend_jobs", recommend_jobs)
workflow.set_entry_point("parse_input")
```

## 특징
- 모듈화된 처리 단계
- 상태 기반 워크플로우
- 유연한 확장성
- 에러 처리 및 복구 