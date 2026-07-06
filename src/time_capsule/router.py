"""Энд поинты капсул времени."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import and_, desc, func, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import get_current_user
from src.auth.models import User
from src.db_depends import get_async_db
from src.time_capsule.models import TimeCapsule
from src.time_capsule.schemas import (
    TimeCapsuleCreateRequest,
    TimeCapsuleFilterParams,
    TimeCapsuleListResponce,
    TimeCapsuleResponce,
    TimeCapsuleUpdateRequest,
)

router = APIRouter(prefix="/time_capsules", tags=["time_capsules"])


@router.get("/", status_code=201)
async def get_time_capsules(  # noqa: C901, PLR0912
    db: Annotated[
        AsyncSession,
        Depends(get_async_db),
    ],
    user: Annotated[
        User,
        Depends(get_current_user),
    ],
    filters: Annotated[TimeCapsuleFilterParams, Depends()],
    page: int = 1,
    page_size: int = 10,
) -> TimeCapsuleListResponce:
    """Получить список капсул времени."""
    filters = filters.model_dump()

    # Сортировка
    order_by = TimeCapsule.create_date
    if filters.get("order_by"):
        raw_order_by = filters["order_by"].split("-")
        # Длинна 2, если был -, т.е desc
        # Иначе длинна 1, т.е asc
        if len(raw_order_by) == 2:  # noqa: PLR2004
            order_by = desc(getattr(TimeCapsule, raw_order_by[1]))
        else:
            order_by = getattr(TimeCapsule, raw_order_by[0])

    # Фильтры
    conditions = [true()]

    if filters.get("is_private"):
        conditions.append(TimeCapsule.is_private == filters["is_private"])

    if filters.get("is_other_users"):
        conditions.append(TimeCapsule.user != user)

    if filters.get("is_locked"):
        conditions.append(TimeCapsule.is_locked == filters["is_locked"])

    if filters.get("is_open"):
        conditions.append(TimeCapsule.is_open == filters["is_open"])

    if filters.get("locked_at_from"):
        conditions.append(TimeCapsule.lock_date >= filters["locked_at_from"])
    if filters.get("locked_at_to"):
        conditions.append(TimeCapsule.lock_date <= filters["locked_at_to"])

    if filters.get("created_at_from"):
        conditions.append(TimeCapsule.create_date >= filters["created_at_from"])
    if filters.get("created_at_to"):
        conditions.append(TimeCapsule.create_date <= filters["created_at_to"])

    if filters.get("title"):
        conditions.append(TimeCapsule.title.ilike(f"%{filters['title']}%"))

    total_stmt = select(func.count()).select_from(TimeCapsule)
    total = await db.scalar(total_stmt) or 0

    items = []
    capsules = (
        await db.scalars(
            select(TimeCapsule)
            .where(
                or_(
                    TimeCapsule.user == user,
                    and_(TimeCapsule.user != user, TimeCapsule.is_private == False),  # noqa: E712
                ),
            )
            .where(and_(*conditions))
            .order_by(order_by)
            .offset((page - 1) * page_size)
            .limit(page_size),
        )
    ).all()
    for i in capsules:
        i.text = ""  # Скрываем текст, для списка он не нужен
        items.append(TimeCapsuleResponce.model_validate(i))

    return TimeCapsuleListResponce(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=TimeCapsuleResponce, status_code=201)
async def create_time_capsule(
    time_capsule: TimeCapsuleCreateRequest,
    db: Annotated[
        AsyncSession,
        Depends(get_async_db),
    ],
    user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> TimeCapsuleResponce:
    """Создать капсулу времени."""
    db_time_capsule = TimeCapsule(
        user_id=user.id,
        user=user,
        **time_capsule.model_dump(),
    )
    db.add(db_time_capsule)
    await db.commit()
    await db.refresh(db_time_capsule)
    return TimeCapsuleResponce.model_validate(db_time_capsule)


@router.get("/{capsule_id}", response_model=TimeCapsuleResponce, status_code=200)
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
) -> TimeCapsuleResponce:
    """Получить капсулу времени по id."""
    time_capsule = (
        await db.scalars(
            select(TimeCapsule).where(TimeCapsule.id == capsule_id),
        )
    ).first()

    # Если капсула времени приватная и принадлежит другому пользователю -> 404
    if time_capsule and time_capsule.user != user and time_capsule.is_private:
        raise HTTPException(status_code=404, detail="Not found")
    if not time_capsule:
        raise HTTPException(status_code=404, detail="Not found")

    response = TimeCapsuleResponce.model_validate(time_capsule)

    if time_capsule.lock_date > datetime.now(UTC):
        # Текст капсулы ещё закрыт
        response.text = ""
    elif time_capsule.lock_date < datetime.now(UTC) and not time_capsule.is_open:
        time_capsule.open_date = datetime.now(UTC)
        time_capsule.is_open = True
        time_capsule.is_locked = False
        await db.commit()
        await db.refresh(time_capsule)
        response = TimeCapsuleResponce.model_validate(time_capsule)

    return response


@router.patch("/{capsule_id}", response_model=TimeCapsuleResponce, status_code=200)
async def update_time_capsule(
    capsule_id: Annotated[int, Path(ge=1, description="id конкретной капсулы времени")],
    update_data: TimeCapsuleUpdateRequest,
    user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_async_db),
    ],
) -> TimeCapsuleResponce:
    """Обновить капсулу времени по id."""
    # 1. Получаем текущую капсулу времени
    time_capsule = (
        await db.scalars(
            select(TimeCapsule)
            .where(TimeCapsule.id == capsule_id)
            .where(TimeCapsule.user == user),
        )
    ).first()
    if not time_capsule:
        raise HTTPException(status_code=404, detail="Not found")

    # 2. Меняем переданные поля
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(time_capsule, field, value)

    # 3. Сохраняем — UPDATE в БД (автоматически, без db.add())
    await db.commit()

    # 4. refresh — чтобы получить обновлённые данные из БД (вычисляемые поля, триггеры)
    await db.refresh(time_capsule)

    return TimeCapsuleResponce.model_validate(time_capsule)


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
    time_capsule = (
        await db.scalars(
            select(TimeCapsule)
            .where(TimeCapsule.id == capsule_id)
            .where(TimeCapsule.user == user),
        )
    ).first()
    if not time_capsule:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(time_capsule)
    await db.commit()
