"""Вспомогательные функции для авторизации."""

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Получить хэш-пароля."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Соотвествует ли пароль, его хэшу."""
    return pwd_context.verify(plain, hashed)
