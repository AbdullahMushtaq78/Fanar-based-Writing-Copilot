"""
Configuration settings for the multi-agent system.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Fanar API Configuration
    fanar_api_key: str = os.getenv("FANAR_API_KEY", "")
    fanar_base_url: str = "https://api.fanar.qa/v1"
    
    # Tavily API Configuration 
    tavily_api_key: Optional[str] = os.getenv("TAVILY_API_KEY", "")
    
    # Model Configuration
    fanar_simple_model: str = "Fanar"
    fanar_rag_model: str = "Islamic-RAG"
    
    # Token Limits
    max_tokens_default: int = 2048
    max_tokens_thinking: int = 2048
    max_tokens_rag: int = 2048
    
    # Islamic Sources for RAG
    preferred_sources: List[str] = [
        "islamqa", "islamweb", "sunnah", "quran", 
        "tafsir", "dorar", "islamonline", "shamela"
    ]
    
    # Application Configuration
    debug: bool = True
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings() 