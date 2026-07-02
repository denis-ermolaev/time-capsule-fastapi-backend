"""Модели базы данных для реализации аутентификации."""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.time_capsule.models import TimeCapsule


class User(Base):
    """Модель реализации пользователя."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    time_capsules: Mapped[list[TimeCapsule]] = relationship(
        "TimeCapsule",
        back_populates="user",
        cascade="all, delete-orphan",
    )
