"""
core/config.py
──────────────
Application-wide settings loaded from environment variables / .env file.
Uses pydantic-settings so every variable is type-checked at startup.
"""

from pathlib import Path

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

    # Resolve .env from the repository root, independent of the process cwd.
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        env_file_encoding="utf-8",
    )


# Module-level singleton — import this everywhere you need settings.
settings = Settings()
