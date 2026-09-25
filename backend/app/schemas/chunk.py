"""
schemas/chunk.py
─────────────────
Pydantic schemas for the Chunk model.
Note: we deliberately omit the `embedding` field from all response schemas —
      1536-float arrays are huge and never useful to an API consumer.
"""

from pydantic import BaseModel, ConfigDict


# ── Base ──────────────────────────────────────────────────────────────────────
class ChunkBase(BaseModel):
    content: str
    chunk_index: int
    page_number: int
    token_count: int | None = None


# ── Response schema ───────────────────────────────────────────────────────────
class ChunkResponse(ChunkBase):
    id: int
    document_id: int

    model_config = ConfigDict(from_attributes=True)


# ── Citation schema (used in query responses — minimal fields only) ────────────
class ChunkCitation(BaseModel):
    """
    Lightweight representation of a chunk used for inline citations.
    Returned as part of POST /query responses in Phase 6.
    """
    chunk_id: int
    document_id: int
    document_title: str
    page_number: int
    excerpt: str        # first ~200 chars of content for the citation tooltip

    model_config = ConfigDict(from_attributes=True)
