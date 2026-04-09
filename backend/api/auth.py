"""Auth endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.audit_log import log_action
from backend.core.security import (
    create_access_token,
    generate_api_key,
    hash_password,
    verify_password,
    get_current_user,
    get_current_user_optional,
)
from backend.db.models import User
from backend.db.session import get_db
from backend.schemas.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    UserBrief,
)

router = APIRouter()


@router.get("/me")
async def get_me(
    current_user: User | None = Depends(get_current_user_optional),
) -> UserBrief | None:
    """Get current authenticated user. Returns null if not authenticated."""
    if current_user is None:
        return None
    return UserBrief(id=current_user.id, email=current_user.email, name=current_user.name)


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest, db: AsyncSession = Depends(get_db)
) -> RegisterResponse:
    user = User(
        email=payload.email,
        name=payload.name,
        hashed_password=hash_password(payload.password),
        api_key=generate_api_key(),
        role="analyst",
        is_active=True,
    )
    db.add(user)
    try:
        await db.flush()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered.")

    try:
        await log_action(
            db, "user.registered", "User", user.id, user=user, details={"email": user.email}
        )
    except Exception:
        pass

    await db.refresh(user)
    return RegisterResponse(user_id=user.id, api_key=user.api_key)


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if (
        user is None
        or not verify_password(payload.password, user.hashed_password)
        or not user.is_active
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    token = create_access_token(user.id)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=60 * 60 * 24,
    )
    try:
        await log_action(db, "user.login", "User", user.id, user=user)
    except Exception:
        pass

    return LoginResponse(
        session_token=token,
        user=UserBrief(id=user.id, email=user.email, name=user.name),
    )
