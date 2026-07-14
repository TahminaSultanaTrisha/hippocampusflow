"""Pydantic schemas = the shapes of JSON going in and out of the API.

FastAPI uses these to validate requests automatically (bad email format ->
422 error before your code even runs) and to filter responses (password_hash
can never leak, because UserOut simply doesn't include it).
"""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=100)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # lets us return ORM objects directly
    id: str
    email: EmailStr
    display_name: str | None
    subscription_tier: str
    created_at: datetime
