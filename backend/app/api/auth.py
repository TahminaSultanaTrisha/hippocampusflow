"""Auth endpoints: register, login, refresh.

Deliberately thin -- validation is done by the schemas, hashing/JWT by
core/security.py. When logic grows (email verification, OAuth), it moves
into a services/auth_service.py, same pattern as the blueprint.
"""
import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import LoginIn, RefreshIn, RegisterIn, TokenPair

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_pair(user_id: str) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, db: Session = Depends(get_db)) -> TokenPair:
    existing = db.scalar(select(User).where(User.email == body.email.lower()))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "email_taken", "message": "An account with this email already exists"},
        )
    user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        display_name=body.display_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _token_pair(user.id)


@router.post("/login", response_model=TokenPair)
def login(body: LoginIn, db: Session = Depends(get_db)) -> TokenPair:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    # Same error for "no such user" and "wrong password" -- never tell an
    # attacker which emails exist in your database.
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "invalid_credentials", "message": "Email or password is incorrect"},
    )
    if user is None or not verify_password(body.password, user.password_hash):
        raise invalid
    return _token_pair(user.id)


@router.post("/refresh", response_model=TokenPair)
def refresh(body: RefreshIn) -> TokenPair:
    try:
        user_id = decode_token(body.refresh_token, expected_type="refresh")
    except pyjwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_refresh_token", "message": "Refresh token is invalid or expired"},
        )
    return _token_pair(user_id)
