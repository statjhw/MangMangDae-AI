from typing import Dict, Any, Union
import logging
import json
import os
from langchain_core.tools import tool
from langsmith import traceable
from WorkFlow.Util.utils import advice_chain, summary_memory_chain, final_answer_chain, intent_analysis_chain, contextual_qa_prompt_chain, reformulate_query_chain, web_search_planner_chain, hyde_reformulation_chain, company_context_planner_chain, confirmation_router_chain
from Retriever.hybrid_retriever import hybrid_search, _format_hit_to_text
from WorkFlow.config import get_tavily_tool, get_perplexity_tool
import re

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LangSmith 환경 변수 설정
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "job_advisor")

tavily_tool = get_tavily_tool()
perplexity_tool = get_perplexity_tool()


@tool
@traceable(name="analyze_intent_tool")
def analyze_intent_tool(state: Dict[str, Any]) -> Dict[str, str]:
    """대화 기록과 현재 질문을 바탕으로 사용자 의도 분석"""
    summary = state.get("summary")
    chat_history = state.get("chat_history", [])
    question = state.get("user_input", {}).get("candidate_question", "")
    
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

    updates = {"intent": intent_result}

    # 사용자가 불만족을 표하며 새로운 검색을 원할 경우, 이전 추천을 제외 목록에 추가
    if intent_result == 'new_search' and state.get('job_list'):
        previous_ids = [job.get('id', '') for job in state.get('job_list', [])]
        
        current_excluded = state.get('excluded_ids', [])
        current_excluded.extend(previous_ids)
        
        updates['excluded_ids'] = list(set(current_excluded))
        logger.info(f"Adding {len(previous_ids)} job IDs to the exclusion list.")
    
    elif intent_result == 'select_job':
        logger.info("Intent is 'select_job', proceeding to load the selected document.")


    return updates

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
    if not isinstance(state, dict) or "user_input" not in state:
        logger.warning("Invalid state provided to recommend_jobs_tool: %s", state)
        return {"error": "직무 추천을 위한 유효한 상태가 제공되지 않았습니다."}

    user_profile = state.get("user_input", {})

    try:
        doc_scores, doc_ids, doc_texts = hybrid_search(
            user_profile=user_profile,
            exclude_ids=state.get("excluded_ids", [])
        )

        if not doc_texts:
            return {"job_list": []}
        candidate_jobs = []
        for i, doc_source in enumerate(doc_texts):
            full_text_document = _format_hit_to_text(doc_source)
            candidate_jobs.append({
                "index": i + 1,
                "id": doc_ids[i],
                "source_data": doc_source,
                "document": full_text_document
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
        source_data = job.get('source_data', {})
        
        company = source_data.get("company_name", "정보 없음")
        title = source_data.get("title", "정보 없음")
        location = source_data.get("location", "정보 없음")
        qualifications = source_data.get("qualifications", [])
        main_tasks = source_data.get('main_tasks', '정보 없음')

        qualifications_str = ""
        main_tasks_str = ""
        if qualifications and isinstance(qualifications, list):
             qualifications_str = f"✨ 자격 요건: {', '.join(qualifications)}"

        if main_tasks and isinstance(main_tasks, list):
            main_tasks_str = f"🏷️ 주요 업무: {', '.join(main_tasks)}"

        response_lines.append(f"**{job['index']}. {company} - {title}**")
        response_lines.append(f"📍 위치: {location}")

        if main_tasks_str:
            response_lines.append(main_tasks_str)
        if qualifications_str:
            response_lines.append(qualifications_str)

        response_lines.append("-" * 20)
    
    response_lines.append("\n더 자세히 알아보고 싶은 공고의 번호를 알려주세요. 해당 공고에 대한 심층 분석을 제공해 드립니다.")
    # 선택 대기 상태 진입
    return {"final_answer": "\n".join(response_lines), "awaiting_selection": True, "awaiting_analysis_confirmation": False}


@tool
@traceable(name="load_selected_job_tool")
def load_selected_job_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """사용자 입력에서 선택된 항목을 파싱하여, selected_job(텍스트)과 selected_job_data(딕셔너리)를 설정합니다."""
    user_question = state.get("user_input", {}).get("candidate_question", "")
    job_list = state.get("job_list", [])
    
    if not job_list:
        return {"final_answer": "오류: 비교할 추천 목록이 없습니다. 다시 검색해주세요."}

    selected_job_info = None
    # 숫자 기반 선택 먼저 시도
    match = re.search(r'\d+', user_question)
    if match:
        try:
            selected_index = int(match.group(0))
            for job in job_list:
                if job.get('index') == selected_index:
                    selected_job_info = job
                    break
        except (ValueError, IndexError):
            pass

    # 숫자가 없으면 회사명 기반 선택 시도
    if not selected_job_info:
        for job in job_list:
            company_name = job.get('source_data', {}).get('company_name')
            if company_name and company_name in user_question:
                selected_job_info = job
                break
    
    # 선택된 직무의 텍스트와 구조화된 데이터를 모두 반환 (문서 형태 확인 필요)
    if selected_job_info:
        logger.info(f"Selected job: {selected_job_info.get('source_data', {}).get('title')}")
        # 회사 컨텍스트 저장/업데이트
        tmp_state = {
            **state,
            "selected_job": selected_job_info.get('document'),
            "selected_job_data": selected_job_info.get('source_data')
        }
        company_contexts = state.get("company_contexts", {}) or {}
        company_name = selected_job_info.get('source_data', {}).get('company_name')

        if company_name:
            context_data = {
                "selected_job": tmp_state["selected_job"],
                "selected_job_data": tmp_state["selected_job_data"],
                "search_result": state.get("search_result", ""),
                "interview_questions_context": state.get("interview_questions_context", ""),
                "company_culture_context": state.get("company_culture_context", ""),
                "preparation_advice": state.get("preparation_advice", "")
            }
            
            if company_name not in company_contexts:
                company_contexts[company_name] = {}
    
            company_contexts[company_name].update(context_data)
        
        return {
            "selected_job": tmp_state["selected_job"],
            "selected_job_data": tmp_state["selected_job_data"],
            "awaiting_selection": False,
            "company_contexts": company_contexts,
            "current_company": company_name
        }
            
    # 최종적으로 아무것도 찾지 못한 경우: 선택 대기 유지
    return {
        "final_answer": "유효한 선택을 인식하지 못했습니다. 목록의 번호(예: 1, 2)나 회사명을 포함하여 다시 말씀해주세요.",
        "awaiting_selection": True
    }

@tool
@traceable(name="request_selection_tool")
def request_selection_tool(state: Dict[str, Any]) -> Dict[str, str]:
    """선택 대기 상태에서 유효하지 않은 입력이 온 경우, 선택 요청 메시지를 재전송합니다."""
    return {"final_answer": "목록에서 보고 싶은 공고의 번호(예: 1, 2)나 회사명을 말씀해 주세요."}


@tool
@traceable(name="confirmation_router_tool")
def confirmation_router_tool(state: Dict[str, Any]) -> Dict[str, str]:
    """LLM을 사용하여 심층 분석 확인 단계에서 사용자의 의도를 분류합니다."""
    logger.info("Routing user's confirmation response using LLM.")
    
    company_name = state.get("current_company", "해당 회사")
    user_question = state.get("user_input", {}).get("candidate_question", "")

    try:
        # LLM을 호출하여 의도 분류
        intent_result = confirmation_router_chain.invoke({
            "company_name": company_name,
            "question": user_question
        }).content.strip()

        logger.info(f"LLM-based router decision: '{intent_result}'")

        # 유효한 결과인지 확인
        valid_routes = ["start_deep_analysis", "reset_and_reformulate", "expert_research", "request_further_action"]
        if intent_result not in valid_routes:
            logger.warning(f"Router returned an invalid route: '{intent_result}'. Defaulting to request_further_action.")
            return {"next_action": "request_further_action"}

        return {"next_action": intent_result}

    except Exception as e:
        logger.error(f"Error in confirmation_router_tool: {e}", exc_info=True)
        # 오류 발생 시 안전하게 재요청 경로로 보냄
        return {"next_action": "request_further_action"}
    
@tool
@traceable(name="request_further_action_tool")
def request_further_action_tool(state: Dict[str, Any]) -> Dict[str, str]:
    """심층 분석 확인 단계에서 사용자가 chit-chat을 입력했을 때, 행동을 다시 요청하는 메시지를 생성합니다."""
    
    company_name = state.get("current_company", "해당 회사")
    
    response_message = (
        f"'{company_name}'에 대한 추가 분석을 진행할까요?\n"
        "원하시면 '네' 또는 '분석해줘'라고 답해주세요.\n"
        "다른 회사를 찾아보려면 '다른 회사'라고 말씀해주셔도 좋습니다.\n"
        "또는, 이 회사에 대해 궁금한 점을 직접 질문하셔도 됩니다."
    )
    
    return {"final_answer": response_message}

@tool
@traceable(name="show_full_posting_and_confirm_tool")
def show_full_posting_and_confirm_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    선택된 공고의 전체 내용을 보여주고, 심층 분석 여부를 사용자에게 확인하며,
    다음 행동을 위한 상태 플래그를 설정합니다.
    """
    logger.info("Showing full job posting and asking for analysis confirmation.")
    selected_job_text = state.get("selected_job", "오류: 선택된 공고를 찾을 수 없습니다.")

    confirmation_prompt = (
        "\n\n--------------------\n"
        "이 채용 공고의 전체 내용입니다.\n\n"
        "**귀하의 프로필을 기반으로 이 포지션에 대한 심층 분석을 진행할까요?**\n"
        "원하시면 '네' 또는 '분석해줘'라고 답변해주세요.\n"
        "혹은, 이 회사에 대해 다른 궁금한 점(예: '이 회사의 최근 평판은 어때?')을 바로 질문하셔도 좋습니다."
    )

    final_answer = selected_job_text + confirmation_prompt

    return {
        "final_answer": final_answer,
        "awaiting_selection": False, # 후보 선택 모드 종료
        "awaiting_analysis_confirmation": True # 분석 확인 모드 시작
    }


@tool
@traceable(name="reformulate_query_tool")
def reformulate_query_tool(state: Dict[str, Any]) -> Dict[str, str]:
    """전체 대화 맥락을 바탕으로 새로운 검색어를 생성합니다."""
    logger.info("Reformulating search query based on conversation context.")
    
    summary = state.get("summary", "")
    chat_history = state.get("chat_history", [])
    question = state.get("user_input", {}).get("candidate_question", "")
    
    # 요약본 또는 전체 기록을 컨텍스트로 사용
    context = summary if summary else "\n".join([f"User: {turn['user']}" for turn in chat_history])

    try:
        # LLM을 호출하여 새로운 검색어 생성
        new_query = reformulate_query_chain.invoke({
            "context": context,
            "question": question
        }).content.strip()
        
        logger.info(f"Reformulated query: '{new_query}'")
        
        # 이렇게 하면 recommend_jobs_tool은 별도 수정 없이 이 쿼리를 사용하게 됨
        updated_user_input = state.get("user_input", {}).copy()
        updated_user_input["candidate_question"] = new_query
        
        return {"user_input": updated_user_input}

    except Exception as e:
        logger.error(f"Query reformulation error: {e}", exc_info=True)
        # 실패 시, 원래 질문을 그대로 사용
        return {"user_input": state.get("user_input")}


@tool
@traceable(name="formulate_retrieval_query_tool")
def formulate_retrieval_query_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """HyDE 기반 채용 공고 생성 도구
    사용자 프로필과 질문을 바탕으로, 가상의 채용 공고를 생성합니다.
    생성된 공고는 리트리버에 입력되어 검색 결과에 포함됩니다.
    """
    if not isinstance(state, dict) or "user_input" not in state:
        logger.warning("Invalid state provided to formulate_retrieval_query_tool: %s", state)
        return {"user_input": state.get("user_input", {})}

    user_input = state.get("user_input", {})

    # 사용자 프로필 요약 문자열 구성
    user_profile_str = (
        f"학력: {user_input.get('candidate_major', '')}, "
        f"경력: {user_input.get('candidate_career', '')}, "
        f"희망 직무: {user_input.get('candidate_interest', '')}, "
        f"기술 스택: {', '.join(user_input.get('candidate_tech_stack', []))}, "
        f"희망 근무지역: {user_input.get('candidate_location', '')}"
    )

    natural_question = user_input.get("candidate_question", "")

    try:
        response_content = hyde_reformulation_chain.invoke({
            "user_profile": user_profile_str,
            "question": natural_question
        }).content.strip()
        result_json = json.loads(response_content)

        hypothetical_document = result_json.get("hypothetical_document", "")
        company_names = result_json.get("company_names", [])

        # HyDE 가짜문서만 hyde_query에 저장
        updated_user_input = {
            **user_input, 
            "hyde_query": hypothetical_document   # HyDE 가짜문서 (리트리버용)
        }
        logger.info(f"Formulated HyDE document: '{hypothetical_document[:100]}...'")
        if company_names:
            logger.info(f"Extracted company filter: {company_names}")

        return {
            "user_input": updated_user_input,
            "company_name_filter": company_names
        }
    except Exception as e:
        logger.error(f"Hiring query formulation error: {e}", exc_info=True)
        # 에러 시에는 원래 user_input 그대로 반환
        return {"user_input": user_input}

@tool
@traceable(name="search_company_info_tool")
def search_company_info_tool(state: Dict[str, Any]) -> Dict[str, str]:
    """회사 정보를 웹에서 검색하며, intent에 따라 검색어의 맥락을 동적으로 구성합니다."""
    
    selected_job_data = state.get("selected_job_data")
    if not selected_job_data:
        return {"search_result": "분석할 직무 정보가 없습니다."}
    
    try:
        company_name = selected_job_data.get("company_name")
        if not company_name:
            return {"search_result": "공고에서 회사 이름을 찾지 못했습니다."}

        # 의도 따라 질문의 출처를 다르게 설정
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
                contextual_question = state.get("user_input", {}).get("candidate_question", "")
        else:
            # 다른 모든 경우에는 현재 턴의 질문을 그대로 사용
            contextual_question = state.get("user_input", {}).get("candidate_question", "")

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
@traceable(name="research_for_advice_tool")
def research_for_advice_tool(state: Dict[str, Any]) -> Dict[str, str]:
    """면접 조언 생성을 위해, 선택된 회사/직무에 대한 웹 검색을 수행합니다."""
    logger.info("Researching for actionable advice...")
    
    selected_job_data = state.get("selected_job_data", {})
    company_name = selected_job_data.get("company_name", "")
    job_title = selected_job_data.get("title", "")

    if not company_name or not job_title:
        return {
            "interview_questions_context": "회사 또는 직무 정보가 없어 관련 면접 질문을 찾을 수 없습니다.",
            "company_culture_context": "회사 또는 직무 정보가 없어 기업 문화 정보를 찾을 수 없습니다."
        }

    # 검색할 쿼리 목록 정의
    queries = {
        "interview": f'"{company_name}" "{job_title}" 면접 질문 후기',
        "culture": f'"{company_name}" 기술 블로그 OR 개발 문화'
    }
    
    # 최종 결과를 저장할 변수 초기화
    interview_questions_context = "해당 직무에 대한 면접 질문 정보를 찾지 못했습니다."
    company_culture_context = "해당 회사의 기술 문화에 대한 정보를 찾지 못했습니다."
    
    try:
        for key, query in queries.items():
            logger.info(f"Executing research query for '{key}': {query}")
            # 각 쿼리에 대해 tavily_tool을 한 번씩 호출
            search_results = tavily_tool.invoke({"query": query})
            
            if not isinstance(search_results, list):
                search_results = [search_results]
            
            # content들을 하나의 문자열로 합침
            content = "\n".join([str(res.get('content', '')) for res in search_results if res])
            
            # 키에 따라 적절한 변수에 결과 저장
            if key == "interview" and content:
                interview_questions_context = content[:1500] # 토큰 수 관리를 위해 글자 수 제한
            elif key == "culture" and content:
                company_culture_context = content[:1500]
        
        return {
            "interview_questions_context": interview_questions_context,
            "company_culture_context": company_culture_context
        }

    except Exception as e:
        logger.error(f"Error during research for advice: {e}")
        return {
            "interview_questions_context": "면접 질문 검색 중 오류가 발생했습니다.",
            "company_culture_context": "기업 문화 검색 중 오류가 발생했습니다."
        }

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
    if not isinstance(state, dict) or "user_input" not in state:
        logger.warning("Invalid state provided to get_preparation_advice_tool: %s", state)
        return {"error": "직무 준비 조언 제공을 위한 유효한 상태가 제공되지 않았습니다."}
    
    
    if "selected_job" not in state or state["selected_job"] is None:
        logger.warning("No selected_job in state for preparation advice")
        state["preparation_advice"] = "선택된 직무 정보가 없어 준비 조언을 제공할 수 없습니다."
        return state
    
    try:
        user_input = state.get("user_input", {})
        # 사용자 프로필 구성
        user_profile_str = (
            f"학력: {user_input.get('candidate_major', '')}, "
            f"경력: {user_input.get('candidate_career', '')}, "
            f"희망 직무: {user_input.get('candidate_interest', '')}, "
            f"기술 스택: {', '.join(user_input.get('candidate_tech_stack', []))}, "
            f"희망 근무지역: {user_input.get('candidate_location', '')}"
        )

        advice_content = advice_chain.invoke({
            "user_profile": user_profile_str,
            "job_data": state.get("selected_job", ""),
            "interview_questions_context": state.get("interview_questions_context", ""),
            "company_culture_context": state.get("company_culture_context", "")
        }).content

        return {"preparation_advice": advice_content}
        
    except Exception as e:
        logger.error("Preparation advice generation error: %s", str(e))
        return {"preparation_advice": f"준비 조언 생성 오류: {str(e)}"}

@tool
@traceable(name="contextual_qa_tool")
def contextual_qa_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """선택된 직무와 웹 검색을 통해 후속 질문에 답변"""
    user_input = state.get("user_input", {})
    question = user_input.get("candidate_question", "")
    company_context = state.get("selected_job", "선택된 채용 공고가 없습니다.")

    # 1. 모든 회사 컨텍스트를 종합
    all_contexts = []
    
    # a. 현재 선택된 회사 정보 추가
    if state.get("selected_job"):
        all_contexts.append(f"[현재 회사 공고 내용]\n{state.get('selected_job')}")

    # b. user_input에서 'other_company_'로 시작하는 다른 회사 정보 추가
    for key, value in user_input.items():
        if key.startswith("other_company_"):
            company_name = key.replace("other_company_", "").replace("_info", "")
            all_contexts.append(f"[{company_name} 회사 정보]\n{str(value)}")

    # 종합된 컨텍스트를 하나의 문자열로 합침
    company_context = "\n\n".join(all_contexts)
    if not company_context:
        company_context = "참고할 채용 공고 정보가 없습니다."


    web_search_context = ""

    try:
        logger.info("Planning step: Checking if web search is necessary.")
        planner_decision = web_search_planner_chain.invoke({
            "company_context": company_context,
            "question": question
        }).content.strip()

        logger.info(f"Planner decision: '{planner_decision}'")

        if "필요함" in planner_decision:
            logger.info("Execution step: Web search is necessary. Calling search_company_info_tool.")
            search_result_dict = search_company_info_tool.func(state)
            web_search_context = search_result_dict.get("search_result", "")
        else:
            logger.info("Execution step: Web search is not necessary. Skipping.")

        logger.info("Answering step: Generating final answer with available context.")
        answer = contextual_qa_prompt_chain.invoke({
            "company_context": company_context,
            "web_search_context": web_search_context,
            "question": question
        }).content

        return {"final_answer": answer}

    except Exception as e:
        logger.error(f"Error in contextual_qa_tool: {e}", exc_info=True)
        return {"final_answer": "후속 질문에 답변하는 중 오류가 발생했습니다."}
    

@tool
@traceable(name="generate_final_answer_tool")
def generate_final_answer_tool(state: Dict[str, Any]) -> Dict[str, str]:
    """현재 GraphState를 기반으로 사용자에게 보여줄 최종 답변을 결정하고 포맷팅합니다."""
    logger.info(f"Generating final answer based on current state. Last intent was: '{state.get('intent')}'")

    # 유형 1: 심층 분석 데이터(`preparation_advice`)가 준비된 경우, 최종 분석 리포트를 생성합니다.
    if state.get("preparation_advice"):
        logger.info("Preparation advice found. Generating the final deep-dive analysis report.")
        user_input = state.get("user_input", {})
        user_profile_str = (
            f"학력: {user_input.get('candidate_major', '')}, "
            f"경력: {user_input.get('candidate_career', '')}, "
            f"희망 직무: {user_input.get('candidate_interest', '')}, "
            f"기술 스택: {', '.join(user_input.get('candidate_tech_stack', []))}, "
            f"희망 근무지역: {user_input.get('candidate_location', '')}"
        )
        # 사용자의 초기 질문 대신, 분석 요청 자체를 맥락으로 삼습니다.
        question = f"'{state.get('current_company')}' 회사와 선택된 직무에 대한 심층 분석 요청"

        final_answer = final_answer_chain.invoke({
            "user_profile": user_profile_str,
            "question": question,
            "selected_job": state.get("selected_job", ""),
            "search_result": state.get("search_result", ""),
            "preparation_advice": state.get("preparation_advice", "")
        }).content
        return {"final_answer": final_answer}

    # 유형 2: 이전 노드에서 이미 final_answer를 생성한 경우, 그대로 사용(pass-through)합니다.
    # (예: 추천 목록 제시, 심층 분석 제안, 후속 질문 답변, 행동 재요청 등)
    if state.get("final_answer"):
        logger.info("A pre-generated final_answer was found in the state. Passing it through.")
        return {"final_answer": state.get("final_answer")}

    # 유형 3: 위 두 경우에 해당하지 않는 chit-chat 또는 예외 상황 처리
    if state.get("intent") == "chit_chat":
        final_answer = "죄송합니다. 저는 채용 관련 질문에만 답변을 드릴 수 있습니다. 궁금하신 직무나 회사에 대해 말씀해주세요."
    else:
        # 이 경우는 발생하면 안 되지만, 안전장치로 남겨둡니다.
        final_answer = "죄송합니다. 요청을 처리하는 중 문제가 발생했습니다. 다시 시도해주세요."
        logger.warning("generate_final_answer_tool was called without 'preparation_advice' or a pre-generated 'final_answer'.")

    return {"final_answer": final_answer}
    return {"final_answer": final_answer}

@tool
@traceable(name="record_history_tool")
def record_history_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """생성된 최종 답변을 chat_history에 기록하고, 파일로 저장 및 요약합니다."""
    final_answer = state.get("final_answer", "")
    
    # 1. 최종 답변을 chat_history에 업데이트
    if state.get("chat_history"):
        state["chat_history"][-1]["assistant"] = final_answer
    
            
    # 2. 대화 턴 길이에 따른 요약 (더 관대하게 변경: 5턴마다)
    if state.get("conversation_turn", 0) % 5 == 0 and state.get("conversation_turn", 0) > 0:
        logger.info("Summarizing conversation history...")
        chat_history_str = "\n".join([f"User: {msg.get('user', '')}\nAssistant: {msg.get('assistant', '')}" for msg in state.get("chat_history", [])])
        summary_input = {"summary": state.get("summary", ""), "new_lines": chat_history_str}
        new_summary = summary_memory_chain.invoke(summary_input).content
        state["summary"] = new_summary
        # 요약 후 대화 내용을 완전히 비우지 않고 최근 2개 정도는 유지
        if len(state.get("chat_history", [])) > 2:
            state["chat_history"] = state["chat_history"][-2:]
        logger.info(f"Conversation summarized and recent history preserved.")

    # 이 도구는 state를 직접 수정했으므로, 변경된 state 자체를 반환
    return state

@tool
@traceable(name="reset_selection_tool")
def reset_selection_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """새 검색/재검색 전에 이전 선택/분석 컨텍스트를 초기화합니다."""
    logger.info("Resetting selected job context for a new search.")
    keys_to_clear = [
        "selected_job",
        "selected_job_data",
        "search_result",
        "interview_questions_context",
        "company_culture_context",
        "preparation_advice",
        "awaiting_analysis_confirmation"
    ]
    updates = {key: None for key in keys_to_clear}
    return updates

@tool
@traceable(name="resolve_company_context_tool")
def resolve_company_context_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """현재 사용자 질문에서 회사명을 추출하거나 유지하여 current_company를 설정하고, 
    LLM이 판단하여 다른 회사 정보가 필요한지 확인하고 필요시 company_contexts에서 로드하여 user_input에 추가합니다.
    """
    
    user_question = state.get("user_input", {}).get("candidate_question", "")
    current_company = state.get("current_company", "")
    company_contexts = state.get("company_contexts", {}) or {}
    user_input = state.get("user_input", {}).copy()

    # 간단한 회사명 추출: 추천 목록 내 회사명 매칭 우선
    detected_company = None
    for job in state.get("job_list", []):
        cname = job.get('source_data', {}).get('company_name')
        if cname and cname in user_question:
            detected_company = cname
            break

    # 없으면 이전 current 유지
    target_company = detected_company or current_company or ""

    # LLM이 현재 질문에 다른 회사 정보가 필요한지 판단
    if company_contexts and len(company_contexts) > 1:
        try:
            # LLM에게 현재 질문과 사용 가능한 회사 컨텍스트를 제공하여 판단 요청
            available_companies = list(company_contexts.keys())
            available_companies.remove(target_company) if target_company in available_companies else None
            
            if available_companies:
                planner_result = company_context_planner_chain.invoke({
                    "current_question": user_question,
                    "current_company": target_company,
                    "available_companies": ", ".join(available_companies),
                    "company_contexts": str(company_contexts)
                }).content.strip()
                
                # LLM 응답에서 0 또는 1 추출
                if "1" in planner_result:
                    # 다른 회사 정보를 user_input에 추가
                    for company_name in available_companies:
                        company_info = company_contexts[company_name]
                        user_input[f"other_company_{company_name}_info"] = company_info
                        logger.info(f"Added context for {company_name} to user_input")
        except Exception as e:
            logger.warning(f"Error in company context planning: {e}")

    result: Dict[str, Any] = {
        "current_company": target_company,
        "company_contexts": company_contexts,
        "user_input": user_input
    }
    
    return result


@tool
@traceable(name="expert_research_tool")
def expert_research_tool(state: Dict[str, Any]) -> Dict[str, str]:
    """
    복잡하고 개방적인 질문에 대해 Perplexity를 사용하여 종합적인 답변을 찾습니다.
    """
    question = state.get("user_input", {}).get("candidate_question", "")

    
    if not question:
        return {"final_answer": "분석할 질문이 없습니다."}
    
    selected_job_data = state.get("selected_job_data")
    if not selected_job_data:
        return {"search_result": "분석할 직무 정보가 없습니다."}

    logger.info(f"Executing expert research with Perplexity for question: '{question}'")
    try:
        # Perplexity API를 호출하여 직접 답변을 얻음
        company_name = selected_job_data.get("company_name")
        if not company_name:
            return {"search_result": "공고에서 회사 이름을 찾지 못했습니다."}
        
        question = f"{company_name} 기업 {question}"
        result = perplexity_tool.invoke(question)
        
        # Perplexity의 답변을 최종 답변으로 설정
        return {"final_answer": result}
        
    except Exception as e:
        logger.error(f"Perplexity search failed: {e}", exc_info=True)
        return {"final_answer": "전문가 검색 중 오류가 발생했습니다."}