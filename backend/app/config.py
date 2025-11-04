"""
Configuration management using Pydantic Settings
Loads environment variables from .env file or environment
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import json


class Settings(BaseSettings):
    """Application configuration loaded from environment variables"""

    # Redis and Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # WhisperX Configuration
    WHISPER_MODEL: str = "large-v2"
    WHISPER_DEVICE: str = "cuda"
    WHISPER_COMPUTE_TYPE: str = "float16"

    # File Storage Configuration
    UPLOAD_DIR: str = "/uploads"
    MAX_FILE_SIZE: int = 2147483648  # 2GB in bytes
    MAX_DURATION_HOURS: int = 2

    # CORS Configuration
    CORS_ORIGINS: str = '["http://localhost:5173"]'

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS JSON string to list"""
        try:
            return json.loads(self.CORS_ORIGINS)
        except json.JSONDecodeError:
            return ["http://localhost:5173"]


# Global settings instance
settings = Settings()
