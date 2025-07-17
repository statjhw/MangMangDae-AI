from typing import Dict, Any, Union
import logging
import json
import os
from langchain_core.tools import tool
from langsmith import traceable
from WorkFlow.Util.utils import advice_chain, summary_memory_chain, final_answer_chain, intent_analysis_chain, contextual_qa_prompt_chain, reformulate_query_chain
from retrieval.embeddings import get_vector_store, retrieve
from config import get_tavily_tool, RateLimitError
import re

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LangSmith 환경 변수 설정
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "job_advisor")

# 벡터 스토어 초기화
vector_store = get_vector_store()
tavily_tool = get_tavily_tool()

@tool
@traceable(name="analyze_intent_tool")
def analyze_intent_tool(state: Dict[str, Any]) -> Dict[str, str]:
    """대화 기록과 현재 질문을 바탕으로 사용자 의도 분석"""
    summary = state.get("summary")
    chat_history = state.get("chat_history", [])
    question = state.get("parsed_input", {}).get("question", "")
    
    context_for_llm = ""
    # 요약본이 존재하면, 요약본을 컨텍스트로 사용
    if summary:
        context_for_llm = f"이전 대화 요약:\n{summary}"
        logger.info("Using conversation summary for intent analysis.")
    # 요약본이 없으면 (초기 대화), 전체 대화 기록을 사용
    else:
        context_for_llm = "\n".join([f"User: {turn['user']}\nAssistant: {turn['assistant']}" for turn in chat_history])
        logger.info("Using full chat history for intent analysis (no summary yet).")
    # 의도 분석 체인 실행
    intent_result = intent_analysis_chain.invoke({
        "chat_history": context_for_llm,
        "question": question
    }).content.strip()

    # 사용자가 불만족을 표하며 새로운 검색을 원할 경우, 이전 추천을 제외 목록에 추가
    if intent_result == 'new_search' and state.get('job_list'):
        # 이전 턴에서 제시했던 후보 목록('job_list')에서 URL들을 추출
        previous_urls = [job.get('document', '') for job in state.get('job_list', [])]
        
        # 정규식으로 각 문서에서 URL만 뽑아냄
        excluded_urls = []
        for doc in previous_urls:
            match = re.search(r"채용공고 URL:\s*(.*)", doc)
            if match:
                excluded_urls.append(match.group(1).strip())

        # 기존 제외 목록에 새로운 URL들을 추가
        current_excluded = state.get('excluded_jobs', [])
        current_excluded.extend(excluded_urls)
        
        # 중복을 제거하여 state 업데이트
        state['excluded_jobs'] = list(set(current_excluded))
        logger.info(f"Adding {len(excluded_urls)} jobs to the exclusion list for the next search.")
    
    elif intent_result == 'select_job':
        logger.info("Intent is 'select_job', proceeding to load the selected document.")


    return {"intent": intent_result}

def _parse_job_posting(text):
    """단일 채용 공고 문서(text)를 파싱해 딕셔너리로 반환하는 함수"""
    data = {}

    data["직무"] = re.search(r"직무:\s*(.*?)\n", text).group(1).strip() if re.search(r"직무:\s*(.*?)\n", text) else None
    data["회사"] = re.search(r"회사:\s*(.*?)\n", text).group(1).strip() if re.search(r"회사:\s*(.*?)\n", text) else None
    data["태그"] = re.search(r"태그:\s*(.*?)\n", text).group(1).split(", ") if re.search(r"태그:\s*(.*?)\n", text) else None
    data["위치"] = re.search(r"위치:\s*(.*?)\n", text).group(1).strip() if re.search(r"위치:\s*(.*?)\n", text) else None
    data["마감일"] = re.search(r"마감일:\s*(.*?)\n", text).group(1).strip() if re.search(r"마감일:\s*(.*?)\n", text) else None
    data["자격 요건"] = re.search(r"3\. 자격([\s\S]*?)우대 사항:", text).group(1).strip() if re.search(r"3\. 자격([\s\S]*?)우대 사항:", text) else None
    data["우대 사항"] = re.search(r"우대 사항:\n([\s\S]*?)혜택 및 복지:", text).group(1).strip() if re.search(r"우대 사항:\n([\s\S]*?)혜택 및 복지:", text) else None
    data["혜택 및 복지"] = re.search(r"혜택 및 복지:\n([\s\S]*?)채용 과정:", text).group(1).strip() if re.search(r"혜택 및 복지:\n([\s\S]*?)채용 과정:", text) else None
    data["채용 과정"] = re.search(r"채용 과정:\s*(.*?)\n", text).group(1).strip() if re.search(r"채용 과정:\s*(.*?)\n", text) else None
    return data

