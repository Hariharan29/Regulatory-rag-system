"""In-memory BM25 retrieval over persisted chunk text."""

import re
from collections.abc import Iterable

from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.document import Document, DocumentSource, DocumentType
from app.services.hybrid_retrieval import RankedChunk
from app.services.retrieval_filters import matches_document_filters

_TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.casefold())


class BM25Retriever:
    """Reusable BM25 index; load once and reuse for multiple queries."""

    def __init__(self, records: Iterable[tuple[Chunk, DocumentSource, DocumentType]]) -> None:
        self._records = list(records)
        self._tokenized_corpus = [tokenize(chunk.content) for chunk, _, _ in self._records]
        self._index = (
            BM25Okapi(self._tokenized_corpus)
            if self._records
            else None
        )

    @classmethod
    def from_session(cls, db: Session) -> "BM25Retriever":
        rows = db.execute(
            select(Chunk, Document.source, Document.doc_type)
            .join(Document, Chunk.document_id == Document.id)
        ).all()
        return cls((chunk, source, doc_type) for chunk, source, doc_type in rows)

    def search(
        self,
        query: str,
        *,
        top_k: int = 10,
        source: DocumentSource | str | None = None,
        doc_type: DocumentType | str | None = None,
    ) -> list[RankedChunk]:
        if top_k < 1:
            raise ValueError("top_k must be positive")
        query_tokens = tokenize(query)
        if not query_tokens or self._index is None:
            return []

        scores = self._index.get_scores(query_tokens)
        query_terms = set(query_tokens)
        matches = [
            (self._records[index][0], float(score))
            for index, score in enumerate(scores)
            if not query_terms.isdisjoint(self._tokenized_corpus[index])
            and matches_document_filters(
                self._records[index][1], self._records[index][2], source, doc_type
            )
        ]
        matches.sort(key=lambda result: (-result[1], result[0].id or 0))
        return [RankedChunk(chunk=chunk, score=score) for chunk, score in matches[:top_k]]
