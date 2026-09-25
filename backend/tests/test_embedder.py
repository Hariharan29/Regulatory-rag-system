from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.services.embedder import EMBEDDING_DIMENSIONS, embed_texts


def test_embed_texts_batches_inputs_and_preserves_order():
    embeddings = Mock()

    def create(*, model, input):
        return SimpleNamespace(
            data=[
                SimpleNamespace(index=index, embedding=[float(index)] * EMBEDDING_DIMENSIONS)
                for index, _ in reversed(list(enumerate(input)))
            ]
        )

    embeddings.create.side_effect = create
    client = SimpleNamespace(embeddings=embeddings)

    vectors = embed_texts(["first", "second", "third"], batch_size=2, client=client)

    assert len(vectors) == 3
    assert vectors[0][0] == 0.0
    assert vectors[1][0] == 1.0
    assert vectors[2][0] == 0.0
    assert embeddings.create.call_count == 2


def test_embed_texts_rejects_wrong_dimensions():
    client = SimpleNamespace(
        embeddings=SimpleNamespace(
            create=lambda **kwargs: SimpleNamespace(
                data=[SimpleNamespace(index=0, embedding=[0.0])]
            )
        )
    )

    with pytest.raises(ValueError, match="1536-dimension"):
        embed_texts(["text"], client=client)
