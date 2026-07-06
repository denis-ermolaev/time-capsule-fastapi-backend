"""conftest.py с изоляцией через очистку таблиц после каждого теста."""

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Annotated

import pytest
import time_machine
from httpx2 import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.app import app
from src.auth.schemas import TokenOut, UserCreate, UserOut
from src.database import Base
from src.db_depends import get_async_db
from src.settings import settings
from src.time_capsule.schemas import (
    TimeCapsuleCreateRequest,
    TimeCapsuleWithTextResponse,
)


# Переменные окружения ----
@pytest.fixture(autouse=True)
def test_with_monkeypatch(monkeypatch):  # noqa: ANN001
    """monkeypatch.setenv временно меняет переменную окружения.

    После теста pytest автоматически восстанавливает исходное значение.
    """
    # Ключ для генерации токенов
    monkeypatch.setenv(
        "SECRET_KEY",
        "617317fe59269d916d39382ee7552b881f20a3bbda0438f593300b2e5d7053d2",
    )
    # Проксирование отключено
    monkeypatch.setenv(
        "ROOT_PATH",
        "",
    )


# Клиент ----
@pytest.fixture
async def async_client(db_session):  # noqa: ANN001
    """Переопределяем зависимость БД на тестовую сессию."""

    async def override_get_async_db():  # noqa: ANN202
        yield db_session

    app.dependency_overrides[get_async_db] = override_get_async_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


# Асинхронная сессия ----
@pytest.fixture
async def async_engine():
    """Engine на каждый тест — изоляция event loop."""
    engine = create_async_engine(settings.database_url)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(async_engine):  # noqa: ANN001
    """Одна сессия на тест. После теста — очистка всех таблиц.

    Каждый тест начинает с пустой БД — полная изоляция.
    """
    async_session = async_sessionmaker(async_engine, expire_on_commit=False)

    async with async_session() as session:
        yield session
        await session.rollback()

    # Очищаем таблицы для следующего теста
    async with async_session() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(
                text(f"TRUNCATE TABLE {table.name} RESTART IDENTITY CASCADE"),
            )
        await session.commit()


@pytest.fixture(scope="session")
def event_loop():
    """Один event loop на всю сессию тестов (для async БД + httpx)."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Заморозка времени ----
@pytest.fixture(autouse=True)
def frozen_time():
    """Замораживает время для всех фикстур и тестов."""
    traveller = time_machine.travel("2026-01-01 00:00:00+00:00")
    yield traveller.start()
    traveller.stop()


# Фикстуры-фабрики ----
@pytest.fixture
async def get_auth_token(async_client: AsyncClient) -> Callable[[], Awaitable[str]]:
    """Регестрация пользователя и получения его токена по запросу."""
    # Регистрация — один раз
    await async_client.post(
        "/auth/register",
        json={
            "username": "test_user",
            "email": "test@example.com",
            "password": "strong_password",
        },
    )

    async def _get_auth_token() -> str:
        response = await async_client.post(
            "/auth/login",
            json={
                "username": "test_user",
                "email": "test@example.com",
                "password": "strong_password",
            },
        )
        return response.json()["access_token"]

    return _get_auth_token


@pytest.fixture
async def capsule_time(
    async_client: AsyncClient,
    get_auth_token: Callable[[], Awaitable[str]],
):
    """Создаёт и возвращает капсулу времени с датой открытия 2026-02-01 и датой создания 2026-01-01."""
    response = await async_client.post(
        "/time_capsules/",
        json={
            "title": "my first test time capsule",
            "is_private": True,
            "text": "example text",
            "lock_date": "2026-02-01 00:00:00+00:00",
        },
        headers={"Authorization": f"Bearer {await get_auth_token()}"},
    )
    return response.json()


@pytest.fixture
async def create_time_capsule(
    async_client: AsyncClient,
):
    """Фабрика для создания капсулы времени."""

    async def _create_time_capsule(
        data: TimeCapsuleCreateRequest,
        auth_token: str,
    ) -> TimeCapsuleWithTextResponse:
        response = await async_client.post(
            "/time_capsules/",
            json=json.loads(data.model_dump_json()),
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        return TimeCapsuleWithTextResponse(**response.json())

    return _create_time_capsule


type_create_user = Callable[
    [UserCreate],
    Awaitable[UserOut],
]


@pytest.fixture
async def create_user(
    async_client: AsyncClient,
):
    """Фабрика для создания пользователей."""

    async def _create_user(
        data: UserCreate,
    ) -> UserOut:
        response = await async_client.post(
            "/auth/register",
            json=json.loads(data.model_dump_json()),
        )
        return UserOut(**response.json())

    return _create_user


type_login_user = Callable[
    [UserCreate],
    Awaitable[Annotated[str, "access_token"]],
]


@pytest.fixture
async def login_user(
    async_client: AsyncClient,
):
    """Фабрика для входа по данным пользователя."""

    async def _login_user(
        data: UserCreate,
    ) -> Annotated[str, "access_token"]:
        response = await async_client.post(
            "/auth/login",
            json=json.loads(data.model_dump_json()),
        )
        return TokenOut(**response.json()).access_token

    return _login_user
