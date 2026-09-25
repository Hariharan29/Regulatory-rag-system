"""
core/config.py
──────────────
Application-wide settings loaded from environment variables / .env file.
Uses pydantic-settings so every variable is type-checked at startup.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Database ─────────────────────────────────────────────────────────────
    # Full PostgreSQL connection string.
    # In docker-compose: postgresql://raguser:ragpass@db:5432/financerag
    # In CI:            postgresql://raguser:ragpass@localhost:5432/financerag_test
    database_url: str

    # ── OpenAI ───────────────────────────────────────────────────────────────
    openai_api_key: str

    # ── Application ──────────────────────────────────────────────────────────
    log_level: str = "INFO"

    # Tells pydantic-settings to read from a .env file in the project root.
    # env_file is only used when the variable isn't already in the environment
    # (environment variables always take precedence).
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Module-level singleton — import this everywhere you need settings.
settings = Settings()
