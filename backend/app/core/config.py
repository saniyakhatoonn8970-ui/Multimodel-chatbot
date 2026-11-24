import os
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application
    APP_NAME: str = "MindBridge AI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS & Security
    FRONTEND_URL: str = "http://localhost:8501"
    ALLOWED_ORIGINS: str = "http://localhost:8501,http://127.0.0.1:8501"

    # Database
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/mindbridge"
    ALLOW_SQLITE_DEV_FALLBACK: bool = True
    DEV_SQLITE_URL: str = "sqlite:///./mindbridge_dev.db"

    # Model Providers ("gemini", "openai", "mock")
    LLM_PROVIDER: str = "mock"
    LLM_MODEL: str = "gemini-1.5-flash"
    LLM_API_KEY: Optional[str] = None

    EMBEDDING_PROVIDER: str = "mock"
    EMBEDDING_MODEL: str = "text-embedding-004"
    EMBEDDING_API_KEY: Optional[str] = None

    VISION_PROVIDER: str = "mock"
    VISION_MODEL: str = "gemini-1.5-flash"
    VISION_API_KEY: Optional[str] = None

    STT_PROVIDER: str = "mock"
    STT_MODEL: str = "whisper-1"
    STT_API_KEY: Optional[str] = None

    TTS_PROVIDER: str = "mock"
    TTS_MODEL: str = "tts-1"
    TTS_API_KEY: Optional[str] = None

    # RAG Settings
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 4
    RAG_RELEVANCE_THRESHOLD: float = 0.35

    # Resource & File Limits
    MAX_DOCUMENT_SIZE_MB: int = 10
    MAX_IMAGE_SIZE_MB: int = 5
    MAX_AUDIO_SIZE_MB: int = 10
    MAX_PDF_PAGES: int = 50
    CONVERSATION_HISTORY_LIMIT: int = 15

    # Crisis & Safety Resources
    CRISIS_HELPLINE_US: str = "988 (Suicide & Crisis Lifeline - call or text 24/7)"
    CRISIS_TEXT_LINE: str = "Text HOME to 741741"
    CRISIS_INTERNATIONAL_URL: str = "https://findahelpline.com/"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


# Global settings instance
settings = Settings()
