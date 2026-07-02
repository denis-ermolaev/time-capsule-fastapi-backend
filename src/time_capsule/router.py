"""Энд поинты капсул времени."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import get_current_user
from src.auth.models import User
from src.db_depends import get_async_db
from src.time_capsule.models import TimeCapsule
from src.time_capsule.schemas import TimeCapsuleCreate, TimeCapsuleCreateOut

router = APIRouter(prefix="/time_capsule", tags=["time_capsule"])


@router.get("/", status_code=201)
async def get_time_capsules(
    db: Annotated[
        AsyncSession,
        Depends(get_async_db),
    ],
    user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> list[TimeCapsuleCreateOut]:
    """Получение списка капсул времени."""
    result = []
    my_capsules = await db.scalars(select(TimeCapsule).where(TimeCapsule.user == user))
    for i in my_capsules:
        result.append(TimeCapsuleCreateOut.model_validate(i))  # noqa: PERF401

    others_capsules = await db.scalars(
        select(TimeCapsule)
        .where(TimeCapsule.user != user)
        .where(TimeCapsule.is_private == False),  # noqa: E712
    )
    for i in others_capsules:
        result.append(TimeCapsuleCreateOut.model_validate(i))  # noqa: PERF401

    return result


@router.post("/", response_model=TimeCapsuleCreateOut, status_code=201)
async def create_time_capsule(
    time_capsule: TimeCapsuleCreate,
    db: Annotated[
        AsyncSession,
        Depends(get_async_db),
    ],
    user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> TimeCapsuleCreateOut:
    """Создание капсулы времени."""
    db_time_capsule = TimeCapsule(
        user_id=user.id,
        user=user,
        is_private=time_capsule.is_private,
        text=time_capsule.text,
        lock_date=time_capsule.lock_date,
    )
    db.add(db_time_capsule)
    await db.commit()
    await db.refresh(db_time_capsule)
    return TimeCapsuleCreateOut.model_validate(db_time_capsule)
