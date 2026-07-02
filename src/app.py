"""Точка входа всего приложения."""

from fastapi import FastAPI

from src.auth.router import router as auth_router
from src.logger import logger
from src.settings import settings
from src.time_capsule.router import router as time_capsule_router

app = FastAPI(
    root_path=settings.root_path,
)

app.include_router(auth_router)
app.include_router(time_capsule_router)

logger.info("app_started", root_path=settings.root_path)
