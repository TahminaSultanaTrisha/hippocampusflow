"""Dependencies: reusable pieces FastAPI injects into route handlers.

get_db      -> a database session per request, always closed afterwards.
get_current_user -> reads the Bearer token, validates it, loads the user.
                    Any route that declares this dependency is protected.
"""
from typing import Generator

import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "unauthorized", "message": "Invalid or missing token"},
    )
    if credentials is None:
        raise unauthorized
    try:
        user_id = decode_token(credentials.credentials, expected_type="access")
    except pyjwt.PyJWTError:
        raise unauthorized
    user = db.get(User, user_id)
    if user is None:
        raise unauthorized
    return user
