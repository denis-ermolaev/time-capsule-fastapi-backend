.DEFAULT_GOAL := help

COMPOSE := docker compose
WEB := $(COMPOSE) exec web

# Самые важные команды
.PHONY: pre-commit_all test review compose_without_build make_migrations migrations

## Справка
help:
	@echo "Available commands:"
	@awk 'prev ~ /^## / && $$0 ~ /^[a-zA-Z_-]+:/ {printf "  \033[36m%-25s\033[0m %s\n", substr($$0, 1, index($$0, ":")-1), substr(prev, 4)}; {prev=$$0}' Makefile

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                                 Качество кода                                #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Качество кода
## Установить pre-commit хуки
pre-commit-install_host:
	uv run pre-commit install --hook-type pre-commit --hook-type pre-push

# Запускает и pre-push и pre-commit хуки!
## Запустить pre-commit хуки на хосте (на всех файлах — полная проверка)
pre-commit_all:
	uv run pre-commit run --all-files --hook-stage pre-push


# Test workflow: Поднимаем контейнеры, запускаем тесты, в конце работы закрываем контейнеры или при необходимости миграции ----
## Поднять тестовые контейнеры и сделать миграцию
up_test:
	$(COMPOSE) --profile test up -d --no-build
	$(COMPOSE) exec -T test uv run alembic upgrade head

## Запустить тесты в тестовом окружении
test:
	$(COMPOSE) exec -T test uv run pytest

## Тесты по docstring в тестовом окружении
test_docs:
	$(COMPOSE) exec -T test uv run python -m pytest --doctest-modules src/

## Удалить тестовые контейнеры
down_test:
	$(COMPOSE) --profile test down

## Единная команда для запуска тестов
test_all:
	$(MAKE) down_test
	$(MAKE) up_test
	$(MAKE) test_docs
	$(MAKE) test
	$(MAKE) down_test

# ИИ-ревью ----
## Ревью кода от ИИ-агента
review_diff:
	opencode run --auto --agent review "Проведи ревью изменённых файлов" > tmp/review-diff-latest.md

review_project:
	opencode run --agent arch-review "Проведи ревью всего проекта" > tmp/review-project-latest.md

# ---------------------------------------------------------------------------- #

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                                  Контейнеры                                  #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# Команды внутри контейнера ----
### Контейнеры
## Показать состояние контейнеров
compose_ps:
	$(COMPOSE) ps

## Смотреть логи web-контейнера
logs_web:
	$(COMPOSE) logs -f web

## Открыть shell в web-контейнере
shell:
	$(WEB) bash
## Запустить контейнер с пересборкой
compose_build:
	$(COMPOSE) --profile main up -d --build

## Запустить контейнер без пересборки
compose_without_build:
	$(COMPOSE) --profile main up -d --no-build

down_web:
	$(COMPOSE) --profile main down

compose_build_test:
	$(COMPOSE) --profile test up -d --build

# ---------------------------------------------------------------------------- #

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                                  Миграции БД                                 #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

### Миграции
## Инициализировать настройки alembic (alembic.ini и env.py)
init_migrations:
	uv run alembic init -t async migrations/

MESSAGE ?= Auto-generated migration
## Создать миграцию
make_migrations:
	$(WEB) uv run alembic revision --autogenerate -m "$(MESSAGE)"

## Приминить миграцию
migrations:
	$(WEB) uv run alembic upgrade head


# ---------------------------------------------------------------------------- #
