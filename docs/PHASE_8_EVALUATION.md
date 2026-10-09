# Phase 8: Evaluation and polish

## Retrieval benchmark

The benchmark contains 15 questions labeled with their expected PDF filenames.
It compares dense vector retrieval, BM25, and reciprocal-rank fusion against
those document labels. It reports:

- **Hit@5**: fraction of questions for which an expected document appears in
  the first five retrieved chunks.
- **MRR@5**: mean reciprocal rank of the first retrieved chunk from an expected
  document, with zero for a miss.

The labels and questions are a small, corpus-specific regression set, not a
complete measure of regulatory answer quality. Review and expand the set when
the document corpus changes. Each query currently has one expected PDF; add
multiple filenames in `backend/evaluation/retrieval_questions.json` when more
than one document is relevant.

Run after starting PostgreSQL, applying migrations, and ingesting all four
labeled PDFs. The embedding provider used for dense retrieval must also be
available:

```powershell
cd backend
python -m scripts.evaluate_retrieval --output evaluation-results/phase8.json
```

The command prints aggregate and per-question ranks. The optional JSON file
contains the detailed rankings; results are not committed automatically.
Missing expected documents fail with an explicit message so incomplete corpus
results are not mistaken for benchmark misses.

## Manual answer and citation review

Retrieval scores do not evaluate generated answers. For a representative set
of questions, submit each through the UI or `POST /query`, then record:

| Criterion | Pass condition |
|---|---|
| Grounding | Material claims are supported by the retrieved excerpts. |
| Citation mapping | Each `[SRC-n]` resolves to the matching returned source, document, and page. |
| Completeness | The response addresses the question without adding unsupported detail. |
| Abstention | When retrieved excerpts do not support a confident response, the answer clearly says so. |
| Filters | Regulator and document-type filters are respected by retrieved sources. |

Use this small scorecard for each manually reviewed query:

| Question ID | Grounded | Citation mapping | Complete | Abstains when needed | Filters respected | Notes |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

Record the tested question, result, and any failure before calling the answer
path validated. Do not infer answer correctness from Hit@5 or MRR@5 alone.

## Current limitations

- The benchmark is intentionally small and tied to the four PDFs in the local
  seed corpus. It does not establish general performance across RBI/SEBI rules.
- The two SEBI seed PDFs are scanned; OCR quality can affect their chunk text and
  retrieval results.
- The automated benchmark evaluates document retrieval, not answer factuality,
  citation correctness, or legal currency. Those require manual review against
  the official source documents.
- Retrieval results can change with the indexed corpus, embeddings, model
  provider, and ranking configuration. Compare runs only when those conditions
  are recorded and held reasonably constant.
