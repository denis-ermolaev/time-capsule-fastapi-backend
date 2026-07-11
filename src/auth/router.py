"""End-point'ы для авторизации."""

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from src.auth.deps import get_current_user
from src.auth.jwt import create_access_token, create_refresh_token, decode_token
from src.auth.models import User
from src.auth.schemas import (
    AccessRequest,
    AccessResponse,
    LoginRequest,
    RefreshRequest,
    TokenOut,
    UserCreate,
    UserOut,
)
from src.auth.utils import hash_password, verify_password
from src.db_depends import get_async_db

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(
    user: UserCreate,
    db: Annotated[
        AsyncSession,
        Depends(get_async_db),
    ],
) -> UserOut:
    """Регестрация."""
    existing = await db.scalars(
        select(User).where(
            (User.username == user.username) | (User.email == user.email),
        ),
    )
    if existing.first():
        raise HTTPException(status_code=400, detail="Username or email already taken")

    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return UserOut.model_validate(db_user)


@router.post("/login", response_model=TokenOut)
async def login(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> TokenOut:
    """Авторизация."""
    result = await db.scalars(select(User).where(User.email == body.email))
    user = result.first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token_data = {"sub": str(user.id)}
    return TokenOut(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/refresh", response_model=TokenOut)
async def refresh(
    body: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> TokenOut:
    """Обновление токенов по refresh токену."""
    payload = decode_token(body.refresh_token)
    if payload is None or payload.get("token_type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = await db.scalar(select(User).where(User.id == int(payload["sub"])))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    token_data = {"sub": str(user.id)}
    return TokenOut(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/access", response_model=AccessResponse)
async def access(
    body: AccessRequest,
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> AccessResponse:
    """Проверка работоспособности access токена."""
    payload = decode_token(body.access_token)
    if payload is None or payload.get("token_type") != "access":
        raise HTTPException(status_code=401, detail="Invalid access token")
    user = await db.scalar(select(User).where(User.id == int(payload["sub"])))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return AccessResponse(message="ok")


@router.get("/me", response_model=UserOut)
async def me(
    user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> UserOut:
    """Проверка работоспособности access токена."""
    return UserOut.model_validate(user)
