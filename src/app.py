"""Точка входа всего приложения."""

from fastapi import FastAPI

from src.auth.router import router
from src.logger import logger
from src.settings import settings

app = FastAPI(
    root_path=settings.root_path,
)

app.include_router(router)

logger.info("app_started", root_path=settings.root_path)
