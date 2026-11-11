---
name: classic-migrations
description: Справка по API библиотеки classic-migrations (classic.migrations) - формат .sql миграций и директив, MigrationsCollection, Migrator, программное применение и откат, CLI. Загружать перед написанием миграций и кода с classic.migrations (тестовые фикстуры БД, команда миграций). Как библиотека применяется в архитектуре - в python-classic-adapters-sql-db.
license: MIT
compatibility: opencode
---

# classic-migrations: API

Только API, сверенный с версией 2.1. Правила применения (именование `NNNN.description.sql`, схемы модулей, снапшот `sql/schema`) - в `python-classic-adapters-sql-db`.

## Файлы миграций
- Миграция - `.sql` файл в каталоге миграций; id миграции = имя файла без расширения (`0001.init`).
- Директивы - в начальных комментариях файла:
  ```sql
  -- transactional: true
  -- depends: 0001.init

  CREATE TABLE library.readers (...);
  ```
  - `-- depends: <id>, <id>` - зависимости по id; несуществующий id - `NoMigration`.
  - `-- transactional: true|false` - выполнять в транзакции.
- Откат - соседний файл `<id>.rollback.sql`; допускает только `-- transactional`. Без него откат лишь пишет событие в историю.
- Хуки `pre-apply.sql`, `post-apply.sql`, `pre-rollback.sql`, `post-rollback.sql` в каталоге миграций выполняются вне транзакции и в историю не попадают.

## Программное применение
```python
from classic.migrations import MigrationsCollection, Migrator

collection = MigrationsCollection(sources=[str(MIGRATIONS_DIR_PATH)])  # str или list[str]
with Migrator(
    driver='psycopg',                    # имя модуля драйвера строкой
    db_host=settings.DB_HOST,
    db_port=settings.DB_PORT,            # int
    db_name=settings.DB_NAME,
    db_user=settings.DB_USER,
    db_pass=settings.DB_PASS,
    migration_table='migrations',        # по умолчанию
    migration_schema=settings.MIGRATIONS_SCHEMA,
) as migrator:
    hooks, migrations = collection.to_apply(migrator.history())
    migrator.apply(migrations, hooks)
```
- `Migrator` - контекстный менеджер: при входе соединение + advisory-lock, при выходе снятие и закрытие. Методы вызываются только внутри `with`.
- `Migrator` принимает параметры подключения по отдельности, а не строку подключения.
- `collection.to_apply(history, target=None)` → `(hooks, migrations)`: неприменённые в топологическом порядке; `target` - до указанной включительно.
- `collection.to_rollback(history, target=None)` → `(hooks, migrations)`: применённые в обратном порядке; применяются `migrator.rollback(migrations, hooks)`.
- `migrator.apply(..., fake=True)` - только запись в историю.
- `collection.list()` - все миграции; `MigrationsCollection.applied_ids(history)` - множество применённых id.
- Исключения: `BadMigration`, `NoMigration`, `MigrationConflict`, `MigrationLockError`, `InvalidArgument`, `BadConnectionURI` (все из `classic.migrations`).

## История
Таблица `migration_table` (в `migration_schema`, если задана) - append-only лог `(migration_id, created_at, status)`, статус `APPLIED` / `ROLLED_BACK` / `PENDING`. Хеши файлов не сверяются: изменённая применённая миграция повторно не выполнится.

## CLI
- Консольная команда `migrations list|apply|rollback [migration_name] [--plan] [--fake] [-v]` читает настройки из окружения/`.env`: `SOURCES` (через `:`), `DATABASE_DRIVER`, `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `MIGRATIONS_TABLE`, `MIGRATIONS_SCHEMA`.
- Из кода с готовыми объектами: `CLI(collection=collection, migrator=migrator)(['apply'])` - возвращает код завершения.
