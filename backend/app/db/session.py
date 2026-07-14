"""Database engine and session factory.

A Session is a short-lived "conversation" with the database. Each API
request gets its own session (see api/deps.py) and it is always closed
afterwards, even if the request raised an error.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# check_same_thread only applies to SQLite (our zero-setup dev database).
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """All ORM models inherit from this so Alembic can discover them."""
