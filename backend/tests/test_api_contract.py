"""PostgreSQL-backed API contract tests with external model calls mocked."""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import get_db
from app.main import app
from app.models.audit_log import AuditLog
from app.models.chunk import Chunk
from app.models.document import Document, DocumentSource, DocumentType
from app.schemas.chunk import ChunkCitation
from app.services.hybrid_retrieval import FusedChunk
from app.services.rag_pipeline import AnswerResult
from app.services.retrieval import HybridSearchResult


@pytest.fixture
def api_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[tuple[TestClient, Session], None, None]:
    """Run API requests inside a rollback-only transaction on a dedicated test DB."""
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to a migrated, dedicated PostgreSQL test database.")

    database_name = make_url(database_url).database
    if not database_name or not database_name.endswith("_test"):
        pytest.fail("TEST_DATABASE_URL must point to a dedicated database ending in '_test'.")

    engine = create_engine(database_url)
    connection = engine.connect()
    transaction = connection.begin()
    test_session_factory = sessionmaker(
        bind=connection,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )
    db = test_session_factory()

    def override_get_db() -> Generator[Session, None, None]:
        yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, override_get_db)
    try:
        with TestClient(app) as client:
            yield client, db
    finally:
        db.close()
        transaction.rollback()
        connection.close()
        engine.dispose()


def add_document(
    db: Session,
    *,
    title: str,
    source: DocumentSource = DocumentSource.RBI,
    doc_type: DocumentType = DocumentType.CIRCULAR,
) -> Document:
    document = Document(
        title=title,
        source=source,
        doc_type=doc_type,
        file_path=f"data/raw_pdfs/{title.replace(' ', '_')}.pdf",
    )
    db.add(document)
    db.flush()
    return document


def test_list_documents_filters_and_paginates(api_client):
    client, db = api_client
    add_document(db, title="RBI KYC Circular")
    add_document(
        db,
        title="SEBI Market Circular",
        source=DocumentSource.SEBI,
    )
    add_document(
        db,
        title="RBI Primary Dealer Direction",
        doc_type=DocumentType.MASTER_DIRECTION,
    )
    db.flush()

    response = client.get(
        "/documents",
        params={"source": "RBI", "offset": 1, "limit": 1},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert len(payload["items"]) == 1
    assert payload["items"][0]["source"] == "RBI"


def test_get_document_returns_chunk_count_and_404_for_missing_id(api_client):
    client, db = api_client
    document = add_document(db, title="RBI KYC Circular")
    db.flush()
    db.add_all(
        [
            Chunk(
                document_id=document.id,
                content=f"Source passage {index}",
                chunk_index=index,
                page_number=index + 1,
            )
            for index in range(2)
        ]
    )
    db.flush()

    response = client.get(f"/documents/{document.id}")
    missing_response = client.get("/documents/999999")

    assert response.status_code == 200
    assert response.json()["chunk_count"] == 2
    assert response.json()["title"] == "RBI KYC Circular"
    assert missing_response.status_code == 404


def test_query_returns_citation_and_persists_audit_record(api_client, monkeypatch):
    client, db = api_client
    document = add_document(db, title="RBI KYC Circular")
    db.flush()
    chunk = Chunk(
        document_id=document.id,
        content="Banks must verify customer identity.",
        chunk_index=0,
        page_number=4,
    )
    db.add(chunk)
    db.flush()

    def fake_hybrid_search(*args, **kwargs):
        return HybridSearchResult(
            chunks=[FusedChunk(chunk=chunk, score=0.75)],
            confidence_score=0.9,
        )

    def fake_generate_answer(*args, **kwargs):
        citation = ChunkCitation(
            chunk_id=chunk.id,
            document_id=document.id,
            document_title=document.title,
            page_number=chunk.page_number,
            excerpt=chunk.content,
        )
        return AnswerResult(
            answer_text="Banks must verify customer identity [SRC-1].",
            citations=[citation],
            chunks_used=[chunk.id],
        )

    monkeypatch.setattr("app.api.query.hybrid_search", fake_hybrid_search)
    monkeypatch.setattr("app.api.query.generate_answer", fake_generate_answer)

    response = client.post(
        "/query",
        json={"question": "What must banks verify?", "top_k": 3},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "Banks must verify customer identity [SRC-1]."
    assert payload["low_confidence"] is False
    assert payload["citations"] == [
        {
            "chunk_id": chunk.id,
            "document_id": document.id,
            "document_title": "RBI KYC Circular",
            "page_number": 4,
            "excerpt": "Banks must verify customer identity.",
        }
    ]
    assert payload["chunks_used"][0]["chunk_id"] == chunk.id

    audit = db.get(AuditLog, payload["audit_id"])
    assert audit is not None
    assert audit.query_text == "What must banks verify?"
    assert audit.answer_text == payload["answer"]
    assert audit.chunk_ids_used == [chunk.id]


def test_query_returns_service_unavailable_when_index_is_empty(api_client):
    client, _ = api_client

    response = client.post(
        "/query",
        json={"question": "What are the KYC requirements?"},
    )

    assert response.status_code == 503
    assert "No documents are indexed" in response.json()["detail"]


def test_query_rejects_invalid_request_parameters(api_client):
    client, _ = api_client

    response = client.post(
        "/query",
        json={"question": "   ", "top_k": 0},
    )

    assert response.status_code == 422


def test_audit_endpoint_returns_paginated_query_history(api_client):
    client, db = api_client
    db.add_all(
        [
            AuditLog(query_text=f"Question {index}", answer_text=f"Answer {index}")
            for index in range(3)
        ]
    )
    db.flush()

    response = client.get("/audit", params={"offset": 1, "limit": 1})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert len(payload["items"]) == 1
    assert payload["items"][0]["query_text"].startswith("Question ")
