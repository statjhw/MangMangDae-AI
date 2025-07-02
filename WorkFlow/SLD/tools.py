from datetime import datetime
from typing import Dict, Any, Union
import logging
import json
import os
from langchain_core.tools import tool
from langchain_core.documents import Document
from langsmith import traceable
from WorkFlow.Util.utils import memory, job_chain, advice_chain, summary_memory_chain, verify_job_chain, final_answer_chain, question_generation_chain
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
            "location": user_input.get("candidate_location", ""),
            "question": user_input.get("candidate_question", "")
        },
        "chat_history": [{
            "user": user_input.get("candidate_question", ""),
            "assistant": "",
            "timestamp": datetime.now().isoformat()
        }],
        "conversation_turn": 1, 
        "job_list": None, # 리트리버를 통한 top-k
        "selected_job": "", # top-1; 최종 선정된 문서 
        "search_result": "", # top-1 문서의 급여 정보 **단순 급여가 아닌,회사에 대한 정보 중 인터넷으로 찾아야 답변이 가능한 정보
        "preparation_advice": "", # 조언
        "final_answer": "", # 최종 답변
        "retry_count": 0,
        "revised_query": ""
    }
    memory.add_user_message(user_input["candidate_question"])
    memory.add_ai_message("")
    logger.info("Parsed input: %s", state["parsed_input"])
    return state



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
        f"기술 스택: {', '.join(state['parsed_input']['tech_stack'])}",
        f"희망 근무지역: {state['parsed_input']['location']}",
        f"사용자 질문: {state['revised_query']}"
    )
    job_chain_input = {}
    job_chain_input["user_profile"] = user_profile

    base_query = state["revised_query"] if state["revised_query"] else state["parsed_input"]["question"]
    query = f"[query] {base_query}" 
    
    logger.info("Similarity search query: %s (retry_count: %d)", query, state["retry_count"])
    
    try:
        doc_scores, doc_texts = retrieve(query)
        logger.info("Retriever results: %s", 
                    [{"score": score, "text": text} for score,text in zip(doc_scores,doc_texts)])
        
        if not doc_texts:
            logger.warning("No job results found for query: %s", query)
            state["job_list"] = {}
            state["selected_job"] = "검색 결과 없음"
        else:
            selected_jobs_dict = [
                {
                    "parsed": _parse_job_posting(text),
                    "original_text": text
                }
                for text in doc_texts
            ]

            for i, result in enumerate(selected_jobs_dict, start=1):
                parsed_data = result["parsed"]
                job_chain_input[f"회사 {i}"] = parsed_data.get("회사", "정보 없음")
                job_chain_input[f"직무 {i}"] = parsed_data.get("직무", "정보 없음")
                job_chain_input[f"위치 {i}"] = parsed_data.get("위치", "정보 없음")
                job_chain_input[f"자격 요건 {i}"] = parsed_data.get("자격 요건", "정보 없음")
                job_chain_input[f"우대 사항 {i}"] = parsed_data.get("우대 사항", "정보 없음")
                job_chain_input[f"원본 {i}"] = result["original_text"] # 최종 답변 생성을 위해 원본은 계속 전달
                job_chain_input[f"코사인유사도 {i}"] = doc_scores[i-1]

            # 만약 검색 결과가 5개 미만일 경우, 나머지 슬롯을 기본값으로 채움.
            for i in range(len(selected_jobs_dict) + 1, 6):
                job_chain_input[f"회사 {i}"] = "N/A"
                job_chain_input[f"직무 {i}"] = "N/A"
                job_chain_input[f"위치 {i}"] = "N/A"
                job_chain_input[f"자격 요건 {i}"] = "N/A"
                job_chain_input[f"우대 사항 {i}"] = "N/A"
                job_chain_input[f"원본 {i}"] = "해당하는 채용공고가 없습니다."
                job_chain_input[f"코사인유사도 {i}"] = 0.0

            state["job_list"] = selected_jobs_dict # top k list

            # 선정 프롬프트 결과를 JSON으로 파싱하여 각각 저장
            try:
                job_result = job_chain.invoke(job_chain_input)
                
                if hasattr(job_result, "content"):
                    parsed = json.loads(job_result.content)
                else:
                    parsed = json.loads(job_result)

                selected_index = parsed.get("selected_job_index")
                state["selected_job_reason"] = parsed.get("selected_job_reason", "")
                if selected_index and 1 <= int(selected_index) <= len(selected_jobs_dict):
                    full_original_text = selected_jobs_dict[int(selected_index) - 1]["original_text"]
                    state["selected_job"] = full_original_text
                else:
                    state["selected_job"] = "적합한 직무를 선택하지 못했습니다."
            except Exception as e:
                logger.error("Failed to parse job_chain result as JSON: %s", str(e))
                state["selected_job"] = "추천 결과 파싱 오류"
                state["selected_job_reason"] = "추천 결과 파싱 오류"
            
            ###################################################################
    
    except RateLimitError as e:
        logger.error("RateLimitError in similarity_search: %s", str(e))
        state["job_list"] = {}
        state["selected_job"] = "API 호출 제한으로 추천 실패"
    
    except Exception as e:
        logger.error("Similarity search error: %s", str(e))
        state["job_list"] = {}
        state["selected_job"] = "검색 오류"
    
    if "selected_job" in state and state["selected_job"]:
        logger.info("Selected job: %s", state["selected_job"])
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
        f"기술 스택: {', '.join(state['parsed_input']['tech_stack'])}",
        f"희망 근무지역: {state['parsed_input']['location']}",
    )

    question = state["revised_query"] if state["revised_query"] else state["parsed_input"]["question"]
    job_document = state["selected_job"] if state["selected_job"] else "정보 없음"
    
    try:
        verification_result = verify_job_chain.invoke({
            "user_profile": user_profile,
            "question": question,
            "job_document": job_document
        }).content
        # 결과가 문자열 'true'/'false' 또는 bool로만 오도록 강제
        if isinstance(verification_result, str):
            result_str = verification_result.strip().lower()
            if result_str in ["true", "false"]:
                is_relevant = result_str == "true"
            else:
                # 예외: JSON 등 다른 형식이 오면 파싱 시도
                try:
                    result_json = json.loads(verification_result)
                    is_relevant = bool(result_json.get("is_relevant", False))
                except Exception:
                    is_relevant = False
        else:
            is_relevant = bool(verification_result)
        state["is_relevant"] = is_relevant
        logger.info("Verification result: is_relevant=%s", is_relevant)
        if not is_relevant:
            state["retry_count"] += 1
            try:
                revised_result = question_generation_chain.invoke({"question": question})
                state["revised_query"] = revised_result.content if hasattr(revised_result, "content") else revised_result
            except Exception as e:
                logger.error("Failed to generate revised_query: %s", str(e))
                state["revised_query"] = ""
        else:
            state["revised_query"] = ""
            state["retry_count"] = 0
    except Exception as e:
        logger.error("Verification error: %s", str(e))
        state["revised_query"] = ""
        state["retry_count"] = 0
    return state

