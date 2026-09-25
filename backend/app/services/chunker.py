"""Token-aware recursive splitting that retains source page numbers."""

from collections.abc import Iterable
from dataclasses import dataclass

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter, TokenTextSplitter


@dataclass(frozen=True, slots=True)
class TextChunk:
    content: str
    page_number: int
    token_count: int


def chunk_pages(
    pages: Iterable[tuple[int, str]],
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[TextChunk]:
    """Split pages independently so every chunk has an unambiguous citation page."""
    if chunk_size < 1 or chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("Require chunk_size > chunk_overlap >= 0")

    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    token_splitter = TokenTextSplitter(
        encoding_name="cl100k_base",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    encoding = tiktoken.get_encoding("cl100k_base")
    chunks = []
    for page_number, text in pages:
        for content in splitter.split_text(text.strip()):
            if content:
                candidates = [content]
                if len(encoding.encode(content)) > chunk_size:
                    candidates = token_splitter.split_text(content)
                for candidate in candidates:
                    token_count = len(encoding.encode(candidate))
                    chunks.append(
                        TextChunk(
                            content=candidate,
                            page_number=page_number,
                            token_count=token_count,
                        )
                    )
    return chunks
