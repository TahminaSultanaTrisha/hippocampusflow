"""Executed actions: expenses, wishlist items, logged meals.
One table for all action types -- the payload carries the specifics.
This is the 'action framework' from the blueprint in its simplest form."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Action(Base):
    __tablename__ = "actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True,
                                    default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"),
                                         nullable=False, index=True)
    scan_id: Mapped[str] = mapped_column(String(36), ForeignKey("scans.id"),
                                         nullable=False)
    action_type: Mapped[str] = mapped_column(String(30), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