@tool
@traceable(name="search_company_info_tool")
def search_company_info_tool(state_or_params: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """선택된 회사에 대한 사용자 질문을 웹에서 검색 (Tavily 활용)."""
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
        logger.warning("Invalid state provided to search_company_info_tool: %s", state_or_params)
        return {"error": "회사 정보 검색을 위한 유효한 상태가 제공되지 않았습니다."}
    
    state = state_or_params
    
    if "selected_job" not in state or not state["selected_job"]:
        logger.warning("No selected_job in state for company info retrieval")
        state["search_result"] = "선택된 직무 정보가 없어 회사 정보를 검색할 수 없습니다."
        return state
    
    try:
        # selected_job(채용공고 원본 텍스트)에서 회사 이름 파싱
        selected_job_text = state["selected_job"]
        parsed_job = _parse_job_posting(selected_job_text)
        company_name = parsed_job.get("회사", "")
        
        if not company_name:
            logger.warning("Could not parse company name from selected_job text.")
            state["search_result"] = "채용 공고에서 회사 이름을 찾을 수 없어 검색에 실패했습니다."
            return state

        # 사용자 질문과 회사 이름으로 검색어 구성
        user_question = state["parsed_input"].get("question", "")
        search_query = f"{company_name} {user_question}"  ####### 수정 필요; 단순히 회사명 + 질문 형태임
        logger.info("Tavily search query: %s", search_query)
        
        # 웹 검색 실행
        search_results = tavily_tool.invoke(search_query)
        
        # 검색 결과를 하나의 텍스트로 정리
        formatted_results = "\n".join([f"Source {i+1}:\n{result['content']}" for i, result in enumerate(search_results)])
        
        # 결과를 state에 저장
        state["search_result"] = formatted_results
        
    except Exception as e:
        logger.error("Company info retrieval (web search) error: %s", str(e))
        state["search_result"] = f"웹 검색 중 오류가 발생했습니다: {str(e)}"
        
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
        # 최종 답변 생성
        final_answer = final_answer_chain.invoke({
            "selected_job": state.get("selected_job", ""),
            "search_result": state.get("search_result", ""),
            "preparation_advice": state.get("preparation_advice", "")
        })
        
        state["final_answer"] = final_answer
        
        # conversation_turn이 6 이상일 때만 대화 내용 요약
        if state.get("conversation_turn", 0) >= 6:
            # 대화 기록 문자열로 변환
            chat_history_str = "\n".join([
                f"User: {msg.get('user', '')}\nAssistant: {msg.get('assistant', '')}"
                for msg in state.get("chat_history", [])
            ])
            
            # LLM 체인으로 대화 내용 요약
            summary = summary_memory_chain.invoke({
                "selected_job": state.get("selected_job", ""),
                "search_result": state.get("search_result", ""),
                "preparation_advice": state.get("preparation_advice", ""),
                "chat_history": chat_history_str
            }).content
            
            # 요약된 내용을 chat_history에 추가
            state["chat_history"].append({
                "user": "System",
                "assistant": summary,
                "timestamp": datetime.now().isoformat()
            })
            
            # 이전 대화 내용 정리 (마지막 2개의 대화만 유지)
            if len(state.get("chat_history", [])) > 2:
                state["chat_history"] = state["chat_history"][-2:]
                logger.info("Cleaned up chat history, keeping only last 2 conversations")
        
    except Exception as e:
        logger.error("Results summarization error: %s", str(e))
        state["chat_history"].append({
            "user": "System",
            "assistant": f"결과 요약 오류: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })
        state["final_answer"] = f"최종 답변 생성 중 오류가 발생했습니다: {str(e)}"
    
    return state