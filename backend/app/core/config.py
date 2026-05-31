from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import os

# Load .env file into environment
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "RAG chatbot"
    API_V1_STR: str = "/api/v1"
    
    # API Keys
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # Qdrant Database configurations
    QDRANT_HOST: Optional[str] = None
    QDRANT_PORT: Optional[int] = 6333
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_PATH: Optional[str] = "qdrant_db"
    QDRANT_LOCATION: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore" # Ignore extra env vars
    )

settings = Settings()

