import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ScanResult(Base):
    __tablename__ = "scan_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True,
                                    default=lambda: str(uuid.uuid4()))
    scan_id: Mapped[str] = mapped_column(String(36), ForeignKey("scans.id"),
                                         unique=True, nullable=False)
    agent: Mapped[str] = mapped_column(String(40), nullable=False)
    # JSON stored as text: works identically on SQLite (dev) and Postgres (prod).
    details_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    actions_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
