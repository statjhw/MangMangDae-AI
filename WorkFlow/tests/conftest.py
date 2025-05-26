import pytest
from typing import Dict, Any
from unittest.mock import MagicMock, patch

class MockGraphState(dict):
    """GraphState 모의 클래스"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self["conversation_turn"] = 0
        self["chat_history"] = []

@pytest.fixture
def vector_store_instance():
    """벡터 스토어 모의 객체 인스턴스"""
    mock_doc = MagicMock()
    mock_doc.page_content = "가짜 직무 내용"
    mock_doc.metadata = {
        "job_name": "백엔드 개발자",
        "company_name": "테스트 회사",
        "tag_name": "좋은 복지"
    }
    
    mock_vs = MagicMock()
    mock_vs.similarity_search.return_value = [mock_doc]
    return mock_vs

@pytest.fixture
def mock_tavily_instance():
    """Tavily 검색 도구 모의 객체 인스턴스"""
    mock_tavily = MagicMock()
    mock_tavily.invoke.return_value = [{
        "title": "테스트 급여 정보",
        "content": "연봉 5,000만원 ~ 7,000만원",
        "url": "https://example.com"
    }]
    return mock_tavily

@pytest.fixture
def mock_memory_instance():
    """메모리 모의 객체 인스턴스"""
    mock_memory = MagicMock()
    mock_memory.save_context = MagicMock()
    mock_memory.clear = MagicMock()
    return mock_memory

@pytest.fixture
def mock_chain_instance():
    """체인 모의 객체"""
    mock_chain = MagicMock()
    mock_chain.run.return_value = "테스트 응답"
    return mock_chain

@pytest.fixture
def mock_pinecone_index():
    """Pinecone Index 모의 객체"""
    mock_index = MagicMock()
    return mock_index

# 실제 모듈 대신 Mock 객체들을 사용하도록 패치
@pytest.fixture(autouse=True)
def mock_imports(monkeypatch, vector_store_instance, mock_tavily_instance, mock_memory_instance, mock_chain_instance, mock_pinecone_index):
    """실제 모듈 대신 Mock 객체들을 사용하도록 설정"""
    # GraphState 모킹
    monkeypatch.setattr("WorkFlow.Util.utils.GraphState", MockGraphState)
    
    # 환경 변수 의존성 제거를 위한 패치
    monkeypatch.setattr("config.get_config", lambda: {
        "openai_api_key": "mock_key",
        "tavily_api_key": "mock_key",
        "pinecone_api_key": "mock_key",
        "huggingface_api_key": "mock_key"
    })
    
    # 외부 API 의존성 모킹
    monkeypatch.setattr("config.get_pinecone_client", lambda: MagicMock())
    monkeypatch.setattr("config.get_pinecone", lambda: mock_pinecone_index)
    monkeypatch.setattr("Retrival.embeddings.get_vector_store", lambda: vector_store_instance)
    monkeypatch.setattr("config.get_tavily_tool", lambda: mock_tavily_instance)
    
    # LLM 체인 모킹
    monkeypatch.setattr("WorkFlow.Util.utils.memory", mock_memory_instance)
    
    # 체인들도 Mock으로 대체
    chain_names = [
        "job_chain", "company_chain", "salary_chain", 
        "advice_chain", "answer_chain", "summary_memory_chain"
    ]
    for chain_name in chain_names:
        monkeypatch.setattr(f"WorkFlow.Util.utils.{chain_name}", mock_chain_instance) 