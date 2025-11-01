"""
Application Configuration
Manages environment variables and settings using Pydantic
"""

from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ============================================
    # Application Settings
    # ============================================
    APP_NAME: str = "Business Search Engine"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # ============================================
    # API Settings
    # ============================================
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    API_WORKERS: int = 1

    # CORS
    CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000", "http://localhost:5173"])
    CORS_CREDENTIALS: bool = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # ============================================
    # Redis Configuration
    # ============================================
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"

    # ============================================
    # Celery Configuration
    # ============================================
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 600  # 10 minutes
    CELERY_TASK_SOFT_TIME_LIMIT: int = 540  # 9 minutes
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = 1000

    # ============================================
    # Web Scraping Settings
    # ============================================
    SCRAPER_TIMEOUT: int = 1000
    SCRAPER_MAX_RETRIES: int = 3
    SCRAPER_RETRY_DELAY: int = 2
    SCRAPER_USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    SCRAPER_HEADLESS: bool = True
    SCRAPER_RATE_LIMIT_DELAY: int = 2

    # Nodriver/Chrome settings
    CHROME_BIN: str = ""
    CHROME_HEADLESS: bool = True

    # ============================================
    # LLM Configuration
    # ============================================
    LLM_PROVIDER: Literal["ollama", "openai", "groq"] = "ollama"
    LLM_MODEL: str = "llama3.2"
    LLM_BASE_URL: str = "http://localhost:11434"
    LLM_TIMEOUT: int = 120
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 2000

    # API Keys for cloud providers
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # ============================================
    # Database (Optional - for future use)
    # ============================================
    DATABASE_URL: str = "sqlite:///./business_search.db"

    # ============================================
    # Security
    # ============================================
    SECRET_KEY: str = "your-secret-key-change-in-production"
    API_KEY_HEADER: str = "X-API-Key"
    API_KEYS: list[str] = Field(default=[])

    @field_validator("API_KEYS", mode="before")
    @classmethod
    def parse_api_keys(cls, v: str | list[str]) -> list[str]:
        """Parse API keys from comma-separated string or list."""
        if isinstance(v, str) and v:
            return [key.strip() for key in v.split(",")]
        return v if isinstance(v, list) else []

    # ============================================
    # Monitoring & Logging
    # ============================================
    ENABLE_METRICS: bool = False
    SENTRY_DSN: str = ""

    # ============================================
    # Task Storage
    # ============================================
    TASK_RESULT_EXPIRES: int = 3600  # 1 hour
    MAX_TASK_RESULTS: int = 1000

    # ============================================
    # Rate Limiting
    # ============================================
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW: int = 60

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"


# Create settings instance
settings = Settings()
