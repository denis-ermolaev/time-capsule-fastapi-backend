"""Зависимость аутентификации."""

from fastapi import Depends, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import decode_token
from src.auth.models import User
from src.db_depends import get_async_db

http_bearer = HTTPBearer()


async def get_current_user(
    # HTTPBearer возвращает HTTPAuthorizationCredentials → берём .credentials
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),  # noqa: B008
    db: AsyncSession = Depends(get_async_db),  # noqa: B008
) -> User:
    """Получить текущего пользователя из токена."""
    token = credentials.credentials
    payload = decode_token(token)
    if payload is None or payload.get("token_type") != "access":
        raise HTTPException(status_code=401, detail="Invalid access token")

    user = await db.scalar(select(User).where(User.id == int(payload["sub"])))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
