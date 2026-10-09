# Finance RAG — RBI/SEBI Compliance Assistant

> A Retrieval-Augmented Generation system that indexes RBI and SEBI regulatory documents and answers compliance questions in plain English, with inline citations pointing to the source document and page number.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Query                           │
└──────────────────────────────┬──────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   FastAPI Backend    │
                    │   POST /query        │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
   ┌──────────▼──────┐  ┌──────▼──────┐  ┌─────▼──────────┐
   │  Dense Retrieval │  │   BM25      │  │  Audit Log     │
   │  (pgvector cos) │  │  (in-memory)│  │  (PostgreSQL)  │
   └──────────┬──────┘  └──────┬──────┘  └────────────────┘
              │                │
              └────────┬───────┘
                       │  RRF Fusion
              ┌────────▼────────┐
              │  Top-k Chunks   │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │  GPT-4o-mini    │
              │  (cited answer) │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │  React Frontend │
              │  (citations UI) │
              └─────────────────┘
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL + pgvector |
| Embeddings | Local Ollama `nomic-embed-text` (or OpenAI `text-embedding-3-small`) |
| Generation | Local Ollama `llama3.2:3b` (or OpenAI `gpt-4o-mini`) |
| Retrieval | Hybrid: pgvector (dense) + BM25 (sparse) via RRF |
| PDF Parsing | PyMuPDF (fitz) |
| Frontend | React, Vite, TailwindCSS |
| Infra | Docker Compose (local), Terraform + EC2 (cloud) |

## Quick Start (Local)

```bash
# 1. Clone and enter the repo
git clone https://github.com/YOUR_USERNAME/finance-rag.git
cd finance-rag

# 2. Install Ollama from https://ollama.com/download and pull local models
ollama pull nomic-embed-text
ollama pull llama3.2:3b

# 3. Copy environment variables (the default uses local Ollama; no API key)
cp .env.example .env

# 4. Start PostgreSQL, apply the schema, then start the backend
docker compose up -d db
docker compose run --rm backend alembic upgrade head
docker compose up --build -d

# 5. Verify the backend is running
curl http://localhost:8000/health
# → {"status": "ok"}

# 6. Explore the API
open http://localhost:8000/docs
```

## Setup Instructions (full)

See [DECISIONS.md](DECISIONS.md) for architectural rationale.

### Ingest PDFs (Phase 3)

Place PDFs in `data/raw_pdfs/` using names such as `RBI_circular_2024_01.pdf` or
`SEBI_master_direction_2023_05.pdf`. From `backend/`, run:

```bash
python -m scripts.ingest
```

The command reads its settings from the repository `.env`, then stores each PDF
and its page-aware chunks. Pages without selectable text are rendered and OCRed
locally using Tesseract. By default, embeddings and answer generation use local
Ollama models, so the demo does not make paid API calls. The backend container
connects to Ollama on the host at `host.docker.internal:11434`.
OCR text is used for indexing and citations; the source PDFs are not modified.

Ollama's `nomic-embed-text` returns 768-dimensional vectors; the app zero-pads
those vectors to fit the existing 1536-dimensional database column. This preserves
cosine similarity and avoids requiring a destructive database migration.
To use OpenAI instead, set `AI_PROVIDER=openai` and provide a funded
`OPENAI_API_KEY`; API use may incur charges.

Run the Phase 3 checks from `backend/` before opening the feature PR:

```bash
pytest -q
ruff check .
```

After those pass, add PDFs and run `python -m scripts.ingest` with PostgreSQL and
the configured model provider available. Push the feature branch and open a PR to
run GitHub CI; merge only after its checks pass.

### Inspect retrieval (Phase 4)

With documents already ingested, run `python -m scripts.evaluate_retrieval` from
`backend/` to compare dense, BM25, and fused rankings for five sample questions.

### Use the API (Phase 6)

Start the backend with Docker Compose, then open `http://localhost:8000/docs` to
explore the API. The API provides:

- `GET /documents` — paginated document list; optional `source` and `doc_type` filters.
- `GET /documents/{document_id}` — document metadata and its chunk count.
- `POST /query` — hybrid retrieval and a grounded, cited answer. Example body:

```json
{
    "question": "What KYC checks must banks perform?",
    "filters": {"source": "RBI", "doc_type": "circular"},
    "top_k": 5
}
```

- `GET /audit` — paginated history of questions, answers, and retrieved chunk IDs.

Querying requires indexed documents, a working PostgreSQL database, and the
configured model provider to be running. With the default Ollama configuration,
no OpenAI API key is required. A query response includes its audit record ID,
citations, and retrieved source excerpts.

## Design Decisions

See [DECISIONS.md](DECISIONS.md).

## Development Workflow

Use [CONTRIBUTING.md](CONTRIBUTING.md) for the required feature-branch,
local-check, PR, CI, merge, and milestone-tag workflow. Pull requests use the
repository's GitHub PR template.

## Project Status

| Phase | Description | Status |
|---|---|---|
| 1 | Scaffolding + CI/CD | ✅ Done |
| 2 | Database Schema | ✅ Done |
| 3 | Ingestion Pipeline | ✅ Validated locally with four PDFs, including OCR |
| 4 | Hybrid Retrieval | ✅ Local retrieval evaluation run |
| 5 | Generation + Citations | ✅ Citation mapping and live local query validated |
| 6 | API Layer | ✅ Merged; API contract tests included |
| 7 | Frontend | 🚧 Document library, filters, and citation source UI implemented; awaiting user validation |
| 8 | Eval & Polish | — |
| 9 | Cloud / Terraform | — |
