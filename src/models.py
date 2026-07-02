"""Регестрация моделей для миграции с помощью alembic."""

from src.auth.models import User

__all__ = [
    "User",
]
