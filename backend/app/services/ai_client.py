"""Create an OpenAI-compatible client for the configured local or hosted model provider."""

from openai import OpenAI


def create_ai_client() -> OpenAI:
    """Build a client without requiring hosted API credentials for local Ollama."""
    from app.core.config import settings

    if settings.ai_provider == "ollama":
        return OpenAI(base_url=settings.ollama_base_url, api_key="ollama")
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required when AI_PROVIDER is 'openai'")
    return OpenAI(api_key=settings.openai_api_key)
