"""Evaluate dense, BM25, and hybrid retrieval against a labeled question set."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

from sqlalchemy import select

from app.core.database import create_session
from app.models.document import Document
from app.services.dense_retrieval import dense_search
from app.services.hybrid_retrieval import FusedChunk, RankedChunk, reciprocal_rank_fusion
from app.services.sparse_retrieval import BM25Retriever

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "evaluation" / "retrieval_questions.json"
DEFAULT_TOP_K = 5


class EvaluationCase(TypedDict):
    id: str
    question: str
    expected_documents: list[str]


SearchResult = RankedChunk | FusedChunk


def normalize_file_path(file_path: str) -> str:
    """Normalize stored Windows or POSIX paths to a case-insensitive basename."""
    return file_path.replace("\\", "/").rsplit("/", maxsplit=1)[-1].casefold()


def load_cases(dataset_path: Path = DATASET_PATH) -> list[EvaluationCase]:
    """Load and validate the retrieval evaluation dataset."""
    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError(f"Evaluation dataset must be a non-empty JSON list: {dataset_path}")

    cases: list[EvaluationCase] = []
    seen_ids: set[str] = set()
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Each evaluation case must be a JSON object")
        case_id = item.get("id")
        question = item.get("question")
        expected_documents = item.get("expected_documents")
        if (
            not isinstance(case_id, str)
            or not case_id.strip()
            or not isinstance(question, str)
            or not question.strip()
            or not isinstance(expected_documents, list)
            or not expected_documents
            or any(not isinstance(name, str) or not name.strip() for name in expected_documents)
        ):
            raise ValueError(f"Invalid evaluation case: {item!r}")
        if case_id in seen_ids:
            raise ValueError(f"Duplicate evaluation case ID: {case_id}")
        seen_ids.add(case_id)
        cases.append(
            {
                "id": case_id,
                "question": question,
                "expected_documents": expected_documents,
            }
        )
    return cases


def score_ranking(
    ranked_documents: Sequence[str],
    expected_documents: set[str],
    *,
    top_k: int,
) -> tuple[int | None, float]:
    """Return the first relevant rank and reciprocal rank within the cutoff."""
    for rank, file_path in enumerate(ranked_documents[:top_k], start=1):
        if normalize_file_path(file_path) in expected_documents:
            return rank, 1.0 / rank
    return None, 0.0


def result_file_path(result: SearchResult) -> str:
    document = result.chunk.document
    if document is None:
        raise ValueError(f"Retrieved chunk {result.chunk.id} has no document relationship")
    return document.file_path


def result_document_title(result: SearchResult) -> str:
    document = result.chunk.document
    if document is None:
        raise ValueError(f"Retrieved chunk {result.chunk.id} has no document relationship")
    return document.title


def evaluate(top_k: int, output_path: Path | None) -> None:
    cases = load_cases()
    db = create_session()
    try:
        stored_paths = {
            normalize_file_path(file_path)
            for file_path in db.execute(select(Document.file_path)).scalars()
        }
        expected_paths = {
            normalize_file_path(file_path)
            for case in cases
            for file_path in case["expected_documents"]
        }
        missing_paths = sorted(expected_paths - stored_paths)
        if missing_paths:
            missing = ", ".join(missing_paths)
            raise ValueError(
                "Evaluation documents are not present in the database: "
                f"{missing}. Ingest the labeled PDFs before running the benchmark."
            )

        sparse_retriever = BM25Retriever.from_session(db)
        per_case: list[dict[str, object]] = []
        metrics = {
            name: {"hits": 0, "reciprocal_rank_sum": 0.0}
            for name in ("dense", "bm25", "hybrid")
        }

        for case in cases:
            dense = dense_search(db, case["question"], top_k=top_k)
            sparse = sparse_retriever.search(case["question"], top_k=top_k)
            hybrid = reciprocal_rank_fusion(dense, sparse, top_k=top_k)
            rankings: dict[str, Sequence[SearchResult]] = {
                "dense": dense,
                "bm25": sparse,
                "hybrid": hybrid,
            }
            expected = {
                normalize_file_path(file_path)
                for file_path in case["expected_documents"]
            }
            case_results: dict[str, object] = {
                "id": case["id"],
                "question": case["question"],
                "expected_documents": case["expected_documents"],
                "rankings": {},
            }
            ranking_details: dict[str, object] = {}

            for name, ranking in rankings.items():
                paths = [result_file_path(result) for result in ranking]
                first_rank, reciprocal_rank = score_ranking(paths, expected, top_k=top_k)
                metrics[name]["hits"] += int(first_rank is not None)
                metrics[name]["reciprocal_rank_sum"] += reciprocal_rank
                ranking_details[name] = {
                    "first_relevant_rank": first_rank,
                    "results": [
                        {
                            "rank": rank,
                            "document": result_document_title(result),
                            "file_path": paths[rank - 1],
                            "page": result.chunk.page_number,
                            "relevant": normalize_file_path(paths[rank - 1]) in expected,
                        }
                        for rank, result in enumerate(ranking, start=1)
                    ],
                }
            case_results["rankings"] = ranking_details
            per_case.append(case_results)

        summary = {
            name: {
                f"hit_rate_at_{top_k}": values["hits"] / len(cases),
                f"mrr_at_{top_k}": values["reciprocal_rank_sum"] / len(cases),
                "hits": values["hits"],
                "total": len(cases),
            }
            for name, values in metrics.items()
        }
        report = {
            "generated_at": datetime.now(UTC).isoformat(),
            "dataset": str(DATASET_PATH.relative_to(ROOT)),
            "top_k": top_k,
            "metrics": summary,
            "cases": per_case,
        }
        print(f"Retrieval evaluation: {len(cases)} questions; Hit@{top_k} and MRR@{top_k}")
        for name, values in summary.items():
            print(
                f"{name:>6}: "
                f"Hit@{top_k}={values[f'hit_rate_at_{top_k}']:.3f} "
                f"({values['hits']}/{values['total']}), "
                f"MRR@{top_k}={values[f'mrr_at_{top_k}']:.3f}"
            )
        for case_result in per_case:
            rankings = case_result["rankings"]
            ranks = ", ".join(
                f"{name}={rankings[name]['first_relevant_rank'] or '-'}"
                for name in ("dense", "bm25", "hybrid")
            )
            print(f"{case_result['id']}: {ranks} | {case_result['question']}")

        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            print(f"Detailed results written to {output_path}")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
        help=f"Number of retrieved chunks to score (default: {DEFAULT_TOP_K})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the detailed JSON report",
    )
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k must be greater than zero")
    evaluate(args.top_k, args.output)


if __name__ == "__main__":
    main()
