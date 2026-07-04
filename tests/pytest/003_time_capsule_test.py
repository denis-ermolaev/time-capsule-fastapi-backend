"""Тесты капсул времени."""

from typing import TYPE_CHECKING

from src.logger import logger

if TYPE_CHECKING:
    from httpx2 import AsyncClient


async def test_time_capsule_flow(async_client: AsyncClient):
    """Интеграционный тест: обычный путь пользователя при использовании капсул времени."""
    # 1. Регестрация ----
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
    # ---------------------------------------------------------------------------- #

    # 2. Логин ----
    response = await async_client.post(
        "/auth/login",
        json={"username": "example", "email": "example@mail.ru", "password": "example"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    access_token = data["access_token"]
    # ---------------------------------------------------------------------------- #

    # 3. Создание капсулы ----
    ## Без авторизации -> 401
    response = await async_client.post(
        "/time_capsules/",
        json={
            "is_private": True,
            "text": "example text",
            "lock_date": "2028-08-02T20:53:52.808Z",
        },
    )
    assert response.status_code == 401

    ## С авторизацией -> 201
    response = await async_client.post(
        "/time_capsules/",
        json={
            "is_private": True,
            "text": "example text",
            "lock_date": "2028-08-02T20:53:52.808Z",
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 201
    # ---------------------------------------------------------------------------- #

    # 4. Получение всех капсул ----
    ## Без авторизации -> 401
    response = await async_client.get(
        "/time_capsules/",
    )
    assert response.status_code == 401

    ## С авторизацией -> 201
    response = await async_client.get(
        "/time_capsules/",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 201
    data = response.json()[0]  # Только для первой капсулы
    assert "id" in data
    assert "is_private" in data
    assert "lock_date" in data
    # ---------------------------------------------------------------------------- #

    # 5. Получение конкретной капсулы ----
    response = await async_client.get(
        "/time_capsules/1",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["is_private"]  # Приватная
    assert "lock_date" in data
    # ---------------------------------------------------------------------------- #

    # 6. Изменение конкретной капсулы ----
    response = await async_client.patch(
        "/time_capsules/1",
        json={
            "is_private": False,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert not data["is_private"]  # Публичная
    assert "lock_date" in data
    logger.debug("Ответ сервера", data=response.json())
    # ---------------------------------------------------------------------------- #

    # 7. Удаление конкретной капсулы ----
    response = await async_client.delete(
        "/time_capsules/1",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 204

    response = await async_client.get(
        "/time_capsules/1",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 404  # Капсулы больше нету
    # ---------------------------------------------------------------------------- #
