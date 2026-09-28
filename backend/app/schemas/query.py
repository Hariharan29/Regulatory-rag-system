"""Request and response schemas for question answering."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.document import DocumentSource, DocumentType
from app.schemas.chunk import ChunkCitation


class QueryFilters(BaseModel):
    source: DocumentSource | None = None
    doc_type: DocumentType | None = None


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    filters: QueryFilters = Field(default_factory=QueryFilters)
    top_k: int = Field(default=5, ge=1, le=20)

    @field_validator("question")
    @classmethod
    def strip_question(cls, question: str) -> str:
        question = question.strip()
        if not question:
            raise ValueError("question cannot be empty")
        return question


class RetrievedChunkResponse(BaseModel):
    chunk_id: int
    document_id: int
    document_title: str
    source: DocumentSource
    page_number: int
    excerpt: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    citations: list[ChunkCitation]
    chunks_used: list[RetrievedChunkResponse]
    low_confidence: bool
    audit_id: int

    model_config = ConfigDict(from_attributes=True)
