from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AuthLoginRequest(BaseModel):
    email: str
    password: str


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int | None = None


class AuthUserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None


class AuthRefreshRequest(BaseModel):
    refresh_token: str


class AuthTokenStatusResponse(BaseModel):
    active: bool
    expired: bool
    token_type: str | None
    user_id: int | None
    email: str | None
    username: str | None
    expires_at: int | None
    seconds_left: int | None
