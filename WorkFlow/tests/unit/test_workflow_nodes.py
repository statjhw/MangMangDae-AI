import pytest
from datetime import datetime
from WorkFlow.SLD.workflow import (
    parse_input, recommend_jobs, get_company_info,
    get_salary_info, get_preparation_advice, summarize_results
)

@pytest.fixture
def sample_state():
    """테스트용 기본 상태 생성"""
    return {
        "user_input": {
            "candidate_major": "컴퓨터공학",
            "candidate_interest": "백엔드 개발자",
            "candidate_career": "3년",
            "candidate_question": "서울 지역 백엔드 개발자 포지션 추천해주세요"
        },
        "conversation_turn": 0,
        "chat_history": []
    }

class TestParseInput:
    def test_successful_parsing(self, sample_state):
        """정상적인 입력 파싱 테스트"""
        result = parse_input(sample_state)
        
        assert "parsed_input" in result
        assert result["parsed_input"]["education"] == "컴퓨터공학"
        assert result["parsed_input"]["desired_job"] == "백엔드 개발자"
        assert result["conversation_turn"] == 1
        assert len(result["chat_history"]) == 1

    def test_empty_question(self, sample_state):
        """빈 질문 입력 테스트"""
        sample_state["user_input"]["candidate_question"] = ""
        with pytest.raises(Exception):
            parse_input(sample_state)

class TestRecommendJobs:
    def test_job_recommendation(self, sample_state):
        """직무 추천 테스트"""
        state = parse_input(sample_state)
        result = recommend_jobs(state)
        
        assert "job_recommendations" in result
        assert "selected_job" in result
        assert result["selected_job"] is not None

class TestCompanyInfo:
    def test_company_info_retrieval(self, sample_state):
        """회사 정보 조회 테스트"""
        state = parse_input(sample_state)
        state = recommend_jobs(state)
        result = get_company_info(state)
        
        assert "company_info" in result
        assert result["company_info"] is not None

class TestSalaryInfo:
    def test_salary_info_retrieval(self, sample_state):
        """급여 정보 조회 테스트"""
        state = parse_input(sample_state)
        state = recommend_jobs(state)
        state = get_company_info(state)
        result = get_salary_info(state)
        
        assert "salary_info" in result
        assert result["salary_info"] is not None

class TestPreparationAdvice:
    def test_advice_generation(self, sample_state):
        """준비 조언 생성 테스트"""
        state = parse_input(sample_state)
        state = recommend_jobs(state)
        state = get_company_info(state)
        state = get_salary_info(state)
        result = get_preparation_advice(state)
        
        assert "preparation_advice" in result
        assert result["preparation_advice"] is not None

class TestSummarizeResults:
    def test_result_summarization(self, sample_state):
        """결과 요약 테스트"""
        state = parse_input(sample_state)
        state = recommend_jobs(state)
        state = get_company_info(state)
        state = get_salary_info(state)
        state = get_preparation_advice(state)
        result = summarize_results(state)
        
        assert "final_answer" in result
        assert result["final_answer"] is not None
        assert len(result["chat_history"]) > 0
        assert result["chat_history"][-1]["assistant"] == result["final_answer"] 