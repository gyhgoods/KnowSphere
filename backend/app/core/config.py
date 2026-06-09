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
    rabbitmq_url: str = "amqp://knowsphere:knowsphere@localhost:5672//"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "knowsphere"
    minio_secret_key: str = "knowsphere-secret"
    minio_secure: bool = False
    minio_bucket: str = "knowsphere-documents"
    max_upload_size_mb: int = 100
    document_parse_timeout_seconds: int = 300
    access_token_minutes: int = 30
    refresh_token_days: int = 7
    cors_origins: list[str] = ["http://localhost:5173"]
    cors_origin_regex: str | None = (
        r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|"
        r"10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)"
        r"(:\d+)?$"
    )
    first_superuser_username: str = "admin"
    first_superuser_email: EmailStr = "admin@example.com"
    first_superuser_password: str = "ChangeMe123!"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
