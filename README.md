# Finance RAG

A local-first research assistant for RBI and SEBI regulatory documents. Ask
questions in plain language, retrieve relevant passages, and review answers with
document and page citations.

## Features

- PDF ingestion with page-aware text extraction and OCR for scanned pages.
- Hybrid search using pgvector, BM25, and reciprocal-rank fusion.
- Grounded answers with mapped source citations.
- Document library, regulator/type filters, and query audit history.

## Stack

FastAPI · PostgreSQL/pgvector · React/Vite · Docker Compose · Ollama

## Run locally

Prerequisites: Docker Desktop, Node.js/npm, and [Ollama](https://ollama.com/download).

Pull the default local models:

```powershell
ollama pull nomic-embed-text
ollama pull llama3.2:3b
```

From the repository root, configure the environment and start the backend:

```powershell
Copy-Item .env.example .env
docker compose up -d db
docker compose run --rm backend alembic upgrade head
docker compose up --build -d
```

Add regulatory PDFs to `data/raw_pdfs`, then ingest them:

```powershell
docker compose run --rm backend python -m scripts.ingest
```

Start the frontend in a separate terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`). The API
is available at `http://localhost:8000`; interactive API docs are at
`http://localhost:8000/docs`.

The default configuration uses local Ollama models. To use OpenAI instead,
set `AI_PROVIDER=openai` and configure `OPENAI_API_KEY` in `.env`; API usage
may incur charges.

## Checks and evaluation

Run frontend checks from `frontend/`:

```powershell
npm run lint
npm run build
```

Run backend tests and lint from `backend/`:

```powershell
python -m pytest -q
python -m ruff check .
```

After the seed PDFs are ingested, run the retrieval benchmark from `backend/`:

```powershell
python -m scripts.evaluate_retrieval --output evaluation-results/phase8.json
```

See [Phase 8 evaluation notes](docs/PHASE_8_EVALUATION.md) for metric
definitions and answer/citation review guidance. See
[CONTRIBUTING.md](CONTRIBUTING.md) for the branch and pull-request workflow.
