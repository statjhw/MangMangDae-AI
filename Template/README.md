# Templates

LLM 프롬프트 템플릿 모음입니다.

## 템플릿 구성
1. `template1.py`: 사용자 입력 처리
   - 학력, 경력, 희망 직무 등 정보 추출
   - 구조화된 JSON 형식으로 변환

2. `template2.py`: 직무 추천
   - 사용자 프로필 기반 맞춤형 직무 추천
   - 추천 이유 및 직무 설명 생성

3. `template3.py`: 회사 정보 제공
   - 회사 개요 및 특징 설명
   - 위치, 산업군, 주요 제품/서비스 정보

4. `template4.py`: 맞춤형 조언
   - 이력서 작성 팁
   - 면접 준비 전략
   - 기술 스택 보완 방안

## 사용 예시
```python
from Template.template1 import input_processing_prompt
from langchain.chains import LLMChain
from langchain_openai import OpenAI

llm = OpenAI()
chain = LLMChain(llm=llm, prompt=input_processing_prompt)
result = chain.run(user_input="프론트엔드 개발자 지원하고 싶습니다.")
```

## 특징
- 일관된 출력 형식
- 상황별 최적화된 프롬프트
- 다국어 지원 (한국어/영어) 