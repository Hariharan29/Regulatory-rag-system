import math

from app.models.chunk import Chunk
from app.models.document import DocumentSource, DocumentType
from app.services.sparse_retrieval import BM25Retriever


def make_chunk(chunk_id: int, text: str) -> Chunk:
    return Chunk(id=chunk_id, content=text, chunk_index=chunk_id, page_number=1)


def test_bm25_search_ranks_relevant_text_and_filters_source():
    retriever = BM25Retriever(
        [
            (
                make_chunk(1, "NBFC customer KYC identity verification requirements"),
                DocumentSource.RBI,
                DocumentType.CIRCULAR,
            ),
            (
                make_chunk(2, "Investment adviser disclosure and registration duties"),
                DocumentSource.SEBI,
                DocumentType.CIRCULAR,
            ),
        ]
    )

    all_results = retriever.search("NBFC KYC identity")
    sebi_results = retriever.search("NBFC KYC identity", source="SEBI")

    assert all_results[0].chunk.id == 1
    assert math.isfinite(all_results[0].score)
    assert sebi_results == []


def test_bm25_filters_by_document_type():
    retriever = BM25Retriever(
        [
            (
                make_chunk(1, "KYC requirements for banks"),
                DocumentSource.RBI,
                DocumentType.CIRCULAR,
            ),
            (
                make_chunk(2, "KYC requirements for banks"),
                DocumentSource.RBI,
                DocumentType.NOTIFICATION,
            ),
        ]
    )

    results = retriever.search("KYC requirements", doc_type="notification")

    assert [item.chunk.id for item in results] == [2]
