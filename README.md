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
| Embeddings | OpenAI `text-embedding-3-small` |
| Generation | OpenAI `gpt-4o-mini` |
| Retrieval | Hybrid: pgvector (dense) + BM25 (sparse) via RRF |
| PDF Parsing | PyMuPDF (fitz) |
| Frontend | React, Vite, TailwindCSS |
| Infra | Docker Compose (local), Terraform + EC2 (cloud) |

## Quick Start (Local)

```bash
# 1. Clone and enter the repo
git clone https://github.com/YOUR_USERNAME/finance-rag.git
cd finance-rag

# 2. Copy and fill in environment variables
cp .env.example .env
# Edit .env: set OPENAI_API_KEY

# 3. Start the database and backend
docker compose up --build

# 4. Verify the backend is running
curl http://localhost:8000/health
# → {"status": "ok"}

# 5. Explore the API
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

The command reads `DATABASE_URL` and `OPENAI_API_KEY` from the repository `.env`,
then stores each PDF and its page-aware chunks. Add real PDFs before this ingestion
smoke test; parser, chunker, embedder-mocked, and ingestion-mocked pytest cases do
not require seed PDFs or OpenAI calls.

Run the Phase 3 checks from `backend/` before opening the feature PR:

```bash
pytest -q
ruff check .
```

After those pass, add PDFs and run `python -m scripts.ingest` with PostgreSQL and
the OpenAI key configured. Push the feature branch and open a PR to run GitHub CI;
merge only after its checks pass.

### Inspect retrieval (Phase 4)

With documents already ingested, run `python -m scripts.evaluate_retrieval` from
`backend/` to compare dense, BM25, and fused rankings for five sample questions.

## Design Decisions

See [DECISIONS.md](DECISIONS.md).

## Project Status

| Phase | Description | Status |
|---|---|---|
| 1 | Scaffolding + CI/CD | ✅ Done |
| 2 | Database Schema | ✅ Done |
| 3 | Ingestion Pipeline | 🚧 Implemented locally; awaiting user validation |
| 4 | Hybrid Retrieval | 🚧 Implemented locally; awaiting user validation |
| 5 | Generation + Citations | — |
| 6 | API Layer | — |
| 7 | Frontend | — |
| 8 | Eval & Polish | — |
| 9 | Cloud / Terraform | — |
