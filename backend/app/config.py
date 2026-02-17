"""Application configuration using Pydantic Settings"""

from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/graph_rag"

    # LLM Configuration
    openai_api_key: Optional[str] = None
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    enable_llm_canonicalization: bool = False

    # API Authentication
    api_key: str = "default-api-key-change-in-production"

    # Application Settings
    max_traversal_depth: int = 5
    environment: str = "development"
    debug: bool = False
    cors_allow_origins: str = "*"

    # Server
    port: int = 8000
    host: str = "0.0.0.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
