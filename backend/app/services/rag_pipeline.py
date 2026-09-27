"""RAG orchestration: retrieval, prompt construction, model generation, and citations."""

from __future__ import annotations

from dataclasses import dataclass, field

from openai import OpenAI

from app.models.chunk import Chunk
from app.schemas.chunk import ChunkCitation
from app.services.citation import build_citation_prompt, extract_marked_citations


@dataclass(slots=True)
class AnswerResult:
    """Structured answer result for query responses and audit logging."""

    answer_text: str
    citations: list[ChunkCitation] = field(default_factory=list)
    chunks_used: list[int] = field(default_factory=list)
    low_confidence: bool = False


def generate_answer(
    question: str,
    chunks: list[Chunk],
    *,
    top_score: float | None = None,
    model: str = "gpt-4o-mini",
    low_confidence_threshold: float = 0.5,
    client: OpenAI | None = None,
) -> AnswerResult:
    """Generate an answer from retrieved chunks with citation extraction and guardrail."""
    if not question.strip():
        raise ValueError("question cannot be empty")

    if not chunks:
        return AnswerResult(
            answer_text=(
                "I cannot provide a confident answer based on the indexed documents for this query. "
                "No relevant chunks were retrieved."
            ),
            citations=[],
            chunks_used=[],
            low_confidence=True,
        )

    if top_score is not None and top_score < low_confidence_threshold:
        return AnswerResult(
            answer_text=(
                "I cannot provide a confident answer based on the indexed documents for this query. "
                "The retrieved evidence is too weak to support a grounded answer."
            ),
            citations=[],
            chunks_used=[chunk.id for chunk in chunks if chunk.id is not None],
            low_confidence=True,
        )

    if client is None:
        from app.core.config import settings

        client = OpenAI(api_key=settings.openai_api_key)

    prompt = build_citation_prompt(question, chunks)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You answer only from the supplied context."},
            {"role": "user", "content": prompt},
        ],
    )
    answer_text = response.choices[0].message.content.strip()

    citations = extract_marked_citations(answer_text, chunks)
    chunk_ids = [citation.chunk_id for citation in citations]
    return AnswerResult(
        answer_text=answer_text,
        citations=citations,
        chunks_used=chunk_ids,
        low_confidence=False,
    )
