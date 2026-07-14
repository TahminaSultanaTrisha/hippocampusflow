"""Executes actions on scans. Each action: reads the scan's structured
details, stores an Action row, and returns a human-friendly confirmation
that includes a running total -- instant feedback is what makes actions
feel real. New action types slot into ACTIONS the same way agents slot
into the router."""
import json
import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.action import Action
from app.models.scan import Scan
from app.models.scan_result import ScanResult


def _amount(value) -> float:
    """'£23.50' / '23.50' / 1450 -> float, else 0."""
    m = re.search(r"\d+(?:[.,]\d+)?", str(value or ""))
    return float(m.group().replace(",", ".")) if m else 0.0


def _details(db: Session, scan: Scan) -> dict:
    result = db.scalar(select(ScanResult).where(ScanResult.scan_id == scan.id))
    return json.loads(result.details_json) if result else {}


def _user_actions(db: Session, user_id: str, action_type: str) -> list[Action]:
    return list(db.scalars(select(Action).where(
        Action.user_id == user_id, Action.action_type == action_type)))


def _record(db: Session, scan: Scan, action_type: str, payload: dict) -> None:
    db.add(Action(user_id=scan.user_id, scan_id=scan.id,
                  action_type=action_type, payload_json=json.dumps(payload)))
    db.commit()


def add_expense(db: Session, scan: Scan) -> str:
    d = _details(db, scan)
    amount = _amount(d.get("total"))
    currency = d.get("currency") or "£"
    merchant = d.get("merchant") or "unknown merchant"
    if amount <= 0:
        return "Couldn't read a total from this receipt, so no expense was added."
    _record(db, scan, "expense",
            {"amount": amount, "currency": currency,
             "merchant": merchant, "date": d.get("date")})
    now = datetime.now(timezone.utc)
    month_total = sum(
        json.loads(a.payload_json).get("amount", 0)
        for a in _user_actions(db, scan.user_id, "expense")
        if a.created_at.month == now.month and a.created_at.year == now.year
    )
    return (f"Expense added: {currency}{amount:.2f} at {merchant}. "
            f"Total tracked this month: {currency}{month_total:.2f}.")


def save_wishlist(db: Session, scan: Scan) -> str:
    d = _details(db, scan)
    name = d.get("name") or scan.summary or "this item"
    _record(db, scan, "wishlist",
            {"name": name, "brand": d.get("brand"),
             "estimated_price": d.get("estimated_price")})
    count = len(_user_actions(db, scan.user_id, "wishlist"))
    return f"Saved to wishlist: {name}. You now have {count} item(s) saved."


def log_meal(db: Session, scan: Scan) -> str:
    d = _details(db, scan)
    name = d.get("name") or "this meal"
    kcal = _amount(d.get("calories"))
    _record(db, scan, "meal", {"name": name, "calories": kcal})
    today = datetime.now(timezone.utc).date()
    day_total = sum(
        json.loads(a.payload_json).get("calories", 0)
        for a in _user_actions(db, scan.user_id, "meal")
        if a.created_at.date() == today
    )
    return (f"Logged: {name} (~{kcal:.0f} kcal). "
            f"Today's total: ~{day_total:.0f} kcal (estimates).")


ACTIONS = {"add_expense": add_expense,
           "save_wishlist": save_wishlist,
           "log_meal": log_meal}


def execute(db: Session, scan: Scan, action_type: str) -> str | None:
    handler = ACTIONS.get(action_type)
    return handler(db, scan) if handler else None
