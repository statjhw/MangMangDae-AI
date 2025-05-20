from typing import Dict, List
from langchain_core.runnables import RunnableSequence
from config import llm
from Template.prompts import job_recommendation_prompt, company_info_prompt, salary_info_prompt, preparation_advice_prompt, career_advice_prompt, summary_memory_prompt
from langchain_core.memory import ConversationBufferMemory

# 대화 메모리
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# llm chain
job_chain = job_recommendation_prompt | llm
company_chain = company_info_prompt | llm
salary_chain = salary_info_prompt | llm
advice_chain = preparation_advice_prompt | llm
answer_chain = career_advice_prompt | llm
summary_memory_chain = summary_memory_prompt | llm

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