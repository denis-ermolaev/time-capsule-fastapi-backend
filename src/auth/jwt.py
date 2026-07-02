"""Вспомогательные функции для работы с jwt-токенами."""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from src.settings import settings


def create_access_token(data: dict[str, Any]) -> str:
    """Создать access токен."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire, "token_type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict[str, Any]) -> str:
    """Создать refresh токен."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(
        days=settings.refresh_token_expire_days,
    )
    to_encode.update({"exp": expire, "token_type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, Any] | None:
    """Декодировать токен для получения данныхю."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None
