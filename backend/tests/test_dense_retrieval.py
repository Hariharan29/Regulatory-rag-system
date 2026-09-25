from types import SimpleNamespace

from app.models.chunk import Chunk
from app.services.dense_retrieval import dense_search


class FakeSession:
    def __init__(self, rows):
        self.rows = rows
        self.statement = None

    def execute(self, statement):
        self.statement = statement
        return SimpleNamespace(all=lambda: self.rows)


def test_dense_search_embeds_query_orders_by_cosine_and_converts_distance():
    chunk = Chunk(id=5, content="KYC controls", chunk_index=0, page_number=2)
    db = FakeSession([(chunk, 0.15)])

    results = dense_search(
        db,
        "KYC controls",
        top_k=3,
        embedder=lambda texts: [[0.25] * 1536],
    )

    assert results[0].chunk is chunk
    assert results[0].score == 0.85
    assert "ORDER BY" in str(db.statement).upper()
