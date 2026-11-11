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

### 04. Книга из каталога ISBN (выполнено)
- App: `use_cases/books/create_book_from_catalog.py` - `CatalogBook`, ABC `IsbnCatalog.find`,
  `CreateBookFromCatalogParams` (13 символов), `BookNotInCatalog` (`AppError`, в файле команды), право `books.edit`.
- Интеграция: `integrations/isbn_catalog/{client,settings}.py` - `CatalogBookPayload`, `IsbnCatalogClient`
  на `urllib3.PoolManager`, `GET {URL}/books?isbn=...` (`urlencode`), `TypeAdapter(...).validate_json`;
  404 -> `None`, прочие коды/невалидный JSON/сетевые ошибки -> `IsbnCatalogUnavailable`.
- Композит: `composites/aspects/retry.py` на `find`, `composites/integrations/isbn_catalog/` (настройки и
  клиент), команда с `engine.transaction`, ресурс `interfaces/api/resources/catalog_books.py` (`POST` -> 201).
- ОТКЛОНЕНИЕ: `tenacity` в `.venv-wsl` нет, установка запрещена. Аспект повтора на stdlib
  (`functools.wraps` + `time.sleep`): 3 попытки, паузы 0.1/0.2 с, исходное исключение пробрасывается.
- Перенос `create_app`: middleware, обработчики ошибок и маршруты переехали в `interfaces/api/app.py`
  без импорта композита и инстансов настроек; `composites/interfaces/api/wsgi.py` теперь только
  импортирует фабрику, ресурсы и собирает модульный `app`. Тесты API импортируют фабрику из
  `library.interfaces.api.app` (отступление от скилла HTTP, иначе импорт требовал бы `ISBN_CATALOG_URL`).
- Тесты: unit app (`FakeIsbnCatalog`, создание, `BookNotInCatalog`, права, длины isbn); клиент против
  `pytest-httpserver` (200/404/500/невалидный JSON/неполный payload/сеть, путь и query запроса);
  HTTP 201/400/403/422; e2e со stub-каталогом (создание и retry после первого 500).
- `tests/conftest.py` задаёт `ISBN_CATALOG_URL` по умолчанию, `tests/composites/conftest.py` поднимает
  session-сервер и подставляет адрес. Состояние: `pytest 166 passed`, `pyright 0 errors`; ruff/vulture
  не запускались (их нет, установка запрещена).

### 05. Регистрация читателя (выполнено)
- Домен `domain/reader.py`: frozen `Contact(email, phone=None)` и `Membership(tier, valid_until)` с
  `ClassVar`-таблицей лимитов (basic 3, premium 10) и `loan_limit`; `Reader` (`id` последним),
  рекурсивный `check()`, критерии `membership_active`/`has_tier`/`not_blocked`, `ReadersRepo`,
  `ReaderNotFound`. Поведение `extend_membership`/`block`/`unblock` не добавлялось - задача 06.
- App: `use_cases/readers/register_reader.py` - `RegisterReaderParams` без дополнительных проверок,
  право `readers.edit` первой строкой, сборка агрегата и `save`.
- БД: `library.readers` в `0001.init.sql` и `DDL.sql`; `aggregates/readers/{get_by_id,insert,update}.sql`,
  `find.sql.tmpl`, `criteria.sql.tmpl` на каждый макрос. `Contact`/`Membership` - `Value` +
  `Assign('contact')`/`Assign('membership')`, колонки `contact__*`/`membership__*`; запись плоскими
  параметрами `contact_email`, `contact_phone`, `membership_tier`, `membership_valid_until`.
  Репозиторий - `infra/db/repos/readers.py` (`DbReadersRepo`).
- HTTP: `POST /library/readers` -> 201 `{"id"}`; `create_app` принимает `readers` третьим ресурсом,
  обновлены `wsgi.py` и API-conftest. Композит: инстансы репозитория, команды (с `engine.transaction`)
  и ресурса.
- Тесты: домен (инварианты, `loan_limit`, критерии в обеих формах и комбинациях, hypothesis на пустые
  ФИО/email без `@`/неизвестные тарифы, граница `valid_until`); команда (регистрация, телефон `None`,
  права, инварианты не обходятся); адаптер (контракт DB+in-memory, roundtrip VO, обновление,
  `ReaderNotFound`, невалидный не пишется, каждый SQL-макрос и комбинации сверяются с
  `is_satisfied_by`); HTTP (201/400/403/422); e2e с очисткой `DELETE FROM library.readers` по email.
- Корневой `tests/conftest.py`: `InMemoryReadersRepo`, `reader_factory` (по умолчанию
  `Membership('basic', TOMORROW)`).
- Состояние: `pytest 224 passed`, `pyright 0 errors`. ruff/vulture не запускались (их нет в `.venv-wsl`).

### 06. Абонемент и блокировка читателя (выполнено)
- Домен `domain/reader.py`: `Reader.extend_membership(until)` (граница `until == valid_until` - ошибка,
  membership заменяется через `dataclasses.replace`), `block()`, `unblock()`; ошибки
  `MembershipNotExtended(reader_id, until)`, `ReaderAlreadyBlocked(reader_id)`, `ReaderNotBlocked(reader_id)` -
  датаклассы `DomainError` с `__str__`.
- `reader_id` в новых ошибках - `int | None`, как `copy_id` в `CopyNotAvailable`: агрегат может быть ещё
  не сохранён, когда поведение бросает ошибку.
- App: `use_cases/readers/{extend_membership,block_reader,unblock_reader}.py` - `Params`, право
  `readers.edit` первой строкой `run`, `get_by_id`, поведение, `save`, логгер в конструкторе.
- HTTP: `MembershipsResource.on_put` (`PUT /library/memberships`, тело `ExtendMembershipParams`);
  `ReaderBlocksResource.on_post` (`POST /library/reader_blocks`, тело `BlockReaderParams`) и `on_delete`
  (`DELETE /library/reader_blocks?reader_id=`, query через `validate_python`). Действия отдают 200,
  тело не пишется. `create_app` принимает `memberships` и `reader_blocks` последними аргументами;
  обновлены `wsgi.py`, композитные инстансы ресурсов и `tests/adapters/interfaces/api/conftest.py`.
- Композит: `composites/app/commands/{extend_membership,block_reader,unblock_reader}.py` с
  `engine.transaction` на `run`; инстансы ресурсов в `composites/interfaces/api/resources/`.
- Тесты: домен (успех, tier сохраняется, граница и более ранняя дата, повторная блокировка/разблокировка,
  hypothesis по датам, `__str__`); команды (успех и состояние репозитория, `ReaderNotFound`, доменные
  ошибки, права до обращения к хранилищу); HTTP (200, 400 на тело и query, 403, 422 с `ctx`); e2e
  регистрация -> продление -> блокировка -> повторная блокировка 422 -> разблокировка -> повторная
  разблокировка 422, очистка `DELETE FROM library.readers` по email.
- Состояние: `pytest 273 passed`, `pyright 0 errors`. ruff/vulture не запускались (их нет в `.venv-wsl`).
