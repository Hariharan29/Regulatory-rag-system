"""
tests/test_models.py
─────────────────────
Phase 2 unit tests — verify ORM models and Pydantic schemas are wired correctly.
These tests do NOT need a live database; they only check Python-level structure.

Database integration tests (actually inserting rows) are covered in test_api_query.py
(Phase 6) where a real test database is available.
"""

from datetime import UTC, date

import pytest

from app.models.audit_log import AuditLog
from app.models.chunk import Chunk
from app.models.document import Document, DocumentSource, DocumentType
from app.schemas.chunk import ChunkCitation
from app.schemas.document import DocumentResponse

# ── Model instantiation tests ─────────────────────────────────────────────────

class TestDocumentModel:
    def test_document_source_enum_values(self) -> None:
        """DocumentSource must contain only RBI and SEBI."""
        assert set(DocumentSource) == {DocumentSource.RBI, DocumentSource.SEBI}

    def test_document_type_enum_values(self) -> None:
        """DocumentType must contain the four expected categories."""
        assert DocumentType.CIRCULAR.value == "circular"
        assert DocumentType.MASTER_DIRECTION.value == "master_direction"
        assert DocumentType.NOTIFICATION.value == "notification"
        assert DocumentType.OTHER.value == "other"

    def test_document_repr(self) -> None:
        """__repr__ should include id, source, and title."""
        doc = Document(
            id=1,
            title="KYC Master Direction 2024",
            source=DocumentSource.RBI,
            doc_type=DocumentType.MASTER_DIRECTION,
            file_path="data/raw_pdfs/RBI_master_direction_2024_01.pdf",
        )
        r = repr(doc)
        assert "Document" in r
        assert "RBI" in r
        assert "KYC Master Direction 2024" in r


class TestChunkModel:
    def test_chunk_repr(self) -> None:
        chunk = Chunk(id=5, document_id=1, page_number=3, chunk_index=2)
        r = repr(chunk)
        assert "Chunk" in r
        assert "doc_id=1" in r

    def test_chunk_embedding_nullable(self) -> None:
        """Embedding should default to None (set during ingestion)."""
        chunk = Chunk(
            document_id=1,
            content="Reserve Bank of India circular on KYC norms.",
            chunk_index=0,
            page_number=1,
        )
        assert chunk.embedding is None


class TestAuditLogModel:
    def test_audit_log_repr(self) -> None:
        log = AuditLog(id=1, query_text="What are KYC norms for NBFCs?")
        r = repr(log)
        assert "AuditLog" in r
        assert "KYC" in r


# ── Pydantic schema tests ─────────────────────────────────────────────────────

class TestDocumentSchema:
    def test_document_response_from_dict(self) -> None:
        """DocumentResponse should validate from a plain dict."""
        from datetime import datetime
        data = {
            "id": 1,
            "title": "KYC Master Direction",
            "source": "RBI",
            "doc_type": "master_direction",
            "issue_date": date(2024, 1, 15),
            "file_path": "data/raw_pdfs/RBI_master_direction_2024_01.pdf",
            "created_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
        }
        doc = DocumentResponse(**data)
        assert doc.id == 1
        assert doc.source == DocumentSource.RBI
        assert doc.doc_type == DocumentType.MASTER_DIRECTION

    def test_document_source_rejects_invalid(self) -> None:
        """Source must be RBI or SEBI — invalid values should raise ValidationError."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            DocumentResponse(
                id=1,
                title="Test",
                source="IRDAI",           # not a valid source
                doc_type="circular",
                file_path="test.pdf",
                created_at="2024-01-01T00:00:00Z",
            )


class TestChunkSchema:
    def test_chunk_citation_fields(self) -> None:
        """ChunkCitation should expose the minimal fields needed for UI rendering."""
        citation = ChunkCitation(
            chunk_id=42,
            document_id=1,
            document_title="RBI KYC Circular 2024",
            page_number=7,
            excerpt="Banks must verify the identity of...",
        )
        assert citation.chunk_id == 42
        assert citation.page_number == 7
        # embedding must NOT be a field on ChunkCitation
        assert not hasattr(citation, "embedding")
