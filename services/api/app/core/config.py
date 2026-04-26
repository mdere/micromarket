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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
