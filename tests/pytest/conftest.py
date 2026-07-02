"""conftest.py с изоляцией через очистку таблиц после каждого теста."""

import pytest
from httpx2 import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.app import app  # ваше приложение
from src.database import Base  # ваша модель
from src.db_depends import get_async_db
from src.settings import settings  # ваши настройки


# Переменные окружения ----
@pytest.fixture(autouse=True)
def test_with_monkeypatch(monkeypatch):  # noqa: ANN001
    """monkeypatch.setenv временно меняет переменную окружения.

    После теста pytest автоматически восстанавливает исходное значение.
    """
    monkeypatch.setenv(
        "SECRET_KEY",
        "617317fe59269d916d39382ee7552b881f20a3bbda0438f593300b2e5d7053d2",
    )
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


@pytest.fixture(scope="session")
def async_engine():
    """Один engine на всю сессию. Создаёт таблицы."""
    return create_async_engine(settings.database_url)  # engine


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
            await session.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))
        await session.commit()
