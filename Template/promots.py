from langchain.prompts import PromptTemplate
# 하위 프롬프트 템플릿
job_recommendation_prompt = PromptTemplate(
    input_variables=["user_profile", "job_list"],
    template="""
    당신은 전문 채용 어드바이저입니다. 사용자의 프로필과 검색된 직무 목록을 바탕으로 사용자에게 가장 적합한 직무를 추천하세요. 최대 3개의 직무만 추천하세요. 출력은 Markdown 형식으로:
    - **직무 제목**: [제목]
      - **회사명**: [회사명]
      - **설명**: [간략한 직무 설명]
      - **추천 이유**: [사용자 프로필과 직무가 매칭되는 이유]

    **사용자 프로필**:
    {user_profile}

    **직무 목록**:
    {job_list}
    """
)

# 회사 정보 프롬프트
company_info_prompt = PromptTemplate(
    input_variables=["company_data"],
    template="""
    당신은 채용 어드바이저입니다. 주어진 회사 정보를 바탕으로 회사의 개요를 간략히 설명하세요. 출력은 Markdown 리스트 형식으로:
    - 회사명: [이름]
    - 설명: [설명]
    - 산업: [산업]
    - 주요 특징: [주요 특징]

    **회사 정보**:
    {company_data}
    """
)

# 급여 정보 프롬프트
salary_info_prompt = PromptTemplate(
    input_variables=["job_data", "search_results"],
    template="""
    당신은 채용 어드바이저입니다. 주어진 직무 정보와 웹 검색 결과를 바탕으로 해당 직무의 급여 정보를 제공하거나 추정하세요. 검색 결과가 없으면 산업 평균을 기반으로 합리적인 추정을 제공하세요. 출력은 Markdown 형식으로:
    - **직무**: [직무]
    - **회사명**: [회사명]
    - **급여 정보**: [급여 범위 또는 추정]
    - **출처**: [검색 결과 링크 또는 추정 근거]

    **직무 정보**:
    {job_data}

    **검색 결과**:
    {search_results}
    """
)

preparation_advice_prompt = PromptTemplate(
    input_variables=["user_profile", "job_data"],
    template="""
    당신은 채용 어드바이저입니다. 사용자의 프로필과 직무 정보를 바탕으로 직무 지원을 위한 조언을 제공하세요. 출력은 Markdown 리스트 형식으로:
    - **이력서 팁**: [이력서에 포함해야 할 내용]
    - **인터뷰 전략**: [인터뷰에서 강조할 점]
    - **기술 스택 보완**: [부족한 기술 및 학습 제안]

    **사용자 프로필**:
    {user_profile}

    **직무 정보**:
    {job_data}
    """
)

career_advice_prompt = PromptTemplate(
    input_variables=[
        "preparation_advice",
        "salary_info",
        "company_info",
        "job_recommendations",
    ],
    template="""
당신은 채용 어드바이저입니다. 아래 정보를 종합해 구직자에게 실질적인 지원 전략을 제시하세요. **출력은 Markdown 리스트**로 작성합니다:

- **이력서 팁**: 주요 항목·작성 요령
- **인터뷰 전략**: 강조해야 할 경험·질문 대비
- **기술 스택 보완**: 부족 기술·학습 로드맵
- **연봉·회사 인사이트**: 협상 포인트·복지 핵심
- **추천 직무 요약**: 가장 적합한 1‑2개 직무와 이유

---
**준비 팁**
{preparation_advice}

**연봉 정보**
{salary_info}

**회사 정보**
{company_info}

**직무 추천**
{job_recommendations}
"""
)


summary_memory_prompt = PromptTemplate(
    input_variables=["chat_history"],
    template="""
    아래 대화 기록을 요약하세요. 주요 질문, 추천 직무, 제공된 조언을 간략히 정리하고, 사용자의 관심사와 선호도를 반영하세요. 요약은 200자 이내로 작성하세요.

    **대화 기록**:
    {chat_history}
    """
)

