"""Prompt construction and citation extraction for grounded answers."""

from __future__ import annotations

import re

from app.models.chunk import Chunk
from app.schemas.chunk import ChunkCitation


def build_citation_prompt(question: str, chunks: list[Chunk]) -> str:
    """Build a context-grounded prompt that asks the model to cite exact chunk IDs."""
    if not question.strip():
        raise ValueError("question cannot be empty")
    if not chunks:
        raise ValueError("at least one chunk is required")

    context_lines: list[str] = []
    for chunk in chunks:
        document = chunk.document
        if document is None:
            title = "Unknown document"
            page_number = chunk.page_number
        else:
            title = document.title
            page_number = chunk.page_number

        content = chunk.content.strip().replace("\n", " ")
        context_lines.append(
            f"Chunk [{chunk.id}] — {title}, page {page_number}\n"
            f"{content}"
        )

    return (
        "You are a compliance research assistant. Answer ONLY from the context below. "
        "If the context does not contain a confident answer, say that you cannot provide a confident answer "
        "based on the indexed documents.\n\n"
        "Rules:\n"
        "1. Use the exact chunk IDs shown in the source list, like [21].\n"
        "2. Each factual statement must include the relevant citation marker.\n"
        "3. Do not invent facts. If unknown, say you cannot provide a confident answer.\n\n"
        "Question: {question}\n\n"
        "Context:\n"
        "{context}\n\n"
        "Answer in plain English, with inline citations like [21]."
    ).format(
        question=question,
        context="\n\n".join(context_lines),
    )


def extract_marked_citations(answer: str, chunks: list[Chunk]) -> list[ChunkCitation]:
    """Parse markers like [21] from the answer and map them back to a chunk/document."""
    if not answer.strip():
        return []

    chunk_lookup = {chunk.id: chunk for chunk in chunks if chunk.id is not None}
    markers = re.findall(r"\[(\d+)\]", answer)
    seen: set[int] = set()
    citations: list[ChunkCitation] = []

    for marker in markers:
        chunk_id = int(marker)
        if chunk_id in seen:
            continue
        seen.add(chunk_id)
        chunk = chunk_lookup.get(chunk_id)
        if chunk is None:
            continue
        document = chunk.document
        citations.append(
            ChunkCitation(
                chunk_id=chunk_id,
                document_id=chunk.document_id,
                document_title=document.title if document is not None else "Unknown document",
                page_number=chunk.page_number,
                excerpt=chunk.content[:200],
            )
        )

    return citations
