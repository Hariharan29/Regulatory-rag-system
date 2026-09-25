"""
models/audit_log.py
────────────────────
Audit log table: records every query the system processes.
Stored in Postgres so the demo has a browsable history of questions + answers.

Scaffolded in Phase 2 (schema-only); written to in Phase 5 (generation).
"""

from datetime import datetime

from sqlalchemy import ARRAY, DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    # ── Primary key ───────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # ── Query ─────────────────────────────────────────────────────────────────
    query_text: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Answer ────────────────────────────────────────────────────────────────
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Retrieval metadata ────────────────────────────────────────────────────
    # IDs of the Chunk rows that were used to generate the answer.
    # Stored as a Postgres integer array for easy inspection.
    chunk_ids_used: Mapped[list[int] | None] = mapped_column(
        ARRAY(Integer),
        nullable=True,
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} query={self.query_text[:40]!r}>"
