from pathlib import Path

from app.models.chunk import Chunk
from app.models.document import Document, DocumentSource, DocumentType
from app.services import ingestion
from app.services.chunker import TextChunk


class FakeQuery:
    def __init__(self, existing=None):
        self.existing = existing

    def filter_by(self, **kwargs):
        return self

    def first(self):
        return self.existing


class FakeSession:
    def __init__(self, existing=None):
        self.existing = existing
        self.added = []
        self.added_chunks = []
        self.committed = False
        self.rolled_back = False

    def query(self, model):
        return FakeQuery(self.existing)

    def add(self, value):
        self.added.append(value)

    def flush(self):
        self.added[0].id = 12

    def add_all(self, values):
        self.added_chunks.extend(values)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def test_ingest_pdf_persists_document_and_page_aware_chunks(monkeypatch, tmp_path):
    pdf_path = tmp_path / "source.pdf"
    monkeypatch.setattr(ingestion, "extract_pages", lambda path: [(3, "passage")])
    monkeypatch.setattr(
        ingestion,
        "chunk_pages",
        lambda pages: [TextChunk("passage", page_number=3, token_count=1)],
    )
    db = FakeSession()

    document = ingestion.ingest_pdf(
        db,
        pdf_path,
        title="RBI Circular",
        source=DocumentSource.RBI,
        doc_type=DocumentType.CIRCULAR,
        stored_path="data/raw_pdfs/RBI_circular.pdf",
        embedder=lambda texts: [[0.1] * 1536],
    )

    assert isinstance(document, Document)
    assert document.id == 12
    assert db.committed
    assert not db.rolled_back
    assert len(db.added_chunks) == 1
    assert isinstance(db.added_chunks[0], Chunk)
    assert db.added_chunks[0].page_number == 3
    assert db.added_chunks[0].embedding == [0.1] * 1536


def test_ingest_pdf_rolls_back_when_embedding_count_is_wrong(monkeypatch, tmp_path):
    monkeypatch.setattr(ingestion, "extract_pages", lambda path: [(1, "passage")])
    monkeypatch.setattr(
        ingestion,
        "chunk_pages",
        lambda pages: [TextChunk("passage", page_number=1, token_count=1)],
    )
    db = FakeSession()

    try:
        ingestion.ingest_pdf(
            db,
            tmp_path / "source.pdf",
            title="RBI Circular",
            source=DocumentSource.RBI,
            doc_type=DocumentType.CIRCULAR,
            embedder=lambda texts: [],
        )
    except ValueError as error:
        assert "Embedding count" in str(error)
    else:
        raise AssertionError("Expected mismatched embeddings to fail")

    assert db.rolled_back
    assert not db.committed


def test_filename_metadata_inference():
    from scripts.ingest import infer_metadata

    metadata = infer_metadata(
        Path("RBI_master_direction_2024_01.pdf")
    )

    assert metadata is not None
    assert metadata.source == "RBI"
    assert metadata.doc_type == "master_direction"
    assert metadata.title == "Rbi Master Direction 2024 01"
