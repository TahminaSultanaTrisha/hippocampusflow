"""Chat messages, tied directly to a scan (one conversation per scan --
simpler than a separate conversations table, and easy to evolve later)."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True,
                                    default=lambda: str(uuid.uuid4()))
    scan_id: Mapped[str] = mapped_column(String(36), ForeignKey("scans.id"),
                                         nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(10), nullable=False)  # user|assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
