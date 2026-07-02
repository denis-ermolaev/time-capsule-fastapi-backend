"""Базовые тесты."""

from pathlib import Path


def test_project_structure():
    """Проверка структуры проекта внутри docker-контейнера."""
    assert Path("/app").is_dir()
    assert Path("/app/Makefile").is_file()
