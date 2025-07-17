from langchain.prompts import PromptTemplate

# 심층분석 경로에서 조언 생성하는 프롬프트
preparation_advice_prompt = PromptTemplate(
    input_variables=["user_profile", "job_data"],
    template="""사용자 프로필: {user_profile}

직무 정보 (직무, 회사, 주요 업무, 자격 요건, 기술 스택, 혜택 및 복지, 희망 근무지, 채용 과정 등 포함):
{job_data}

위 정보를 바탕으로 직무 준비 조언을 제공하세요."""
)

# llm에 이전 대화내용을 요약해서 전달하기 위해 요약본을 생성하는 프롬프트
summary_memory_prompt = PromptTemplate(
    input_variables=["summary", "new_lines"],
    template="""당신은 대화 내용을 계속해서 누적하여 요약하는 유용한 AI 어시스턴트입니다.

현재까지의 대화 요약본은 다음과 같습니다:
{summary}

최근에 다음과 같은 대화가 추가되었습니다:
{new_lines}

기존 요약본에 최근 대화 내용을 자연스럽게 통합하여, 전체 대화의 맥락을 담은 새로운 요약본을 만들어 주세요.
만약 기존 요약본이 비어있다면, 최근 대화 내용만으로 첫 요약본을 생성하면 됩니다.
"""
)

# 최종 답변 생성을 위한 프롬프트 템플릿
final_answer_prompt = PromptTemplate(
    input_variables=["user_profile", "question", "selected_job", "search_result", "preparation_advice"],
    template="""당신은 사용자의 구체적인 고민에 공감하고, 주어진 정보를 활용하여 실질적인 해결책을 제시하는 전문 커리어 코치입니다.

당신의 최우선 목표는 사용자의 **{question}**에 직접적으로 답변하는 것입니다.

아래에 제공된 [추천 회사 정보]와 [준비 조언]은 단순히 나열하는 것이 아니라, 사용자의 질문에 대한 답변을 뒷받침하는 **핵심 근거**로 활용해야 합니다.

**[매우 중요]**
사용자의 고민(예: '블록체인 경험이 없는데 기여할 수 있을까요?')과 [준비 조언]의 각 항목을 직접적으로 연결하여, '왜' 이 조언이 사용자의 현재 문제를 해결하는 데 도움이 되는지 구체적으로 설명해주세요.

예를 들어, "Selenium 학습"이라는 조언이 있다면, "Selenium을 통해 테스트 자동화 역량을 키우는 것은, 귀하가 비록 블록체인 도메인 지식은 부족하더라도 강력한 QA 엔지니어링 기술로 팀의 개발 효율성을 높이는 데 직접적으로 기여할 수 있는 방법입니다." 와 같이 연결해야 합니다.

---
[사용자 프로필]
{user_profile}

[사용자 질문]
{question}

[추천 회사 정보]
{selected_job}

[인터넷 검색 추가 정보]
{search_result}

[준비 조언]
{preparation_advice}
---

위 내용을 바탕으로 사용자의 질문에 대한 맞춤형 답변을 친절하고 전문적인 어조로 작성해주세요.
"""
)

# 의도 분석을 위한 프롬프트 템플릿
intent_analysis_prompt = PromptTemplate(
    input_variables=["chat_history", "question"],
    template="""당신은 대화의 맥락을 파악하여 사용자 의도를 5가지 중 하나로 분류하는 AI입니다.
대화 기록과 현재 질문을 바탕으로 가장 적절한 의도를 하나만 선택하여 소문자로 출력하세요.
(initial_search, new_search, select_job, follow_up_qa, chit_chat)

1.  **initial_search**: 사용자가 대화의 가장 처음에서, 구체적인 조건(전공, 경력 등)을 제시하며 직무 추천을 '처음으로' 요청하는 경우.
2.  **new_search**: 이미 직무 목록을 추천받은 후에, "다른 회사 추천해줘", "이거 말고 다른거" 와 같이 '새로운 목록'을 요구하는 경우. (추천 결과 불만족 포함)
3.  **select_job**: 바로 직전의 AI 응답이 '추천 공고 목록'이었고, 사용자가 그 목록에서 특정 항목을 선택하는 경우. (예: "1번 알려줘", "두 번째 회사 정보 좀", "넥써쓰 회사에 대해 더 궁금해요")
4.  **follow_up_qa**: 특정 회사에 대한 '심층 분석이 완료된 후', 그 회사에 대해 추가적인 질문을 하는 경우. (예: "그럼 면접은 어떻게 준비해야 할까요?", "연봉 정보는 없나요?")
5.  **chit_chat**: "고마워", "안녕" 등 직무 추천과 직접적인 관련이 없는 일상적인 대화.

[대화 기록]
{chat_history}

[현재 사용자 질문]
{question}

[분류 결과]
"""
)

# 후속 질문 답변을 위한 프롬프트 템플릿
contextual_qa_prompt = PromptTemplate(
    input_variables=["company_context", "web_search_context", "question"],
    template="""당신은 채용 공고와 웹 검색 결과를 바탕으로 사용자의 질문에 답변하는 AI 어시스턴트입니다.
제공된 [채용 공고 내용]과 [웹 검색 정보]를 근거로 하여 질문에 대해 상세하고 친절하게 답변해주세요.

- 만약 정보가 없다면, "제공된 정보만으로는 답변하기 어렵습니다." 라고 솔직하게 답변하세요.
- 절대로 추측해서 답변하지 마세요.

[채용 공고 내용]
{company_context}

[웹 검색 정보]
{web_search_context}

[사용자 질문]
{question}

[답변]
"""
)

# 다른 회사로 변환되었을 때 심층분석에서의 새로운 쿼리 생성
reformulate_query_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""당신은 대화의 전체 맥락을 이해하고, 사용자의 다음 검색 의도를 하나의 검색어로 요약하는 AI입니다.
[이전 대화 맥락]
{context}

[사용자의 마지막 요청]
{question}

[지시사항]
위 모든 내용을 바탕으로, 사용자가 진짜 원하는 '다음 검색어'를 한 문장으로 생성하세요.
예시 1: 마지막 요청이 "다른거 찾아줘"라면, 이전 맥락을 바탕으로 "서울 QA 엔지니어"를 생성합니다.
예시 2: 마지막 요청이 "그럼 이번엔 판교로"라면, 이전 맥락과 조합하여 "판교 QA 엔지니어"를 생성합니다.

[생성된 검색어]:
"""
)