"""
Application configuration με environment variable support.
Uses pydantic-settings για type-safe config.
"""
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Production-grade settings via env vars + .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Environment
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # API
    API_BASE_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Database (Postgres via Supabase)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/jobhunter"

    # Auth (Clerk)
    CLERK_PUBLIC_KEY: str = ""
    CLERK_SECRET_KEY: str = ""
    CLERK_WEBHOOK_SECRET: str = ""

    # Storage (Supabase)
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "cvs"

    # AI (Anthropic Claude)
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL_DEFAULT: str = "claude-haiku-4-5"
    CLAUDE_MODEL_PREMIUM: str = "claude-sonnet-4-7"

    # Payments (Stripe)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_PRO: str = ""        # price_xxx
    STRIPE_PRICE_PREMIUM: str = ""

    # Email (SendGrid)
    SENDGRID_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@jobhunter.app"

    # Background jobs (Redis via Upstash)
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"

    # Observability
    SENTRY_DSN: str = ""

    # Tier limits
    FREE_TIER_JOBS_PER_DAY: int = 10
    PRO_TIER_JOBS_PER_DAY: int = 50
    PREMIUM_TIER_JOBS_PER_DAY: int = 999

    PRO_TIER_COVER_LETTERS_PER_DAY: int = 5
    PREMIUM_TIER_COVER_LETTERS_PER_DAY: int = 999

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 100


settings = Settings()
