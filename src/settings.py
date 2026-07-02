"""Конфигурация приложения через переменные окружения.

Этот модуль предоставляет единую точку доступа к настройкам
проекта. Все конфигурационные параметры загружаются из .env-файла
или переменных окружения (см. pydantic-settings).

Attributes:
    settings: Глобальный экземпляр Settings, инициализированный
              при импорте модуля.

Typical usage example:
    >>> from src.config import settings
    >>> settings.db_host
    'test_db'
"""

from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация приложения из переменных окружения.

    Загружает настройки из .env-файла (см. model_config).
    Все поля имеют значения по умолчанию, пригодные для локальной
    разработки, но в production рекомендуется переопределить
    db_password через .env или переменные окружения.

    Attributes:
        db_name:     Название базы данных PostgreSQL.
        db_user:     Имя пользователя для подключения к БД.
        db_password: Пароль пользователя БД (пустая строка по умолчанию).
        db_host:     Хост сервера PostgreSQL (по умолч. localhost).
        db_port:     Порт сервера PostgreSQL (по умолч. 5432).
        root_path:   URL-префикс для FastAPI при размещении за reverse-proxy.
    """

    # База данных
    db_name: str = "api"
    db_user: str = "api"
    db_password: str = ""
    db_host: str = "localhost"
    db_port: int = 5432

    # Базовые настройки FastAPI
    root_path: str = ""

    # Авторизация
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("secret_key", mode="after")
    @classmethod
    def check_secret_key_not_empty(cls, v: str) -> str:
        """Секретный ключ для шифрования токенов не должен быть пустым и должен быть задан в `.env`."""
        if not v:
            msg = "Секретный ключ (SECRET_KEY) для шифрования токенов не должен быть пустым и должен быть задан в .env"
            raise ValueError(msg)
        return v

    @computed_field
    @property
    def database_url(self) -> str:
        """Создание ссылки на базу данных."""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


settings = Settings()
