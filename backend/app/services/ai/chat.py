"""Follow-up chat about a scan -- now with the user's memories in context,
so questions like "is this the same one I scanned before?" can be answered."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.message import Message
from app.models.scan import Scan
from app.services import memory_service
from app.services.ai import client
from app.services.storage_service import LocalImageStorage

_SYSTEM = """You are HippocampusFlow, a friendly AI assistant. The user scanned
an object with their camera; the image, your earlier analysis, and relevant
memories of their past scans are provided. Answer follow-up questions helpfully
and concisely. Be honest when you can't tell something from the image."""


def reply(db: Session, scan: Scan) -> str:
    history = db.scalars(
        select(Message).where(Message.scan_id == scan.id).order_by(Message.created_at)
    ).all()

    path = LocalImageStorage().path_for(scan.image_key)
    image = client.image_block(path.read_bytes(), path.suffix.lstrip("."))

    last_user_text = history[-1].content if history else ""
    memories = memory_service.related(db, scan.user_id, last_user_text, limit=4)
    context = (f"[Scan context -- category: {scan.category or 'unknown'}; "
               f"analysis: {scan.summary or 'not analyzed yet'}]\n"
               f"{memory_service.format_block(memories)}")

    messages: list[dict] = []
    for i, m in enumerate(history):
        if i == 0 and m.role == "user":
            messages.append({"role": "user", "content": [
                image, {"type": "text", "text": f"{context}\n\n{m.content}"}]})
        else:
            messages.append({"role": m.role, "content": m.content})

    return client.chat_text(get_settings().agent_model, _SYSTEM, messages)
