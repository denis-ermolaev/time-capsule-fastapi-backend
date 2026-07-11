# General Git Commit Guide

> Единый стандарт коммитов Conventional Commit
> Необходимые команды
> Версия от 05.07.2026

---

## Оглавление

- [Структура коммита](#2-структура-коммита)

---

## Структура коммита

```
┌ type ┐┌── scope ──┐┌────── subject ─────────────────────────────┐
  feat    (capsule):  добавлен эндпоинт создания капсулы времени
└─────────────── subject max 72 символа ──────────────────────────┘
Обязательная пустая строка! Между заголовком и телом!
┌──────────────────body───────────────────────────────────────────┐
    Реализует POST /capsules/:
    - Pydantic-модель Item со strict mode
    - structlog для логирования запросов
    - HTTP 201 при успешном создании
└─────────────── опционально ─────────────────────────────────────┘
Обязательная пустая строка! Между телом и сносками!
┌──────────────────footer─────────────────────────────────────────┐
  Related to TASK-120

  BREAKING CHANGE: unlock_at переименован в available_from.
  Старые клиенты будут получать 422.
  Миграция: заменить unlock_at на available_from во всех запросах.

  Co-authored-by: Иван Иванов <ivan@example.com>
└─────────────── опционально ─────────────────────────────────────┘
```

```bash
# Только заголовок
git commit -m "feat(vcf): добавлен парсинг мультиаллельных вариантов"

# После второй m идёт тело коммита, ещё одна -m добавляет сноски
git commit -m "fix(gwas): исправлен расчёт lambda GC" -m "Раньше коэффициент инфляции считался по медиане хи-квадрат, что занижало значение. Осуществлён переход на регрессионный метод."

# Открывает редактор (По умолчанию может быть vim, изменить - git config --global core.editor "nano")
git commit
```

---

### 1. Типы коммитов (Conventional Commits)

| Тип            | Когда использовать　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　|     |
| ----------------| ---------------------------------------------------------------------------------------------------------------------------| -----|
| **`feat`**     | ✨ Новая функциональность (фича)　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　 |     |
| **`fix`**      | 🐛 Исправление ошибки (бага)　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　|     |
| **`refactor`** | ♻️ Переписывание кода без изменения поведения　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　|     |
| **`test`**     | ✅ Добавление или правка тестов　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　|     |
| **`docs`**     | 📝 Документация: README, докстринги, комментарии　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　|     |
| **`style`**    | 🎨 Форматирование: ruff, пробелы, запятые　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　 |     |
| **`perf`**     | ⚡ Оптимизация производительности　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　|     |
| **`build`**    | 📦 Зависимости и сборка (Как собирается проект): зависимости, сборка, пакеты.lock　　　　　　　　　　　　　　　　　　　　 |     |
| **`ci`**       | 👷 CI/CD и инфраструктура (Как тестируется и доставляется проект): экшены, дocker-образ, деплой　　　　　　　　　　　　　 |     |
| **`chore`**    | 🔧 Всё остальное обслуживание (Обслуживание проекта): конфиги, гитигнор, pre-commit　　　　　　　　　　　　　　　　　　　 |     |
| **`revert`**   | ⏪ Откат коммита　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　 |     |
| **`wip`**      | Для черновых коммитов, чтобы часто сохранять историю, даже для не рабочего кода, но их всегда склеивают в один аккуратный |     |

---

### 2. Заголовок (subject)

- **Максимум 72 символа** - иначе git обрезает в `git log --oneline`.
- **Тип на английском** - `feat:`, `fix:`, `refactor:`.
- **Область коммита** - в каком модуле/компоненте внесено изменение (time_capsule).
- **Описание на русском** - что было сделано в этом коммите, без точки в конце, без заглавной буквы в начале (добавление; добавлен эндпоинт создания капсулы времени; реализован, сделан, обнавлён FastAPI и т.п).

> Подробнее про scope

- Нижний регистр, английский язык.
- Одно слово (если нужно — дефис: `ci-cd`).
- Не указывать, если изменение затрагивает несколько областей или весь проект.
- Общие scope для проекта: `deps` - версии зависимостей, `config` - конфигурация проекта.

---

### 3. Тело (body)

Тело нужно, если заголовок не может уместить всю информацию. А также дополнительно:

- **Почему** сделано именно так.
- **Как** это работает (если неочевидно из кода).
- **Какие альтернативы** рассматривались.

```
Реализует POST /capsules/:
- Pydantic-модель Item со strict mode
- structlog для логирования запросов
- HTTP 201 при успешном создании
```

---

### 4. Нижний колонтитул (footer)

Дополнительная информация: ссылка на задачу, или баг.

```
Closes #42
Refs #41
Implements TASK-123
Related to TASK-120
```

BREAKING CHANGE - если изменение ломает обратную совместимость:

```
BREAKING CHANGE: unlock_at переименован в available_from.
Старые клиенты будут получать 422.
Миграция: заменить unlock_at на available_from во всех запросах.
```

`BREAKING CHANGE:` в footer автоматически делает следующую версию **major**.

Co-authored-by - если коммит совместный:

```
Co-authored-by: Иван Иванов <ivan@example.com>
```

---

### 5. Примеры коммитов

```
feat(capsule): добавление эндпоинта создания с Pydantic-валидацией

Реализует POST /capsules/:
- Модель Item со strict mode
- Логирование запросов через structlog
- HTTP 201 при успешном создании

Closes #42
```

```
fix(auth): корректная обработка просроченных JWT-токенов

Возвращает 401 с понятным сообщением вместо 500.
Добавлен тест для сценария с истёкшим токеном.

Refs TASK-123
```

```
docs(README): добавлена инструкция по установке и запуску

Включает:
- Системные требования (Python 3.14, uv)
- Переменные окружения
- Команды docker compose
- Ссылку на документацию API
```

```
refactor(security): вынесено хеширование пароля в отдельный модуль

Переносит bcrypt-логику из auth.py в security/hasher.py.
Подготовка к добавлению Argon2.
```

```
chore(deps): обновлён fastapi с 0.108.0 до 0.138.2

Список изменений: https://github.com/fastapi/fastapi/releases/tag/0.138.2
```

```
ci: добавлены GitHub Actions для линтера и тестов

Запускает ruff check, ty check и pytest на каждый push.
Требуется uv 0.11+.
```

## Workflow
Общий процесс разработки:
```bash
# GitHub Flow
# 1. Начало работы
git checkout master
git pull origin master # Начиная со второго раза, используем просто
#git pull
git checkout -b feat/new-plot

# 2. Процесс работы
# ...редактируем файлы...
git add .
git commit -m "feat(final-analysis): добавлен манхэттенский график"

# 3. Пуш и PR(пул-реквест, запрос на слияние)
git push -u origin feat/new-plot # Начиная со второго раза, используем просто
# git push

# Создаём Pull Request на GitHub, для проверки другими разработчиками

# 4. После одобрения (или самопроверки) нажимаем "Squash and merge" на сайте

# 5. Очистка
git checkout master # Или main, или dev - главная ветвь разработки
git pull # Стягивание изменений с удалённого репозитория
git branch -d feat/new-plot # Создание новой ветви
git push
# git remote prune origin — удалит локальные ссылки на ветки, которые уже удалены на GitHub
```

### 1. Когда и как коммитить
- **Один коммит = одно логическое изменение** - не смешиваем разные типы `feat` + `fix` + `style`
- **Частые коммиты** - каждые 15-30 минут работы
- **Не коммитим сломанный код** - запускаем перед этим тесты

### 2. Модель ветвления
Для отдельного действия(фикса/добавление новой функциональности) создаётся отдельная ветвь

```
main
├── feature/add-capsule - новая функциональность
├── fix/handle-empty-name - исправление бага
├── refactor/extract-validator - рефакторинг
├── docs/update-readme - документация
└── chore/<описание> - обслуживание
```

```bash
# Создать и переключиться
git checkout -b feat/add-capsule
git switch -c feat/add-capsule # современный аналог

# Переключиться
git checkout main
git switch main # современный аналог

# Показать ветки проекта
git branch              # локальные
git branch -a           # все (локальные + удалённые)(После клонирования видны не все ветки удалённого репозитория)

# Слить ветку в текущую
git merge feat/add-capsule # находясь в main
#При конфликте, создаётся файл с системными записями от git, там нужно решить как разрешить конфликт слияния, а после закоммитить разрешение конфликта.
```

### 3. Отмена коммитов
```bash
# ----- git rebase -----
# rebase только для НЕзапушенных коммитов. Если коммиты уже на GitHub — используй revert
# Объединить последние 3 коммита
git rebase -i HEAD~3
# Или для всех коммитов git rebase -i --root
# Для одного красивого init коммита при создании проекта

# Откроется редактор:
# pick  a1b2c3d wip: начал делать
# pick  e4f5g6h fix: опечатка
# pick  j7k8l9m feat: готово
# Меняем на:
# pick  a1b2c3d wip: начал делать
# squash e4f5g6h fix: опечатка ← объединить с предыдущим
# fixup j7k8l9m feat: готово ← объединить, отбросить сообщение
```

```bash
# ----- git revert -----
# Для коммитов на GitHub
# Новый коммит, отменяющий изменения последнего коммита (безопасно для истории)
git revert HEAD
# Или для 3-х коммитов
git revert HEAD~3
```

```bash
# ----- git commit --amend -----
# Только сообщение
git commit --amend -m "Новое сообщение"

# Добавить забытые файлы в последний коммит
git add забытый-файл
git commit --amend --no-edit

# Переписать автора коммита
git commit --amend --reset-author
```

```bash
# Уровень 1: Файл изменён, но НЕ добавлен
git restore file.txt # отменить изменения в файле

# Уровень 2: Файл уже добавлен (staged)
git restore --staged file.txt # убрать из Staging (→ modified)

# Уровень 3: Уже закоммичено, но НЕ запушено
git reset --soft HEAD~1 # отменить коммит, изменения остались в Staging
git reset --hard HEAD~1 # отменить коммит + стереть изменения ⚠️

# Уровень 4: Уже запушено на GitHub
git revert HEAD # безопасно: новый коммит "отмены"

# Уровень 5: Ошибочный merge
git merge --abort # отменить merge до его завершения
```

### 6. Создание git-репозитория

```bash
# Инициализация локального репозитория
git init
# Загрузка удалённого репозитория
git clone git@github.com:denis-ermolaev/test.git
```

### 7. История проекта

```bash
# ----- git status -----
git status # Перед каждым commit/push

# ----- git diff -----
git diff # что изменил, но ещё не добавил
git diff --staged # что уже добавил (в Staging)
git diff HEAD~1 # что изменилось в последнем коммите
git diff main..feature # чем ветка отличается от main
git diff --stat # только статистика (файлы + строки)

# ----- git log -----
git log --oneline # история коммитов (кратко)
git log --oneline --graph # с графом ветвлений
git log --oneline -5 # последние 5 коммитов
git log --author="имя" # по автору
git log --after="2026-06-01" # по дате

# ----- git show -----
git show a1b2c3d # что конкретно поменял коммит
git show HEAD # последний коммит
```

### 8. `git stash` - отложить изменения для работы в другой ветки
```bash
git stash                     # отложить все изменения
git stash push -m "wip"       # отложить с пометкой
git stash pop                 # вернуть последнее отложенное
git stash list                # посмотреть стек отложенного
git stash apply               # вернуть, но оставить в стеке
git stash drop                # удалить из стека
git stash clear               # очистить весь стек
```

### 9. Разрешение конфликтов merge
```bash
# При конфликте:
# 1. Смотрим какие файлы конфликтуют
git status

# 2. Открываем файл, видим:
# <<<<<<< HEAD
# текущий код
# =======
# вливаемый код
# >>>>>>> feature-branch

# 3. Редактируем, оставляя нужное
# 4. Отмечаем как решённое
git add file.txt

# 5. Завершаем слияние
git commit

# 6. Если нужно отменить слияние
git merge --abort
```

### 10. `git bisect` — поиск коммита, который всё сломал
```bash
# Начать бинарный поиск
git bisect start

# Отметить текущий коммит как "сломанный"
git bisect bad

# Отметить известный рабочий коммит
git bisect good v1.0.0

# Git автоматически переключается на середину истории
# Тестируешь, помечаешь: git bisect good или git bisect bad
# Повторяешь ~log2(N) раз

# Выйти из bisect
git bisect reset

# Автоматический bisect (если есть скрипт тестирования)
git bisect run pytest tests/test_bug.py
```

### 11. `git reflog` - если случайно была удалена ветка
```bash
# Показать все действия HEAD (локальная история)
git reflog

# Пример: восстановить коммит после git reset --hard
git reflog                    # находим хэш нужного коммита
git reset --hard <hash>       # возвращаемся

# Пример: восстановить удалённую ветку
git reflog                    # находим последний коммит ветки
git checkout -b recovered-branch <hash>
```

### 12. `git cherry-pick` - перенос коммита
```bash
# Перенести один коммит в текущую ветку
git cherry-pick a1b2c3d

# Перенести несколько коммитов
git cherry-pick a1b2c3d e4f5g6h

# Без автоматического коммита (чтобы внести правки)
git cherry-pick --no-commit a1b2c3d
```

### 13. `git blame` - кто написал строку
```bash
# Кто и когда менял каждую строку файла
git blame file.txt

# Диапазон строк
git blame -L 10,30 file.txt

# Игнорировать правки форматирования (whitespace)
git blame -w file.txt

# Показать хэш коммита и автора в одну строку
git blame -s file.txt
```

# 14. Теги (git tag) — версионирование
```bash
# Создать lightweight-тег
git tag v1.0.0

# Создать annotated-тег (рекомендуется — хранит автора, дату, сообщение)
git tag -a v1.0.0 -m "Релиз: добавлен эндпоинт капсул"

# Отправить теги на удалённый репозиторий
git push origin v1.0.0
git push origin --tags   # все теги сразу

# Посмотреть теги
git tag -n               # с сообщениями
git tag -l "v1.*"        # фильтр

# Удалить тег локально
git tag -d v1.0.0

# Удалить тег на удалённом
git push --delete origin v1.0.0
```

---

## Настройки

### 1. История и алиасы
- Поиск в истории Ctrl + R , либо начать вводить текст и стрелки вверх/вниз

```
# .bashrc
# Включить сохранение истории
shopt -s histappend
export HISTFILE=~/.bash_history
export HISTSIZE=10000
export HISTFILESIZE=20000
export PROMPT_COMMAND="history -a; history -n; $PROMPT_COMMAND"

# Включение поиска в истории
bind '"\e[A": history-search-backward'
bind '"\e[B": history-search-forward'

# Настройка истории
HISTCONTROL=ignoredups:erasedups  # Удаляет дублирующие команды
shopt -s histappend               # Добавляет команды в историю, не перезаписывая
export PROMPT_COMMAND="history -a; history -n; $PROMPT_COMMAND"
```

- Можно настроить алиасы в `.bashrc`
```
alias gs='git status'
alias ll='ls -al'
alias gl='git log --oneline --graph --all'
alias gd='git diff'
```

### 2. Глобальные настройки Git

1) Глобальные настройки

