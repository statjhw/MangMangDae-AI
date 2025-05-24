from datetime import datetime
from typing import Dict, Any, Union
import logging
import json
import os
from langchain_core.tools import tool
from langchain_core.documents import Document
from langsmith import traceable
from WorkFlow.Util.utils import memory, job_chain, company_chain, salary_chain, advice_chain, summary_memory_chain, verify_job_chain
from retrieval.embeddings import get_vector_store
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
@traceable(name="parse_input_tool")
def parse_input_tool(user_input: Union[Dict[str, str], str]) -> Dict[str, Any]:
    """사용자 입력 파싱."""
    # 문자열로 전달된 경우 딕셔너리로 변환
    if isinstance(user_input, str):
        try:
            # 먼저 JSON으로 파싱 시도
            try:
                user_input = json.loads(user_input)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 Python eval 시도
                user_input = eval(user_input)
        except Exception as e:
            logger.error("Failed to parse user_input string: %s", str(e))
            raise ValueError(f"Invalid user_input format: {user_input}")
    
    if not isinstance(user_input, dict):
        logger.error("user_input must be a dictionary after parsing")
        raise ValueError("user_input must be a dictionary")
    
    # 필수 필드 확인
    required_fields = ["candidate_major", "candidate_career", "candidate_interest", "candidate_tech_stack", "candidate_question"]
    for field in required_fields:
        if field not in user_input:
            user_input[field] = ""
    
    # tech_stack 필드가 문자열이면 리스트로 변환
    if isinstance(user_input["candidate_tech_stack"], str):
        if user_input["candidate_tech_stack"]:
            user_input["candidate_tech_stack"] = [item.strip() for item in user_input["candidate_tech_stack"].split(",")]
        else:
            user_input["candidate_tech_stack"] = []
    
    state = {
        "user_input": user_input,
        "parsed_input": {
            "education": user_input.get("candidate_major", ""),
            "experience": user_input.get("candidate_career", ""),
            "desired_job": user_input.get("candidate_interest", ""),
            "tech_stack": user_input.get("candidate_tech_stack", []),
            "question": user_input.get("candidate_question", "")
        },
        "chat_history": [{
            "user": user_input.get("candidate_question", ""),
            "assistant": "",
            "timestamp": datetime.now().isoformat()
        }],
        "conversation_turn": 1,
        "job_recommendations": "",
        "selected_job": None,
        "company_info": "",
        "salary_info": "",
        "preparation_advice": "",
        "final_answer": "",
        "retry_count": 0,
        "revised_query": ""
    }
    memory.add_user_message(user_input["candidate_question"])
    memory.add_ai_message("")
    logger.info("Parsed input: %s", state["parsed_input"])
    return state

