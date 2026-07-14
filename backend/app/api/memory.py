"""Memory endpoints:
GET  /memory/search?q=...   keyword search across past scans
POST /memory/ask            AI answers a question from the user's scan history
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.scan import ScanOut
from app.models.memory import Memory
from app.services import memory_service

router = APIRouter(prefix="/memory", tags=["memory"])


class AskIn(BaseModel):
    question: str


class AskOut(BaseModel):
    answer: str
    scans: list[ScanOut]


@router.get("/search", response_model=AskOut)
def search(q: str, db: Session = Depends(get_db),
           current_user: User = Depends(get_current_user)) -> AskOut:
    scans = memory_service.search_scans(db, current_user.id, q)
    return AskOut(answer="", scans=[ScanOut.model_validate(s) for s in scans])


@router.post("/ask", response_model=AskOut)
def ask(body: AskIn, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)) -> AskOut:
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={"code": "empty_question", "message": "Ask something"})
    answer = memory_service.ask(db, current_user.id, question)
    scans = memory_service.search_scans(db, current_user.id, question, limit=10)
    return AskOut(answer=answer, scans=[ScanOut.model_validate(s) for s in scans])

class MemoryOut(BaseModel):
    id: str
    content: str
    created_at: datetime


class MemoryListOut(BaseModel):
    memories: list[MemoryOut]


@router.get("", response_model=MemoryListOut)
def list_memories(db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)) -> MemoryListOut:
    from sqlalchemy import select
    rows = db.scalars(select(Memory).where(Memory.user_id == current_user.id)
                      .order_by(Memory.created_at.desc()).limit(200))
    return MemoryListOut(memories=[
        MemoryOut(id=m.id, content=m.content, created_at=m.created_at) for m in rows])


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(memory_id: str, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)) -> None:
    m = db.get(Memory, memory_id)
    if m is None or m.user_id != current_user.id:
        raise HTTPException(status_code=404, detail={
            "code": "memory_not_found", "message": "Memory not found"})
    db.delete(m)
    db.commit()
