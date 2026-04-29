from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = Field(default="local", alias="MICROMARKET_ENV")
    database_url: str = Field(
        default="postgresql+psycopg://micromarket:micromarket@localhost:5432/micromarket",
        alias="DATABASE_URL",
    )
    artifact_root: str = Field(default="./data", alias="ARTIFACT_ROOT")
    cors_origins_raw: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    market_lookback_days: int = Field(default=30, alias="MARKET_LOOKBACK_DAYS")
    sentiment_provider: str = Field(default="baseline", alias="SENTIMENT_PROVIDER")
    sentiment_provider_fallback: str | None = Field(
        default="baseline",
        alias="SENTIMENT_PROVIDER_FALLBACK",
    )
    ollama_base_url: str = Field(default="http://localhost:11434/api", alias="OLLAMA_BASE_URL")
    ollama_sentiment_model: str = Field(
        default="llama3.1:8b",
        alias="OLLAMA_SENTIMENT_MODEL",
    )
    ollama_timeout_seconds: float = Field(default=30.0, alias="OLLAMA_TIMEOUT_SECONDS")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
