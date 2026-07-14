"""Scan endpoints. Phase 2 additions:
- POST /scans now schedules AI analysis as a background task
- GET /scans/{id} returns the agent's structured result once complete
- GET/POST /scans/{id}/messages: follow-up chat about the scan
"""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.models.action import Action
from app.models.memory import Memory
from app.models.message import Message
from app.models.scan import Scan
from app.models.scan_result import ScanResult
from app.models.user import User
from app.schemas.scan import (
    MessageIn, MessageListOut, MessageOut,
    ScanDetailOut, ScanListOut, ScanOut,
)
from app.services import action_service
from app.services.ai import analysis, chat as chat_service
from app.services.storage_service import LocalImageStorage, get_storage

router = APIRouter(prefix="/scans", tags=["scans"])


@router.post("", response_model=ScanOut, status_code=status.HTTP_201_CREATED)
async def create_scan(
    file: UploadFile,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage: LocalImageStorage = Depends(get_storage),
) -> Scan:
    ext = storage.extension_for(file.content_type or "")
    if ext is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={"code": "bad_image_type", "message": "Upload a JPEG, PNG, or WebP image"},
        )
    data = await file.read()
    if len(data) > get_settings().max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"code": "image_too_large", "message": "Image exceeds the 10 MB limit"},
        )
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "empty_file", "message": "The uploaded file is empty"},
        )

    # Free-tier limit: scans this calendar month.
    if current_user.subscription_tier == "free":
        month_start = datetime.now(timezone.utc).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)
        used = db.scalar(select(func.count(Scan.id)).where(
            Scan.user_id == current_user.id, Scan.created_at >= month_start)) or 0
        if used >= get_settings().free_scan_limit:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={"code": "scan_limit_reached",
                        "message": f"You've used all {get_settings().free_scan_limit} free scans this month."})

    scan = Scan(user_id=current_user.id, image_key="pending")
    db.add(scan)
    db.flush()
    scan.image_key = storage.save(current_user.id, scan.id, data, ext)
    db.commit()
    db.refresh(scan)

    # The upload response returns immediately; the AI pipeline runs after.
    # The app polls GET /scans/{id} until status becomes complete/failed.
    background.add_task(analysis.run_analysis, scan.id)
    return scan


@router.get("", response_model=ScanListOut)
def list_scans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScanListOut:
    scans = db.scalars(
        select(Scan).where(Scan.user_id == current_user.id)
        .order_by(Scan.created_at.desc()).limit(100)
    ).all()
    return ScanListOut(scans=list(scans))


def _owned_scan(scan_id: str, db: Session, user: User) -> Scan:
    scan = db.get(Scan, scan_id)
    if scan is None or scan.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "scan_not_found", "message": "Scan not found"},
        )
    return scan


@router.get("/{scan_id}", response_model=ScanDetailOut)
def get_scan(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScanDetailOut:
    scan = _owned_scan(scan_id, db, current_user)
    out = ScanDetailOut.model_validate(scan)
    result = db.scalar(select(ScanResult).where(ScanResult.scan_id == scan.id))
    if result is not None:
        out.agent = result.agent
        out.details = json.loads(result.details_json)
        out.suggested_actions = json.loads(result.actions_json)
    return out


@router.get("/{scan_id}/image")
def get_scan_image(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage: LocalImageStorage = Depends(get_storage),
) -> FileResponse:
    scan = _owned_scan(scan_id, db, current_user)
    path = storage.path_for(scan.image_key)
    if not path.exists():
        raise HTTPException(status_code=404, detail={"code": "image_missing", "message": "Image file missing"})
    return FileResponse(path)


@router.get("/{scan_id}/messages", response_model=MessageListOut)
def list_messages(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageListOut:
    _owned_scan(scan_id, db, current_user)
    messages = db.scalars(
        select(Message).where(Message.scan_id == scan_id).order_by(Message.created_at)
    ).all()
    return MessageListOut(messages=list(messages))


@router.post("/{scan_id}/messages", response_model=MessageOut)
def send_message(
    scan_id: str,
    body: MessageIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Message:
    scan = _owned_scan(scan_id, db, current_user)
    text = body.content.strip()
    if not text:
        raise HTTPException(status_code=400, detail={"code": "empty_message", "message": "Message is empty"})
    if len(text) > 2000:
        raise HTTPException(status_code=400, detail={"code": "message_too_long", "message": "Keep messages under 2000 characters"})

    db.add(Message(scan_id=scan.id, role="user", content=text))
    db.commit()

    reply_text = chat_service.reply(db, scan)
    reply = Message(scan_id=scan.id, role="assistant", content=reply_text)
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply

class ActionIn(BaseModel):
    action_type: str


class ActionOut(BaseModel):
    message: str


@router.post("/{scan_id}/actions", response_model=ActionOut)
def run_action(
    scan_id: str,
    body: ActionIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActionOut:
    scan = _owned_scan(scan_id, db, current_user)
    message = action_service.execute(db, scan, body.action_type)
    if message is None:
        raise HTTPException(status_code=400, detail={
            "code": "unknown_action",
            "message": f"Unknown action type: {body.action_type}"})
    return ActionOut(message=message)


def _erase_scan(db: Session, storage: LocalImageStorage, scan: Scan) -> None:
    """Full erasure: the scan row, its AI result, chat messages, memories,
    logged actions, and the image file on disk. Privacy control, not soft
    delete -- when the user says forget it, it is gone."""
    db.execute(delete(Message).where(Message.scan_id == scan.id))
    db.execute(delete(Memory).where(Memory.scan_id == scan.id))
    db.execute(delete(Action).where(Action.scan_id == scan.id))
    db.execute(delete(ScanResult).where(ScanResult.scan_id == scan.id))
    path = storage.path_for(scan.image_key)
    db.delete(scan)
    db.commit()
    if path.exists():
        path.unlink()


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scan(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage: LocalImageStorage = Depends(get_storage),
) -> None:
    _erase_scan(db, storage, _owned_scan(scan_id, db, current_user))


class BatchDeleteIn(BaseModel):
    scan_ids: list[str]


class BatchDeleteOut(BaseModel):
    deleted: int


@router.post("/batch-delete", response_model=BatchDeleteOut)
def batch_delete(
    body: BatchDeleteIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage: LocalImageStorage = Depends(get_storage),
) -> BatchDeleteOut:
    """Delete many scans in one call. Only the caller's own scans are
    touched -- foreign or unknown ids are silently skipped."""
    deleted = 0
    for scan_id in body.scan_ids[:100]:
        scan = db.get(Scan, scan_id)
        if scan is not None and scan.user_id == current_user.id:
            _erase_scan(db, storage, scan)
            deleted += 1
    return BatchDeleteOut(deleted=deleted)
