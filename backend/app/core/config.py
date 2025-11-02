import secrets
from typing import Annotated, Any, Literal, List

from pydantic import (
    AnyUrl,
    BeforeValidator,
    Field,
    HttpUrl,
    PostgresDsn,
    computed_field,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from .logging_config import configure_logging


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../../../.env", # Adjusted path for the new structure
        env_ignore_empty=True,
        extra="ignore",
    )
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    FRONTEND_HOST: str = "http://localhost:5173"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    PROJECT_NAME: str = "AudioAlchemist"
    SENTRY_DSN: HttpUrl | None = None
    
    # MySQL settings
    MYSQL_SERVER: str = "192.168.0.200"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "alchemist"
    MYSQL_PASSWORD: str = "Alchemist.169828"
    MYSQL_DB: str = "audio_alchemist"

    # Postgres settings (fallback)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str | None = None

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> MultiHostUrl | PostgresDsn | str:
        # Prioritize MySQL if configured
        if self.MYSQL_USER and self.MYSQL_DB:
            return MultiHostUrl.build(
                scheme="mysql+aiomysql",
                username=self.MYSQL_USER,
                password=self.MYSQL_PASSWORD,
                host=self.MYSQL_SERVER,
                port=self.MYSQL_PORT,
                path=self.MYSQL_DB,
            )
        # Fallback to Postgres
        if self.POSTGRES_USER and self.POSTGRES_DB:
            return PostgresDsn.build(
                scheme="postgresql+psycopg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        # Default to SQLite if neither is configured
        return "sqlite+aiosqlite:///./audioalchemist_refactored.db"

    # App specific settings
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 100
    SUPPORTED_AUDIO_TYPES: List[str] = ["audio/mpeg", "audio/wav", "audio/x-m4a", "audio/flac", "audio/ogg", "video/mp4", "video/x-ms-wmv", "video/quicktime"]
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"
    LOG_FILE_MAX_SIZE: int = 10
    LOG_FILE_BACKUP_COUNT: int = 5
    LOG_FORMAT: str = "console"

    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 10

    # Model cache settings - paths are relative to the backend_refactored root
    MODEL_CACHE_DIR: str = "./models" # Set to the main models directory
    HF_HOME: str = "./models" # This is the primary setting for Hugging Face
    HUGGINGFACE_TOKEN: str | None = None

    # AI Services settings
    MODEL_LOAD_TIMEOUT_S: int = Field(default=120, description="Timeout in seconds for loading AI models.")
    WHISPERX_MODEL: str = Field(default="large-v3", description="WhisperX模型大小 - large-v3提供最佳质量")
    WHISPERX_DEVICE: str = Field(default="cuda", description="计算设备 (cpu/cuda)")
    WHISPERX_COMPUTE_TYPE: str = Field(default="float16", description="计算精度类型 - float16平衡质量和性能")
    WHISPERX_LANGUAGE: str = Field(default="zh", description="转录语言 (auto/zh/en/ja/ko等) - auto为自动检测，zh为中文，默认中文以提高识别准确度")
    WHISPERX_VAD_METHOD: str = Field(default="silero", description="VAD方法 (silero/pyannote) - silero更轻量，pyannote更精确")
    WHISPERX_VAD_ONSET: float = Field(default=0.300, description="VAD起始阈值 - 降低此值可检测更多语音")
    WHISPERX_VAD_OFFSET: float = Field(default=0.200, description="VAD结束阈值 - 降低此值可检测更多语音")
    WHISPERX_VAD_CHUNK_SIZE: int = Field(default=2, description="VAD分块大小（秒）- 设置为2s以获得更精细的自然分段")
    BATCH_SIZE: int = Field(default=1, description="批处理大小")
    
    # Celery settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    @computed_field
    @property
    def CELERY_BROKER_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @computed_field
    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return self.CELERY_BROKER_URL


settings = Settings()

# Setup logging after settings are loaded
configure_logging(settings)