@tool
@traceable(name="recommend_jobs_tool")
def recommend_jobs_tool(state_or_params: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """직무 추천 (vector_store.similarity_search, 재검색 지원)."""
    # 입력 처리
    if isinstance(state_or_params, str):
        try:
            state_or_params = json.loads(state_or_params)
        except:
            try:
                state_or_params = eval(state_or_params)
            except:
                pass
    
    # state가 아닌 경우 이전 단계의 state 가져오기
    if not isinstance(state_or_params, dict) or "parsed_input" not in state_or_params:
        # 로그인 기록된 마지막 상태를 가져옵니다
        # 현재 구현에서는 메모리에서 직접 상태를 가져올 수 없으므로 기본값 사용
        logger.warning("Invalid state provided to recommend_jobs_tool: %s", state_or_params)
        return {"error": "직무 추천을 위한 유효한 상태가 제공되지 않았습니다."}
    
    state = state_or_params
    
    user_profile = (
        f"학력: {state['parsed_input']['education']}, "
        f"경력: {state['parsed_input']['experience']}, "
        f"희망 직무: {state['parsed_input']['desired_job']}, "
        f"기술 스택: {', '.join(state['parsed_input']['tech_stack'])}"
    )
    base_query = state["revised_query"] if state["revised_query"] else state["parsed_input"]["question"]
    query = f"{base_query} {' '.join(state['parsed_input']['tech_stack'])}"
    
    logger.info("Similarity search query: %s (retry_count: %d)", query, state["retry_count"])
    
    try:
        job_results = vector_store.similarity_search(query)
        logger.info("vector_store.similarity_search results: %s", 
                    [{"page_content": doc.page_content, "id": doc.metadata} for doc in job_results])
        
        if not job_results:
            logger.warning("No job results found for query: %s", query)
            job_list = "검색 결과 없음"
            state["selected_job"] = Document(
                page_content="내용: 검색 결과 없음",
                metadata={"id": "검색 결과 없음"}
            )
            state["job_recommendations"] = "검색 결과 없음"
        else:
            # 문서의 페이지 내용으로 직무 목록 구성
            job_list = "\n".join([doc.page_content for doc in job_results[:3]])
            
            # 선택된 직무를 첫 번째 결과로 설정
            selected_job = job_results[0]
            
            # 정규식으로 직무명과 회사명 추출
            text = selected_job.page_content
            
            # 직무 추출: '직무:' 와 '회사:' 사이
            job_match = re.search(r"직무:\s*(.*?)\s*회사:", text, re.DOTALL)
            job_name = job_match.group(1).strip() if job_match else "정보 없음"
            
            # 회사 추출: '회사:' 와 '직무 카테고리:' 사이
            company_match = re.search(r"회사:\s*(.*?)\s*직무 카테고리:", text, re.DOTALL)
            company_name = company_match.group(1).strip() if company_match else "정보 없음"
            
            # 태그 추출: '태그:' 와 '위치:' 사이
            tag_match = re.search(r"태그:\s*(.*?)\s*위치:", text, re.DOTALL)
            tag_name = tag_match.group(1).strip() if tag_match else "정보 없음"
            
            # 메타데이터 설정
            if not hasattr(selected_job, "metadata") or not isinstance(selected_job.metadata, dict):
                selected_job.metadata = {}
            
            # 메타데이터에 직무명, 회사명, 태그명 추가
            selected_job.metadata["job_name"] = job_name
            selected_job.metadata["company_name"] = company_name
            selected_job.metadata["tag_name"] = tag_name
            
            state["selected_job"] = selected_job
            state["job_recommendations"] = job_chain.invoke({"user_profile": user_profile, "job_list": job_list}).content
    
    except RateLimitError as e:
        logger.error("RateLimitError in similarity_search: %s", str(e))
        job_list = "API 호출 제한으로 검색 실패"
        state["selected_job"] = Document(
            page_content="내용: API 호출 제한",
            metadata={"id": "정보 없음"}
        )
        state["job_recommendations"] = "API 호출 제한으로 추천 실패"
    
    except Exception as e:
        logger.error("Similarity search error: %s", str(e))
        job_list = "검색 오류"
        state["selected_job"] = Document(
            page_content="내용: 검색 오류",
            metadata={"id": "정보 없음"}
        )
        state["job_recommendations"] = "검색 오류"
    
    if "selected_job" in state and state["selected_job"] and hasattr(state["selected_job"], "metadata"):
        logger.info("Selected job: %s", state["selected_job"].metadata)
    else:
        logger.info("Selected job: None")
    
    return state

@tool
@traceable(name="verify_job_relevance_tool")
def verify_job_relevance_tool(state_or_params: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """LLM으로 직무 문서 적합성 검증."""
    # 입력 처리
    if isinstance(state_or_params, str):
        try:
            state_or_params = json.loads(state_or_params)
        except:
            try:
                state_or_params = eval(state_or_params)
            except:
                pass
    
    # state가 아닌 경우 이전 단계의 state 가져오기
    if not isinstance(state_or_params, dict) or "parsed_input" not in state_or_params:
        logger.warning("Invalid state provided to verify_job_relevance_tool: %s", state_or_params)
        return {"error": "직무 적합성 검증을 위한 유효한 상태가 제공되지 않았습니다."}
    
    state = state_or_params
    
    if "selected_job" not in state or state["selected_job"] is None:
        logger.warning("No selected_job in state for verification")
        return state
    
    user_profile = (
        f"학력: {state['parsed_input']['education']}, "
        f"경력: {state['parsed_input']['experience']}, "
        f"희망 직무: {state['parsed_input']['desired_job']}, "
        f"기술 스택: {', '.join(state['parsed_input']['tech_stack'])}"
    )
    question = state["parsed_input"]["question"]
    job_documents = state["selected_job"].page_content if state["selected_job"] else "정보 없음"
    
    try:
        verification_result = verify_job_chain.invoke({
            "user_profile": user_profile,
            "question": question,
            "job_documents": job_documents
        }).content
        result = json.loads(verification_result)
        is_relevant = result.get("is_relevant", False)
        revised_query = result.get("revised_query", "")
        
        logger.info("Verification result: is_relevant=%s, revised_query=%s", is_relevant, revised_query)
        
        if not is_relevant:
            state["retry_count"] += 1
            state["revised_query"] = revised_query
        else:
            state["revised_query"] = ""
            state["retry_count"] = 0
    
    except Exception as e:
        logger.error("Verification error: %s", str(e))
        state["revised_query"] = ""
        state["retry_count"] = 0
    
    return state

@tool
@traceable(name="get_company_info_tool")
def get_company_info_tool(state_or_params: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """회사 정보 조회."""
    # 입력 처리
    if isinstance(state_or_params, str):
        try:
            state_or_params = json.loads(state_or_params)
        except:
            try:
                state_or_params = eval(state_or_params)
            except:
                pass
    
    # state가 아닌 경우 이전 단계의 state 가져오기
    if not isinstance(state_or_params, dict) or "parsed_input" not in state_or_params:
        logger.warning("Invalid state provided to get_company_info_tool: %s", state_or_params)
        return {"error": "회사 정보 조회를 위한 유효한 상태가 제공되지 않았습니다."}
    
    state = state_or_params
    
    if "selected_job" not in state or state["selected_job"] is None:
        logger.warning("No selected_job in state for company info retrieval")
        state["company_info"] = "선택된 직무 정보가 없어 회사 정보를 조회할 수 없습니다."
        return state
    
    try:
        # 선택된 직무에서 회사명 추출
        company_name = state["selected_job"].metadata.get("company_name", "정보 없음") if hasattr(state["selected_job"], "metadata") else "정보 없음"
        
        # 회사 정보 포함된 내용 추출
        page_content = state["selected_job"].page_content if hasattr(state["selected_job"], "page_content") else ""
        
        # [회사 소개] 섹션 추출 (없는 경우 포지션 상세 사용)
        company_intro_match = re.search(r"\[회사 소개\]\s*(.*?)(?=\[|$)", page_content, re.DOTALL)
        if company_intro_match:
            company_data = company_intro_match.group(1).strip()
        else:
            # 포지션 상세 섹션 추출
            position_detail_match = re.search(r"포지션 상세:\s*(.*?)(?=주요 업무:|$)", page_content, re.DOTALL)
            if position_detail_match:
                company_data = position_detail_match.group(1).strip()
            else:
                logger.warning("No [회사 소개] found in page_content: %s", page_content)
                company_data = f"회사명: {company_name}\n{page_content}"
        
        # LLM 체인으로 회사 정보 요약
        state["company_info"] = company_chain.invoke({"company_data": company_data}).content
        
    except Exception as e:
        logger.error("Company info retrieval error: %s", str(e))
        state["company_info"] = f"회사 정보 조회 오류: {str(e)}"
    
    return state

@tool
@traceable(name="get_salary_info_tool")
def get_salary_info_tool(state_or_params: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """급여 정보 조회 (웹 검색 활용)."""
    # 입력 처리
    if isinstance(state_or_params, str):
        try:
            state_or_params = json.loads(state_or_params)
        except:
            try:
                state_or_params = eval(state_or_params)
            except:
                pass
    
    # state가 아닌 경우 이전 단계의 state 가져오기
    if not isinstance(state_or_params, dict) or "parsed_input" not in state_or_params:
        logger.warning("Invalid state provided to get_salary_info_tool: %s", state_or_params)
        return {"error": "급여 정보 조회를 위한 유효한 상태가 제공되지 않았습니다."}
    
    state = state_or_params
    
    if "selected_job" not in state or state["selected_job"] is None:
        logger.warning("No selected_job in state for salary info retrieval")
        state["salary_info"] = "선택된 직무 정보가 없어 급여 정보를 조회할 수 없습니다."
        return state
    
    try:
        # 선택된 직무에서 직무명과 회사명 추출
        job_name = state["selected_job"].metadata.get("job_name", "정보 없음") if hasattr(state["selected_job"], "metadata") else "정보 없음"
        company_name = state["selected_job"].metadata.get("company_name", "정보 없음") if hasattr(state["selected_job"], "metadata") else "정보 없음"
        
        # 검색어 구성
        search_query = f"{job_name} {company_name} salary Korea AI"
        logger.info("Tavily search query: %s", search_query)
        
        # 웹 검색 실행
        search_results = tavily_tool.invoke(search_query)
        search_results_text = "\n".join([f"{i+1}. {result['content']}" for i, result in enumerate(search_results)])
        
        # 직무 정보 구성
        job_data = (
            f"직무: {job_name}\n"
            f"회사: {company_name}\n"
            f"분야: {state['parsed_input']['desired_job']}"
        )
        
        # LLM 체인으로 급여 정보 요약
        state["salary_info"] = salary_chain.invoke({
            "job_data": job_data,
            "search_results": search_results_text
        }).content
        
    except Exception as e:
        logger.error("Salary info retrieval error: %s", str(e))
        state["salary_info"] = f"급여 정보 조회 오류: {str(e)}"
    
    return state

@tool
@traceable(name="get_preparation_advice_tool")
def get_preparation_advice_tool(state_or_params: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """직무 준비 조언 제공."""
    # 입력 처리
    if isinstance(state_or_params, str):
        try:
            state_or_params = json.loads(state_or_params)
        except:
            try:
                state_or_params = eval(state_or_params)
            except:
                pass
    
    # state가 아닌 경우 이전 단계의 state 가져오기
    if not isinstance(state_or_params, dict) or "parsed_input" not in state_or_params:
        logger.warning("Invalid state provided to get_preparation_advice_tool: %s", state_or_params)
        return {"error": "직무 준비 조언 제공을 위한 유효한 상태가 제공되지 않았습니다."}
    
    state = state_or_params
    
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
            f"기술 스택: {', '.join(state['parsed_input']['tech_stack'])}"
        )
        
        # 직무 정보 구성
        job_data = state["selected_job"].page_content if hasattr(state["selected_job"], "page_content") else "정보 없음"
        
        # LLM 체인으로 준비 조언 생성
        state["preparation_advice"] = advice_chain.invoke({
            "user_profile": user_profile,
            "job_data": job_data
        }).content
        
    except Exception as e:
        logger.error("Preparation advice generation error: %s", str(e))
        state["preparation_advice"] = f"준비 조언 생성 오류: {str(e)}"
    
    return state

@tool
@traceable(name="summarize_results_tool")
def summarize_results_tool(state_or_params: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """결과 요약."""
    # 입력 처리
    if isinstance(state_or_params, str):
        try:
            state_or_params = json.loads(state_or_params)
        except:
            try:
                state_or_params = eval(state_or_params)
            except:
                pass
    
    # state가 아닌 경우 이전 단계의 state 가져오기
    if not isinstance(state_or_params, dict) or "parsed_input" not in state_or_params:
        logger.warning("Invalid state provided to summarize_results_tool: %s", state_or_params)
        return {"error": "결과 요약을 위한 유효한 상태가 제공되지 않았습니다."}
    
    state = state_or_params
    
    try:
        # 대화 기록 문자열로 변환
        chat_history_str = "\n".join([
            f"User: {msg.get('user', '')}\nAssistant: {msg.get('assistant', '')}"
            for msg in state.get("chat_history", [])
        ])
        
        # LLM 체인으로 결과 요약
        summary = summary_memory_chain.invoke({
            "job_recommendations": state.get("job_recommendations", ""),
            "company_info": state.get("company_info", ""),
            "salary_info": state.get("salary_info", ""),
            "preparation_advice": state.get("preparation_advice", ""),
            "chat_history": chat_history_str
        }).content
        
        state["final_answer"] = summary
        
    except Exception as e:
        logger.error("Results summarization error: %s", str(e))
        state["final_answer"] = f"결과 요약 오류: {str(e)}"
    
    return state