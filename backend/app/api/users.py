"""User endpoints. /users/me now includes this month's scan usage so the
app can show 'X of 10 free scans used' -- the subscription tier made
visible instead of invisible plumbing."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.models.scan import Scan
from app.models.user import User
from app.schemas.auth import UserOut

router = APIRouter(prefix="/users", tags=["users"])


class MeOut(UserOut):
    scans_used_this_month: int = 0
    scan_limit: int | None = None  # None = unlimited (premium)


@router.get("/me", response_model=MeOut)
def read_me(current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db)) -> MeOut:
    month_start = datetime.now(timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0)
    used = db.scalar(select(func.count(Scan.id)).where(
        Scan.user_id == current_user.id,
        Scan.created_at >= month_start)) or 0
    out = MeOut.model_validate(current_user)
    out.scans_used_this_month = used
    out.scan_limit = (get_settings().free_scan_limit
                      if current_user.subscription_tier == "free" else None)
    return out
