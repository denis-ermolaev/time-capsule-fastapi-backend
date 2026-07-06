# Testing Guide

> Полное руководство по тестированию FastAPI-приложений с pytest.
> Можно скопировать в любой проект и сразу запустить.

---

## Оглавление

- [1. Быстрый старт: скопируй и запусти](#1-быстрый-старт-скопируй-и-запусти)
- [2. Как работают фикстуры pytest](#2-как-работают-фикстуры-pytest)
- [3. conftest.py — готовый файл для любого FastAPI-проекта](#3-conftestpy--готовый-файл-для-любого-fastapi-проекта)
- [4. Изоляция тестов: работа с базой данных](#4-изоляция-тестов-работа-с-базой-данных)
- [5. Тестовые данные: как заполнять БД перед тестами](#5-тестовые-данные-как-заполнять-бд-перед-тестами)
- [6. Пограничные сценарии: что вручную не проверишь](#6-пограничные-сценарии-что-вручную-не-проверишь)
- [7. Переопределение переменных окружения для тестов](#7-переопределение-переменных-окружения-для-тестов)
- [8. Тестирование эндпоинтов FastAPI](#8-тестирование-эндпоинтов-fastapi)
- [9. Тестирование аутентификации и JWT](#9-тестирование-аутентификации-и-jwt)
- [10. Параметризация тестов](#10-параметризация-тестов)
- [11. conftest.py — расширенная версия](#11-conftestpy--расширенная-версия)
- [12. Запуск тестов](#12-запуск-тестов)
- [13. Настройка pyproject.toml](#13-настройка-pyprojecttoml)
- [Приложение A: Шпаргалка по assert](#приложение-a-шпаргалка-по-assert)
- [Приложение B: Установка зависимостей](#приложение-b-установка-зависимостей)

---

## 1. Быстрый старт: скопируй и запусти

### Шаг 1. Файл тестов

```python
# tests/test_001_base.py
from fastapi.testclient import TestClient
from your_app.main import app  # <-- замени на путь к твоему app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
```

### Шаг 2. Запуск

```bash
pytest tests/test_001_base.py -v
```

### Шаг 3. Если хочешь coverage

```bash
pip install pytest-cov
pytest --cov=your_app --cov-report=term-missing tests/
```

**Готово.** Это минимальный набор, с которого можно начать.

Если в проекте есть база данных — читай раздел [4. Изоляция тестов](#4-изоляция-тестов-работа-с-базой-данных).

---

## 2. Как работают фикстуры pytest

Фикстура — это функция, которая подготавливает данные для теста. Pytest сам решает, когда её вызвать и когда «прибраться».

### Простейшая фикстура

```python
import pytest


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from your_app.main import app
    return TestClient(app)


def test_something(client):      # pytest видит параметр client,
    response = client.get("/")   # находит фикстуру client,
    ...                          # вызывает её и передаёт результат в тест.
```

### Жизненный цикл фикстуры

```python
@pytest.fixture
def resource():
    print("🟢 setup — создаём ресурс")
    obj = create_expensive_resource()
    yield obj                          # ← здесь тест использует фикстуру
    print("🔴 teardown — уничтожаем ресурс")
    obj.cleanup()


def test_one(resource):
    print("   test_one работает")
    assert resource.is_ready


def test_two(resource):
    print("   test_two работает")
    assert resource.is_ready
```

Вывод в консоль:

```
🟢 setup — создаём ресурс
   test_one работает
🔴 teardown — уничтожаем ресурс
🟢 setup — создаём ресурс
   test_two работает
🔴 teardown — уничтожаем ресурс
```

**Фикстура создаётся заново для каждого теста** (scope="function"). Это изоляция.

### Scope — как часто пересоздавать фикстуру

| Scope        | Когда создаётся             | Когда уничтожается  | Для чего подходит                        |
| ------------ | ----------------------------------------- | ------------------------------------ | ------------------------------------------------------- |
| `function` | Перед каждым тестом      | После каждого теста | Изоляция тестов (по умолчанию) |
| `class`    | Перед тестами в классе | После класса              | Группировка тестов                     |
| `module`   | Перед тестами в файле   | После файла                | Тяжёлые ресурсы на файл             |
| `session`  | Один раз за прогон         | После всех тестов     | Очень тяжёлые (БД, клиенты)        |

```python
@pytest.fixture(scope="session")
def db_engine():
    """Один engine на всю сессию тестов."""
    engine = create_async_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()
```

### autouse — фикстура без явного запроса

Если у фикстуры есть `autouse=True`, она применяется к **каждому тесту** автоматически. Параметр в тест добавлять не нужно.

```python
@pytest.fixture(autouse=True)
def clean_db_between_tests():
    """Очищает БД после каждого теста. Тесты не подозревают об этом."""
    yield
    wipe_database()
```

Используй `autouse` осторожно — он делает неявные действия, что усложняет понимание тестов.

---

## 3. conftest.py — готовый файл для любого FastAPI-проекта

Файл `conftest.py` pytest находит автоматически во всех папках. Фикстуры из него доступны во всех тестах без импорта.

Создай `tests/conftest.py`:

```python
"""Фикстуры для всех тестов проекта."""

import pytest
from fastapi.testclient import TestClient
from your_app.main import app  # замени на свой импорт


@pytest.fixture
def client():
    """TestClient для HTTP-запросов без запуска сервера.

    Пригодится в 99% тестов. Быстрый, синхронный,
    не требует uvicorn.
    """
    return TestClient(app)
```

Всё. Теперь в любом файле `tests/test_*.py` можно писать:

```python
def test_something(client):
    response = client.get("/some-endpoint")
    assert response.status_code == 200
```

### Что можно добавить в conftest.py

| Фикстура | Назначение                                                               | Описание                           |
| ---------------- | ---------------------------------------------------------------------------------- | ------------------------------------------ |
| `client`       | Базовый HTTP-клиент                                                   | Всегда                               |
| `auth_headers` | `Authorization: Bearer <token>` для защищённых эндпоинтов | См. раздел 9                       |
| `db_session`   | Сессия БД с изоляцией                                            | См. раздел 4 и раздел 11    |
| `async_client` | `httpx.AsyncClient` для async-тестов                                    | Если есть async-эндпоинты |

---

## 4. Изоляция тестов: работа с базой данных

### Проблема

Тест №1 создаёт пользователя `alice`. Тест №2 пытается создать пользователя `alice` — и получает 400, потому что он уже есть.

**Тесты не должны влиять друг на друга.**

### Решение

#### Вариант A: тестовая БД в Docker + очистка (рекомендуется)

Поднимается отдельный PostgreSQL + тестовый контейнер. После каждого теста — полная очистка таблиц.

**docker-compose.yml:**

```yaml
services:
  test_db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: test_db
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
    tmpfs: /var/lib/postgresql/data  # данные в RAM, быстро и чисто
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test_user -d test_db"]

  test_runner:
    build: .
    depends_on:
      test_db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://test_user:test_pass@test_db:5432/test_db
    volumes:
      - .:/app
    command: pytest tests/ -v
```

**conftest.py для этого варианта:**

```python
"""conftest.py с изоляцией через очистку таблиц после каждого теста."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from your_app.database import Base      # ваша модель
from your_app.main import app           # ваше приложение
from your_app.settings import settings  # ваши настройки

# ---------- Клиент ----------

@pytest.fixture
def client():
    return TestClient(app)


# ---------- Асинхронная сессия ----------

@pytest.fixture(scope="session")
def async_engine():
    """Один engine на всю сессию. Создаёт таблицы."""
    engine = create_async_engine(settings.database_url)
    return engine


@pytest.fixture
async def db_session(async_engine):
    """Одна сессия на тест. После теста — очистка всех таблиц.

    Каждый тест начинает с пустой БД — полная изоляция.
    """
    async_session = async_sessionmaker(async_engine, expire_on_commit=False)

    async with async_session() as session:
        yield session
        await session.rollback()

    # Очищаем таблицы для следующего теста
    async with async_session() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))
        await session.commit()
```

#### Вариант B: SQLite в памяти (для быстрых тестов)

Если проект небольшой — можно использовать SQLite вместо PostgreSQL.

```python
"""conftest.py с SQLite в памяти — вообще не нужен Docker."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from your_app.database import Base
from your_app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    """Каждый тест получает чистую БД в памяти."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)

    session = sessionmaker(bind=engine)()
    yield session

    session.close()
    Base.metadata.drop_all(engine)
```

#### Вариант B1: SQLite + monkeypatch (переопределение зависимости)

Лучший способ для unit-тестов — подменить зависимость БД через `app.dependency_overrides`:

```python
"""conftest.py с подменой зависимости БД на SQLite в памяти."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from your_app.database import Base, get_db
from your_app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL)


def override_get_db():
    """Подмена зависимости get_db."""
    TestSessionLocal = sessionmaker(bind=test_engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    """Создать таблицы перед тестом, удалить после."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)
```

#### Вариант C: Транзакционная изоляция (продвинутый)

Каждый тест оборачивается в транзакцию, которая **откатывается** после завершения. Данные физически не записываются.

```python
"""conftest.py с транзакционной изоляцией — самый надёжный вариант."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from your_app.database import Base
from your_app.main import app
from your_app.settings import settings

# ---------- Клиент ----------

@pytest.fixture
def client():
    return TestClient(app)


# ---------- Engine ----------

@pytest.fixture(scope="session")
def async_engine():
    """Один engine на все тесты."""
    engine = create_async_engine(settings.database_url)
    return engine


# ---------- Транзакционная изоляция ----------

@pytest.fixture
async def db_session(async_engine):
    """Каждый тест работает внутри транзакции, которая откатывается.

    Как это работает:
    1. Создаём подключение к БД (connection)
    2. Начинаем транзакцию (BEGIN)
    3. Создаём сессию, привязанную к этой транзакции
    4. Отдаём сессию тесту
    5. После завершения теста: ROLLBACK
       — все INSERT/UPDATE/DELETE теста отменяются
       — БД возвращается к исходному состоянию
    6. Закрываем подключение

    Преимущество: не нужно TRUNCATE таблиц.
    Недостаток: если тест вызывает session.commit(),
    транзакция фиксируется и откат не сработает.
    """
    async with async_engine.connect() as connection:
        async with connection.begin() as transaction:
            session = AsyncSession(bind=connection, expire_on_commit=False)
            yield session
            # После yield — автоматический ROLLBACK
```

---

## 5. Тестовые данные: как заполнять БД перед тестами

Это самый важный раздел. Ты должен уметь быстро создавать тестовые объекты в БД, чтобы тестировать разные сценарии.

### Способ 1: фикстуры-фабрики (рекомендуется)

Самый гибкий способ — пишем фикстуру, которая создаёт объекты в БД и возвращает их.

```python
# tests/conftest.py

@pytest.fixture
async def sample_user(db_session):
    """Создаёт одного пользователя и возвращает его.

    Использование:
        async def test_something(sample_user):
            assert sample_user.username == "test_user"
    """
    from your_app.auth.utils import hash_password
    from your_app.auth.models import User

    user = User(
        username="test_user",
        email="test@example.com",
        hashed_password=hash_password("secret123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
```

### Способ 2: фабрика с параметрами

Одна фикстура — много разных пользователей.

```python
@pytest.fixture
async def user_factory(db_session):
    """Фабрика пользователей. Создаёт пользователя с любыми параметрами.

    Использование:
        async def test_something(user_factory):
            alice = await user_factory(username="alice", email="alice@test.com")
            bob = await user_factory(username="bob", email="bob@test.com")
    """

    async def _make_user(
        username: str = "default_user",
        email: str = "default@example.com",
        password: str = "default_pass",
        is_active: bool = True,
    ) -> User:
        from your_app.auth.utils import hash_password
        from your_app.auth.models import User

        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            is_active=is_active,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _make_user
```

**Использование в тестах:**

```python
async def test_two_users(user_factory):
    """Создаём двух пользователей с разными данными."""
    alice = await user_factory(username="alice", email="alice@test.com")
    bob = await user_factory(username="bob", email="bob@test.com")

    assert alice.id != bob.id
    assert alice.username == "alice"
    assert bob.username == "bob"


async def test_inactive_user(user_factory):
    """Неактивный пользователь."""
    user = await user_factory(username="ghost", is_active=False)
    assert user.is_active is False
```

### Способ 3: factory_boy (для сложных проектов)

Самая мощная библиотека для тестовых данных. Требует установки: `pip install factory_boy`.

```python
# tests/factories.py

import factory
from your_app.auth.models import User
from your_app.auth.utils import hash_password


class UserFactory(factory.Factory):
    """Фабрика пользователей. Автоматически заполняет поля."""
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user_{n:03d}")
    email = factory.Sequence(lambda n: f"user_{n:03d}@example.com")
    hashed_password = factory.LazyFunction(lambda: hash_password("default_pass"))
    is_active = True
```

**Использование в тестах:**

```python
async def test_user_factory(db_session):
    # Создаёт пользователя с дефолтными данными
    user = UserFactory.__class__()  # это не сработает, нужно build/BUILD
    # Правильный синтаксис factory_boy:
    user = UserFactory()  # ← объект создан, но не в БД!
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    print(user.username)  # user_001
    print(user.email)     # user_001@example.com
```

**factory_boy + SQLAlchemy (через `factory.alchemy`):**

```python
# tests/factories.py
import factory
from factory.alchemy import SQLAlchemyModelFactory
from your_app.auth.models import User
from your_app.auth.utils import hash_password


class UserFactory(SQLAlchemyModelFactory):
    """Фабрика, которая сразу сохраняет в БД.

    Использование:
        user = UserFactory()  # создано и сохранено в БД
        user = UserFactory(username="custom")  # с переопределением
    """
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"  # сохранять сразу

    username = factory.Sequence(lambda n: f"user_{n:03d}")
    email = factory.Sequence(lambda n: f"user_{n:03d}@example.com")
    hashed_password = factory.LazyFunction(lambda: hash_password("default_pass"))
    is_active = True
```

**Где хранить фабрики:**

```
tests/
├── factories.py          # ← все фабрики в одном файле
├── conftest.py
├── test_001_base.py
├── test_002_auth.py
└── ...
```

### Способ 4: JSON / YAML — фикстуры-файлы

Для статических данных, которые не меняются от теста к тесту.

```json
# tests/fixtures/users.json
[
    {
        "username": "alice",
        "email": "alice@example.com",
        "password": "secret123",
        "is_active": true
    },
    {
        "username": "bob",
        "email": "bob@example.com",
        "password": "secret456",
        "is_active": false
    }
]
```

```python
import json
from pathlib import Path


async def test_load_fixture(db_session):
    with open(Path(__file__).parent / "fixtures" / "users.json") as f:
        users_data = json.load(f)

    from your_app.auth.utils import hash_password
    from your_app.auth.models import User

    for data in users_data:
        user = User(
            username=data["username"],
            email=data["email"],
            hashed_password=hash_password(data["password"]),
            is_active=data["is_active"],
        )
        db_session.add(user)
    await db_session.commit()
```

### Способ 5: Model Bakery — лёгкая альтернатива factory_boy

Если не хочешь писать классы фабрик — library model_bakery (бывш. model_mommy) создаёт объекты автоматически.

```bash
pip install model_bakery
```

```python
from model_bakery import baker


async def test_model_bakery(db_session):
    from your_app.auth.models import User

    # Создаёт пользователя со случайными данными
    user = baker.make(User, _session=db_session)
    print(user.username)   # какой-то случайный username
    print(user.email)      # какой-то случайный email

    # С переопределением полей
    user = baker.make(User, _session=db_session, username="fix", is_active=False)
    assert user.username == "fix"
    assert user.is_active is False

    # Создать несколько
    users = baker.make(User, _session=db_session, _quantity=5)
    assert len(users) == 5
```

### Сводка по инструментам

| Инструмент          | Когда использовать                                        | Нужно ли писать классы |
| ----------------------------- | -------------------------------------------------------------------------- | ----------------------------------------- |
| Фикстура-объект | Один-два объекта для нескольких тестов    | Нет                                    |
| Фабрика-функция | Много объектов с разными параметрами       | Нет (одна функция)          |
| factory_boy                   | Сложная логика, связанные объекты             | Да                                      |
| model_bakery                  | «Просто создай что-нибудь»                          | Нет                                    |
| JSON/YAML файлы          | Статические данные (справочники, валюты) | Нет (файлы)                       |

---

## 6. Пограничные сценарии: что вручную не проверишь

Вручную сложно проверить ситуации, которые требуют точного времени, больших объёмов данных или специальных условий. Тесты с этим справляются легко.

### 6.1 Заморозка времени (time-dependent логика)

Самая частая потребность: «капсулу можно открыть только после unlock_at».

Для этого используй библиотеку `freezegun`:

```bash
pip install freezegun
```

```python
from freezegun import freeze_time


@freeze_time("2025-01-01 12:00:00")
def test_capsule_not_unlocked_before_date(client, auth_headers):
    """Капсула с unlock_at в будущем — недоступна."""
    # Создаём капсулу, которая откроется в 2026 году
    response = client.post(
        "/capsules/",
        headers=auth_headers,
        json={"content": "secret", "unlock_at": "2026-06-01T00:00:00Z"},
    )
    capsule_id = response.json()["id"]

    # Пытаемся открыть — сейчас 2025 год, рано
    response = client.get(f"/capsules/{capsule_id}", headers=auth_headers)
    assert response.status_code == 403
    assert "not yet unlocked" in response.json()["detail"]


@freeze_time("2026-06-01 12:00:00")
def test_capsule_unlocked_after_date(client, auth_headers):
    """После unlock_at капсула доступна."""
    # Создаём капсулу с unlock_at = 2026-06-01
    response = client.post(
        "/capsules/",
        headers=auth_headers,
        json={"content": "secret", "unlock_at": "2026-06-01T00:00:00Z"},
    )
    capsule_id = response.json()["id"]

    # Открываем — сейчас 2026 год, можно
    response = client.get(f"/capsules/{capsule_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["content"] == "secret"


@freeze_time("2025-06-15 00:00:00")
def test_capsule_unlock_boundary_midnight(client, auth_headers):
    """Граничный случай: ровно в полночь unlock_at."""
    # unlock_at = сегодня в 00:00 — уже можно
    response = client.post(
        "/capsules/",
        headers=auth_headers,
        json={"content": "secret", "unlock_at": "2025-06-15T00:00:00Z"},
    )
    capsule_id = response.json()["id"]

    response = client.get(f"/capsules/{capsule_id}", headers=auth_headers)
    assert response.status_code == 200
```

#### Альтернатива: time-machine (быстрее freezegun)

```bash
pip install time-machine
```

```python
import time_machine


@time_machine.travel("2025-01-01 12:00:00")
def test_with_time_machine(client, auth_headers):
    """Быстрее, чем freezegun."""
    response = client.get("/capsules/today")
    assert response.json()["date"] == "2025-01-01"
```

### 6.2 Большие объёмы данных (пагинация, производительность)

```python
import pytest


async def test_pagination(user_factory):
    """Проверка пагинации: 100 пользователей, страница по 20."""
    # Создаём 100 пользователей
    for i in range(100):
        await user_factory(username=f"user_{i:03d}")

    # Проверяем пагинацию — это уже через API-тест с client
    # (здесь показана логика создания большого объёма данных)
    assert True  # заглушка, реальный тест — ниже


def test_list_users_pagination(client, auth_headers, user_factory):
    """API возвращает пользователей постранично."""
    # Сначала нужно создать пользователей в БД.
    # Если используется синхронный TestClient, то db_session не подойдёт.
    # Придётся создавать через API или использовать хитрость с
    # dependency_overrides + синхронная сессия.
    # Подробнее — в разделе 5, способ 2 фабрика-функция.
    pass
```

### 6.3 Граничные длины строк

```python
import pytest


@pytest.mark.parametrize(
    "username, expected_status",
    [
        ("a", 201),                           # минимальная длина
        ("a" * 50, 201),                      # ровно 50 символов
        ("a" * 100, 201),                     # ровно 100 (максимум по модели)
        ("a" * 101, 422),                     # 101 символ — превышение
        ("valid_user_name_123", 201),         # обычное имя
        ("", 422),                            # пустая строка
        ("   ", 422),                         # только пробелы
        ("user name", 201),                   # с пробелом

        # Спецсимволы — эмуляция SQL-инъекции
        ("'; DROP TABLE users; --", 201),     # попытка SQL-инъекции
        ("<script>alert(1)</script>", 201),   # XSS-попытка

        # Unicode
        ("ユーザー名", 201),                   # японский
        ("имя_пользователя", 201),            # кириллица
        ("اسم_المستخدم", 201),                # арабский
    ],
    ids=[
        "min_length",
        "exact_50",
        "max_length",
        "overflow",
        "normal",
        "empty",
        "whitespace",
        "with_space",
        "sql_injection",
        "xss",
        "japanese",
        "cyrillic",
        "arabic",
    ],
)
def test_username_boundaries(client, username, expected_status):
    """Проверка граничных значений username при регистрации."""
    response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": "test@example.com",
            "password": "strong_password",
        },
    )
    assert response.status_code == expected_status
```

### 6.4 Конфликты уникальности

```python
async def test_duplicate_username(db_session, user_factory):
    """Попытка создать пользователя с существующим username — ошибка."""
    from sqlalchemy.exc import IntegrityError
    from your_app.auth.models import User
    from your_app.auth.utils import hash_password

    # Создаём первого пользователя
    await user_factory(username="unique_user")

    # Пытаемся создать второго с тем же username
    duplicate = User(
        username="unique_user",
        email="another@example.com",
        hashed_password=hash_password("pass"),
    )
    db_session.add(duplicate)

    with pytest.raises(IntegrityError):
        await db_session.commit()
```

### 6.5 Конкурентные запросы (race conditions)

```python
import asyncio


async def test_concurrent_registration(async_client):
    """Два одновременных запроса на регистрацию с одним username.

    Один должен пройти (201), второй — упасть (400 или 409).
    """
    payload = {
        "username": "concurrent_user",
        "email": "concurrent@example.com",
        "password": "strong_pass",
    }

    # Запускаем два запроса одновременно
    resp1, resp2 = await asyncio.gather(
        async_client.post("/auth/register", json=payload),
        async_client.post("/auth/register", json=payload),
    )

    # Один 201, другой 400/409
    statuses = {resp1.status_code, resp2.status_code}
    assert statuses == {201, 400} or statuses == {201, 409}


async def test_concurrent_token_refresh(async_client, user_factory, db_session):
    """Одновременный refresh токена двумя запросами."""
    user = await user_factory()

    # Логинимся — получаем refresh_token
    resp = await async_client.post(
        "/auth/login",
        json={"username": user.username, "email": user.email, "password": "default_pass"},
    )
    refresh_token = resp.json()["refresh_token"]

    # Два одновременных refresh
    resp1, resp2 = await asyncio.gather(
        async_client.post("/auth/refresh", json={"refresh_token": refresh_token}),
        async_client.post("/auth/refresh", json={"refresh_token": refresh_token}),
    )

    # Оба должны пройти (refresh_token можно использовать多次 до истечения)
    assert resp1.status_code == 200
    assert resp2.status_code == 200
```

### 6.6 Истечение и невалидность токенов

```python
from freezegun import freeze_time
from your_app.auth.jwt import create_access_token


def test_expired_access_token(client):
    """Просроченный access_token — 401."""
    with freeze_time("2025-01-01 12:00:00"):
        # Создаём токен, который «сейчас» валиден
        token = create_access_token({"sub": "1"})

    # Отматываем время вперёд на 10 лет
    with freeze_time("2035-01-01 12:00:00"):
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            "/auth/access",
            json={"access_token": token},
        )
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()


def test_malformed_token(client):
    """Битый токен — 401."""
    test_cases = [
        "not-a-token",
        "eyJ.eyJ.eyJ",                      # невалидный JWT
        "Bearer ",                           # пустой токен
        "",                                  # пустая строка
        "   ",                               # пробелы
        "null",                              # строка null
        "undefined",                         # строка undefined
    ]

    for bad_token in test_cases:
        headers = {"Authorization": f"Bearer {bad_token}"}
        response = client.get("/items/", headers=headers)
        assert response.status_code == 401, f"Failed for token: {bad_token!r}"
```

### 6.7 Мокирование внешних API

Если твой эндпоинт вызывает внешний сервис (например, отправка email, платёжный шлюз):

```python
from unittest.mock import patch


@patch("your_app.services.email.send_welcome_email")
async def test_register_sends_email(mock_send, async_client):
    """При регистрации отправляется приветственное письмо."""
    resp = await async_client.post(
        "/auth/register",
        json={"username": "new_user", "email": "new@test.com", "password": "pass"},
    )
    assert resp.status_code == 201
    mock_send.assert_called_once()  # проверяем, что функция была вызвана
    mock_send.assert_called_with("new@test.com")  # с правильным аргументом


@patch("your_app.services.payment.charge_card")
async def test_payment_failure_returns_error(mock_charge, async_client):
    """Ошибка платежного шлюза — 402 Payment Required."""
    mock_charge.side_effect = ConnectionError("Payment gateway timeout")

    resp = await async_client.post(
        "/payments/",
        json={"card": "4111-1111-1111-1111", "amount": 100},
    )
    assert resp.status_code == 502  # Bad Gateway
    assert "payment" in resp.json()["detail"].lower()
```

### 6.8 Пустые состояния (empty states)

```python
def test_empty_list(client, auth_headers):
    """Когда в БД нет элементов — возвращается пустой список."""
    response = client.get("/items/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []  # или {"items": [], "total": 0}


def test_get_nonexistent_item(client, auth_headers):
    """Запрос несуществующего ID — 404."""
    response = client.get("/items/99999", headers=auth_headers)
    assert response.status_code == 404


def test_nonexistent_user_login(client):
    """Логин с несуществующим пользователем — 401."""
    response = client.post(
        "/auth/login",
        json={
            "username": "nobody_exists",
            "email": "nobody@test.com",
            "password": "whatever",
        },
    )
    assert response.status_code == 401
```

### 6.9 Специальные значения полей

```python
@pytest.mark.parametrize(
    "email, expected_status",
    [
        ("test@example.com", 201),           # обычный email
        ("test+alias@example.com", 201),     # с плюсом (Gmail-style)
        ("test@subdomain.example.com", 201), # поддомен
        ("test@example.co.uk", 201),         # многоуровневый домен
        ("тест@пример.рф", 201),             # кириллический домен
        ("a@b.c", 201),                      # минимальный валидный email
        ("@example.com", 422),               # без локальной части
        ("test@", 422),                      # без домена
        ("test@.com", 422),                  # домен без имени
        ("test@example", 422),               # домен без TLD
    ],
    ids=[
        "normal",
        "plus_alias",
        "subdomain",
        "uk_domain",
        "cyrillic_domain",
        "minimal",
        "no_local",
        "no_domain",
        "empty_domain_name",
        "no_tld",
    ],
)
def test_email_validation(client, email, expected_status):
    """Валидация email при регистрации."""
    response = client.post(
        "/auth/register",
        json={"username": "test_user", "email": email, "password": "strong_pass"},
    )
    assert response.status_code == expected_status
```

---

## 7. Переопределение переменных окружения для тестов

Твоё приложение читает настройки из `.env` через `pydantic-settings` (или `os.getenv`). В тестах эти переменные можно и нужно переопределять.

### Способ 1: Фикстура temp_env (через os.environ)

Самое простое — временно подменить переменную окружения через `os.environ`.

```python
import os
import pytest


@pytest.fixture
def temp_env():
    """Временно подменяет DATABASE_URL на SQLite в памяти.

    После теста возвращает оригинальное значение.
    """
    original_value = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    yield
    if original_value is None:
        del os.environ["DATABASE_URL"]
    else:
        os.environ["DATABASE_URL"] = original_value
```

**Использование:**

```python
def test_with_sqlite(client, temp_env):
    """Тест работает с SQLite вместо PostgreSQL.

    Фикстура temp_env подменяет DATABASE_URL до того,
    как приложение инициализирует engine.
    """
    response = client.get("/items/")
    assert response.status_code == 200
```

**Важно:** фикстура должна быть указана как параметр теста. pytest вызовет её до выполнения теста, так что `os.environ` изменится до того, как код начнёт читать конфигурацию.

### Способ 2: monkeypatch (встроенная фикстура pytest)

pytest предоставляет встроенную фикстуру `monkeypatch`. Она безопаснее, чем ручное `os.environ`, и автоматически всё восстанавливает.

```python
@pytest.fixture
def test_with_monkeypatch(monkeypatch):
    """monkeypatch.setenv временно меняет переменную окружения.

    После теста pytest автоматически восстанавливает исходное значение.
    """
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "test_secret_key_12345")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1")  # токен живет 1 минуту

    # Теперь при создании Settings() будут использоваться эти значения
    from your_app.settings import settings
    assert settings.database_url == "sqlite:///:memory:"
    assert settings.secret_key == "test_secret_key_12345"
    assert settings.access_token_expire_minutes == 1
```

**Другие методы monkeypatch:**

| Метод                                   | Что делает                                                |
| -------------------------------------------- | ------------------------------------------------------------------ |
| `monkeypatch.setenv(name, value)`          | Устанавливает переменную окружения |
| `monkeypatch.delenv(name)`                 | Удаляет переменную окружения             |
| `monkeypatch.setattr(obj, name, value)`    | Подменяет атрибут объекта                   |
| `monkeypatch.setitem(mapping, key, value)` | Подменяет элемент словаря                   |

### Способ 3: dependency_overrides (для FastAPI-зависимостей)

Лучший способ подменить именно FastAPI-зависимость (например, `get_db`):

```python
from your_app.deps import get_db


def override_get_db():
    """Тестовая БД вместо настоящей."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client_with_test_db():
    """Клиент с подменённой зависимостью БД."""
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)
```

### Что переопределять в тестах

| Переменная            | Зачем переопределять                                                | Пример значения |
| ------------------------------- | -------------------------------------------------------------------------------------- | ----------------------------- |
| `DATABASE_URL`                | Чтобы тесты не трогали реальную БД                        | `sqlite:///:memory:`        |
| `SECRET_KEY`                  | Фиксированный ключ для JWT                                         | `test_secret_key`           |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Сделать токены «быстроистекающими» для тестов | `1`                         |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | Аналогично                                                                   | `1`                         |
| `REDIS_URL`                   | Не подключаться к настоящему Redis                            | `redis://localhost:6380`    |
| `SMTP_HOST`                   | Не отправлять реальные письма                                | `localhost`                 |
| `LOG_LEVEL`                   | Меньше логов в тестах                                                | `ERROR`                     |

### Фикстура с несколькими переменными

```python
@pytest.fixture
def test_env(monkeypatch):
    """Одним вызовом настраивает всё тестовое окружение."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "testing_key")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1")
    monkeypatch.setenv("LOG_LEVEL", "ERROR")
    yield
    # monkeypatch всё восстанавливает автоматически


def test_with_full_env(client, test_env):
    """Все переменные окружения настроены для теста."""
    from your_app.settings import settings
    assert settings.database_url == "sqlite:///:memory:"
    assert settings.secret_key == "testing_key"
```

### Структура теста

```python
def test_<что_тестируем>(<фикстуры>):
    """Описание: что проверяем, какой результат ожидаем."""
    # 1. Arrange — подготовка данных
    # 2. Act — запрос к эндпоинту
    # 3. Assert — проверка результата
```

Пример:

```python
def test_create_item(client):
    """POST /items/ должен вернуть 201 и созданный объект."""
    # Arrange
    payload = {"name": "test_item", "price": 100.0}

    # Act
    response = client.post("/items/", json=payload)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test_item"
    assert data["price"] == 100.0
    assert "id" in data
```

### HTTP-методы

```python
# POST — создание
response = client.post("/items/", json={"name": "new"})
assert response.status_code == 201

# GET — получение списка
response = client.get("/items/")
assert response.status_code == 200
assert isinstance(response.json(), list)

# GET /{id} — получение одного
response = client.get("/items/1")
assert response.status_code == 200

# PUT /{id} — полное обновление
response = client.put("/items/1", json={"name": "updated", "price": 200})
assert response.status_code == 200

# PATCH /{id} — частичное обновление
response = client.patch("/items/1", json={"price": 150})
assert response.status_code == 200

# DELETE /{id} — удаление
response = client.delete("/items/1")
assert response.status_code == 204  # No Content
```

### Assert — проверка ответа

```python
# Статус-код
assert response.status_code == 200

# Тело ответа — точное совпадение
assert response.json() == {"id": 1, "name": "test"}

# Тело ответа — частичная проверка
data = response.json()
assert data["name"] == "test"
assert data.get("optional_field") is None

# Типы данных
assert isinstance(data["id"], int)
assert isinstance(data["created_at"], str)

# Вложенные структуры
assert "items" in data
assert len(data["items"]) > 0
assert data["items"][0]["active"] is True

# Заголовки
assert response.headers["content-type"] == "application/json"
```

### Тестирование ошибок

```python
def test_get_nonexistent_item(client):
    """GET /items/999 — несуществующий объект."""
    response = client.get("/items/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"


def test_create_invalid_data(client):
    """POST /items/ с невалидными данными."""
    response = client.post("/items/", json={"name": ""})
    # 422 — Validation Error от FastAPI/Pydantic
    assert response.status_code == 422
    # В ответе — детали валидации
    errors = response.json()["detail"]
    assert any(err["loc"] == ["body", "name"] for err in errors)
```

---

## 9. Тестирование аутентификации и JWT

### Переопределение Secret Key для тестов

В тестовом окружении должен быть свой `SECRET_KEY`. Самый простой способ — задать в `docker-compose.yml`:

```yaml
services:
  test_runner:
    environment:
      - SECRET_KEY=test_secret_key_12345
```

### Фикстура auth_headers — готовый код

```python
# Добавь в tests/conftest.py

@pytest.fixture
def auth_headers(client):
    """Регистрирует пользователя, логинит его и возвращает заголовки.

    Используй в тестах, которым нужна авторизация:
        def test_protected(client, auth_headers):
            response = client.get("/secret", headers=auth_headers)
    """
    # Регистрация
    client.post(
        "/auth/register",
        json={
            "username": "test_user",
            "email": "test@example.com",
            "password": "strong_password",
        },
    )

    # Логин — получаем токен
    resp = client.post(
        "/auth/login",
        json={
            "username": "test_user",
            "email": "test@example.com",
            "password": "strong_password",
        },
    )
    token = resp.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}
```

### Использование auth_headers

```python
def test_protected_endpoint(client, auth_headers):
    """Авторизованный запрос — 200."""
    response = client.get("/items/", headers=auth_headers)
    assert response.status_code == 200


def test_protected_endpoint_no_auth(client):
    """Без авторизации — 401."""
    response = client.get("/items/")
    assert response.status_code == 401


def test_protected_endpoint_bad_token(client):
    """С битым токеном — 401."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/items/", headers=headers)
    assert response.status_code == 401
```

### Прямое создание JWT-токена (без эндпоинта логина)

```python
from your_app.auth.jwt import create_access_token


def test_with_direct_token(client):
    """Быстрый тест без регистрации/логина."""
    token = create_access_token({"sub": "1"})
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/items/", headers=headers)
    assert response.status_code == 200
```

### Полный сценарий auth flow

```python
def test_full_auth_flow(client):
    """Регистрация → логин → access → refresh."""
    # 1. Регистрация
    resp = client.post(
        "/auth/register",
        json={"username": "alice", "email": "alice@test.com", "password": "secret"},
    )
    assert resp.status_code == 201
    user_id = resp.json()["id"]

    # 2. Логин
    resp = client.post(
        "/auth/login",
        json={"username": "alice", "email": "alice@test.com", "password": "secret"},
    )
    assert resp.status_code == 200
    access_token = resp.json()["access_token"]
    refresh_token = resp.json()["refresh_token"]
    assert resp.json()["token_type"] == "bearer"

    # 3. Проверка access-токена
    resp = client.post(
        "/auth/access",
        json={"access_token": access_token},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "ok"

    # 4. Refresh
    resp = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert "refresh_token" in resp.json()
```

---

## 10. Параметризация тестов

### @pytest.mark.parametrize

Запускает один и тот же тест с разными данными.

```python
import pytest


@pytest.mark.parametrize(
    "item_id, expected_status",
    [
        (1, 200),    # существует
        (2, 200),    # существует
        (999, 404),  # не существует
        (-1, 404),   # отрицательный ID
    ],
)
def test_get_item(client, item_id, expected_status):
    """GET /items/{item_id} — проверка разных ID."""
    response = client.get(f"/items/{item_id}")
    assert response.status_code == expected_status
```

### Параметризация с несколькими аргументами

```python
@pytest.mark.parametrize(
    ("username", "email", "password", "expected_status"),
    [
        ("alice",  "alice@example.com",  "strong_pass",   201),
        ("bob",    "bob@example.com",    "password123",   201),
        ("",       "empty@example.com",  "pass",          422),   # пустой username
        ("valid",  "not-an-email",       "strong_pass",   422),   # невалидный email
        ("a" * 101, "long@example.com",  "pass",          422),   # слишком длинный (101 символ)
    ],
    ids=[
        "valid_user",
        "another_valid",
        "empty_username",
        "invalid_email",
        "username_too_long",
    ],
)
def test_register_validation(client, username, email, password, expected_status):
    """Регистрация с разными комбинациями данных."""
    response = client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert response.status_code == expected_status
```

Параметр `ids` задаёт человекочитаемые имена тестов. Без него pytest покажет `test_register_validation[0]`, `test_register_validation[1]` и т.д.

### Комбинированная параметризация

```python
# Тест выполнится 6 раз: 2 username × 3 email_domain
@pytest.mark.parametrize("username", ["alice", "bob"])
@pytest.mark.parametrize("email_domain", ["example.com", "test.org", "mail.ru"])
def test_register_combinations(client, username, email_domain):
    email = f"{username}@{email_domain}"
    response = client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": "pass"},
    )
    assert response.status_code == 201
```

---

## 11. conftest.py — расширенная версия

Готовый файл, который можно скопировать в любой проект с FastAPI + SQLAlchemy + аутентификацией.

```python
"""Расширенный conftest.py для FastAPI-проекта.

Содержит:
- client       — синхронный TestClient
- async_client — асинхронный httpx-клиент
- db_session   — сессия БД с изоляцией (очистка таблиц)
- sample_user  — готовый пользователь в БД
- user_factory — фабрика пользователей
- auth_headers — JWT-токен для авторизованных запросов

Как использовать:
    pip install pytest httpx pytest-asyncio factory_boy
    cp этот_файл tests/conftest.py
    # поправь импорты your_app → свой модуль
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# ═══════════════════════════════════════════════
#  ЗДЕСЬ: замени импорты на свои
# ═══════════════════════════════════════════════
from your_app.main import app
from your_app.database import Base
from your_app.settings import settings
# ═══════════════════════════════════════════════


# ======================================================
# 1. Клиенты
# ======================================================

@pytest.fixture
def client():
    """Синхронный TestClient для обычных тестов."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Асинхронный клиент для тестов с async-контекстом.

    Используется, когда нужно:
    - тестировать WebSocket
    - тестировать streaming-ответы
    - делать несколько параллельных запросов

    Пример:
        async def test_ws(async_client):
            async with async_client.websocket_connect("/ws") as ws:
                await ws.send_json({"msg": "hello"})
                data = await ws.receive_json()
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ======================================================
# 2. База данных
# ======================================================

@pytest.fixture(scope="session")
def async_engine():
    """Один engine на всё время тестов.

    scope="session" — engine создаётся один раз.
    Это безопасно, потому что engine — это пул соединений,
    а сами соединения создаются внутри db_session.
    """
    engine = create_async_engine(settings.database_url)
    return engine


@pytest.fixture
async def db_session(async_engine):
    """Сессия БД с очисткой таблиц после каждого теста.

    Как это работает:
    1. Создаётся сессия через async_sessionmaker
    2. Сессия передаётся тесту (yield)
    3. После теста — rollback (откат незакоммиченных изменений)
    4. TRUNCATE всех таблиц (удаление закоммиченных данных)
    5. COMMIT очистки

    Это гарантирует, что каждый тест начинается с пустой БД.
    """
    async_session = async_sessionmaker(async_engine, expire_on_commit=False)

    async with async_session() as session:
        yield session
        await session.rollback()

    # Очистка таблиц для следующего теста
    async with async_session() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))
        await session.commit()


# ======================================================
# 3. Тестовые данные
# ======================================================

@pytest.fixture
async def sample_user(db_session):
    """Один стандартный пользователь в БД.

    Используй, когда нужен «какой-нибудь пользователь».
    """
    from your_app.auth.utils import hash_password
    from your_app.auth.models import User

    user = User(
        username="test_user",
        email="test@example.com",
        hashed_password=hash_password("secret123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def user_factory(db_session):
    """Фабрика пользователей с любыми параметрами.

    Пример:
        admin = await user_factory(username="admin", is_active=True)
        guest = await user_factory(username="guest", is_active=False)
    """
    from your_app.auth.utils import hash_password
    from your_app.auth.models import User

    async def _make_user(
        username: str = "default_user",
        email: str = "default@example.com",
        password: str = "default_pass",
        is_active: bool = True,
    ) -> User:
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            is_active=is_active,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _make_user


# ======================================================
# 4. Аутентификация
# ======================================================

@pytest.fixture
def auth_headers(client):
    """Регистрирует пользователя и возвращает заголовки авторизации.

    Внимание: если тест использует и client, и auth_headers,
    убедись, что сначала идёт auth_headers, потом client:
        def test_me(auth_headers, client):  # ❌ auth_headers создаст
            ...                             #    пользователя до client
        def test_me(client, auth_headers):  # ✅ правильно
            ...
    """
    # Регистрация
    client.post(
        "/auth/register",
        json={
            "username": "pytest_user",
            "email": "pytest@example.com",
            "password": "pytest_pass",
        },
    )

    # Логин
    resp = client.post(
        "/auth/login",
        json={
            "username": "pytest_user",
            "email": "pytest@example.com",
            "password": "pytest_pass",
        },
    )
    token = resp.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}
```

---

## 12. Запуск тестов

### Локально

```bash
# Установить зависимости
pip install pytest pytest-cov pytest-asyncio httpx

# Запустить все тесты
pytest tests/ -v

# С покрытием
pytest tests/ --cov=your_app --cov-report=term-missing

# С HTML-отчётом
pytest tests/ --cov=your_app --cov-report=html
# → открыть htmlcov/index.html в браузере
```

### Полезные флаги pytest

| Флаг                       | Что делает                                           | Пример                      |
| ------------------------------ | ------------------------------------------------------------- | --------------------------------- |
| `-v` или `--verbose`    | Подробный вывод каждого теста       | `pytest -v`                     |
| `-s`                         | Показать print() и логи                          | `pytest -s`                     |
| `-x`                         | Остановиться после первой ошибки | `pytest -x`                     |
| `--lf`                       | Запустить только упавшие тесты     | `pytest --lf`                   |
| `--ff`                       | Сначала упавшие, потом все              | `pytest --ff`                   |
| `-k "часть_имени"` | Фильтр по имени теста                       | `pytest -k "login or register"` |
| `-m "smoke"`                 | Запустить тесты с маркером smoke       | `pytest -m "smoke"`             |
| `--tb=short`                 | Короткий traceback                                    | `pytest --tb=short`             |
| `--tb=line`                  | Одна строка на ошибку                       | `pytest --tb=line`              |

### Полезные комбинации

```bash
# Быстрая итерация: verbose + остановка на первой ошибке + короткий traceback
pytest tests/ -v -x --tb=short

# Только один тест-файл
pytest tests/test_auth.py -v

# Только одна тест-функция
pytest tests/test_auth.py::test_login -v

# Только smoke-тесты с покрытием
pytest tests/ -m smoke --cov=your_app --cov-report=term-missing

# Перезапуск упавших
pytest --lf -v
```

### В Docker

Если используешь Docker Compose:

```bash
# Полный прогон тестов
docker compose --profile test up --build --abort-on-container-exit

# Или через Makefile
make test
```

---

## 13. Настройка pyproject.toml

Скопируй этот блок в свой `pyproject.toml`:

```toml
# ======================================================
# Pytest
# ======================================================
[tool.pytest.ini_options]
addopts = [
    "-p no:cacheprovider",    # не кэшировать результаты
    "--cov=src",              # измерять покрытие модуля src
    "--cov-report=term-missing",  # показывать непокрытые строки
]
asyncio_mode = "auto"         # async-тесты работают без @pytest.mark.asyncio
norecursedirs = [             # не искать тесты в этих папках
    "migrations",
    ".venv",
    ".env",
    "tmp",
]
python_files = [              # какие файлы считать тестами
    "*_test.py",
    "*_tests.py",
]
testpaths = [                 # где искать тесты
    "tests",
]


# ======================================================
# Coverage
# ======================================================
[tool.coverage.run]
data_file = "tmp/.coverage"


# ======================================================
# Ruff: отключить некоторые правила для тестов
# ======================================================
[tool.ruff.lint.per-file-ignores]
"tests/**" = [
    "S101",     # assert разрешён в тестах
    "INP001",   # не нужен __init__.py
    "ANN201",   # тесты могут возвращать None
    "PLR2004",  # магические числа в assert (201, 404 и т.д.)
    "D103",     # необязательный докстринг теста
]
```

---

## Приложение A: Шпаргалка по assert

```python
# ---- Статус-коды ----
assert response.status_code == 200          # OK
assert response.status_code == 201          # Created
assert response.status_code == 204          # No Content
assert response.status_code == 400          # Bad Request
assert response.status_code == 401          # Unauthorized
assert response.status_code == 403          # Forbidden
assert response.status_code == 404          # Not Found
assert response.status_code == 409          # Conflict
assert response.status_code == 422          # Unprocessable Entity (Validation Error)

# ---- JSON-ответ ----
data = response.json()
assert data == {"key": "value"}             # полное совпадение
assert data["key"] == "value"               # частичная проверка
assert "key" in data                        # наличие ключа
assert data.get("optional") is None         # отсутствие ключа

# ---- Типы ----
assert isinstance(data["id"], int)
assert isinstance(data["name"], str)
assert isinstance(data["price"], float | int)

# ---- Списки ----
assert len(data) == 3
assert data[0]["name"] == "first"
assert any(item["active"] for item in data)
assert all(item["price"] > 0 for item in data)

# ---- HTTP-заголовки ----
assert response.headers["content-type"] == "application/json"

# ---- Исключения (для unit-тестов) ----
import pytest

with pytest.raises(ValueError, match="invalid value"):
    my_function(-1)

with pytest.raises(HTTPException) as exc_info:
    my_protected_function()
assert exc_info.value.status_code == 401

# ---- Моки ----
from unittest.mock import patch, MagicMock

mock_obj = MagicMock()
mock_obj.return_value = "mocked"
assert mock_obj() == "mocked"
mock_obj.assert_called_once()

with patch("your_module.external_api") as mock_api:
    mock_api.return_value = {"status": "ok"}
    result = my_function()
    assert result == "ok"
```

---

## Приложение B: Установка зависимостей

```bash
# Минимальный набор
pip install pytest httpx

# С coverage
pip install pytest-cov

# Для async-тестов
pip install pytest-asyncio

# Для заморозки времени
pip install freezegun    # или time-machine (быстрее)

# Для тестовых данных
pip install factory_boy  # мощные фабрики
pip install model_bakery # авто-фабрики

# Для моков HTTP-запросов
pip install responses    # мок для httpx/requests

# Всё одной командой:
pip install pytest pytest-cov pytest-asyncio httpx freezegun factory_boy responses
```

---

## time_machine

```python
import time_machine

# Фикстура для pytest
@pytest.fixture
def frozen_time():
    """Заморозка времени в будущем, чтобы lock_date был в прошлом."""
    traveller = time_machine.travel("2028-01-01 00:00:00+00:00")
    traveller.start()
    yield
    traveller.stop()

# В тесте: сдвиг времени
async def test_capsule_unlock(async_client, access_token):
    with time_machine.travel("2028-01-01 00:00:00+00:00") as traveller:
        # Создаём капсулу с lock_date = 2029-01-01
        response = await async_client.post(
            "/time_capsules/",
            json={
                "title": "future capsule",
                "text": "secret",
                "lock_date": "2029-01-01T00:00:00Z",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        capsule_id = response.json()["id"]

        # Пытаемся открыть — locked
        response = await async_client.get(
            f"/time_capsules/{capsule_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.json()["is_locked"] is True

        # Сдвигаем время на 2 года вперёд
        traveller.shift(datetime.timedelta(days=365*2))

        # Теперь капсула должна открыться
        response = await async_client.get(
            f"/time_capsules/{capsule_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.json()["is_locked"] is False
        assert "secret" in response.json()["text"]
```

*Создано для проекта time-capsule-backend. 2026.*
