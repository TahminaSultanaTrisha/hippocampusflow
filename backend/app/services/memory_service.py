"""HippocampusFlow's hippocampus.

remember()     store a one-sentence memory after each scan analysis
related()      pull memories relevant to some text (keyword + recency)
search_scans() find past scans matching a query (for the search UI)
ask()          have the AI answer a question using the user's memories

Retrieval is keyword-based for now. When the app moves to Postgres,
swapping related() to pgvector similarity is a change inside this file
only -- nothing else in the codebase knows how retrieval works.
"""
import re
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.memory import Memory
from app.models.scan import Scan
from app.services.ai import client

_STOPWORDS = {"this", "that", "with", "have", "what", "when", "where", "which",
              "there", "their", "about", "from", "your", "scan", "scanned",
              "user", "owns", "photo", "image", "show", "find", "last", "week",
              "month", "yesterday", "thing", "stuff"}


def _keywords(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    return [w for w in dict.fromkeys(words) if w not in _STOPWORDS][:12]


def remember(db: Session, user_id: str, scan_id: str | None, content: str) -> None:
    content = (content or "").strip()
    if not content:
        return
    stamp = datetime.now(timezone.utc).strftime("%d %b %Y")
    if "scanned" not in content.lower():
        content = f"{content} (scanned {stamp})"
    db.add(Memory(user_id=user_id, scan_id=scan_id, content=content))
    db.commit()


def related(db: Session, user_id: str, query_text: str, limit: int = 5) -> list[Memory]:
    """Keyword matches first, padded with most-recent memories."""
    base = select(Memory).where(Memory.user_id == user_id).order_by(Memory.created_at.desc())
    keywords = _keywords(query_text)
    results: list[Memory] = []
    if keywords:
        cond = or_(*[Memory.content.ilike(f"%{k}%") for k in keywords])
        results = list(db.scalars(base.where(cond).limit(limit)))
    if len(results) < limit:
        seen = {m.id for m in results}
        for m in db.scalars(base.limit(limit * 2)):
            if m.id not in seen:
                results.append(m)
                seen.add(m.id)
            if len(results) >= limit:
                break
    return results


def format_block(memories: list[Memory]) -> str:
    if not memories:
        return ""
    lines = "\n".join(f"- {m.content}" for m in memories)
    return ("Things you remember about this user's previous scans:\n"
            f"{lines}\n"
            "If any are clearly relevant, mention the connection naturally.\n")


def search_scans(db: Session, user_id: str, query: str, limit: int = 20) -> list[Scan]:
    keywords = _keywords(query) or [query.strip().lower()]
    mem_scan_ids = {
        m.scan_id for m in db.scalars(
            select(Memory).where(
                Memory.user_id == user_id,
                or_(*[Memory.content.ilike(f"%{k}%") for k in keywords]),
            )
        ) if m.scan_id
    }
    cond = or_(
        Scan.id.in_(mem_scan_ids) if mem_scan_ids else Scan.id.is_(None),
        *[Scan.summary.ilike(f"%{k}%") for k in keywords],
        *[Scan.category.ilike(f"%{k}%") for k in keywords],
    )
    return list(db.scalars(
        select(Scan).where(Scan.user_id == user_id, cond)
        .order_by(Scan.created_at.desc()).limit(limit)
    ))


_ASK_SYSTEM = """You are HippocampusFlow's memory. You answer questions about
the user's scan history using ONLY the memories provided. Be specific and
concise (1-3 sentences). If the memories don't contain the answer, say you
don't have a scan matching that -- never invent one."""


def ask(db: Session, user_id: str, question: str) -> str:
    memories = related(db, user_id, question, limit=12)
    if not memories:
        return "You don't have any scans yet — go scan something and I'll start remembering."
    lines = "\n".join(f"- {m.content}" for m in memories)
    return client.complete_text(
        model=get_settings().agent_model,
        system=_ASK_SYSTEM,
        content=[{"type": "text",
                  "text": f"Memories:\n{lines}\n\nQuestion: {question}"}],
    )
