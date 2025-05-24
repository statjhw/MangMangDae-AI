import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langsmith import Client

# 환경 변수 로드
load_dotenv()

def get_config():
    """환경 변수를 가져오는 함수"""
    required_env_vars = [
        "OPENAI_API_KEY", 
        "TAVILY_API_KEY", 
        "PINECONE_API_KEY", 
        "HugginfFace_API_KEY",
        "LANGSMITH_API_KEY"
    ]
    
    for var in required_env_vars:
        if not os.getenv(var):
            raise ValueError(f"Environment variable {var} is not set.")
    
    return {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "tavily_api_key": os.getenv("TAVILY_API_KEY"),
        "pinecone_api_key": os.getenv("PINECONE_API_KEY"),
        "huggingface_api_key": os.getenv("HugginfFace_API_KEY"),
        "langsmith_api_key": os.getenv("LANGSMITH_API_KEY"),
        "langsmith_project": os.getenv("LANGSMITH_PROJECT", "job_advisor")
    }

# LangSmith 설정
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = get_config().get("langsmith_project")
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

# 싱글턴 인스턴스 저장용 변수
_llm = None
_pinecone_index = None
_tavily_tool = None
_langsmith_client = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(model_name="gpt-3.5-turbo")
    return _llm

def get_pinecone_client():
    """Pinecone 클라이언트 객체를 반환"""
    config = get_config()
    return Pinecone(api_key=config["pinecone_api_key"])

def get_pinecone():
    """Pinecone Index 객체를 반환"""
    global _pinecone_index
    if _pinecone_index is None:
        pc = get_pinecone_client()
        _pinecone_index = pc.Index('mmdindex') #################### index 이름 변경
    return _pinecone_index

def get_tavily_tool():
    global _tavily_tool
    if _tavily_tool is None:
        _tavily_tool = TavilySearchResults(max_results=3)
    return _tavily_tool

def get_langsmith_client():
    """LangSmith 클라이언트 객체를 반환"""
    global _langsmith_client
    if _langsmith_client is None:
        config = get_config()
        _langsmith_client = Client(api_key=config["langsmith_api_key"])
    return _langsmith_client

# RateLimitError 직접 정의
class RateLimitError(Exception):
    """API 호출 제한에 도달했을 때 발생하는 예외"""
    pass
