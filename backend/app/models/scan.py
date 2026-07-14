"""The scans table: one row per photo the user takes.

category / confidence / summary are nullable on purpose -- they stay empty
in Phase 1 and get filled in by the AI pipeline in Phase 2. Designing the
table for the next phase now means no schema change later.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    image_key: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="uploaded", nullable=False)
    # Filled by the AI in Phase 2:
    category: Mapped[str | None] = mapped_column(String(40), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
