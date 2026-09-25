"""Initial schema — documents, chunks, audit_logs + pgvector extension

Revision ID: 0001
Revises: (none — this is the first migration)
Create Date: 2026-09-25

What this migration does:
  1. Enables the pgvector extension so Postgres understands the VECTOR column type.
  2. Creates two ENUM types used by the documents table.
  3. Creates the `documents` table.
  4. Creates the `chunks` table with a 1536-dim vector column.
  5. Creates the `audit_logs` table.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

# Alembic revision identifiers
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. Enable pgvector extension ─────────────────────────────────────────
    # Must run before creating any VECTOR column.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── 2. documents table and its ENUM types ────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column(
            "source",
            sa.Enum("RBI", "SEBI", name="document_source"),
            nullable=False,
        ),
        sa.Column(
            "doc_type",
            sa.Enum(
                "circular", "master_direction", "notification", "other",
                name="document_type",
            ),
            nullable=False,
        ),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("file_path", sa.String(1024), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_documents_id", "documents", ["id"])
    op.create_index("ix_documents_source", "documents", ["source"])
    op.create_index("ix_documents_doc_type", "documents", ["doc_type"])

    # ── 4. chunks table ───────────────────────────────────────────────────────
    op.create_table(
        "chunks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "document_id",
            sa.Integer(),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        # Vector(1536) → Postgres type: vector(1536)
        # Supports cosine similarity via the <=> operator (pgvector)
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
    )
    op.create_index("ix_chunks_id", "chunks", ["id"])
    op.create_index("ix_chunks_document_id", "chunks", ["document_id"])

    # HNSW index for fast approximate nearest-neighbour search.
    # cosine distance (vector_cosine_ops) matches how we embed queries.
    # m=16, ef_construction=64 are conservative defaults — tune if retrieval is slow.
    op.execute(
        "CREATE INDEX ix_chunks_embedding_hnsw "
        "ON chunks USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )

    # ── 5. audit_logs table ───────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("chunk_ids_used", sa.ARRAY(sa.Integer()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_audit_logs_id", "audit_logs", ["id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    # Drop in reverse order (FK constraints)
    op.drop_table("audit_logs")
    op.execute("DROP INDEX IF EXISTS ix_chunks_embedding_hnsw")
    op.drop_table("chunks")
    op.drop_table("documents")

    # Drop ENUM types
    sa.Enum(name="document_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="document_source").drop(op.get_bind(), checkfirst=True)

    # Drop extension last (only if no other tables use it)
    op.execute("DROP EXTENSION IF EXISTS vector")
