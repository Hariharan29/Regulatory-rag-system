import json

import pytest

from scripts.evaluate_retrieval import load_cases, normalize_file_path, score_ranking


def test_normalize_file_path_handles_windows_and_posix_paths():
    assert normalize_file_path(r"data\raw_pdfs\RBI_notice.PDF") == "rbi_notice.pdf"
    assert normalize_file_path("data/raw_pdfs/RBI_notice.PDF") == "rbi_notice.pdf"


def test_benchmark_contains_fifteen_uniquely_identified_questions():
    cases = load_cases()

    assert len(cases) == 15
    assert len({case["id"] for case in cases}) == 15


def test_score_ranking_returns_first_relevant_rank_and_reciprocal_rank():
    rank, reciprocal_rank = score_ranking(
        ["unrelated.pdf", r"data\RBI_expected.PDF", "also-unrelated.pdf"],
        {"rbi_expected.pdf"},
        top_k=3,
    )

    assert rank == 2
    assert reciprocal_rank == 0.5


def test_score_ranking_misses_relevant_document_after_cutoff():
    rank, reciprocal_rank = score_ranking(
        ["unrelated.pdf", "RBI_expected.pdf"],
        {"rbi_expected.pdf"},
        top_k=1,
    )

    assert rank is None
    assert reciprocal_rank == 0.0


def test_load_cases_rejects_duplicate_ids(tmp_path):
    dataset = tmp_path / "cases.json"
    dataset.write_text(
        json.dumps(
            [
                {
                    "id": "same",
                    "question": "Question one?",
                    "expected_documents": ["one.pdf"],
                },
                {
                    "id": "same",
                    "question": "Question two?",
                    "expected_documents": ["two.pdf"],
                },
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate evaluation case ID"):
        load_cases(dataset)
