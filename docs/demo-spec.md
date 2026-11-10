# Спецификация демо-проекта «Библиотека» (`library`)

## Назначение

Небольшое приложение, которое демонстрирует все правила навыков:
- `python-classic-architecture`;
- `python-classic-adapters-sql-db`;
- `python-classic-adapters-http-api`;
- `python-classic-mutation-testing`.

Проект служит эталоном. В каждом файле код должен буквально следовать навыкам,
а не только работать.

## Предметная область

Библиотека хранит книги в нескольких экземплярах, ведёт читателей
и выдаёт им экземпляры на время.

В модели три агрегата. В каждом агрегате 3 класса и 3 критерия.

### Агрегат «Книга» (`Book`)

| Класс | Вид | Поля |
|---|---|---|
| `Book` | корень, сущность | `id` (int, выдаёт БД), `isbn`, `title`, `authors: list[str]`, `published_year`, `copies: list[Copy]` |
| `Copy` | вложенная сущность | `inventory_number` (идентификатор экземпляра), `shelf: ShelfLocation`, `is_available` |
| `ShelfLocation` | объект-значение, frozen | `hall`, `rack`, `shelf` |

Инварианты (`check()`):
- `isbn` — 13 цифр;
- название не пустое;
- `published_year` не больше текущего года;
- инвентарные номера экземпляров уникальны внутри книги;
- `rack` и `shelf` ≥ 1.

Поведение:
- `add_copy(inventory_number, shelf)`;
- `take_copy(inventory_number)` — бросает доменную ошибку, если экземпляр недоступен;
- `return_copy(inventory_number)`.

Критерии:
- `has_available_copies()`;
- `published_after(year)`;
- `written_by(author)`.

### Агрегат «Читатель» (`Reader`)

| Класс | Вид | Поля |
|---|---|---|
| `Reader` | корень, сущность | `id` (int), `full_name`, `contact: Contact`, `membership: Membership`, `is_blocked` |
| `Membership` | объект-значение, frozen | `tier` (`basic` / `premium`), `valid_until: date` |
| `Contact` | объект-значение, frozen | `email`, `phone` (необязательный) |

Инварианты:
- ФИО не пустое;
- `email` содержит `@`;
- `tier` из допустимого набора.

Лимит одновременно выданных книг зависит от тарифа: `basic` — 3, `premium` — 10.
Константа хранится в `Membership`.

Поведение:
- `extend_membership(until)`;
- `block()`;
- `unblock()`.

Критерии:
- `membership_active(on: date)`;
- `has_tier(tier)`;
- `not_blocked()`.

### Агрегат «Выдача» (`Loan`)

| Класс | Вид | Поля |
|---|---|---|
| `Loan` | корень, сущность | `id` (int), `reader_id` и `book_id` (ссылки на корни других агрегатов), `inventory_number`, `issued_at: date`, `period: LoanPeriod`, `returned_at: date \| None`, `extensions: list[Extension]` |
| `LoanPeriod` | объект-значение, frozen | `start: date`, `due: date` |
| `Extension` | объект-значение, frozen | `extended_at: date`, `new_due: date` |

Инварианты:
- `period.due` > `period.start`;
- продлений не больше 2;
- каждое продление сдвигает срок вперёд;
- `returned_at` не раньше `issued_at`.

Поведение:
- `extend(on, days)` — нельзя продлить просроченную или возвращённую выдачу;
- `close(on)`.

Критерии:
- `overdue(on: date)`;
- `returned()`;
- `due_within(on: date, days)`.

Критерии используются двумя способами:
- в домене — проверка через `is_satisfied_by`, например в `extend` и `IssueLoan`;
- в репозиториях — поиск по дереву критериев, которое транслируется в SQL через `traverse`.

### Доменные usecase (работают с несколькими агрегатами)

`IssueLoan` выдаёт экземпляр читателю.

Проверки:
- `Reader`: `membership_active(today) & not_blocked()`;
- число активных выдач читателя меньше лимита тарифа. Число берётся из `LoansRepo` поиском по `~returned()` и `reader_id`;
- у читателя нет просроченных выдач;
- у книги есть доступный экземпляр.

Действия:
- `Book.take_copy`;
- создаётся `Loan`;
- испускается сигнал `LoanIssued(loan_id, reader_id)`.

`ReturnLoan` принимает экземпляр обратно.

Действия:
- `Loan.close`;
- `Book.return_copy`.

### Внешняя система: каталог ISBN (integration)

- HTTP-сервис вне контура: `GET {ISBN_CATALOG_URL}/books?isbn=<isbn>` → `{"isbn": str, "title": str, "authors": [str], "year": int}`.
- В app объявляется ABC `IsbnCatalog` с методом `find(isbn) -> CatalogBook | None`. `CatalogBook` — датакласс из app.
- В `integrations/isbn_catalog/` лежат:
  - клиент на `urllib3`;
  - pydantic-модель ответа, которая служит контрактом;
  - класс настроек.
- Команда `CreateBookFromCatalog` создаёт книгу по ISBN. Если в каталоге книги нет, бросается доменная ошибка.

### Сигналы и уведомления

- `LoanIssued` обрабатывает подписчик в infra. Он пишет строку в таблицу `notifications` (outbox).
- Планировщик напрямую запускает команду `RemindOverdueLoans` (инстанс собран в композите):
  - находит выдачи по критерию `overdue(on)`;
  - на каждую кладёт уведомление в outbox.

## Сценарии

### Команды (`app/commands/use_cases/`)

