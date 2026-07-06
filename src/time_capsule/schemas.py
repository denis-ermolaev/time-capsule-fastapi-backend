"""Pydantic схемы для капсул времени."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class TimeCapsuleCreateRequest(BaseModel):
    """Данные необходимые для создания капсулы."""

    # TODO: Валидация lock_date, чтобы оно было в будущем  # noqa: FIX002, TD002, TD003

    title: str
    is_private: bool
    text: str
    lock_date: datetime


class TimeCapsuleResponce(BaseModel):
    """Данные по капсуле времени."""

    model_config = ConfigDict(from_attributes=True)

    id: int

    is_private: bool
    is_locked: bool
    is_open: bool

    title: str

    create_date: datetime
    lock_date: datetime
    open_date: datetime | None = None


class TimeCapsuleWithTextResponce(BaseModel):
    """Данные по капсуле времени."""

    model_config = ConfigDict(from_attributes=True)

    id: int

    is_private: bool
    is_locked: bool
    is_open: bool

    title: str
    text: str

    create_date: datetime
    lock_date: datetime
    open_date: datetime | None = None


class TimeCapsuleListResponce(BaseModel):
    """Пагинация для списка капсул времени."""

    items: list[TimeCapsuleResponce]
    total: int
    page: int
    page_size: int


class TimeCapsuleUpdateRequest(BaseModel):
    """Схема для частичного обновления капсулы — все поля опциональны."""

    title: str | None = None
    is_private: bool | None = None
    text: str | None = None
    lock_date: datetime | None = None


class TimeCapsuleFilterParams(BaseModel):
    """Фильтры для списка капсул времени."""

    order_by: (
        Literal["create_date", "lock_date", "-create_date", "-lock_date"] | None
    ) = None

    title: str | None = None

    is_private: bool | None = None

    is_other_users: bool | None = None

    is_locked: bool | None = None

    is_open: bool | None = None

    locked_at_from: datetime | None = None
    locked_at_to: datetime | None = None

    created_at_from: datetime | None = None
    created_at_to: datetime | None = None
