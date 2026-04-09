"""Security utilities: hashing, API keys, tokens, and auth dependencies."""

from datetime import datetime, timedelta, timezone
import secrets
import string

import bcrypt
from fastapi import Cookie, Depends, Header, HTTPException, status
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.db.models import User
from backend.db.session import get_db


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def generate_api_key() -> str:
    alphabet = string.ascii_letters + string.digits
    random_part = "".join(secrets.choice(alphabet) for _ in range(40))
    return f"{settings.API_KEY_PREFIX}{random_part}"


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
    session_token: str | None = Cookie(default=None),
) -> User:
    api_key: str | None = None
    bearer_token: str | None = None

    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            # Check if it looks like a JWT (has two dots) - treat as session token
            # Otherwise treat as API key
            if token.count(".") == 2:
                bearer_token = token
            else:
                api_key = token

    user: User | None = None

    # First try session token (JWT)
    if bearer_token:
        user = await _get_user_by_session_token(db, bearer_token)
    # Then try API key
    if user is None and api_key:
        user = await _get_user_by_api_key(db, api_key)
    # Finally try session cookie
    if user is None and session_token:
        user = await _get_user_by_session_token(db, session_token)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide valid API key or session token.",
        )
    return user


async def _get_user_by_api_key(db: AsyncSession, api_key: str) -> User | None:
    result = await db.execute(select(User).where(User.api_key == api_key))
    return result.scalar_one_or_none()


async def _get_user_by_session_token(db: AsyncSession, session_token: str) -> User | None:
    payload = decode_access_token(session_token)
    if not payload or "sub" not in payload:
        return None
    result = await db.execute(select(User).where(User.id == str(payload["sub"])))
    return result.scalar_one_or_none()


async def get_current_user_optional(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
    session_token: str | None = Cookie(default=None),
) -> User | None:
    """Optional auth check - returns None instead of raising 401."""
    api_key: str | None = None
    bearer_token: str | None = None

    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            if token.count(".") == 2:
                bearer_token = token
            else:
                api_key = token

    user: User | None = None

    if bearer_token:
        user = await _get_user_by_session_token(db, bearer_token)
    if user is None and api_key:
        user = await _get_user_by_api_key(db, api_key)
    if user is None and session_token:
        user = await _get_user_by_session_token(db, session_token)

    if user is None or not user.is_active:
        return None
    return user
