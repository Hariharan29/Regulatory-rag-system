"""
models/document.py
──────────────────
SQLAlchemy ORM model for a regulatory document (RBI / SEBI).
Each Document row represents one PDF file that has been ingested.
"""

import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DocumentSource(enum.StrEnum):
    """Which regulator issued this document."""
    RBI = "RBI"
    SEBI = "SEBI"


class DocumentType(enum.StrEnum):
    """Category of the regulatory document."""
    CIRCULAR = "circular"
    MASTER_DIRECTION = "master_direction"
    NOTIFICATION = "notification"
    OTHER = "other"


class Document(Base):
    __tablename__ = "documents"

    # ── Primary key ───────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # ── Document metadata ─────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(512), nullable=False)

    # RBI or SEBI — enforced at DB level via Postgres ENUM
    source: Mapped[DocumentSource] = mapped_column(
        Enum(DocumentSource, name="document_source"),
        nullable=False,
        index=True,
    )

    # circular / master_direction / notification / other
    doc_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type"),
        nullable=False,
        index=True,
    )

    # Date the regulator issued the document (parsed from filename / PDF metadata)
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relative path to the original PDF, e.g. "data/raw_pdfs/RBI_circular_2024_01.pdf"
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)

    # ── Audit timestamps ──────────────────────────────────────────────────────
    # server_default=func.now() means the DB sets this, not the app — consistent
    # even if the row is inserted directly via SQL.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    # One document → many chunks.
    # cascade="all, delete-orphan" means deleting a Document deletes its Chunks too.
    chunks: Mapped[list["Chunk"]] = relationship(  # noqa: F821
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} source={self.source} title={self.title!r}>"
