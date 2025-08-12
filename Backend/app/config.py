import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: Optional[str] = None
    aws_rds_host: Optional[str] = None
    aws_rds_db: Optional[str] = None
    aws_rds_user: Optional[str] = None
    aws_rds_password: Optional[str] = None
    aws_rds_port: int = 5432
    
    # Redis
    redis_url: Optional[str] = None
    redis_host: Optional[str] = None
    redis_port: int = 6379
    redis_user: str = "default"
    redis_password: Optional[str] = None
    
    # AWS
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "ap-northeast-2"
    
    # OpenSearch
    opensearch_host: Optional[str] = None
    opensearch_port: int = 443
    opensearch_index: str = "opensearch_job"
    aws_opensearch_access_key_id: Optional[str] = None
    aws_opensearch_secret_access_key: Optional[str] = None
    
    # API Keys
    openai_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    pinecone_api_key: Optional[str] = None
    langsmith_api_key: Optional[str] = None
    huggingface_api_key: Optional[str] = None
    
    # App Settings
    debug: bool = False
    cors_origins: list[str] = [
        "https://mangmangdae-ai.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def get_database_url(self) -> str:
        """Get database URL from Railway or construct from components"""
        if self.database_url:
            return self.database_url
        
        if all([self.aws_rds_host, self.aws_rds_user, self.aws_rds_password, self.aws_rds_db]):
            return f"postgresql://{self.aws_rds_user}:{self.aws_rds_password}@{self.aws_rds_host}:{self.aws_rds_port}/{self.aws_rds_db}"
        
        raise ValueError("Database configuration not found")
    
    @property
    def get_redis_url(self) -> str:
        """Get Redis URL from Railway or construct from components"""
        if self.redis_url:
            return self.redis_url
        
        if self.redis_host and self.redis_password:
            return f"redis://{self.redis_user}:{self.redis_password}@{self.redis_host}:{self.redis_port}"
        
        return "redis://localhost:6379"


# Global settings instance
settings = Settings()