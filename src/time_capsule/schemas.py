"""Pydantic схемы для капсул времени."""

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from datetime import datetime


class TimeCapsuleCreate(BaseModel):
    """Данные необходимые для создания капсулы."""

    is_private: bool
    text: str
    lock_date: datetime


class TimeCapsuleCreateOut(BaseModel):
    """Данные необходимые для создания капсулы."""

    model_config = ConfigDict(from_attributes=True)

    id: int

    is_private: bool
    is_locked: bool
    is_open: bool

    text: str
    create_date: datetime
    lock_date: datetime
    open_date: datetime | None = None


class TimeCapsuleUpdate(BaseModel):
    """Схема для частичного обновления капсулы — все поля опциональны."""

    is_private: bool | None = None
    text: str | None = None
    lock_date: datetime | None = None
