"""
models/__init__.py
──────────────────
Re-export all ORM models from a single import point.

IMPORTANT: This file must import every model so that SQLAlchemy's
declarative registry (Base.metadata) knows about all tables.
Alembic's env.py imports Base from here — if a model isn't imported
here, its table will be invisible to `alembic revision --autogenerate`.
"""

from app.models.audit_log import AuditLog
from app.models.chunk import Chunk
from app.models.document import Document, DocumentSource, DocumentType

__all__ = [
    "Document",
    "DocumentSource",
    "DocumentType",
    "Chunk",
    "AuditLog",
]
