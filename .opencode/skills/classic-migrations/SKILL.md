---
name: classic-migrations
description: Справка по API библиотеки classic-migrations 3.x (classic.migrations) - формат .sql миграций и директив, MigrationsCollection, Migrator, программное применение и откат, CLI. Загружать перед написанием миграций и кода с classic.migrations (тестовые фикстуры БД, команда миграций). Как библиотека применяется в архитектуре - в python-classic-adapters-sql-db.
license: MIT
compatibility: opencode
---

# classic-migrations 3.x: API

Только API, сверенный с версией 3.0. Правила применения (именование `NNNN.description.sql`, схемы модулей, снапшот `sql/schema`) - в `python-classic-adapters-sql-db`.

## Файлы миграций
- Миграция - `.sql` файл (расширение в нижнем регистре) в каталоге миграций; id миграции = имя файла без расширения (`0001.init`). Дубликат id - `MigrationConflict`.
- Директивы - в начальных комментариях файла:
  ```sql
  -- transactional: true
  -- depends: 0001.init

  CREATE TABLE library.readers (...);
  ```
  - `-- depends: <id>, <id>` - зависимости по id; несуществующий id - `NoMigration`.
  - `-- transactional: true|false` - выполнять в транзакции (для PostgreSQL по умолчанию `true`).
  - Разбор строгий: опечатка или неизвестная директива в шапке - `BadMigration`.
- Порядок - топологический по `depends`, среди независимых - лексикографический по id (не по номеру в имени). Цепочку задавай через `-- depends`.
- Откат - соседний файл `<id>.rollback.sql`; допускает только `-- transactional`. Без него откат лишь пишет событие в историю (с предупреждением в лог).
- Хуки `pre-apply.sql`, `post-apply.sql`, `pre-rollback.sql`, `post-rollback.sql` в каталоге миграций выполняются вне транзакции и в историю не попадают.
- Схему объектов приложения библиотека не создаёт: `CREATE SCHEMA` - в первой миграции. Не совпадай ею с `migration_schema` (её библиотека создаёт сама, и `CREATE SCHEMA` без `IF NOT EXISTS` упадёт).

## Программное применение
```python
from classic.migrations import MigrationsCollection, Migrator

collection = MigrationsCollection(sources=[MIGRATIONS_DIR_PATH])  # str | PathLike | список
with Migrator(
    driver='psycopg',                    # имя модуля драйвера строкой
    db_host=settings.DB_HOST,
    db_port=settings.DB_PORT,            # int
    db_name=settings.DB_NAME,
    db_user=settings.DB_USER,
    db_pass=settings.DB_PASS,
    migration_table='migrations',        # по умолчанию
    migration_schema=settings.MIGRATIONS_SCHEMA,
    lock_timeout=30,                     # сек; None - ждать бесконечно, 0 - не ждать
) as migrator:
    hooks, migrations = collection.to_apply(migrator.history())
    migrator.apply(migrations, hooks)
```
- `Migrator` - контекстный менеджер: при входе соединение + advisory-lock, при выходе снятие и закрытие. Методы вызываются только внутри `with`.
- `Migrator` принимает параметры подключения по отдельности, а не строку подключения; дополнительные параметры `connect()` - `db_args={'connect_timeout': 5}`.
- Блокировка привязана к имени таблицы истории: разные проекты в одной БД - разные `migration_table`/`migration_schema`.
- `collection.to_apply(history, target=None, *, fake=False)` → `(hooks: dict, migrations: list)`: неприменённые в топологическом порядке; `target` - она и её транзитивные зависимости.
- `collection.to_rollback(history, target=None, *, fake=False)` → `(hooks, migrations)`: применённые в обратном порядке; применяются `migrator.rollback(migrations, hooks)`.
- `migrator.apply(..., fake=True)` - только запись в историю.
- `collection.list()` - все миграции (`.id`, `.depends`, `.path`); `MigrationsCollection.applied_ids(history)`, `MigrationsCollection.statuses(history)`.
- Исключения (все из `classic.migrations`): `BadMigration`, `NoMigration`, `MigrationConflict`, `MigrationLockError`, `MigrationPending`, `MissingSource`, `BadConnectionURI`.

## История
Таблица `migration_table` (в `migration_schema`, если задана) - append-only лог; `history()` возвращает кортежи `(migration_id, created_at, status)`, статус `APPLIED` / `ROLLED_BACK` / `PENDING`. Хеши файлов не сверяются: изменённая применённая миграция повторно не выполнится. Миграция в `PENDING` (упала посреди нетранзакционного выполнения) блокирует apply/rollback - `MigrationPending`.

## CLI
- Консольная команда `migrations list|apply|rollback [migration_name] [--plan] [--fake] [-v]` (или `python -m classic.migrations ...`) читает настройки из окружения/`.env` текущего каталога: `SOURCES` (через `os.pathsep`), `DATABASE_DRIVER`, `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `MIGRATIONS_TABLE`, `MIGRATIONS_SCHEMA`, `MIGRATIONS_LOCK_TIMEOUT`.
- Из кода с готовыми объектами: `CLI(collection=collection, migrator=migrator)(['apply'])` - возвращает код завершения (`0` успех, `1` ошибка, `2` неверные аргументы).
