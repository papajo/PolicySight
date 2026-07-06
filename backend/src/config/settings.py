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
    openai_api_key: str = "***"
    openai_model: str = "gpt-4"
    openai_base_url: str = ""  # Empty = default OpenAI; set for Groq/OpenRouter etc.

    # Auth — local JWT (fallback when Clerk is not configured)
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Clerk (production auth) — leave blank to use local JWT only
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""

    # Redis (optional, for Celery scheduler)
    redis_url: str = "redis://localhost:6379/0"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Stripe (placeholder)
    stripe_secret_key: str = "sk_test_placeholder"
    stripe_webhook_secret: str = "whsec_placeholder"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()