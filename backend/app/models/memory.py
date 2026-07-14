"""One row per thing the AI remembers about the user.

Phase 3 stores AI-written memory sentences and retrieves them by keyword +
recency. The table deliberately matches the blueprint's design (minus the
embedding column) so upgrading to pgvector later is an ALTER TABLE, not a
redesign.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True,
                                    default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"),
                                         nullable=False, index=True)
    scan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("scans.id"),
                                                nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="scan", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
