import pytest
from datetime import datetime
from WorkFlow.SLD.tools import (
    parse_input, recommend_jobs, get_company_info,
    get_salary_info, get_preparation_advice, summarize_results
)
from WorkFlow.Util.utils import GraphState

@pytest.fixture
def sample_state():
    """테스트용 기본 상태 생성"""
    return GraphState({
        "user_input": {
            "candidate_major": "컴퓨터공학",
            "candidate_interest": "백엔드 개발자",
            "candidate_career": "3년",
            "candidate_question": "서울 지역 백엔드 개발자 포지션 추천해주세요"
        },
        "conversation_turn": 0,
        "chat_history": []
    })

class TestWorkflowIntegration:
    def test_complete_workflow(self, sample_state):
        """전체 워크플로우 통합 테스트"""
        # 각 노드 순차 실행
        state = parse_input(sample_state)
        state = recommend_jobs(state)
        state = get_company_info(state)
        state = get_salary_info(state)
        state = get_preparation_advice(state)
        state = summarize_results(state)
        
        # 최종 결과 검증
        assert all(key in state for key in [
            "parsed_input", "job_recommendations", "selected_job",
            "company_info", "salary_info", "preparation_advice",
            "final_answer", "chat_history"
        ])
        assert state["conversation_turn"] == 1
        assert len(state["chat_history"]) > 0

    def test_workflow_with_multiple_turns(self, sample_state):
        """여러 턴의 대화 테스트"""
        # 첫 번째 턴
        state = parse_input(sample_state)
        state = recommend_jobs(state)
        state = get_company_info(state)
        state = get_salary_info(state)
        state = get_preparation_advice(state)
        state = summarize_results(state)
        
        # 두 번째 턴
        state["user_input"]["candidate_question"] = "이 회사의 복지 혜택은 어떤가요?"
        state = parse_input(state)
        state = recommend_jobs(state)
        state = get_company_info(state)
        state = get_salary_info(state)
        state = get_preparation_advice(state)
        state = summarize_results(state)
        
        assert state["conversation_turn"] == 2
        assert len(state["chat_history"]) == 2

    def test_workflow_error_recovery(self, sample_state):
        """에러 복구 테스트"""
        # 첫 번째 턴 (성공)
        state = parse_input(sample_state)
        state = recommend_jobs(state)
        state = get_company_info(state)
        state = get_salary_info(state)
        state = get_preparation_advice(state)
        state = summarize_results(state)
        
        # 두 번째 턴 (에러 발생)
        state["user_input"]["candidate_question"] = ""
        with pytest.raises(Exception):
            parse_input(state)
        
        # 세 번째 턴 (정상 복구)
        state["user_input"]["candidate_question"] = "다른 회사도 추천해주세요"
        state = parse_input(state)
        state = recommend_jobs(state)
        state = get_company_info(state)
        state = get_salary_info(state)
        state = get_preparation_advice(state)
        state = summarize_results(state)
        
        assert state["conversation_turn"] == 2
        assert len(state["chat_history"]) == 2 