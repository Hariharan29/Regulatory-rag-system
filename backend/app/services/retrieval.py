"""Coordinate dense and sparse search and expose RRF results to the API."""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.document import DocumentSource, DocumentType
from app.services.dense_retrieval import dense_search
from app.services.hybrid_retrieval import FusedChunk, reciprocal_rank_fusion
from app.services.sparse_retrieval import BM25Retriever


@dataclass(slots=True)
class HybridSearchResult:
    chunks: list[FusedChunk]
    confidence_score: float


def hybrid_search(
    db: Session,
    question: str,
    *,
    top_k: int = 5,
    source: DocumentSource | None = None,
    doc_type: DocumentType | None = None,
) -> HybridSearchResult:
    """Search dense and BM25 indexes, fuse their rankings, and retain dense confidence."""
    dense_results = dense_search(
        db,
        question,
        top_k=top_k,
        source=source.value if source is not None else None,
        doc_type=doc_type.value if doc_type is not None else None,
    )
    sparse_retriever = BM25Retriever.from_session(db)
    sparse_results = sparse_retriever.search(
        question,
        top_k=top_k,
        source=source,
        doc_type=doc_type,
    )
    fused_results = reciprocal_rank_fusion(dense_results, sparse_results, top_k=top_k)

    # RRF scores are rank-based and far below the generator's semantic threshold.
    confidence_score = max((result.score for result in dense_results), default=0.0)
    return HybridSearchResult(chunks=fused_results, confidence_score=confidence_score)
