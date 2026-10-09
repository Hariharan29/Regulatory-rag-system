"""Prompt construction and citation extraction for grounded answers."""

from __future__ import annotations

import re

from app.models.chunk import Chunk
from app.schemas.chunk import ChunkCitation


def build_citation_prompt(question: str, chunks: list[Chunk]) -> str:
    """Build a grounded prompt using short source references distinct from legal citations."""
    if not question.strip():
        raise ValueError("question cannot be empty")
    if not chunks:
        raise ValueError("at least one chunk is required")

    context_lines: list[str] = []
    for source_number, chunk in enumerate(chunks, start=1):
        document = chunk.document
        if document is None:
            title = "Unknown document"
            page_number = chunk.page_number
        else:
            title = document.title
            page_number = chunk.page_number

        content = chunk.content.strip().replace("\n", " ")
        context_lines.append(
            f"Source [SRC-{source_number}] — {title}, page {page_number}\n"
            f"{content}"
        )

    return (
        "You are a compliance research assistant. Answer ONLY from the context below. "
        "If the context does not contain a confident answer, say that you cannot "
        "provide a confident answer based on the indexed documents.\n\n"
        "Rules:\n"
        "1. Cite sources using their exact reference, like [SRC-1].\n"
        "2. Use only source references listed in the context. Do not use database chunk IDs.\n"
        "3. Each factual statement must include the relevant source reference.\n"
        "4. Do not invent facts. If unknown, say you cannot provide a confident answer.\n\n"
        "Question: {question}\n\n"
        "Context:\n"
        "{context}\n\n"
        "Answer in plain English, with inline source references like [SRC-1]."
    ).format(
        question=question,
        context="\n\n".join(context_lines),
    )


def extract_marked_citations(answer: str, chunks: list[Chunk]) -> list[ChunkCitation]:
    """Map source references such as [SRC-1] to their retrieved chunk and document."""
    if not answer.strip():
        return []

    markers = re.findall(r"\[SRC-(\d+)\]", answer, flags=re.IGNORECASE)
    seen: set[int] = set()
    citations: list[ChunkCitation] = []

    for marker in markers:
        source_number = int(marker)
        if source_number in seen or source_number < 1 or source_number > len(chunks):
            continue
        seen.add(source_number)
        chunk = chunks[source_number - 1]
        if chunk.id is None:
            continue
        document = chunk.document
        citations.append(
            ChunkCitation(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_title=document.title if document is not None else "Unknown document",
                page_number=chunk.page_number,
                excerpt=chunk.content[:200],
            )
        )

    return citations


def has_unmapped_citation_markers(answer: str, chunks: list[Chunk]) -> bool:
    """Return whether an explicit source reference is outside the retrieved source list."""
    return any(
        int(marker) < 1 or int(marker) > len(chunks)
        for marker in re.findall(r"\[SRC-(\d+)\]", answer, flags=re.IGNORECASE)
    )
