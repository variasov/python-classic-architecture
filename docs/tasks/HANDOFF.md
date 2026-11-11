# Передача между задачами

Каждый агент по завершении задачи дописывает сюда свой раздел (10-20 строк): что создано,
принятые решения, отклонения от спецификации, что нужно знать следующим задачам.
Следующий агент читает этот файл перед началом работы.

## Окружение
- venv в WSL: `.venv-wsl` в корне репо, собран `uv sync` по `uv.lock`
  (`UV_PROJECT_ENVIRONMENT=.venv-wsl ~/.local/bin/uv sync --python /usr/bin/python3.10`).
  Новые зависимости - в `pyproject.toml`, затем `uv lock` и `uv sync` с тем же `UV_PROJECT_ENVIRONMENT`.
- Тестовая БД: креды в `.env` в корне репо (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASS`),
  используется вместо `.env.test` из спецификации. Содержимое `.env` не выводить и не менять.

## Задачи

### 00. Каркас (выполнено)
- Создан `pyproject.toml` (setuptools, `src` + namespace-пакеты, конфиги pyright strict / ruff / vulture / pytest с `--import-mode=importlib`).
- Пакет `library` в `src/library/` без единого `__init__.py`; слои: `app`, `app/commands/domain`, `infra/db`, `interfaces/api`, `composites`.
- `app/errors.py` (`AppError`, независимый `AuthError`), `app/roles.py` (`Permissions`, `Account.require`, `PermissionDenied`), `app/commands/domain/errors.py`.
- `infra/db`: `settings.py` (чувствительные DB_* без дефолтов, `MIGRATIONS_SCHEMA=library_migrations`), `constants.py`, `sql/migrations/0001.init.sql`, `sql/schema/DDL.sql`.
- `interfaces/api`: `UserMiddleware` (X-User → Account в `req.context.account`), `current_account(req)`, `errors.py` (400/403/422, тело `[{"type","msg","ctx"}]`), `settings.py` (`API_HOST`, `API_PORT`, таблица `USERS`).
- Композит: `composites/app/hub.py`, `composites/infra/db/{settings,engine}.py`, `composites/interfaces/api/{settings,wsgi,__main__}.py`. `create_app` живёт в `wsgi.py` (по скиллу HTTP), ресурсы передаются аргументами.
- `tests/conftest.py`: грузит `.env`, при отсутствии API_HOST/API_PORT ставит тестовые значения, даёт `migrated_db` (classic.migrations + дроп схем `library` и `library_migrations`), `db_engine`, `raw_db`, in-memory репозитории и фабрики.
- В `.venv-wsl` НЕТ ruff, vulture, tenacity, freezegun. Ставить запрещено: ruff/vulture не запускаются, tenacity/freezegun в коде пока не используются (только объявлены в pyproject).
- Pyright запускать так: `.venv-wsl/bin/pyright --pythonpath .venv-wsl/bin/python` (иначе node-версия не видит venv).

### 01. Создание книги (выполнено)
- Домен `domain/book.py`: `Book` (isbn 13 цифр, непустое имя, год не в будущем), критерии `published_after`/`written_by`, `BooksRepo` (`get_by_id`/`save`/`find`), ошибки `BookNotFound`, `BookIsbnInvalid`, `BookTitleEmpty`, `BookPublishedInFuture`.
- Команда `CreateBook` (`use_cases/books/create_book.py`): права `books.edit` первой строкой, `CreateBookParams` (`authors` не пуст, `isbn` 13 символов).
- БД: таблицы `books`, `book_authors` (`position` 0-based, PK `(book_id, position)`), каскад; `aggregates/books/{get_by_id,insert,update,delete_authors,insert_authors}.sql`, `find.sql.tmpl`, `criteria.sql.tmpl`. Авторы читаются одним `array_agg(... ORDER BY position)` в поле `Book__authors`, при сохранении перезаписываются delete+insert.
- HTTP: `POST /library/books` → 201 `{"id"}`; ресурс `interfaces/api/resources/books.py`, инстанс в композите, маршрут в `create_app`.
- `create_app(settings, books=...)` теперь требует ресурсы явно; тесты API собирают приложение через него (probe-ресурс добавляется тестом).
- Тесты: unit домена/команды, контрактные (DB+in-memory), SQL-макросы, HTTP с FakeUseCase, e2e (успех + откат транзакции при сбое после вставки).
- Состояние: `pytest 44 passed`, `pyright 0 errors`.
