from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, Request, Response

from app.config import settings
from app.db import get_admin, verify_password

COOKIE = "admin_session"
TTL_SECONDS = 60 * 60 * 24
ISSUER = "nanda-admin"
ALGORITHM = "HS256"


def _secret() -> str:
    secret = (settings.admin_secret or "").strip()
    if len(secret) < 32:
        raise HTTPException(status_code=503, detail="ADMIN_SECRET must be at least 32 characters for JWT.")
    return secret


def make_session_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": username,
            "iat": now,
            "exp": now + timedelta(seconds=TTL_SECONDS),
            "iss": ISSUER,
        },
        _secret(),
        algorithm=ALGORITHM,
    )


def parse_session_token(token: str) -> str:
    try:
        payload = jwt.decode(token, _secret(), algorithms=[ALGORITHM], issuer=ISSUER)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Session expired. Sign in again.") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token. Sign in again.") from exc
    username = str(payload.get("sub") or "").strip()
    if not username or not get_admin(username):
        raise HTTPException(status_code=401, detail="Invalid token. Sign in again.")
    return username


def check_login(username: str, password: str) -> None:
    admin = get_admin(username)
    if not admin or not verify_password(password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Wrong username or password.")


def _request_token(request: Request) -> str:
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header.split(" ", 1)[1].strip()
    return request.cookies.get(COOKIE, "")


def current_admin(request: Request) -> str:
    token = _request_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not signed in.")
    return parse_session_token(token)


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE,
        token,
        httponly=True,
        samesite="lax",
        max_age=TTL_SECONDS,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE, path="/")
