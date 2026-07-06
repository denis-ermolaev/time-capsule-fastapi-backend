"""Тесты капсул времени."""

import datetime
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from conftest import type_create_user, type_login_user
from time_machine import Traveller

from src.auth.schemas import UserCreate
from src.logger import logger
from src.time_capsule.schemas import (
    TimeCapsuleCreateRequest,
    TimeCapsuleWithTextResponse,
)

if TYPE_CHECKING:
    from httpx2 import AsyncClient


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                              Интеграционный тест                             #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #


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
            "title": "my first time capsule",
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
            "title": "my first time capsule",
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
        params={
            "page": 1,
            "page_size": 10,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()  # Только для первой капсулы
    logger.debug("Ответ сервера", data=data)
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    data = data["items"][0]
    assert "id" in data
    assert "is_locked" in data
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


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                                  Тест фабрик                                 #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #


async def test_factory_create_time_capsule(
    create_time_capsule: Callable[
        [TimeCapsuleCreateRequest, str],
        Awaitable[TimeCapsuleWithTextResponse],
    ],
    create_user: type_create_user,
    login_user: type_login_user,
):
    """Тестирование фабрики по созданию капсул времени (create_time_capsule)."""
    user = UserCreate(
        username="test_user",
        email="test@example.com",
        password="strong124",  # noqa: S106
    )
    await create_user(user)
    access_token = await login_user(user)
    time_capsule = await create_time_capsule(
        TimeCapsuleCreateRequest(
            title="my first test time capsule",
            is_private=True,
            text="example text",
            lock_date=datetime.datetime.fromisoformat("2026-02-01 00:00:00"),
        ),
        access_token,
    )
    assert "text" in time_capsule.model_dump()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                           Открытие капсулы времени                           #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #


async def test_open_capsule(
    async_client: AsyncClient,
    get_auth_token: Callable[[], Awaitable[str]],
    capsule_time: dict,
    frozen_time: Traveller,
):
    """Тест на открытие капсулы времени для получения доступа к тексту."""
    assert "id" in capsule_time

    response = await async_client.post(
        f"/time_capsules/{capsule_time['id']}",
        headers={"Authorization": f"Bearer {await get_auth_token()}"},
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Not open"}

    frozen_time.shift(datetime.timedelta(days=365 * 1))

    response = await async_client.post(
        f"/time_capsules/{capsule_time['id']}",
        headers={"Authorization": f"Bearer {await get_auth_token()}"},
    )
    assert response.status_code == 200
    data = response.json()
    logger.debug("Ответ сервера", data=response.json())
    # Текст уже доступен
    assert data["text"] == capsule_time["text"]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                             Список капсул времени                            #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #


async def test_list_view(
    async_client: AsyncClient,
    create_time_capsule: Callable[
        [TimeCapsuleCreateRequest, str],
        Awaitable[TimeCapsuleWithTextResponse],
    ],
    create_user: type_create_user,
    login_user: type_login_user,
    frozen_time: Traveller,
):
    """Тестирование end-point для получения списка капсул времени."""
    # 1. Подготовка пользователей и их access_token ----
    first_user = UserCreate(
        username="test_user",
        email="test@example.com",
        password="strong124",  # noqa: S106
    )
    second_user = UserCreate(
        username="test_user_2",
        email="test_2@example.com",
        password="strong124",  # noqa: S106
    )
    await create_user(first_user)
    await create_user(second_user)
    first_access_token = await login_user(first_user)
    second_access_token = await login_user(second_user)

    # 2. Подготовка капсул времени ----
    # capsule_(Номер пользователя)_(Номер капсулы у этого пользователя)
    capsule_01_01 = await create_time_capsule(
        TimeCapsuleCreateRequest(
            title="Test#1 First User",
            is_private=True,
            text="example text: Test#1 First User",
            lock_date=datetime.datetime.fromisoformat("2026-10-01 00:00:00"),
        ),
        first_access_token,
    )
    capsule_02_01 = await create_time_capsule(
        TimeCapsuleCreateRequest(
            title="Test#1 Second User",
            is_private=True,
            text="example text: Test#1 Second User",
            lock_date=datetime.datetime.fromisoformat("2026-10-01 00:00:00"),
        ),
        second_access_token,
    )

    # Смещение времени
    frozen_time.shift(datetime.timedelta(days=36))
    # Обновление токенов
    first_access_token = await login_user(first_user)
    second_access_token = await login_user(second_user)

    capsule_01_02 = await create_time_capsule(
        TimeCapsuleCreateRequest(
            title="Test#2 First User",
            is_private=False,
            text="example text: Test#2 First User",
            lock_date=datetime.datetime.fromisoformat("2026-03-01 00:00:00"),
        ),
        first_access_token,
    )
    capsule_02_02 = await create_time_capsule(
        TimeCapsuleCreateRequest(
            title="Test#2 Second User",
            is_private=True,
            text="example text: Test#2 Second User",
            lock_date=datetime.datetime.fromisoformat("2026-03-01 00:00:00"),
        ),
        second_access_token,
    )
    # 3. Списки для тестов ----
    # Капсулы времени, которые видны первому пользователю
    first_user_can_view = [capsule_01_01.id, capsule_01_02.id]

    # Капсулы времени, которые видны второму пользователю
    second_user_can_view = [capsule_02_01.id, capsule_01_02.id, capsule_02_02.id]
    # Сортировка по порядку создания для второго пользователя
    order_by_create_date = [capsule_02_01.id, capsule_02_02.id]

    # 4. Тесты эндпоинта ----
    ## 4.1. Второму пользователю видно 3 капсулы времени (2-е своих и 1-у чужую) ----
    response = await async_client.get(
        "/time_capsules/",
        params={
            "page": 1,
            "page_size": 10,
        },
        headers={"Authorization": f"Bearer {second_access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert data["total"] == len(second_user_can_view)
    # ✅ Проверка, что чужая публичная капсула действительно публичная
    assert not next(
        i["is_private"] for i in data["items"] if i["id"] == capsule_01_02.id
    )

    ## 4.2. Первому пользователю видно 2 капсулы времени (только 2-е своих) ----
    response = await async_client.get(
        "/time_capsules/",
        params={
            "page": 1,
            "page_size": 10,
        },
        headers={"Authorization": f"Bearer {first_access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert data["total"] == len(first_user_can_view)

    ## 4.3. Сортировка: первой в списке идёт капсула, созданная позже & Только капсулы второго пользователя (2-е вместо 3-х) ----
    response = await async_client.get(
        "/time_capsules/",
        params={
            "page": 1,
            "page_size": 10,
            "order_by": "-create_date",
            "is_mine": True,
        },
        headers={"Authorization": f"Bearer {second_access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    logger.debug("Ответ сервера", data=data)
    # Сортировка наоборот
    assert order_by_create_date[::-1] == [i["id"] for i in data["items"]]
