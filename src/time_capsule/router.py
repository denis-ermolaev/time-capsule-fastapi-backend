"""Энд поинты капсул времени."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import get_current_user
from src.auth.models import User
from src.db_depends import get_async_db
from src.time_capsule.models import TimeCapsule
from src.time_capsule.schemas import (
    TimeCapsuleCreate,
    TimeCapsuleCreateOut,
    TimeCapsuleUpdate,
)

router = APIRouter(prefix="/time_capsules", tags=["time_capsules"])


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
    """Получить список капсул времени."""
    # TODO @denis-ermolaev: Сделать пагинацию  # noqa: FIX002, TD003
    result = []
    my_capsules = (
        await db.scalars(select(TimeCapsule).where(TimeCapsule.user == user))
    ).all()
    for i in my_capsules:
        result.append(TimeCapsuleCreateOut.model_validate(i))  # noqa: PERF401

    others_capsules = (
        await db.scalars(
            select(TimeCapsule)
            .where(TimeCapsule.user != user)
            .where(TimeCapsule.is_private == False),  # noqa: E712 Здесь не работает not bool
        )
    ).all()
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
    """Создать капсулу времени."""
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


@router.get("/{capsule_id}", response_model=TimeCapsuleCreateOut, status_code=200)
async def get_time_capsule(
    capsule_id: Annotated[int, Path(ge=1, description="id конкретной капсулы времени")],
    user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_async_db),
    ],
) -> TimeCapsuleCreateOut:
    """Получить капсулу времени по id."""
    # TODO @denis-ermolaev: id+user для своих и id + private(False) для чужих  # noqa: FIX002, TD003
    time_capsule = (
        await db.scalars(
            select(TimeCapsule)
            .where(TimeCapsule.id == capsule_id)
            .where(TimeCapsule.user == user),
        )
    ).first()

    if not time_capsule:
        raise HTTPException(status_code=404, detail="Not found")

    return TimeCapsuleCreateOut.model_validate(time_capsule)


@router.patch("/{capsule_id}", response_model=TimeCapsuleCreateOut, status_code=200)
async def update_time_capsule(
    capsule_id: Annotated[int, Path(ge=1, description="id конкретной капсулы времени")],
    update_data: TimeCapsuleUpdate,
    user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_async_db),
    ],
) -> TimeCapsuleCreateOut:
    """Обновить капсулу времени по id."""
    time_capsule = await db.scalar(
        select(TimeCapsule)
        .where(TimeCapsule.id == capsule_id)
        .where(TimeCapsule.user == user),
    )
    if not time_capsule:
        raise HTTPException(status_code=404, detail="Not found")
    # 2. Меняем переданные поля
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(time_capsule, field, value)
    # 3. Сохраняем — UPDATE в БД (автоматически, без db.add())
    await db.commit()
    # 4. refresh — чтобы получить обновлённые данные из БД (вычисляемые поля, триггеры)
    await db.refresh(time_capsule)
    return TimeCapsuleCreateOut.model_validate(time_capsule)


@router.delete("/{capsule_id}", status_code=204)
async def delete_time_capsule(
    capsule_id: Annotated[int, Path(ge=1, description="id конкретной капсулы времени")],
    user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_async_db),
    ],
) -> None:
    """Удалить капсулу времени по id."""
    time_capsule = await db.scalar(
        select(TimeCapsule)
        .where(TimeCapsule.id == capsule_id)
        .where(TimeCapsule.user == user),
    )
    if not time_capsule:
        raise HTTPException(status_code=404, detail="Not found")
    # db.delete() — помечает объект на удаление. Реально удалится при commit.
    await db.delete(time_capsule)
    await db.commit()
