"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Athena API"
    debug: bool = False

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Database
    database_url: str = "postgresql+asyncpg://athena:athena@localhost:5432/athena"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Authentication
    nextauth_secret: str = ""

    # External APIs
    openrouter_api_key: str = ""

    # LLM Reasoning
    llm_reasoning_model: str = "openai/gpt-4o-mini"
    llm_reasoning_cache_ttl: int = 86400  # 24 hours

    # Search Enhancement Features
    enable_query_enhancement: bool = True
    enable_reranking: bool = True
    reranking_candidates: int = 10

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
