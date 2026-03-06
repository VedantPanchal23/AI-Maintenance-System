"""
Application Configuration — Environment-based settings using Pydantic.

All configuration is loaded from environment variables with sensible defaults
for local development. Production values MUST be set via .env or environment.
"""

import logging
import secrets
import warnings
from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings

_INSECURE_DEFAULTS = {
    "dev-secret-key-replace-in-production",
    "change_me_in_production",
    "test-secret-key-for-unit-testing",
    "dev-secret-key-for-local-testing-only",
    "super-secret-key-change-in-production",
}


class Settings(BaseSettings):
    """Central configuration for the entire application."""

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "predictive-maintenance"
    APP_ENV: str = "development"  # development | staging | production
    APP_DEBUG: bool = False
    APP_VERSION: str = "1.0.0"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # ── Database ─────────────────────────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "predictive_maintenance"
    POSTGRES_USER: str = "pmuser"
    POSTGRES_PASSWORD: str = ""
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ── Redis ────────────────────────────────────────────────────
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ── JWT ──────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = secrets.token_urlsafe(48)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── ML ───────────────────────────────────────────────────────
    ML_MODEL_DIR: str = "./ml_models/saved_models"
    ML_DEFAULT_MODEL: str = "xgboost"
    ML_PREDICTION_THRESHOLD: float = 0.7
    ML_RETRAIN_INTERVAL_HOURS: int = 24

    # ── Alerts ───────────────────────────────────────────────────
    ALERT_HIGH_RISK_THRESHOLD: float = 0.8
    ALERT_MEDIUM_RISK_THRESHOLD: float = 0.5
    ALERT_EMAIL_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    ALERT_FROM_EMAIL: str = ""

    # ── Simulation ───────────────────────────────────────────────
    SIMULATION_ENABLED: bool = False
    SIMULATION_INTERVAL_SECONDS: int = 5
    SIMULATION_EQUIPMENT_COUNT: int = 10

    # ── Logging ──────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json | console
    LOG_FILE: Optional[str] = "logs/app.log"

    # ── Trusted Hosts ────────────────────────────────────────────
    ALLOWED_HOSTS: List[str] = ["localhost"]

    # ── CORS ─────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    @model_validator(mode="after")
    def validate_security(self):
        """Warn or block on insecure secrets in non-development environments."""
        is_prod = self.APP_ENV in ("production", "staging")

        # JWT Secret validation
        if self.JWT_SECRET_KEY in _INSECURE_DEFAULTS:
            if is_prod:
                raise ValueError(
                    "CRITICAL: JWT_SECRET_KEY is using an insecure default. "
                    "Set a strong secret via JWT_SECRET_KEY environment variable."
                )
            else:
                warnings.warn(
                    "JWT_SECRET_KEY is using an insecure default. "
                    "Set a strong secret via environment variable.",
                    stacklevel=2,
                )

        if len(self.JWT_SECRET_KEY) < 32 and is_prod:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters in production."
            )

        # DB password validation
        if (not self.POSTGRES_PASSWORD or self.POSTGRES_PASSWORD in _INSECURE_DEFAULTS) and is_prod:
            raise ValueError(
                "CRITICAL: POSTGRES_PASSWORD is missing or insecure. "
                "Set it via POSTGRES_PASSWORD environment variable."
            )

        # Disable debug in production
        if is_prod and self.APP_DEBUG:
            warnings.warn(
                "APP_DEBUG is enabled in production. This exposes sensitive info.",
                stacklevel=2,
            )

        return self

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton for application settings."""
    return Settings()
