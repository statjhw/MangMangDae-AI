from langchain.prompts import PromptTemplate

job_recommendation_prompt = PromptTemplate(
    input_variables=["user_profile", "job_list"],
    template="""사용자 프로필: {user_profile}

직무 목록 (각 직무는 직무, 회사, 직무 카테고리, 태그, 위치, 마감일, 포지션 상세, 주요 업무, 자격 요건, 우대 사항, 기술 스택, 혜택 및 복지, 채용 과정, 채용공고 URL 포함):
{job_list}

사용자의 프로필과 질문에 가장 적합한 직무를 추천하고, 추천 이유를 직무 정보(직무, 회사, 기술 스택, 자격 요건 등)를 기반으로 설명하세요."""
)

company_info_prompt = PromptTemplate(
    input_variables=["company_data"],
    template="""회사 정보 (포지션 상세 포함):
{company_data}

위 정보를 바탕으로 회사 개요를 간결히 작성하세요."""
)

salary_info_prompt = PromptTemplate(
    input_variables=["job_data", "search_results"],
    template="""직무 정보 (직무, 회사 포함):
{job_data}

검색 결과:
{search_results}

위 정보를 바탕으로 급여 정보를 요약하세요."""
)

preparation_advice_prompt = PromptTemplate(
    input_variables=["user_profile", "job_data"],
    template="""사용자 프로필: {user_profile}

직무 정보 (직무, 회사, 주요 업무, 자격 요건, 기술 스택, 혜택 및 복지 등 포함):
{job_data}

위 정보를 바탕으로 직무 준비 조언을 제공하세요."""
)

summary_memory_prompt = PromptTemplate(
    input_variables=["job_recommendations", "company_info", "salary_info", "preparation_advice", "chat_history"],
    template="추천: {job_recommendations}\n회사: {company_info}\n급여: {salary_info}\n조언: {preparation_advice}\n대화: {chat_history}\n요약하세요."
)

job_verification_prompt = PromptTemplate(
    input_variables=["user_profile", "question", "job_documents"],
    template="""사용자 프로필: {user_profile}
질문: {question}
직무 문서 (직무, 회사, 직무 카테고리, 태그, 위치, 마감일, 포지션 상세, 주요 업무, 자격 요건, 우대 사항, 기술 스택, 혜택 및 복지, 채용 과정, 채용공고 URL 포함):
{job_documents}

위 문서가 사용자의 질문과 프로필에 적합한지 평가하세요. 적합하면 "is_relevant: true"를, 적합하지 않으면 "is_relevant: false"와 함께 수정된 검색 쿼리("revised_query")를 JSON 형식으로 반환하세요. 예시 형식:

{{
  "is_relevant": false,
  "revised_query": "프롬프트 엔지니어 직무 한국"
}}"""
)

react_prompt = PromptTemplate(
    input_variables=["input", "agent_scratchpad", "tools", "tool_names"],
    template="""사용자 입력: {input}

다음 도구를 사용해 단계를 순차적으로 수행하세요:
1. parse_input_tool: 입력을 파싱.
2. recommend_jobs_tool: 직무 추천.
3. verify_job_relevance_tool: 추천 직무 적합성 검증 (retry_count < 2이고 revised_query 있으면 recommend_jobs_tool 재호출).
4. get_company_info_tool: 회사 정보 조회.
5. get_salary_info_tool: 급여 정보 조회.
6. get_preparation_advice_tool: 준비 조언 제공.
7. summarize_results_tool: 결과 요약.

사용 가능한 도구: {tool_names}
도구 세부 정보:
{tools}

각 단계에서 다음 형식으로 응답:
Thought: [생각]
Action: [도구 이름]
Action Input: [state]

대화 기록과 중간 결과를 참고하세요. retry_count가 2에 도달하면 재검색 없이 다음 단계로 진행.

{agent_scratchpad}
"""
)