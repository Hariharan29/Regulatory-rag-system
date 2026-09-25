"""OpenAI embedding client for chunk batches."""

from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


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

    if client is None:
        from app.core.config import settings

        client = OpenAI(api_key=settings.openai_api_key)

    vectors = []
    for start in range(0, len(texts), batch_size):
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts[start : start + batch_size],
        )
        batch = sorted(response.data, key=lambda item: item.index)
        for item in batch:
            if len(item.embedding) != EMBEDDING_DIMENSIONS:
                raise ValueError(
                    f"Expected {EMBEDDING_DIMENSIONS}-dimension embedding, "
                    f"received {len(item.embedding)}"
                )
            vectors.append(item.embedding)
    return vectors
