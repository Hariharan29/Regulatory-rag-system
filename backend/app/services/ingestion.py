"""Synchronous, transactional ingestion of one PDF at a time."""

from collections.abc import Callable
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.document import Document, DocumentSource, DocumentType
from app.services.chunker import chunk_pages
from app.services.embedder import embed_texts
from app.services.pdf_parser import extract_pages

Embedder = Callable[[list[str]], list[list[float]]]


def ingest_pdf(
    db: Session,
    pdf_path: str | Path,
    *,
    title: str,
    source: DocumentSource,
    doc_type: DocumentType,
    issue_date: date | None = None,
    stored_path: str | None = None,
    embedder: Embedder = embed_texts,
) -> Document | None:
    """Persist one PDF and its embedded chunks; return None for an existing path."""
    stored_path = stored_path or Path(pdf_path).as_posix()
    try:
        if db.query(Document).filter_by(file_path=stored_path).first() is not None:
            return None

        chunks = chunk_pages(extract_pages(pdf_path))
        if not chunks:
            raise ValueError(f"PDF contains no extractable text: {pdf_path}")

        embeddings = embedder([chunk.content for chunk in chunks])
        if len(embeddings) != len(chunks):
            raise ValueError("Embedding count does not match chunk count")

        document = Document(
            title=title,
            source=source,
            doc_type=doc_type,
            issue_date=issue_date,
            file_path=stored_path,
        )
        db.add(document)
        db.flush()
        db.add_all(
            [
                Chunk(
                    document_id=document.id,
                    content=chunk.content,
                    chunk_index=index,
                    page_number=chunk.page_number,
                    embedding=embedding,
                    token_count=chunk.token_count,
                )
                for index, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True))
            ]
        )
        db.commit()
        return document
    except Exception:
        db.rollback()
        raise
