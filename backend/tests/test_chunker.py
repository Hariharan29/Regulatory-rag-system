import tiktoken

from app.services.chunker import chunk_pages


def test_chunks_respect_token_limit_overlap_and_page_number():
    text = " ".join(
        "alpha bravo charlie delta echo foxtrot golf hotel india juliet".split() * 18
    )
    chunks = chunk_pages([(4, text)], chunk_size=30, chunk_overlap=6)

    assert len(chunks) > 1
    assert all(chunk.page_number == 4 for chunk in chunks)
    assert all(chunk.token_count <= 30 for chunk in chunks)

    first_words = chunks[0].content.split()
    second_words = chunks[1].content.split()
    overlap = 0
    for size in range(1, min(len(first_words), len(second_words)) + 1):
        if first_words[-size:] == second_words[:size]:
            overlap = size
    assert overlap > 0


def test_chunker_skips_empty_pages_and_counts_tokens():
    chunks = chunk_pages([(1, "  "), (2, "A short regulatory passage.")])
    encoding = tiktoken.get_encoding("cl100k_base")

    assert len(chunks) == 1
    assert chunks[0].page_number == 2
    assert chunks[0].token_count == len(encoding.encode(chunks[0].content))
