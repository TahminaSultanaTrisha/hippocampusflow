from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ScanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: str
    category: str | None
    confidence: float | None
    summary: str | None
    created_at: datetime


class ScanDetailOut(ScanOut):
    """ScanOut + the specialist agent's structured output (when complete)."""
    agent: str | None = None
    details: dict = {}
    suggested_actions: list[str] = []


class ScanListOut(BaseModel):
    scans: list[ScanOut]


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    role: str
    content: str
    created_at: datetime


class MessageIn(BaseModel):
    content: str


class MessageListOut(BaseModel):
    messages: list[MessageOut]
