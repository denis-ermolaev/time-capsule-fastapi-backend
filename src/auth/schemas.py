"""Pydantic схемы для реализации аутентификации."""

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    """Входные данные при создании пользователя."""

    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    """Вход пользователя по email и паролю."""

    email: str
    password: str


class UserOut(BaseModel):
    """Выходные данные при создании пользователя."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    is_active: bool


class TokenOut(BaseModel):
    """Получение токенов."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105


class RefreshRequest(BaseModel):
    """Запрос на получение новых токенов по refresh токену."""

    refresh_token: str


class AccessRequest(BaseModel):
    """Запрос на проверку access токена."""

    access_token: str


class AccessResponse(BaseModel):
    """Ответ на проверку access токена."""

    message: str
