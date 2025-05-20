import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults

# 환경 변수 로드
load_dotenv()

# 필수 환경 변수 확인
required_env_vars = ["OPENAI_API_KEY", "TAVILY_API_KEY", "PINECONE_API_KEY", "HugginfFace_API_KEY"]
for var in required_env_vars:
    if not os.getenv(var):
        raise ValueError(f"Environment variable {var} is not set.")

# OpenAI 클라이언트
llm = ChatOpenAI(model_name="gpt-3.5-turbo")

# Pinecone 클라이언트
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
index = pc.Index('job-offer')

# Tavily 검색 도구
tavily_tool = TavilySearchResults(max_results=3) 