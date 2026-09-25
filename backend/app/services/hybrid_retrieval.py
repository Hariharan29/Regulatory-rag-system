"""Reciprocal Rank Fusion for dense and sparse retrieval rankings."""

from collections.abc import Sequence
from dataclasses import dataclass

from app.models.chunk import Chunk


@dataclass(frozen=True, slots=True)
class RankedChunk:
    chunk: Chunk
    score: float


@dataclass(frozen=True, slots=True)
class FusedChunk:
    chunk: Chunk
    score: float


def reciprocal_rank_fusion(
    *rankings: Sequence[RankedChunk],
    top_k: int = 10,
    rrf_constant: int = 60,
) -> list[FusedChunk]:
    """Fuse ranked lists using 1 / (rrf_constant + one-based rank)."""
    if top_k < 1:
        raise ValueError("top_k must be positive")
    if rrf_constant < 0:
        raise ValueError("rrf_constant cannot be negative")

    scores: dict[int, float] = {}
    chunks: dict[int, Chunk] = {}
    for ranking in rankings:
        for rank, result in enumerate(ranking, start=1):
            chunk_id = result.chunk.id
            if chunk_id is None:
                raise ValueError("RRF requires persisted chunks with IDs")
            chunks[chunk_id] = result.chunk
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1 / (rrf_constant + rank)

    ordered_ids = sorted(scores, key=lambda chunk_id: (-scores[chunk_id], chunk_id))
    return [FusedChunk(chunks[chunk_id], scores[chunk_id]) for chunk_id in ordered_ids[:top_k]]
