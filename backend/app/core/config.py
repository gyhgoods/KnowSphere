from functools import lru_cache

from pydantic import EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "KnowSphere API"
    app_env: str = "development"
    app_secret_key: str = Field(min_length=32)
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    access_token_minutes: int = 30
    refresh_token_days: int = 7
    cors_origins: list[str] = ["http://localhost:5173"]
    first_superuser_username: str = "admin"
    first_superuser_email: EmailStr = "admin@example.com"
    first_superuser_password: str = "ChangeMe123!"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