| Группа | Usecase | Право |
|---|---|---|
| books | `CreateBook` | `books.edit` |
| books | `CreateBookFromCatalog` | `books.edit` |
| books | `AddCopy` | `books.edit` |
| readers | `RegisterReader` | `readers.edit` |
| readers | `ExtendMembership` | `readers.edit` |
| readers | `BlockReader` | `readers.edit` |
| loans | `IssueLoanCommand` (вызывает доменный `IssueLoan`) | `loans.edit` |
| loans | `ExtendLoan` | `loans.edit` |
| loans | `ReturnLoanCommand` (вызывает доменный `ReturnLoan`) | `loans.edit` |
| loans | `RemindOverdueLoans` (фоновый, без пользователя) | — |

### Запросы (`app/queries/`)

| Группа | Query | Описание |
|---|---|---|
| books | `FindBooks` | Фильтры: подстрока названия (не короче 3 символов, иначе `ValueError` из `__post_init__` → 400), автор, `only_available`, год от/до. Сортировка по белому списку колонок, пагинация `limit`/`offset`. Динамический `.sql.tmpl` |
| books | `GetBook` | Карточка книги с экземплярами и их местом на полке. Статический `.sql`. Если книги нет, бросается ошибка запроса → 422 |
| readers | `FindReaders` | Список читателей с числом активных и просроченных выдач |
| loans | `FindLoans` | Фильтры: `reader_id`, `only_overdue`, `only_active` |

Каждый запрос — конкретный класс со своими DTO и ABC гейтвея. Запросы не импортируют ничего из `app/commands`.

## Права и пользователь

- `app/roles.py`:
  - класс `Permissions` с константами прав;
  - датакласс `Account(login, permissions)`;
  - ошибка приложения `PermissionDenied` (наследник `AppError`).
- Usecase принимает `account: Account` явным параметром и проверяет право в начале `run`.
- HTTP: middleware в `interfaces/api` строит `Account` из заголовка `X-User` по статической таблице
  пользователей из настроек (демо-аутентификация). Результат кладётся в `req.context.account`.

## HTTP API (falcon + waitress)

Префикс `/library`, без параметров в URL:
- `/library/books` — `GET` (FindBooks), `POST` (CreateBook → 201);
- `/library/book` — `GET ?id=` (GetBook);
- `/library/catalog_books` — `POST` (CreateBookFromCatalog → 201);
- `/library/copies` — `POST` (AddCopy);
- `/library/readers` — `GET` (FindReaders), `POST` (RegisterReader → 201);
- `/library/memberships` — `PUT` (ExtendMembership);
- `/library/reader_blocks` — `POST` (BlockReader);
- `/library/loans` — `GET` (FindLoans), `POST` (IssueLoanCommand → 201);
- `/library/loan_extensions` — `POST` (ExtendLoan);
- `/library/returns` — `POST` (ReturnLoanCommand).

Ошибки: `pydantic.ValidationError` → 400, `PermissionDenied` → 403, прочие `AppError`/`DomainError` → 422.

## Хранилище

- PostgreSQL, драйвер `psycopg`, `classic-db-tools`, миграции `classic-migrations`.
- Своя схема БД `library`.
- Таблицы:
  - `books`, `copies`;
  - `readers`;
  - `loans`, `loan_extensions`;
  - `notifications`.
- Миграций минимум две, чтобы было видно `-- depends:`:
  - `0001.init`;
  - `0002.add_notifications`.
- `sql/schema/DDL.sql` всегда актуален. Ограничений CHECK нет.
- Вложенные коллекции (`copies`, `loan_extensions`) синхронизируются upsert-ом с удалением отсутствующих строк.

## Процессы (точки входа в `composites/interfaces/`)

- `api` — `python -m library.composites.interfaces.api`.
- `overdue_scheduler` — `classic-scheduler` по cron напрямую вызывает команду `RemindOverdueLoans` (инстанс из композита) с `on=today`.

## Окружение для разработки и тестов

- Тесты запускаются в WSL против виндового PostgreSQL: адрес хоста Windows из WSL (шлюз из `ip route show default`), порт 5432, пользователь `test`, пароль `test`, БД `test`.
- Виртуальное окружение создаётся в WSL через `uv` на системном Python 3.10.

## Тесты (`tests/`)

По навыку тестирования:
- доменные тесты без БД: инварианты, критерии через `is_satisfied_by`, hypothesis;
- unit-тесты команд и запросов с in-memory репозиториями, гейтвеями и `FakeIsbnCatalog` (ABC из app), без БД и сети;
- тесты репозиториев, гейтвеев и подписчиков на тестовой PostgreSQL с миграциями через `classic.migrations`;
- e2e-тесты композита на тестовой PostgreSQL со stub-сервером каталога (`pytest-httpserver`);
- фабрики данных (параметров, агрегатов) — функции с дефолтами и `**overrides` в `conftest.py`;
- HTTP через `falcon.testing.TestClient`;
- проверки 400, 403 и 422.

Мутационное тестирование домена и app по навыку `python-classic-mutation-testing`.

## Ограничения

- Python ≥ 3.10, пакет `library` в `src/`, namespace-пакеты без `__init__.py`.
- Зависимости:
  - `falcon`, `waitress`, `pydantic`, `pydantic-settings`, `psycopg[binary]`;
  - `classic-db-tools`, `classic-migrations`, `classic-criteria`, `classic-signals`, `classic-scheduler`;
  - `urllib3`;
  - dev: `pytest`, `hypothesis`, `mutmut`.
