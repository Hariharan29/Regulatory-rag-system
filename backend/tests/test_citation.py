from types import SimpleNamespace

import pytest

from app.models.chunk import Chunk
from app.models.document import Document, DocumentSource, DocumentType
from app.services.citation import build_citation_prompt, extract_marked_citations
from app.services.rag_pipeline import generate_answer


def make_chunk(chunk_id: int, *, title: str, page_number: int, text: str) -> Chunk:
    document = Document(
        id=chunk_id,
        title=title,
        source=DocumentSource.RBI,
        doc_type=DocumentType.CIRCULAR,
        file_path=f"data/raw_pdfs/{title}.pdf",
    )
    return Chunk(
        id=chunk_id,
        document_id=document.id,
        content=text,
        chunk_index=0,
        page_number=page_number,
        document=document,
    )


def test_build_citation_prompt_includes_context_and_rules():
    chunks = [
        make_chunk(1, title="KYC Circular 2024", page_number=5, text="Banks must verify customer identity."),
        make_chunk(2, title="KYC Circular 2024", page_number=7, text="NBFCs must keep a transaction log."),
    ]

    prompt = build_citation_prompt("What must banks do?", chunks)

    assert "Answer ONLY from the context below" in prompt
    assert "[1]" in prompt
    assert "KYC Circular 2024" in prompt
    assert "Banks must verify customer identity" in prompt


def test_extract_marked_citations_maps_answer_markers_to_chunk_ids():
    chunks = [
        make_chunk(11, title="RBI KYC Circular 2024", page_number=5, text="Banks must verify customer identity."),
        make_chunk(12, title="RBI KYC Circular 2024", page_number=8, text="NBFCs must keep transaction records."),
    ]

    answer = "Banks must verify customer identity [11]. NBFCs must keep records [12]."
    citations = extract_marked_citations(answer, chunks)

    assert [citation.chunk_id for citation in citations] == [11, 12]
    assert citations[0].document_title == "RBI KYC Circular 2024"
    assert citations[0].page_number == 5


def test_generate_answer_uses_mocked_client_and_guardrail():
    chunks = [
        make_chunk(21, title="RBI Circular 2024", page_number=12, text="Banks must perform KYC before onboarding customers."),
    ]

    class FakeClient:
        class chat:
            class completions:
                @staticmethod
                def create(*, model, messages):
                    return SimpleNamespace(
                        choices=[
                            SimpleNamespace(
                                message=SimpleNamespace(
                                    content="Banks must perform KYC before onboarding customers [21]."
                                )
                            )
                        ]
                    )

    answer = generate_answer(
        "What must banks do before onboarding customers?",
        chunks,
        top_score=0.87,
        client=FakeClient(),
    )

    assert answer.answer_text.startswith("Banks must perform KYC")
    assert [citation.chunk_id for citation in answer.citations] == [21]
    assert answer.low_confidence is False


def test_generate_answer_rejects_low_confidence_queries():
    answer = generate_answer(
        "What is IRDAI's stance on crypto?",
        [],
        top_score=0.1,
    )

    assert answer.low_confidence is True
    assert "confident answer" in answer.answer_text.lower()
