"""The users table, defined as a Python class (SQLAlchemy ORM).

Phase 0 only needs users. scans, scan_results, memories, etc. arrive in
later phases as their own model files, each mapping 1:1 to the blueprint's
database design.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _uuid() -> str:
    # Stored as a string so it works identically on SQLite and Postgres.
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subscription_tier: Mapped[str] = mapped_column(String(20), default="free", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
