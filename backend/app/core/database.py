"""
core/database.py
────────────────
SQLAlchemy engine, session factory, and declarative Base.
All models import Base from here; all API routes use get_db() as a dependency.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# ── Engine ────────────────────────────────────────────────────────────────────
# pool_pre_ping=True tells SQLAlchemy to test the connection before using it,
# which prevents "server closed the connection unexpectedly" errors after
# Postgres restarts (e.g. after docker compose down/up).
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

# ── Session factory ───────────────────────────────────────────────────────────
# autocommit=False  → we commit explicitly; nothing is auto-committed.
# autoflush=False   → we control when SQLAlchemy flushes pending changes to DB.
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# ── Declarative base ──────────────────────────────────────────────────────────
# All ORM models inherit from this Base so Alembic can discover them.
class Base(DeclarativeBase):
    pass


# ── FastAPI dependency ────────────────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """
    Yield a SQLAlchemy session per request and ensure it is closed afterwards.
    Usage in a route:
        def my_route(db: Session = Depends(get_db)): ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
