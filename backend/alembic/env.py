"""
alembic/env.py
───────────────
Alembic migration environment.
Reads the database URL from the app's Settings object (not from alembic.ini)
so there's a single source of truth for the connection string.
"""

from logging.config import fileConfig

import app.models  # noqa: F401 — side effect: registers all ORM models with Base
from alembic import context

# ── App imports ───────────────────────────────────────────────────────────────
from app.core.config import settings

# Import Base and trigger all model registrations via models/__init__.py
from app.core.database import Base, _get_engine

# ── Alembic Config ────────────────────────────────────────────────────────────
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override the sqlalchemy.url so alembic.ini doesn't need hardcoded credentials.
# _get_engine() already normalises the URL to use psycopg2.
url = settings.database_url
if url.startswith("postgresql://") or url.startswith("postgres://"):
    url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    url = url.replace("postgres://", "postgresql+psycopg2://", 1)
config.set_main_option("sqlalchemy.url", url)

target_metadata = Base.metadata


# ── Run migrations ────────────────────────────────────────────────────────────
def run_migrations_offline() -> None:
    """Offline mode — emit SQL to stdout without a live DB connection."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Online mode (default) — apply migrations to the live database."""
    connectable = _get_engine()
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
