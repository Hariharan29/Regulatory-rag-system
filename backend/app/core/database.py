"""
core/database.py
────────────────
SQLAlchemy engine, session factory, and declarative Base.
All models import Base from here; all API routes use get_db() as a dependency.

DESIGN NOTE — Lazy engine initialization
─────────────────────────────────────────
The engine is created on first use (_get_engine()), NOT at module import time.
This means importing any model (which imports Base from here) does NOT
immediately try to open a Postgres connection.

Why this matters:
  - Unit tests can import models and test Python-level behaviour without
    a running database (no Docker required for model/schema tests).
  - The engine is still created once and cached (_engine singleton), so
    there's no performance cost in normal operation.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# ── Lazy engine singleton ─────────────────────────────────────────────────────
_engine: Engine | None = None


def _get_engine() -> Engine:
    """
    Return the SQLAlchemy engine, creating it on the first call.
    Uses psycopg2 explicitly (postgresql+psycopg2://) so SQLAlchemy
    never accidentally picks up psycopg3 (which needs system libpq).
    """
    global _engine
    if _engine is None:
        url = settings.database_url
        # Normalise the URL scheme to always use psycopg2.
        # Handles both "postgresql://" and "postgres://" variants.
        if url.startswith("postgresql://") or url.startswith("postgres://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        _engine = create_engine(url, pool_pre_ping=True)
    return _engine


# ── Session factory ───────────────────────────────────────────────────────────
# Uses a lambda so the engine is only resolved when a session is first needed.
def _make_session_factory() -> sessionmaker:
    return sessionmaker(
        bind=_get_engine(),
        autocommit=False,
        autoflush=False,
    )


# ── Declarative base ──────────────────────────────────────────────────────────
# All ORM models inherit from this Base so Alembic can discover them.
# Importing Base here does NOT create an engine — safe to import anywhere.
class Base(DeclarativeBase):
    pass


# ── FastAPI dependency ────────────────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """
    Yield a SQLAlchemy session per request and ensure it is closed afterwards.
    Usage in a route:
        def my_route(db: Session = Depends(get_db)): ...
    """
    SessionLocal = _make_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
