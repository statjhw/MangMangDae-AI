from typing import Dict, List, Any, Callable
from WorkFlow.config import get_llm
from Template.prompts import actionable_advice_prompt, summary_memory_prompt, final_answer_prompt, intent_analysis_prompt, contextual_qa_prompt, reformulate_query_prompt, web_search_planner_prompt

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
    
    def invoke(self, data):
        """invoke 메소드 추가"""
        if isinstance(data, dict):
            return self.runnable.invoke(data)
        return self.runnable.invoke({"input": data})

# llm chain (각 체인에 run 메소드 제공)
#advice_chain = RunInvokeAdapter(preparation_advice_prompt | llm)
advice_chain = RunInvokeAdapter(actionable_advice_prompt | llm)
final_answer_chain = RunInvokeAdapter(final_answer_prompt | llm)
summary_memory_chain = RunInvokeAdapter(summary_memory_prompt | llm)
intent_analysis_chain = RunInvokeAdapter(intent_analysis_prompt | llm)
contextual_qa_prompt_chain =  RunInvokeAdapter(contextual_qa_prompt | llm)
reformulate_query_chain = RunInvokeAdapter(reformulate_query_prompt | llm)
web_search_planner_chain = RunInvokeAdapter(web_search_planner_prompt | llm)

# Graph 상태 타입 정의
class GraphState(Dict):
    """Graph 상태를 저장하는 클래스"""
    pass

# 도구 함수 호출 유틸리티
def invoke_tool(tool_func: Callable, input_data: Any) -> Any:
    """LangChain 도구 함수를 직접 호출하는 유틸리티"""
    try:
        # 도구 타입 감지
        if hasattr(tool_func, "func"):
            # 데코레이터로 생성된 도구의 원본 함수 추출
            # LangChain의 @tool 데코레이터는 원본 함수를 'func' 속성에 저장
            original_func = tool_func.func
            return original_func(input_data)
        
        # LangChain BaseTool.invoke() 메서드 호출
        elif hasattr(tool_func, "invoke"):
            # 이 방식이 가장 권장됨 (LangChain 공식 인터페이스)
            return tool_func.invoke(input_data)
        
        # 일반 함수 직접 호출
        elif callable(tool_func):
            return tool_func(input_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        tool_name = getattr(tool_func, "name", str(tool_func))
        raise RuntimeError(f"Error calling tool {tool_name}: {str(e)}")
    
    tool_name = getattr(tool_func, "name", str(tool_func))
    raise ValueError(f"Cannot invoke tool: {tool_name}")

