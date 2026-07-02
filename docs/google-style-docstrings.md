# Google Style Docstrings

> Полное руководство по написанию докстрингов в Google Style

---

## Оглавление

- [1. Быстрый старт](#1-быстрый-старт)
- [2. Шаблоны для всех конструкций](#2-шаблоны-для-всех-конструкций)
- [3. Форматирование](#3-форматирование)
- [4. Инструменты и проверка](#4-инструменты-и-проверка)
- [5. Doctest — документация, которая не врёт](#5-doctest--документация-которая-не-врёт)
- [6. Частые случаи](#6-частые-случаи)
- [7. Плохие примеры](#7-плохие-примеры)

---

## 1. Быстрый старт

Скопируй и вставь:

```python
# Модуль
"""Public API для работы с капсулами времени."""

# Класс
class Capsule:
    """Одна капсула времени с метаданными и содержимым."""

# Функция / метод
def create(user_id: int) -> Capsule:
    """Создаёт новую капсулу.

    Args:
        user_id: Владелец капсулы.

    Returns:
        Созданный объект Capsule.
    """
```

**Главные правила:**

- После заголовка — пустая строка (кроме однострочников)
- `Args:` / `Returns:` / `Raises:` — с новой строки, с отступом
- Каждый параметр — отдельная строка: `имя: Описание.`
- Типы не дублировать — они в аннотации функции

---

## 2. Шаблоны для всех конструкций

### 2.1 Модуль

Первый `"""..."""` в файле — докстринг модуля.

```python
"""Public API для работы с капсулами времени.

Опционально — подробное описание, контекст, зависимости.

Attributes:
    settings: Глобальный синглтон конфигурации.

Typical usage example:
    >>> from src import create_capsule
    >>> create_capsule(1, "text", tomorrow())
    Capsule(...)
"""
```

### 2.2 Класс

```python
class Capsule(BaseModel):
    """Одна капсула времени.

    Attributes:
        public_id: Публичный идентификатор для шаринга.
        content:   Зашифрованное содержимое.
        unlock_at: Дата/время, когда капсулу можно открыть.
    """

    public_id: str = ""
    content: str = ""
    unlock_at: datetime | None = None
```

### 2.3 Функция / метод

```python
def create_capsule(user_id: int, content: str, unlock_at: datetime) -> Capsule:
    """Создаёт капсулу времени с отложенной доступностью.

    Детали реализации (опционально): шифрование, запись в БД.

    Args:
        user_id:   ID владельца.
        content:   Текстовое содержимое (непустое).
        unlock_at: Когда капсулу можно открыть.

    Returns:
        Capsule-объект со всеми полями.

    Raises:
        ValueError: Если unlock_at в прошлом.
    """
```

| Секция             | Когда нужна                                                    |
| ------------------------ | ------------------------------------------------------------------------ |
| `Args:`                | Всегда, если есть параметры (кроме self/cls) |
| `Returns:`             | Всегда, если возвращает значение             |
| `Raises:`              | Если выбрасывает исключение (не Exception)    |
| `Yields:`              | Если это генератор                                       |
| `Examples:`            | Хороший тон — доктест                                  |
| `Note:` / `Warning:` | Если есть подводные камни                          |

**Однострочник для простых функций:**

```python
def health() -> dict:
    """Health-check endpoint."""
    return {"status": "ok"}
```

### 2.4 Метод класса / staticmethod / property

```python
@classmethod
def from_db(cls, row: dict) -> Self:
    """Восстанавливает капсулу из строки БД.

    Args:
        row: Словарь с полями из БД.

    Returns:
        Новый экземпляр Capsule.
    """
    ...

@property
def is_unlocked(self) -> bool:
    """True, если капсулу уже можно открыть."""
    return datetime.now() >= self.unlock_at
```

### 2.5 Переменные

В Python **нельзя** прикрепить `"""..."""` к переменной. Используй один из способов:

#### 🔥 `Annotated` (PEP 593) — приоритет для Python 3.14+

```python
from typing import Annotated

db_password: Annotated[str, "Пароль для подключения к БД"] = ""
```

#### `Attributes:` в докстринге модуля (Google Style)

```python
"""Модуль конфигурации.

Attributes:
    settings: Глобальный экземпляр Settings.
"""
settings = Settings()
```

#### `TypeAlias` + докстринг

```python
JSON: TypeAlias = dict[str, Any]
"""JSON-совместимый словарь для API-ответов."""

type JSON = dict[str, Any]  # PEP 695 (3.14)
"""JSON-совместимый словарь."""
```

#### `#:` для Sphinx

```python
#: Пароль для подключения к БД.
db_password: str = ""
```

### 2.6 `__init__.py`

```python
"""Time Capsule Backend.

Пакет публичного API для работы с капсулами времени.
"""

from .capsule import Capsule, create_capsule

__all__ = ["Capsule", "create_capsule"]
```

### 2.7 Dataclass

```python
@dataclass
class Capsule:
    """Капсула времени.

    Attributes:
        content:   Содержимое.
        unlock_at: Дата открытия.
    """
    content: str
    unlock_at: datetime
```

### 2.8 Перегрузка (overload)

Докстринг только на реализации, не на `@overload`:

```python
@overload
def parse(data: str) -> dict: ...
@overload
def parse(data: bytes) -> dict: ...

def parse(data: str | bytes) -> dict:
    """Парсит данные в словарь.

    Args:
        data: Строка или байты.

    Returns:
        Словарь.
    """
```

---

## 3. Форматирование

### Отступы

```python
def func(param_one: int, param_two: str) -> None:
    """Описание.

    Args:
        param_one: Описание.
                    Если не влезает — перенос с отступом
                    относительно начала описания.
        param_two: Ещё параметр.
    """
```

- 4 пробела отступ самого докстринга
- `Args:` / `Returns:` — на том же уровне
- Параметры — ещё +4 пробела
- Многострочное описание — отступ до текста

### Пунктуация

| Элемент                                          | Правило                                                             |
| ------------------------------------------------------- | -------------------------------------------------------------------------- |
| Первая строка (однострочник)    | Фраза без точки или предложение с точкой |
| Первая строка (многострочник)  | Предложение с точкой`.`                                |
| `Args:` / `Returns:`                                | Двоеточие обязательно                                  |
| Пустая строка после заголовка | Всегда (кроме однострочника)                       |
| Пустая строка перед`Returns:`        | Всегда                                                               |
| Кавычки                                          | Только`"""..."""` (PEP 257)                                        |

---

## 4. Инструменты и проверка

### 4.1 ruff

```toml
[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint]
extend-select = ["D417"]   # все параметры обязательны в докстринге
```

**Основные коды ошибок:**

| Код | Что проверяет                                                  |
| ------ | -------------------------------------------------------------------------- |
| D100   | Нет докстринга модуля                                   |
| D101   | Нет докстринга класса                                   |
| D102   | Нет докстринга публичного метода              |
| D103   | Нет докстринга публичной функции              |
| D104   | Нет докстринга пакета (`__init__.py`)                 |
| D105   | Нет докстринга магического метода            |
| D200   | Однострочник должен быть в одну строку    |
| D205   | Пустая строка после резюме                          |
| D400   | Первая строка заканчивается`.`                  |
| D401   | Первое слово — повелительное наклонение |
| D405   | `Args` (с капсом), не `args`                                  |
| D406   | `Returns` (с капсом)                                              |
| D407   | Пустая строка после`Args:`                              |
| D408   | Отступ параметра — 4 пробела                        |
| D410   | `Returns:` на отдельной строке                          |
| D411   | Пустая строка перед`Returns:`                           |
| D413   | Пустая строка после`Returns:`                           |
| D414   | `Returns:` не пустой                                             |
| D417   | **Не все параметры описаны**                    |

### 4.2 interrogate — процент покрытия

```bash
pip install interrogate
interrogate src/ --fail-under=90
```

---

## 5. Doctest — документация, которая не врёт

Любой блок `>>> code` внутри докстринга выполняется как тест:

```python
def add(a: int, b: int) -> int:
    """Складывает два числа.

    Examples:
        >>> add(2, 3)
        5
        >>> add(-1, 1)
        0
    """
    return a + b
```

```bash
pytest --doctest-modules src/
```

Если пример врёт — тест упадёт:

```
Expected:
    6
Got:
    5
FAILED
```

### Проблема: переменные окружения

```python
# ❌ Упадёт — db_host зависит от окружения
>>> settings.db_host
'localhost'
```

**Решение 1 (🔥 лучшее) — проверяй типы:**

```python
"""...
Typical usage example:
    >>> isinstance(settings.db_host, str)
    True
    >>> isinstance(settings.db_port, int)
    True
"""
```

**Решение 2 — `# doctest: +SKIP`:**

```python
>>> settings.db_host  # doctest: +SKIP
'localhost'
```

### Директивы doctest

| Директива           | Что делает                                                     |
| ---------------------------- | ----------------------------------------------------------------------- |
| `+SKIP`                    | Пропускает строку                                       |
| `+ELLIPSIS`                | `...` = любой текст                                         |
| `+NORMALIZE_WHITESPACE`    | Пробелы не важны                                          |
| `+IGNORE_EXCEPTION_DETAIL` | Сообщение исключения может отличаться |

### Настройка в проекте

```bash
# Запуск (обязательно python -m — добавляет cwd в sys.path)
python -m pytest --doctest-modules src/

# Или в Docker
docker compose --profile test run --rm test uv run python -m pytest --doctest-modules src/
```

---

## 6. Частые случаи

### `@dataclass`

Докстринг — на класс, не на `__init__`:

```python
@dataclass
class Point:
    """Точка на координатной плоскости.

    Attributes:
        x: Координата X.
        y: Координата Y.
    """
    x: float = 0.0
    y: float = 0.0
```

### `Enum`

```python
class Status(StrEnum):
    """Статус капсулы.

    Attributes:
        PENDING:   Ожидает открытия.
        OPENED:    Уже открыта.
        EXPIRED:   Истекла (не была открыта вовремя).
    """
    PENDING = "pending"
    OPENED = "opened"
    EXPIRED = "expired"
```

### `Pydantic` модели

```python
class Item(BaseModel):
    """Модель товара.

    Attributes:
        name:  Название (непустое).
        price: Цена (строгий режим, только числа).
    """
    name: str
    price: float
```

### Async-функции

Никаких отличий от синхронных:

```python
async def fetch_capsule(public_id: str) -> Capsule | None:
    """Получает капсулу по public_id.

    Args:
        public_id: Публичный идентификатор.

    Returns:
        Capsule или None, если не найдена.

    Raises:
        HTTPException 404: Если капсула не существует.
    """
```

---

## 7. Плохие примеры

```python
# ❌ Нет докстринга модуля
import something

# ❌ Докстринг есть, но пустой
def open(self) -> str:
    """ """

# ❌ Неправильный формат секций
def create(user_id: int) -> Capsule:
    """Создаёт капсулу.
    create user_id: ID пользователя.      ← нет Args:, просто текст
    return: Капсула                       ← должно быть Returns:
    """

# ❌ Типы в Args — НЕ НУЖНО (они в аннотации)
def add(a: int, b: int) -> int:
    """Складывает.
    Args:
        a (int): Первое.                  ← int уже в аннотации
    """

# ❌ Одинарные кавычки (PEP 257 запрещает)
def func():
    '''Описание.'''                       # должно быть """
```

---

*Создано для проекта time-capsule-backend. 2026.*
