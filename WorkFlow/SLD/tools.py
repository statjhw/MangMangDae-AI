from typing import Dict, Any, Union
import logging
import json
import os
from langchain_core.tools import tool
from langsmith import traceable
from WorkFlow.Util.utils import advice_chain, summary_memory_chain, final_answer_chain, intent_analysis_chain, contextual_qa_prompt_chain, reformulate_query_chain, web_search_planner_chain, hyde_reformulation_chain
from Retrieval.hybrid_retriever import hybrid_search, _format_hit_to_text
from WorkFlow.config import get_tavily_tool, RateLimitError
import re

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LangSmith 환경 변수 설정
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "job_advisor")

tavily_tool = get_tavily_tool()

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

    # 사용자가 불만족을 표하며 새로운 검색을 원할 경우, 이전 추천을 제외 목록에 추가
    if intent_result == 'new_search' and state.get('job_list'):
        previous_ids = [job.get('id', '') for job in state.get('job_list', [])]
        
        current_excluded = state.get('excluded_ids', [])
        current_excluded.extend(previous_ids)
        
        state['excluded_ids'] = list(set(current_excluded))
        logger.info(f"Adding {len(previous_ids)} job IDs to the exclusion list.")
    
    elif intent_result == 'select_job':
        logger.info("Intent is 'select_job', proceeding to load the selected document.")


    return {"intent": intent_result}

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

    # base_query = user_profile.get("question", "")
    # query = f"[query] {base_query}" 
    
    try:
        #doc_scores, doc_texts = retrieve(query, exclude_urls=state.get("excluded_jobs", []))
        
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
    return {"final_answer": "\n".join(response_lines)}

# 신규 도구 2: 사용자 선택 로드
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
    
    # [핵심] 선택된 직무의 텍스트와 구조화된 데이터를 모두 반환
    if selected_job_info:
        logger.info(f"Selected job: {selected_job_info.get('source_data', {}).get('title')}")
        return {
            "selected_job": selected_job_info.get('document'),
            "selected_job_data": selected_job_info.get('source_data')
        }
            
    # 최종적으로 아무것도 찾지 못한 경우
    return {"final_answer": "오류: 유효한 공고를 선택하지 못했습니다. 목록에 있는 번호나 회사명을 포함하여 다시 말씀해주세요."}

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

        # --- intent에 따라 질문의 출처를 다르게 설정 ---
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
    question = state.get("user_input", {}).get("candidate_question", "") #################
    company_context = state.get("selected_job", "선택된 채용 공고가 없습니다.")
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
            user_input = state.get("user_input", {})
            user_profile_str = (
                f"학력: {user_input.get('candidate_major', '')}, "
                f"경력: {user_input.get('candidate_career', '')}, "
                f"희망 직무: {user_input.get('candidate_interest', '')}, "
                f"기술 스택: {', '.join(user_input.get('candidate_tech_stack', []))}, "
                f"희망 근무지역: {user_input.get('candidate_location', '')}"
            )
            question = state.get("user_input", {}).get("question", "")
            
            # 모든 분석(회사정보, 준비조언 등)을 종합하여 최종 답변 생성
            final_answer = final_answer_chain.invoke({
                "user_profile": user_profile_str,
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