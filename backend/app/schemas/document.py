"""
schemas/document.py
────────────────────
Pydantic schemas for the Document model.
These are used for API request/response serialization — they are separate
from the ORM model so we can control exactly what fields are exposed.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentSource, DocumentType


# ── Base (shared fields) ──────────────────────────────────────────────────────
class DocumentBase(BaseModel):
    title: str
    source: DocumentSource
    doc_type: DocumentType
    issue_date: date | None = None
    file_path: str


# ── Response schema (what the API returns) ────────────────────────────────────
class DocumentResponse(DocumentBase):
    id: int
    created_at: datetime

    # from_orm=True / from_attributes=True tells Pydantic to read data from
    # ORM model attributes instead of a plain dict.
    model_config = ConfigDict(from_attributes=True)


# ── List response (used by GET /documents) ────────────────────────────────────
class DocumentListResponse(BaseModel):
    total: int
    items: list[DocumentResponse]
