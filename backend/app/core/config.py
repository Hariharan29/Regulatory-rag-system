"""
core/config.py
──────────────
Application-wide settings loaded from environment variables / .env file.
Uses pydantic-settings so every variable is type-checked at startup.
"""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Database ─────────────────────────────────────────────────────────────
    # Full PostgreSQL connection string.
    # In docker-compose: postgresql://raguser:ragpass@db:5432/financerag
    # In CI:            postgresql://raguser:ragpass@localhost:5432/financerag_test
    database_url: str

    # ── Model provider ───────────────────────────────────────────────────────
    ai_provider: Literal["ollama", "openai"] = "ollama"
    openai_api_key: str | None = None
    ollama_base_url: str = "http://host.docker.internal:11434/v1"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_chat_model: str = "llama3.2:3b"

    # ── Application ──────────────────────────────────────────────────────────
    log_level: str = "INFO"

    # Resolve .env from the repository root, independent of the process cwd.
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        env_file_encoding="utf-8",
    )


# Module-level singleton — import this everywhere you need settings.
settings = Settings()
