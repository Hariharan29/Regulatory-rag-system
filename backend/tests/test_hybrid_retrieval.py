import pytest

from app.models.chunk import Chunk
from app.services.hybrid_retrieval import RankedChunk, reciprocal_rank_fusion


def result(chunk_id: int, score: float = 0.0) -> RankedChunk:
    return RankedChunk(
        chunk=Chunk(id=chunk_id, content=f"chunk {chunk_id}", chunk_index=chunk_id, page_number=1),
        score=score,
    )


def test_rrf_fuses_rankings_with_hand_calculated_order():
    dense = [result(1, 0.9), result(2, 0.8)]
    sparse = [result(3, 12.0), result(1, 8.0)]

    fused = reciprocal_rank_fusion(dense, sparse, rrf_constant=60)

    assert [item.chunk.id for item in fused] == [1, 3, 2]
    assert fused[0].score == pytest.approx(1 / 61 + 1 / 62)
    assert fused[1].score == pytest.approx(1 / 61)
    assert fused[2].score == pytest.approx(1 / 62)


def test_rrf_deduplicates_and_limits_results():
    fused = reciprocal_rank_fusion(
        [result(1), result(2)], [result(1), result(3)], top_k=2
    )

    assert [item.chunk.id for item in fused] == [1, 2]
    assert len(fused) == 2


@pytest.mark.parametrize("top_k,constant", [(0, 60), (1, -1)])
def test_rrf_rejects_invalid_limits(top_k, constant):
    with pytest.raises(ValueError):
        reciprocal_rank_fusion(top_k=top_k, rrf_constant=constant)
