"""Question answering endpoint backed by hybrid retrieval and grounded generation."""

from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAIError
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.audit_log import AuditLog
from app.models.document import Document
from app.schemas.query import QueryRequest, QueryResponse, RetrievedChunkResponse
from app.services.rag_pipeline import generate_answer
from app.services.retrieval import hybrid_search

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def answer_question(request: QueryRequest, db: Session = Depends(get_db)) -> QueryResponse:
    """Retrieve evidence, generate a cited answer, and persist an audit record."""
    try:
        document_count = db.scalar(select(func.count(Document.id))) or 0
        if document_count == 0:
            raise HTTPException(
                status_code=503,
                detail="No documents are indexed yet. Ingest documents before querying.",
            )

        search_result = hybrid_search(
            db,
            request.question,
            top_k=request.top_k,
            source=request.filters.source,
            doc_type=request.filters.doc_type,
        )
        retrieved_chunks = search_result.chunks
        chunks = [result.chunk for result in retrieved_chunks]
        answer_result = generate_answer(
            request.question,
            chunks,
            top_score=search_result.confidence_score,
        )

        audit = AuditLog(
            query_text=request.question,
            answer_text=answer_result.answer_text,
            chunk_ids_used=[chunk.id for chunk in chunks if chunk.id is not None],
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)
    except HTTPException:
        raise
    except OpenAIError as exc:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail="The embedding or answer generation service failed.",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database service is unavailable.") from exc

    citations = answer_result.citations
    chunks_used = [
        RetrievedChunkResponse(
            chunk_id=result.chunk.id,
            document_id=result.chunk.document_id,
            document_title=result.chunk.document.title,
            source=result.chunk.document.source,
            page_number=result.chunk.page_number,
            excerpt=result.chunk.content[:240],
            score=result.score,
        )
        for result in retrieved_chunks
        if result.chunk.id is not None
    ]
    return QueryResponse(
        answer=answer_result.answer_text,
        citations=citations,
        chunks_used=chunks_used,
        low_confidence=answer_result.low_confidence,
        audit_id=audit.id,
    )
