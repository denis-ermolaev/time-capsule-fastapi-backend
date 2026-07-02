"""Тесты капсул времени."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from httpx2 import AsyncClient


async def test_time_capsule_flow(async_client: AsyncClient):
    """Интеграционный тест: обычный путь пользователя при создании капсул времени."""
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
        json={"username": "example", "email": "example@mail.ru", "password": "example"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    access_token = data["access_token"]

    # Без авторизации
    response = await async_client.post(
        "/time_capsule/",
        json={
            "is_private": True,
            "text": "example text",
            "lock_date": "2028-08-02T20:53:52.808Z",
        },
    )
    assert response.status_code == 401

    response = await async_client.post(
        "/time_capsule/",
        json={
            "is_private": True,
            "text": "example text",
            "lock_date": "2028-08-02T20:53:52.808Z",
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 201

    response = await async_client.get(
        "/time_capsule/",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 201

    response = await async_client.get(
        "/time_capsule/",
    )
    assert response.status_code == 401
