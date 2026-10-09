"""Generate embeddings with the configured local or hosted model provider."""

from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
OLLAMA_EMBEDDING_DIMENSIONS = 768


def embed_texts(
    texts: list[str],
    batch_size: int = 100,
    client: OpenAI | None = None,
) -> list[list[float]]:
    """Embed texts in bounded batches and return vectors in input order."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    if not texts:
        return []
    if any(not text.strip() for text in texts):
        raise ValueError("Embedding input cannot contain empty text")

    model = EMBEDDING_MODEL
    if client is None:
        from app.core.config import settings
        from app.services.ai_client import create_ai_client

        client = create_ai_client()
        if settings.ai_provider == "ollama":
            model = settings.ollama_embedding_model

    vectors = []
    for start in range(0, len(texts), batch_size):
        response = client.embeddings.create(
            model=model,
            input=texts[start : start + batch_size],
        )
        batch = sorted(response.data, key=lambda item: item.index)
        for item in batch:
            if len(item.embedding) == OLLAMA_EMBEDDING_DIMENSIONS:
                vectors.append(item.embedding + [0.0] * OLLAMA_EMBEDDING_DIMENSIONS)
            elif len(item.embedding) == EMBEDDING_DIMENSIONS:
                vectors.append(item.embedding)
            else:
                raise ValueError(
                    f"Expected {OLLAMA_EMBEDDING_DIMENSIONS}- or "
                    f"{EMBEDDING_DIMENSIONS}-dimension embedding, "
                    f"received {len(item.embedding)}"
                )
    return vectors
