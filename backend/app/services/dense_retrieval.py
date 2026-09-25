"""Cosine-similarity retrieval backed by PostgreSQL and pgvector."""

from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.document import Document
from app.services.embedder import embed_texts
from app.services.hybrid_retrieval import RankedChunk
from app.services.retrieval_filters import apply_document_filters

QueryEmbedder = Callable[[list[str]], list[list[float]]]


def dense_search(
    db: Session,
    query: str,
    *,
    top_k: int = 10,
    source: str | None = None,
    doc_type: str | None = None,
    embedder: QueryEmbedder = embed_texts,
) -> list[RankedChunk]:
    """Return nearest chunks, ordered by cosine similarity, with optional filters."""
    if top_k < 1:
        raise ValueError("top_k must be positive")
    if not query.strip():
        return []

    vectors = embedder([query])
    if len(vectors) != 1:
        raise ValueError("Query embedder must return exactly one vector")
    distance = Chunk.embedding.cosine_distance(vectors[0]).label("distance")
    statement = (
        select(Chunk, distance)
        .join(Document, Chunk.document_id == Document.id)
        .where(Chunk.embedding.is_not(None))
    )
    statement = apply_document_filters(statement, source, doc_type)
    rows = db.execute(statement.order_by(distance).limit(top_k)).all()
    return [RankedChunk(chunk=chunk, score=1.0 - float(distance_value))
            for chunk, distance_value in rows]
