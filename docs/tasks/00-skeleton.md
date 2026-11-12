# 00. Каркас

Сквозной «скелет» без бизнес-функций: пакеты всех слоёв, ошибки и права, тестовая БД,
HTTP-приложение с обработкой ошибок, композит API. После задачи следующие задачи только
добавляют фичи в готовые места.

## Спецификация
- «Права и пользователь»; «HTTP API» - префикс, формат ошибок, коды; «Хранилище» - схема `library`;
  «Процессы» - точка входа `api`; «Окружение для разработки и тестов»; «Ограничения».

## Скиллы
`python-classic-architecture`, `python-classic-app` (разделы про ошибки и права),
`python-classic-adapters-sql-db` + `classic-db-tools` + `classic-migrations`,
`python-classic-adapters-http-api`, `python-classic-composite`.

## Сделать
- `pyproject.toml`: зависимости из «Ограничений», которых не хватает (`tenacity`, `freezegun` и т.п.).
- `app/errors.py` (`AppError`, `AuthError`), `app/roles.py` (`Permissions`, `Account`, `PermissionDenied`).
- `app/domain/errors.py` (`DomainError`).
- `infra/db/`: `settings.py`, `constants.py`, `sql/migrations/0001.init.sql` (пока только схема
  `library`), `sql/schema/DDL.sql`.
- `interfaces/web_api/`: `create_app` (обработчики ошибок 400/403/422, middleware `X-User` → `Account`),
  настройки API с таблицей пользователей.
- `composites/`: настройки, `Engine`, `Hub`, точка входа `interfaces/web_api` (`__main__.py`).
- `tests/conftest.py` (загрузка тестовых настроек), фикстуры тестовой БД
  (`migrated_db`, `db_engine`, `raw_db`) по `python-classic-adapters-sql-db/references/testing.md`.

## Критерии приёмки
- Миграции применяются на тестовой БД и после прогона схемы удаляются.
- HTTP: неизвестный URL → 404; middleware кладёт `Account` для известного `X-User`.
- Обработчики ошибок: `ValidationError` → 400, `AuthError` → 403, `AppError`/`DomainError` → 422,
  тело `[{"type", "msg", "ctx"}]` (проверяется на тестовом ресурсе в тестах).
- Импорт модулей композита не открывает соединений с БД (тест импорта).
