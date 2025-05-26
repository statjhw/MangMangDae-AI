from typing import Dict, List
from langchain_core.runnables import RunnableSequence
from config import get_llm
from Template.promots import job_recommendation_prompt, company_info_prompt, salary_info_prompt, preparation_advice_prompt, career_advice_prompt, summary_memory_prompt
from langchain.memory import ConversationBufferMemory

# 대화 메모리
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# llm 객체를 함수로 받아옴
llm = get_llm()

# RunnableSequence 객체 생성
class RunInvokeAdapter:
    """RunnableSequence에 run 메소드를 제공하는 어댑터"""
    def __init__(self, runnable):
        self.runnable = runnable
        
    def run(self, **kwargs):
        """invoke 메소드를 run 인터페이스로 노출"""
        return self.runnable.invoke(kwargs)

# llm chain (각 체인에 run 메소드 제공)
job_chain = RunInvokeAdapter(job_recommendation_prompt | llm)
company_chain = RunInvokeAdapter(company_info_prompt | llm)
salary_chain = RunInvokeAdapter(salary_info_prompt | llm)
advice_chain = RunInvokeAdapter(preparation_advice_prompt | llm)
answer_chain = RunInvokeAdapter(career_advice_prompt | llm)
summary_memory_chain = RunInvokeAdapter(summary_memory_prompt | llm)

# LangGraph 상태 정의
class GraphState(Dict):
    user_input: str
    parsed_input: Dict
    job_recommendations: str
    company_info: str
    salary_info: str
    preparation_advice: str
    final_answer: str
    selected_job: Dict
    chat_history: List[Dict]
    conversation_turn: int 