@tool
@traceable(name="recommend_jobs_tool")
def recommend_jobs_tool(state: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """직무 추천 (vector_store.similarity_search, 재검색 지원)."""
    # 입력 처리
    if isinstance(state, str):
        try:
            state = json.loads(state)
        except:
            try:
                state = eval(state)
            except:
                pass
    
    # state가 아닌 경우 이전 단계의 state 가져오기
    if not isinstance(state, dict) or "parsed_input" not in state:
        logger.warning("Invalid state provided to recommend_jobs_tool: %s", state)
        return {"error": "직무 추천을 위한 유효한 상태가 제공되지 않았습니다."}

    user_profile = state.get("parsed_input", {})

    base_query = user_profile.get("question", "")
    query = f"[query] {base_query}" 
    
    try:
        doc_scores, doc_texts = retrieve(query, exclude_urls=state.get("excluded_jobs", []))
        if not doc_texts:
            return {"job_list": []}
        
        # LLM으로 하나를 선택하는 대신, 전체 후보 목록을 state에 저장
        candidate_jobs = []
        for i, text in enumerate(doc_texts):
            parsed_data = _parse_job_posting(text)
            candidate_jobs.append({
                "index": i + 1,
                "company": parsed_data.get("회사", "정보 없음"),
                "title": parsed_data.get("직무", "정보 없음"),
                "score": doc_scores[i],
                "document": text
            })
        
        return {"job_list": candidate_jobs}

    except Exception as e:
        logger.error("Job recommendation (retrieval) error: %s", str(e))
        
    return {"job_list": []}

@tool
@traceable(name="present_candidates_tool")
def present_candidates_tool(state: Dict[str, Any]) -> Dict[str, str]:
    """job_list를 사용자에게 보여줄 최종 답변 텍스트로 포맷팅합니다."""
    job_list = state.get("job_list", [])
    if not job_list:
        return {"final_answer": "죄송하지만, 현재 조건에 맞는 채용 공고를 찾지 못했습니다. 다른 조건으로 다시 시도해 주시겠어요?"}
    
    response_lines = ["다음은 추천하는 채용 공고 목록입니다. 더 자세히 알아보고 싶은 공고의 번호를 알려주세요.\n"]
    for job in job_list:
        # 각 문서의 전체 텍스트를 파싱하여 주요 정보 추출
        print(job)
        doc_text = job.get('document', '')
        # _parse_job_posting이 None을 반환할 경우를 대비해 빈 dict로 처리
        parsed_data = _parse_job_posting(doc_text) or {}
        
        # 보여줄 정보 가공
        company = parsed_data.get("회사", "정보 없음")
        title = parsed_data.get("직무", "정보 없음")
        location = parsed_data.get("위치", "정보 없음")
        
        # 핵심 태그 3개만 추출
        tags = parsed_data.get("태그", [])
        key_tags = f"🏷️ 핵심 태그: {' / '.join(tags[:3])}" if tags else ""
        
        # (수정된 부분) 자격 요건을 안전하게 가져와서 처리
        summary = "" # summary 변수 초기화
        qualifications_text = parsed_data.get("자격 요건")

        # qualifications_text가 실제 문자열일 때만 요약 생성
        if qualifications_text and isinstance(qualifications_text, str):
            first_line = qualifications_text.split('\n')[0].strip('- ')
            if first_line: # 첫 줄이 비어있지 않다면
                summary = f"✨ 주요 요건: {first_line}"

        # 최종 출력 문자열 조합
        response_lines.append(f"**{job['index']}. {company} - {title}**")
        response_lines.append(f"📍 위치: {location}")
        if key_tags:
            response_lines.append(key_tags)
        if summary: # summary에 내용이 있을 때만 추가
            response_lines.append(summary)
        response_lines.append("-" * 20)
    
    response_lines.append("\n더 자세히 알아보고 싶은 공고의 번호를 알려주세요. 해당 공고에 대한 심층 분석을 제공해 드립니다.")
    return {"final_answer": "\n".join(response_lines)}

# 신규 도구 2: 사용자 선택 로드
@tool
@traceable(name="load_selected_job_tool")
def load_selected_job_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """사용자 입력에서 선택된 번호를 파싱하여 selected_job을 설정합니다."""
    user_question = state.get("parsed_input", {}).get("question", "")
    job_list = state.get("job_list", [])
    
    # "1번", "두번째", "2" 등 숫자 추출
    match = re.search(r'\d+', user_question)
    if match:
        try:
            selected_index = int(match.group(0))
            for job in job_list:
                if job.get('index') == selected_index:
                    logger.info(f"Selected job by index: {selected_index}")
                    return {"selected_job": job.get('document')}
        except (ValueError, IndexError):
            pass # 숫자를 찾았지만 유효하지 않은 경우, 아래의 이름 기반으로 넘어감

    # 2. 숫자가 없으면 회사명 기반 선택 시도
    for job in job_list:
        company_name = job.get('company')
        # 사용자의 질문에 회사명이 포함되어 있는지 확인
        if company_name and company_name in user_question:
            logger.info(f"Selected job by company name: {company_name}")
            return {"selected_job": job.get('document')}
            
    # 최종적으로 아무것도 찾지 못한 경우
    logger.warning(f"Could not parse a valid selection from user input: '{user_question}'")
    return {"selected_job": "오류: 유효한 공고를 선택하지 못했습니다. 목록에 있는 번호나 회사명을 포함하여 다시 말씀해주세요."}


@tool
@traceable(name="reformulate_query_tool")
def reformulate_query_tool(state: Dict[str, Any]) -> Dict[str, str]:
    """전체 대화 맥락을 바탕으로 새로운 검색어를 생성합니다."""
    logger.info("Reformulating search query based on conversation context.")
    
    summary = state.get("summary", "")
    chat_history = state.get("chat_history", [])
    question = state.get("parsed_input", {}).get("question", "") # 예: "다른거 찾아줘"
    
    # 요약본 또는 전체 기록을 컨텍스트로 사용
    context = summary if summary else "\n".join([f"User: {turn['user']}" for turn in chat_history])

    try:
        # LLM을 호출하여 새로운 검색어 생성
        new_query = reformulate_query_chain.invoke({
            "context": context,
            "question": question
        }).content.strip()
        
        logger.info(f"Reformulated query: '{new_query}'")
        
        # 생성된 새 쿼리를 'parsed_input'의 question에 덮어써서 다음 노드로 전달
        # 이렇게 하면 recommend_jobs_tool은 별도 수정 없이 이 쿼리를 사용하게 됨
        updated_parsed_input = state.get("parsed_input", {}).copy()
        updated_parsed_input["question"] = new_query
        
        return {"parsed_input": updated_parsed_input}

    except Exception as e:
        logger.error(f"Query reformulation error: {e}", exc_info=True)
        # 실패 시, 원래 질문을 그대로 사용
        return {"parsed_input": state.get("parsed_input")}


@tool
@traceable(name="search_company_info_tool")
def search_company_info_tool(state: Dict[str, Any]) -> Dict[str, str]:
    """회사 정보를 웹에서 검색하며, intent에 따라 검색어의 맥락을 동적으로 구성합니다."""
    
    selected_job_text = state.get("selected_job")
    if not selected_job_text:
        return {"search_result": "분석할 직무가 선택되지 않았습니다."}
    
    try:
        parsed_job = _parse_job_posting(selected_job_text)
        company_name = parsed_job.get("회사")
        if not company_name:
            return {"search_result": "공고에서 회사 이름을 찾지 못했습니다."}

        # --- [핵심 수정] intent에 따라 질문의 출처를 다르게 설정 ---
        intent = state.get("intent")
        contextual_question = ""

        # 사용자가 후보 목록에서 방금 선택한 경우, 이전 턴의 원래 검색어를 컨텍스트로 사용
        if intent == "select_job":
            chat_history = state.get("chat_history", [])
            # chat_history[-1]은 현재 턴("2번 알려줘"), chat_history[-2]가 이전 턴의 질문
            if len(chat_history) >= 2:
                contextual_question = chat_history[-2].get("user", "")
                logger.info(f"Using previous question for context: '{contextual_question}'")
            else:
                # 예외적인 경우, 현재 턴의 질문을 fallback으로 사용 (거의 발생하지 않음)
                contextual_question = state.get("parsed_input", {}).get("question", "")
        else:
            # 다른 모든 경우에는 현재 턴의 질문을 그대로 사용
            contextual_question = state.get("parsed_input", {}).get("question", "")
        # --- 수정 끝 ---

        search_query = f"{company_name} {contextual_question}"
        logger.info(f"Executing web search with query: '{search_query}'")
        
        search_results = tavily_tool.invoke({"query": search_query})
        
        if not isinstance(search_results, list):
            search_results = [search_results]

        # 제목과 300자로 요약된 내용을 조합
        result_lines = []
        for result in search_results:
            title = result.get('title', '제목 없음')
            content = ' '.join(str(result.get('content', '')).strip().split())
            truncated_content = content[:300] + '...' if len(content) > 300 else content
            result_lines.append(f"Title: {title}\nContent: {truncated_content}")
        
        formatted_results = "\n\n".join(result_lines)
        
        return {"search_result": formatted_results}

    except Exception as e:
        logger.error(f"Error in search_company_info_tool: {e}", exc_info=True)
        return {"search_result": "웹 검색 중 오류가 발생했습니다."}

@tool
@traceable(name="get_preparation_advice_tool")
def get_preparation_advice_tool(state: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """직무 준비 조언 제공."""
    # 입력 처리
    if isinstance(state, str):
        try:
            state = json.loads(state)
        except:
            try:
                state = eval(state)
            except:
                pass
    
    # state가 아닌 경우 이전 단계의 state 가져오기
    if not isinstance(state, dict) or "parsed_input" not in state:
        logger.warning("Invalid state provided to get_preparation_advice_tool: %s", state)
        return {"error": "직무 준비 조언 제공을 위한 유효한 상태가 제공되지 않았습니다."}
    
    
    if "selected_job" not in state or state["selected_job"] is None:
        logger.warning("No selected_job in state for preparation advice")
        state["preparation_advice"] = "선택된 직무 정보가 없어 준비 조언을 제공할 수 없습니다."
        return state
    
    try:
        # 사용자 프로필 구성
        user_profile = (
        f"학력: {state['parsed_input']['education']}, "
        f"경력: {state['parsed_input']['experience']}, "
        f"희망 직무: {state['parsed_input']['desired_job']}, "
        f"기술 스택: {', '.join(state['parsed_input']['tech_stack'])}",
        f"희망 근무지역: {state['parsed_input']['location']}",
    )
        
        # 직무 정보 구성
        selected_job_text = state["selected_job"]

        # LLM 체인으로 준비 조언 생성
        state["preparation_advice"] = advice_chain.invoke({
            "user_profile": user_profile,
            "job_data": selected_job_text
        }).content
        
    except Exception as e:
        logger.error("Preparation advice generation error: %s", str(e))
        state["preparation_advice"] = f"준비 조언 생성 오류: {str(e)}"
    
    return state

@tool
@traceable(name="contextual_qa_tool")
def contextual_qa_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """선택된 직무와 웹 검색을 통해 후속 질문에 답변"""
    question = state["parsed_input"]["question"]
    company_context = state.get("selected_job", "선택된 채용 공고가 없습니다.")
    
    # 웹 검색이 필요한 질문인지 판단하여 search_company_info_tool 재활용
    web_search_needed_keywords = ["연봉", "뉴스", "평판", "최신", "이슈"]
    web_search_context = ""
    if any(keyword in question for keyword in web_search_needed_keywords):
        search_result_state = search_company_info_tool.func(state)
        web_search_context = search_result_state.get("search_result", "")

    # 답변 생성 체인 실행
    answer = contextual_qa_prompt_chain.invoke({
        "company_context": company_context,
        "web_search_context": web_search_context,
        "question": question
    }).content

    return {"final_answer": answer}


@tool
@traceable(name="generate_final_answer_tool")
def generate_final_answer_tool(state: Dict[str, Any]) -> Dict[str, str]:
    """대화의 intent에 따라 각기 다른 방식으로 최종 답변을 생성합니다."""
    intent = state.get("intent", "chit_chat")
    logger.info(f"Generating final answer for intent: '{intent}'")
    final_answer = ""
    
    try:
        # 유형 1: 단순 인사 또는 부적절한 질문
        if intent == "chit_chat":
            final_answer = "죄송합니다. 저는 채용 관련 질문에만 답변을 드릴 수 있습니다. 궁금하신 직무나 회사에 대해 말씀해주세요."

        # 유형 2: '처음 검색' 또는 '다른거 찾아줘' 후, 후보 목록을 제시하는 경우
        elif intent in ["initial_search", "new_search"]:
            # present_candidates_tool에서 생성된 답변("...번호를 알려주세요.")을 최종 답변으로 사용
            final_answer = state.get("final_answer", "추천 목록을 생성하는 데 실패했습니다.")
        
        # 유형 3: 사용자가 특정 회사를 '선택'한 후, 모든 정보를 종합한 심층 분석 결과를 제공하는 경우
        elif intent == "select_job":
            user_profile = (
                f"학력: {state.get('parsed_input', {}).get('education', '')}, "
                f"경력: {state.get('parsed_input', {}).get('experience', '')}, "
                f"희망 직무: {state.get('parsed_input', {}).get('desired_job', '')}, "
                f"기술 스택: {', '.join(state.get('parsed_input', {}).get('tech_stack', []))}, "
                f"희망 근무지역: {state.get('parsed_input', {}).get('location', '')}"
            )
            question = state.get("parsed_input", {}).get("question", "")
            
            # 모든 분석(회사정보, 준비조언 등)을 종합하여 최종 답변 생성
            final_answer = final_answer_chain.invoke({
                "user_profile": user_profile,
                "question": question,
                "selected_job": state.get("selected_job", ""),
                "search_result": state.get("search_result", ""),
                "preparation_advice": state.get("preparation_advice", "")
            }).content

        # 유형 4: 심층 분석이 끝난 후, 추가적인 '후속 질문'에 답변하는 경우
        elif intent == "follow_up_qa":
            # contextual_qa_tool에서 이미 생성한 답변을 최종 답변으로 그대로 사용합니다.
            final_answer = state.get("final_answer", "죄송합니다. 해당 질문에 대한 답변을 찾지 못했습니다.")
        
        else:
            final_answer = "죄송합니다. 요청을 이해하지 못했습니다. 다시 말씀해주세요."
            
    except Exception as e:
        logger.error(f"Final answer generation error: {e}", exc_info=True)
        final_answer = "답변을 생성하는 중 오류가 발생했습니다."

    return {"final_answer": final_answer}

@tool
@traceable(name="record_history_tool")
def record_history_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """생성된 최종 답변을 chat_history에 기록하고, 파일로 저장 및 요약합니다."""
    final_answer = state.get("final_answer", "")
    
    # 1. 최종 답변을 chat_history에 업데이트
    if state.get("chat_history"):
        state["chat_history"][-1]["assistant"] = final_answer
    
            
    # 2. 대화 턴 길이에 따른 요약 
    if state.get("conversation_turn", 0) % 3 == 0 and state.get("conversation_turn", 0) > 0:
        logger.info("Summarizing conversation history...")
        chat_history_str = "\n".join([f"User: {msg.get('user', '')}\nAssistant: {msg.get('assistant', '')}" for msg in state.get("chat_history", [])])
        summary_input = {"summary": state.get("summary", ""), "new_lines": chat_history_str}
        new_summary = summary_memory_chain.invoke(summary_input).content
        state["summary"] = new_summary
        # state["chat_history"] = [] # 요약 후 현재 대화 내용은 비워줌
        logger.info(f"Conversation summarized and history cleared.")

    # 이 도구는 state를 직접 수정했으므로, 변경된 state 자체를 반환
    return state