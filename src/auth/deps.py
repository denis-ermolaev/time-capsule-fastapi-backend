"""Зависимость аутентификации."""

from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select

from src.auth.jwt import decode_token
from src.auth.models import User
from src.db_depends import get_async_db

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db),  # noqa: B008
) -> User:
    """Получить текущего пользователя из токена. Выдать ошибки при проблемах с токеном."""
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await db.scalar(select(User).where(User.id == int(payload["sub"])))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