- `git config --global user.name "Имя для коммитов"`
- `git config --global user.email "адрес@почты.com"`
- `git config --global core.editor "nano"` - редактор по умолчанию
- `git config --global --list` - посмотреть глобальные настройки

2) Настройки конца строки:

Windows:

- `git config --global core.autocrlf true`
- `git config --global core.safecrlf warn`
- `git config --global core.quotepath off`

Linux | macOS:

- `git config --global core.autocrlf input`
- `git config --global core.safecrlf warn`
- `git config --global core.quotepath off`

3) Название ветки по умолчанию (main или master)

- `git config --global init.defaultBranch main`

## Работа с GitHub

Настройка ssh ключа для связи git и github

- `ssh-keygen`
- `cat ~/.ssh/id_ed25519.pub` - вывести ключ в консоль. Далее загружаем этот ключ на гитхаб Настройки-ssh ключ

### 1. Управление удалённым репозиторием

```bash
# Проверить текущий origin(Удалённый репозиторий)
git remote -v
# Изменить ссылку origin на другой url
git remote set-url origin git@github.com:denis-ermolaev/final-work-Bioengineering-and-bioinformatics.git
# Первая отправка - связь origin с main(master), в последующем просто git push
git push -u origin main
# Альтернативно, удалить origin и добавить новый
git remote remove origin
git remote add origin git@github.com:denis-ermolaev/final-work-Bioengineering-and-bioinformatics.git

# Два удалённых репозитория
git remote add personal https://github.com/username/personal-repo.git # Отдельная ссылка
git push origin main # Два push
git push personal main

git remote set-url --add --push origin https://github.com/username/personal-repo.git # Две ссылки для origin
git push origin main # Один push сразу в два репозитория
```

## .gitignore

Файл-настройка в корне проекта, в которой указываются файлы, которые не нужно отслеживать (через `git add`), влияет только на те файлы, которые ещё не добавлены в отслеживаемые (при добавлении таких, их нужно удалить)

```plain
# Рекурсивно во всех папках
**/**/__pycache__
# Любое название файла с фиксированые расширением
*.egg-info
# Конкретная папка
build/
# Конкретный файл
DEV.md
# Содержимое папки
migrations/versions/*
```

### 1. Удаление отслеживания файлов из репозитория

После внесения файлов в .gitignore, если они уже отслеживаются.

```bash
git rm --cached <файл>
git rm -r --cached <папка>
# Или удалить все, добавить все
git rm -r --cached .
git add .
```
