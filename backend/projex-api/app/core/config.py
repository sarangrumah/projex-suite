"""Application configuration via environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """ProjeX API configuration. All values sourced from environment / Vault."""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False}

    # App
    app_name: str = "ProjeX Suite API"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = Field(default="development", pattern=r"^(development|staging|production)$")
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Database
    database_url: str = "postgresql+asyncpg://projex:projex_secret@localhost:5432/projex"
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_private_key: str = "change-me-in-production"
    jwt_public_key: str = "change-me-in-production"
    jwt_algorithm: str = "RS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # Encryption (PII)
    encryption_key: str = "change-me-32-byte-key-for-aes256"

    # Meilisearch
    meilisearch_url: str = "http://localhost:7700"
    meilisearch_api_key: str = ""

    # MinIO / S3
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "projex-files"
    minio_secure: bool = False

    # Rate limiting
    rate_limit_per_minute: int = 1000

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Microservice URLs
    era_ai_url: str = "http://era-ai-api:8100"
    erabudget_url: str = "http://erabudget-api:8200"
    appcatalog_url: str = "http://appcatalog-api:8300"
    collab_url: str = "http://collab-server:8400"
    wahub_url: str = "http://wahub-gateway:8500"


settings = Settings()
