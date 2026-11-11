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

### 02. Экземпляры книг (выполнено)
- Домен `domain/copy.py`: `Copy` (id последним полем, как у `Book`), frozen `ShelfLocation`, инварианты
  `InventoryNumberEmpty` / `ShelfLocationInvalid`, поведение `take`/`give_back` и ошибки
  `CopyNotAvailable` / `CopyNotTaken`, критерии `available`/`of_book`/`with_inventory_number`,
  `CopiesRepo` (`get_by_id`/`save`/`find`), `CopyNotFound`.
- Команда `AddCopy` (`use_cases/books/add_copy.py`): право `books.edit` первой строкой, `BookNotFound`,
  проверка уникальности через `CopiesRepo.find(Copy.with_inventory_number(...))`, `InventoryNumberTaken`.
  `AddCopyParams.MIN_POSITION` - ClassVar, `rack`/`shelf` >= 1 в `__post_init__`.
- БД: таблица `library.copies` в `0001.init.sql` и `DDL.sql` (`book_id` с `ON DELETE CASCADE`,
  уникальный индекс `copies_inventory_number_uq`), `aggregates/copies/{get_by_id,insert,update}.sql`,
  `find.sql.tmpl`, `criteria.sql.tmpl`. `ShelfLocation` маппится `Value` + `Assign('shelf')`.
- HTTP: `POST /library/copies` -> 201 `{"id"}`; ресурс и инстансы в композите, транзакция на `run`.
- Тесты: домен (инварианты, поведение, критерии в обеих формах и комбинациях, hypothesis на границы),
  команда (создание, `BookNotFound`, `InventoryNumberTaken`, права, границы rack/shelf),
  адаптер (контракт DB+in-memory, отсутствие записи при невалидном агрегате, каждый SQL-макрос и
  комбинации сверяются с `is_satisfied_by`), HTTP (201/400/403/422), e2e книга -> экземпляр и
  повтор инвентарного номера -> 422.
- Общие фикстуры `books_repo`/`create_book` перенесены в `tests/unit/app/conftest.py`; корневой
  `tests/conftest.py` дополнен `InMemoryCopiesRepo` и `copy_factory`.
- Состояние: `pytest 93 passed`, `pyright 0 errors`. ruff/vulture не запускались: их нет в `.venv-wsl`,
  установка запрещена. Отклонений от спецификации нет.

### 03. Карточка и поиск книг (выполнено)
- App: `app/queries/books/get_book.py` (`GetBookParams`, `BookCopyDTO`/`BookCardDTO`, `GetBookNotFound`,
  `GetBookGateway`, `GetBook`), `find_books.py` (`FindBooksParams` с `ClassVar`-границами и проверками
  в `__post_init__`, `BookListItemDTO`, `FindBooksGateway`, `FindBooks`). Запросы не импортируют
  `app/commands`, DTO свои.
- БД: `infra/db/gateways/get_book.py` и `find_books.py` (два файла по правилу «класс=файл»);
  `sql/gateways/books/get_book.sql` - статический запрос с `LEFT JOIN copies` и подзапросом авторов,
  карточка маппится `Entity` + `Append('copy')`; `find_books.sql.tmpl` - динамический, `{% if %}` на
  каждый фильтр, сортировка из белого списка `SORT_COLUMNS` через `identifier`, `LIMIT/OFFSET`
  биндятся. Дополнительно в списке отдаётся `available_copies` (число доступных экземпляров).
- `GetBookGateway.run` возвращает `BookCardDTO | None`, `GetBookNotFound` бросает usecase-запрос:
  так ошибка запроса остаётся в app, а гейтвей только читает.
- HTTP: `BooksResource.on_get` (`GET /library/books`), `BookResource.on_get` (`GET /library/book?id=`),
  `create_app` принимает `book` четвёртым ресурсом; тестовый `conftest` обновлён. Запросы в композите
  без транзакции (автокоммит); инстансы в `composites/app/queries/books`, `composites/infra/db/gateways`,
  `composites/interfaces/api/resources/book.py`.
- Тесты: unit запросов с fake-гейтвеями и все границы `FindBooksParams`; гейтвеи на тестовой БД
  (каждый фильтр, комбинации, оба `order_by`, пагинация, пустой результат, карточка с местом на полке);
  HTTP 200/400/422; e2e книга + 2 экземпляра -> карточка и поиск.
- Состояние: `pytest 148 passed`, `pyright 0 errors`. ruff/vulture не запускались: их нет в `.venv-wsl`,
  установка запрещена. Отклонения: гейтвеи разложены в два файла (не `books.py`) по правилу
  «класс=файл»; `BookListItemDTO` содержит `available_copies`.
