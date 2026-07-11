"""Тесты авторизации."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from httpx2 import AsyncClient


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#         Интеграционный тест: обычный путь пользователя в авторизации.        #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #


async def test_auth_flow(async_client: AsyncClient):
    """Интеграционный тест: обычный путь пользователя в авторизации."""
    response = await async_client.post(
        "/auth/register",
        json={"username": "example", "email": "example@mail.ru", "password": "example"},
    )
    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "username": "example",
        "email": "example@mail.ru",
        "is_active": True,
    }

    response = await async_client.post(
        "/auth/login",
        json={"email": "example@mail.ru", "password": "example"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    refresh_token = data["refresh_token"]
    access_token = data["access_token"]

    response = await async_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "username": "example",
        "email": "example@mail.ru",
        "is_active": True,
    }

    response = await async_client.post(
        "/auth/access",
        json={"access_token": access_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert data == {"message": "ok"}

    response = await async_client.post(
        "/auth/access",
        json={"access_token": refresh_token},
    )
    assert response.status_code == 401

    response = await async_client.post(
        "/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert response.status_code == 401

    response = await async_client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
