"""
Configuration management using Pydantic Settings
Loads environment variables from .env file or environment
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Literal, Optional
import json


class Settings(BaseSettings):
    """Application configuration loaded from environment variables"""

    # Redis and Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # WhisperX model settings
    WHISPER_MODEL: str = "base"  # large-v2, large-v3, medium, small, base, tiny
    WHISPER_DEVICE: str = "cuda"  # cuda, cpu
    WHISPER_COMPUTE_TYPE: str = "float16"

    # BELLE-2 model settings
    BELLE2_MODEL_NAME: Optional[str] = None

    # Epic 3: Timestamp Optimization Settings
    OPTIMIZER_ENGINE: Literal["whisperx", "heuristic", "auto"] = Field(
        default="auto",
        description=(
            "Timestamp optimizer strategy. 'auto' prefers WhisperX if available, "
            "falling back to the heuristic implementation."
        ),
    )
    ENABLE_OPTIMIZATION: bool = Field(
        default=True,
        description=(
            "Feature flag for Epic 3 pipeline. Disable to bypass optimization and "
            "return raw BELLE-2 segments."
        ),
    )

    # File Storage Configuration
    UPLOAD_DIR: str = "/uploads"
    MAX_FILE_SIZE: int = 2147483648  # 2GB in bytes
    MAX_DURATION_HOURS: int = 2
    ALLOWED_FORMATS: List[str] = [
        "audio/mpeg",      # MP3
        "video/mp4",       # MP4
        "audio/wav",       # WAV
        "audio/x-m4a",     # M4A
        "audio/mp4",       # M4A alternative MIME type
        "audio/x-ms-wma",  # WMA (Windows Media Audio)
        "audio/wma",       # WMA alternative MIME type
    ]

    # CORS Configuration
    CORS_ORIGINS: str = '["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"]'

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
