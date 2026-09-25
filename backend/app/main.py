"""
app/main.py
───────────
FastAPI application entry point.
Mounts all API routers and exposes a /health endpoint.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)

# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Finance RAG — RBI/SEBI Compliance Assistant",
    description=(
        "Retrieval-Augmented Generation over RBI and SEBI regulatory documents. "
        "Ask compliance questions in plain English and receive cited, grounded answers."
    ),
    version="0.1.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Allow the local Vite dev server (port 5173) and any origin for demo purposes.
# Tighten this to specific origins before any public deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health endpoint ───────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """
    Lightweight liveness probe.
    Returns 200 {"status": "ok"} if the server is running.
    Docker Compose, load balancers, and CI all use this to gate readiness.
    """
    return {"status": "ok"}


# ── Routers (added per phase) ─────────────────────────────────────────────────
# Phase 6 will register:
#   from app.api import documents, query, audit
#   app.include_router(documents.router, prefix="/documents", tags=["documents"])
#   app.include_router(query.router, prefix="/query", tags=["query"])
#   app.include_router(audit.router, prefix="/audit", tags=["audit"])

logger.info("Finance RAG backend started. Visit /docs for the Swagger UI.")
