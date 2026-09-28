"""Document listing and detail endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.chunk import Chunk
from app.models.document import Document, DocumentSource, DocumentType
from app.schemas.document import (
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentResponse,
)
from app.services.retrieval_filters import apply_document_filters

router = APIRouter()


@router.get("/documents", response_model=DocumentListResponse)
def list_documents(
    source: DocumentSource | None = None,
    doc_type: DocumentType | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    """Return a filtered, paginated list of indexed documents."""
    count_statement = apply_document_filters(
        select(func.count(Document.id)), source, doc_type
    )
    items_statement = apply_document_filters(select(Document), source, doc_type)
    items_statement = items_statement.order_by(
        Document.created_at.desc(), Document.id.desc()
    ).offset(offset).limit(limit)

    try:
        total = db.scalar(count_statement) or 0
        documents = db.scalars(items_statement).all()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="Document storage is unavailable.",
        ) from exc

    return DocumentListResponse(
        total=total,
        items=[DocumentResponse.model_validate(document) for document in documents],
    )


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: int, db: Session = Depends(get_db)) -> DocumentDetailResponse:
    """Return document metadata and chunk count, or 404 when it does not exist."""
    try:
        document = db.get(Document, document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found.")
        chunk_count = db.scalar(
            select(func.count(Chunk.id)).where(Chunk.document_id == document_id)
        ) or 0
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="Document storage is unavailable.",
        ) from exc

    document_data = DocumentResponse.model_validate(document).model_dump()
    return DocumentDetailResponse(**document_data, chunk_count=chunk_count)
