from types import SimpleNamespace

from app.models.chunk import Chunk
from app.models.document import Document, DocumentSource, DocumentType
from app.services.citation import (
    build_citation_prompt,
    extract_marked_citations,
    has_unmapped_citation_markers,
)
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
        make_chunk(
            1,
            title="KYC Circular 2024",
            page_number=5,
            text="Banks must verify customer identity.",
        ),
        make_chunk(
            2,
            title="KYC Circular 2024",
            page_number=7,
            text="NBFCs must keep a transaction log.",
        ),
    ]

    prompt = build_citation_prompt("What must banks do?", chunks)

    assert "Answer ONLY from the context below" in prompt
    assert "Source [SRC-1]" in prompt
    assert "Source [SRC-2]" in prompt
    assert "Do not use database chunk IDs" in prompt
    assert "KYC Circular 2024" in prompt
    assert "Banks must verify customer identity" in prompt


def test_extract_marked_citations_maps_answer_markers_to_chunk_ids():
    chunks = [
        make_chunk(
            11,
            title="RBI KYC Circular 2024",
            page_number=5,
            text="Banks must verify customer identity.",
        ),
        make_chunk(
            12,
            title="RBI KYC Circular 2024",
            page_number=8,
            text="NBFCs must keep transaction records.",
        ),
    ]

    answer = "Banks must verify customer identity [SRC-1]. NBFCs must keep records [SRC-2]."
    citations = extract_marked_citations(answer, chunks)

    assert [citation.chunk_id for citation in citations] == [11, 12]
    assert citations[0].document_title == "RBI KYC Circular 2024"
    assert citations[0].page_number == 5
    assert citations[1].chunk_id == 12
    assert citations[1].page_number == 8


def test_extract_marked_citations_ignores_legal_section_numbers():
    chunks = [
        make_chunk(
            15,
            title="RBI Circular",
            page_number=3,
            text="Primary dealers must follow section [5].",
        ),
    ]

    citations = extract_marked_citations("See section [5] [SRC-1].", chunks)

    assert [citation.chunk_id for citation in citations] == [15]
    assert not has_unmapped_citation_markers("See section [5] [SRC-1].", chunks)


def test_unmapped_source_reference_is_detected():
    chunks = [
        make_chunk(15, title="RBI Circular", page_number=3, text="Regulatory text."),
    ]

    assert has_unmapped_citation_markers("Unsupported claim [SRC-2].", chunks)
    assert not has_unmapped_citation_markers("Supported claim [SRC-1].", chunks)


def test_generate_answer_uses_mocked_client_and_guardrail():
    chunks = [
        make_chunk(
            21,
            title="RBI Circular 2024",
            page_number=12,
            text="Banks must perform KYC before onboarding customers.",
        ),
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
                                    content=(
                                        "Banks must perform KYC before onboarding customers "
                                        "[SRC-1]."
                                    )
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


def test_generate_answer_returns_fallback_for_unmapped_model_citation():
    chunk = make_chunk(
        21,
        title="RBI Circular 2024",
        page_number=12,
        text="Banks must perform KYC before onboarding customers.",
    )

    class FakeClient:
        class chat:
            class completions:
                @staticmethod
                def create(*, model, messages):
                    return SimpleNamespace(
                        choices=[
                            SimpleNamespace(
                                message=SimpleNamespace(
                                    content="Banks must perform KYC [SRC-21]."
                                )
                            )
                        ]
                    )

    answer = generate_answer(
        "What must banks do before onboarding customers?",
        [chunk],
        top_score=0.87,
        client=FakeClient(),
    )

    assert answer.low_confidence is True
    assert answer.citations == []
    assert answer.chunks_used == [21]
    assert "could not be matched" in answer.answer_text


def test_generate_answer_returns_fallback_if_model_omits_source_references():
    chunk = make_chunk(
        21,
        title="RBI Circular 2024",
        page_number=12,
        text="Banks must perform KYC before onboarding customers.",
    )

    class FakeClient:
        class chat:
            class completions:
                @staticmethod
                def create(*, model, messages):
                    return SimpleNamespace(
                        choices=[
                            SimpleNamespace(
                                message=SimpleNamespace(content="Banks must perform KYC.")
                            )
                        ]
                    )

    answer = generate_answer(
        "What must banks do before onboarding customers?",
        [chunk],
        top_score=0.87,
        client=FakeClient(),
    )

    assert answer.low_confidence is True
    assert answer.citations == []
    assert "could not be matched" in answer.answer_text


def test_generate_answer_rejects_low_confidence_queries():
    answer = generate_answer(
        "What is IRDAI's stance on crypto?",
        [],
        top_score=0.1,
    )

    assert answer.low_confidence is True
    assert "confident answer" in answer.answer_text.lower()
