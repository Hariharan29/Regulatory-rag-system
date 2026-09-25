"""
models/chunk.py
───────────────
SQLAlchemy ORM model for a text chunk extracted from a Document.
Each Chunk stores:
  - The raw text excerpt
  - Its position in the source document (page number, chunk index)
  - A 1536-dimensional embedding vector (OpenAI text-embedding-3-small output)
  - A token count (used for context-window budgeting during generation)
"""

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Chunk(Base):
    __tablename__ = "chunks"

    # ── Primary key ───────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # ── Foreign key ───────────────────────────────────────────────────────────
    # Links back to the Document this chunk was extracted from.
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Content ───────────────────────────────────────────────────────────────
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Position of this chunk within its document (0-based counter)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Page in the source PDF where this chunk's text starts
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # ── Embedding ─────────────────────────────────────────────────────────────
    # 1536 dimensions = output size of text-embedding-3-small.
    # The pgvector extension stores this as a native Postgres vector column,
    # which supports cosine similarity search via the <=> operator.
    # nullable=True during ingestion (we embed after inserting the row stub).
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1536),
        nullable=True,
    )

    # Approximate token count of `content` — used to budget the LLM context window
    # when assembling the prompt in the generation step.
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Relationship ──────────────────────────────────────────────────────────
    document: Mapped["Document"] = relationship(  # noqa: F821
        "Document",
        back_populates="chunks",
    )

    def __repr__(self) -> str:
        return (
            f"<Chunk id={self.id} doc_id={self.document_id} "
            f"page={self.page_number} idx={self.chunk_index}>"
        )
