"""База данных."""

from src.database import AsyncSessionLocal


async def get_async_db():  # noqa: ANN201
    """База данных."""
    async with AsyncSessionLocal() as session:
        yield session
