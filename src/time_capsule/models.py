"""Модели базы данных для реализации капсул времени."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.auth.models import User


class TimeCapsule(Base):
    """Модель реализации капсул времени."""

    __tablename__ = "time_capsule"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    user: Mapped[User] = relationship(
        "User",
        back_populates="time_capsules",
    )

    # Приватная - только пользователь создавший может прочитать и открыть
    is_private: Mapped[bool] = mapped_column(default=True)
    # Закрыта и не может быть прочитана
    is_locked: Mapped[bool] = mapped_column(default=True)
    # Кто-то когда-то уже прочитал, если True
    is_open: Mapped[bool] = mapped_column(default=False)

    # Название капсулы времени
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    # Содержание капсулы времени
    text: Mapped[str] = mapped_column(Text, nullable=False)

    create_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    # до какой даты закрыта
    lock_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Когда конкретно была открыта впервые
    open_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
    )

    def __repr__(self) -> str:
        """Текстовое описание."""
        return f"<TimeCapsule(id={self.id}, user_id={self.user_id}, is_locked={self.is_locked})>"
