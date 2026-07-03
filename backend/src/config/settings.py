from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "PolicySight"
    app_env: str = "development"
    app_secret: str = "change-me-in-production"
    debug: bool = True

    # Database
    database_url: str = "postgresql://policysight:policysight@localhost:5432/policysight"
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "policysight"
    db_password: str = "policysight"
    db_name: str = "policysight"

    # AI / LLM
    openai_api_key: str = "sk-placeholder"
    openai_model: str = "gpt-4"

    # Auth
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Redis (optional, for Celery scheduler)
    redis_url: str = "redis://localhost:6379/0"

    # Stripe (placeholder)
    stripe_secret_key: str = "sk_test_placeholder"
    stripe_webhook_secret: str = "whsec_placeholder"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()