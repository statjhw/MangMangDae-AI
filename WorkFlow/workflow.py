from langgraph.graph import StateGraph, END
from datetime import datetime
from utils import GraphState, memory, job_chain, company_chain, salary_chain, advice_chain, answer_chain, summary_memory_chain
from retrival.embeddings import vector_store
from config import tavily_tool


# 워크플로우 노드
def parse_input(state: GraphState) -> GraphState:
    """사용자 입력 파싱 (LLM 없이 직접 매핑)."""
    # user_input은 dict로 candidate_major, candidate_interest, candidate_career, candidate_question 포함
    state["parsed_input"] = {
        "education": state["user_input"]["candidate_major"],
        "experience": state["user_input"]["candidate_career"],
        "desired_job": state["user_input"]["candidate_interest"],
        "question": state["user_input"]["candidate_question"]
    }
    state["conversation_turn"] += 1
    # chat_history에 candidate_question 기록
    state["chat_history"].append({
        "user": state["user_input"]["candidate_question"],
        "assistant": "",
        "timestamp": datetime.now().isoformat()
    })
    memory.save_context({"input": state["user_input"]["candidate_question"]}, {"output": ""})
    return state

def recommend_jobs(state: GraphState) -> GraphState:
		# 템플릿 2
    user_profile = (
        f"학력: {state['parsed_input']['education']}, "
        f"경력: {state['parsed_input']['experience']}, "
        f"희망 직무: {state['parsed_input']['desired_job']}, "
    )
    job_results = vector_store.similarity_search(state["parsed_input"]["question"]) ######### 리트리버

    ####################################### 여기도 벡터 db업데이트하면 수정 필요
    job_list = "\n".join(
        [f"내용: {doc.page_content}"
         f"직무: {doc.metadata['job_name']}"
         f"회사명: {doc.metadata['company_name']}"
         f"복지: {doc.metadata['tag_name']}"
         for doc in job_results[:3]]
    )
    ###########################################
    state["job_recommendations"] = job_chain.run(user_profile=user_profile, job_list=job_list)
    state["selected_job"] = job_results[0]
    return state

def get_company_info(state: GraphState) -> GraphState:
    """회사 정보 조회 (selected_job의 job_list 사용)."""
    selected_job = state["selected_job"]
    # page_content에서 [회사 소개] 추출
    content_lines = selected_job.page_content.split("\n")
    ####################################### 여기도 벡터 db업데이트하면 수정 필요
    company_description = ""
    for i, line in enumerate(content_lines):
        if line.startswith("[회사 소개]"):
            company_description = "\n".join(content_lines[i+1:content_lines.index("", i) if "" in content_lines[i:] else None]).strip()
            break
    company_data_str = (
        f"이름: {selected_job.metadata['company_name']}, "
        f"설명: {company_description}, "
        f"위치: 정보 없음, "
        f"산업: 스타트업, AI, "
        f"주요 특징: {selected_job.metadata['tag_name']}"
    )
    ###########################################
    state["company_info"] = company_chain.run(company_data=company_data_str)
    return state

def get_salary_info(state: GraphState) -> GraphState:
    """급여 정보 조회 (웹 검색 사용)."""
    job_data = (
        f"직무: {state['selected_job'].metadata['job_name']}, "
        f"회사: {state['selected_job'].metadata['company_name']}"
    )
    search_query = f"{state['selected_job'].metadata['job_name']} {state['selected_job'].metadata['company_name']} salary Korea"
    try:
        search_results = tavily_tool.invoke(search_query)
        search_results_str = (
            "\n".join([f"- {res['title']}: {res['content']} (링크: {res['url']})" for res in search_results])
            if search_results else "검색 결과 없음"
        )
    except Exception as e:
        search_results_str = f"검색 오류: {str(e)}"
    state["salary_info"] = salary_chain.run(job_data=job_data, search_results=search_results_str)
    return state


def get_preparation_advice(state: GraphState) -> GraphState:
    """준비 조언 제공 (selected_job의 job_list 사용)."""
    user_profile = (
        f"학력: {state['parsed_input']['education']}, "
        f"경력: {state['parsed_input']['experience']}, "
        f"희망 직무: {state['parsed_input']['desired_job']}, "
    )
    ####################################### 여기도 벡터 db업데이트하면 수정 필요
    job_data = (
        f"직무: {state['selected_job'].metadata['job_name']}, "
        f"회사: {state['selected_job'].metadata['company_name']}, "
        f"설명: {state['selected_job'].page_content.split('[우리가 찾는 인재상]')[0].replace('[회사 소개]', '').strip()}, " ##############################3
        f"복지: {state['selected_job'].metadata['tag_name']}"
    )
    ##############################

    state["preparation_advice"] = advice_chain.run(user_profile=user_profile, job_data=job_data)
    return state

def summarize_results(state: GraphState) -> GraphState:
    """결과 요약 및 대화 메모리 관리."""
    chat_history = "\n".join(
        [f"[{msg['timestamp']}] 사용자: {msg['user']}\n어시스턴트: {msg['assistant']}" for msg in state['chat_history']]
    )
    state["final_answer"] = answer_chain.run(
        job_recommendations=state["job_recommendations"],
        company_info=state["company_info"],
        salary_info=state["salary_info"],
        preparation_advice=state["preparation_advice"]
    )
    state["chat_history"][-1]["assistant"] = state["final_answer"]
    memory.save_context({"input": state["user_input"]["candidate_question"]}, {"output": state["final_answer"]})

    if state["conversation_turn"] >= 6:
        summary = summary_memory_chain.run(chat_history=chat_history)
        state["chat_history"] = [{"user": "대화 요약", "assistant": summary, "timestamp": datetime.now().isoformat()}]
        memory.clear()
        memory.save_context({"input": "대화 요약"}, {"output": summary})
    return state

# 워크플로우 설정
workflow = StateGraph(GraphState)
workflow.add_node("parse_input", parse_input)
workflow.add_node("recommend_jobs", recommend_jobs)
workflow.add_node("get_company_info", get_company_info)
workflow.add_node("get_salary_info", get_salary_info)
workflow.add_node("get_preparation_advice", get_preparation_advice)
workflow.add_node("summarize_results", summarize_results)

# 엣지 정의
workflow.set_entry_point("parse_input")
workflow.add_edge("parse_input", "recommend_jobs")
workflow.add_edge("recommend_jobs", "get_company_info")
workflow.add_edge("get_company_info", "get_salary_info")
workflow.add_edge("get_salary_info", "get_preparation_advice")
workflow.add_edge("get_preparation_advice", "summarize_results")
workflow.add_edge("summarize_results", END)

# 워크플로우 컴파일
app = workflow.compile()