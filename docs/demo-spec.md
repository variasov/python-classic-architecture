# Спецификация демо-проекта «Библиотека» (`library`)

## Назначение

Небольшое приложение, которое демонстрирует все правила навыков:
- `python-classic-architecture`;
- `python-classic-app`;
- `python-classic-domain`;
- `python-classic-adapters-sql-db`;
- `python-classic-adapters-http-api`;
- `python-classic-composite`;
- `python-classic-mutation-testing`.

Проект служит эталоном. В каждом файле код должен буквально следовать навыкам,
а не только работать.

## Предметная область

Библиотека хранит книги в нескольких экземплярах, ведёт читателей
и выдаёт им экземпляры на время. О выдачах и просрочках читателям
готовятся уведомления.

В модели пять агрегатов: `Book`, `Copy`, `Reader`, `Loan`, `Notification`.
Идентификаторы корней (`id: int | None`) выдаёт БД, до сохранения они равны `None`.
Агрегаты ссылаются друг на друга только по id корня.

Критерии в домене и в usecase проверяются вызовом на инстансе (`loan.returned()`),
ленивая форма на классе (`Loan.overdue(on=today)`) используется, когда критерий
передаётся в репозиторий (`find`) или комбинируется через `&`, `|`, `~`.
У `find` один вход - критерий: условия по ссылкам на другие агрегаты (`reader_id`,
`book_id`) тоже оформляются критериями.

Текущую дату (`date.today()`) берёт тот, кому она нужна: usecase app или домен.
Usecase получает дату один раз и передаёт её во все вызовы домена в рамках операции.

### Агрегат «Книга» (`Book`)

| Класс | Вид | Поля |
|---|---|---|
| `Book` | корень, сущность | `id: int \| None`, `isbn: str`, `title: str`, `authors: list[str]`, `published_year: int` |

Инварианты (`check()`):
- `isbn` - 13 цифр (`BookIsbnInvalid`);
- название не пустое и не из одних пробелов (`BookTitleEmpty`);
- `published_year` не больше текущего года (`BookPublishedInFuture`).

Критерии:
- `published_after(year)`;
- `written_by(author)`.

Ошибки репозитория: `BookNotFound(id)`.

### Агрегат «Экземпляр» (`Copy`)

Экземпляр - самостоятельный агрегат: на него ссылается выдача, а ссылаться
можно только на корень агрегата.

| Класс | Вид | Поля |
|---|---|---|
| `Copy` | корень, сущность | `id: int \| None`, `book_id: int` (ссылка на `Book`), `inventory_number: str`, `shelf: ShelfLocation`, `is_available: bool = True` |
| `ShelfLocation` | объект-значение, frozen | `hall: str`, `rack: int`, `shelf: int` |

Инварианты:
- инвентарный номер не пустой (`InventoryNumberEmpty`);
- `rack` и `shelf` ≥ 1 (`ShelfLocationInvalid`).

Уникальность инвентарного номера - правило между агрегатами, его проверяет
команда `AddCopy` (см. ниже).

Поведение:
- `take()` - бросает `CopyNotAvailable(copy_id)`, если экземпляр уже выдан;
- `give_back()` - бросает `CopyNotTaken(copy_id)`, если экземпляр не выдан.

Критерии:
- `available()`;
- `of_book(book_id)`;
- `with_inventory_number(inventory_number)`.

Ошибки репозитория: `CopyNotFound(id)`.

### Агрегат «Читатель» (`Reader`)

| Класс | Вид | Поля |
|---|---|---|
| `Reader` | корень, сущность | `id: int \| None`, `full_name: str`, `contact: Contact`, `membership: Membership`, `is_blocked: bool = False` |
| `Membership` | объект-значение, frozen | `tier: str` (`basic` / `premium`), `valid_until: date` |
| `Contact` | объект-значение, frozen | `email: str`, `phone: str \| None = None` |

Лимит одновременно выданных экземпляров зависит от тарифа: `basic` - 3, `premium` - 10.
Таблица лимитов - `ClassVar` в `Membership`, лимит читателя отдаёт свойство `Membership.loan_limit`.

Инварианты:
- ФИО не пустое (`ReaderNameEmpty`);
- `email` содержит `@` (`ContactEmailInvalid`);
- `tier` из допустимого набора (`MembershipTierInvalid`).

Поведение:
- `extend_membership(until)` - новая дата должна быть позже текущей `valid_until` (`MembershipNotExtended`);
- `block()` - бросает `ReaderAlreadyBlocked`, если читатель уже заблокирован;
- `unblock()` - бросает `ReaderNotBlocked`, если читатель не заблокирован.

Критерии:
- `membership_active(on: date)`;
- `has_tier(tier)`;
- `not_blocked()`.

Ошибки репозитория: `ReaderNotFound(id)`.

### Агрегат «Выдача» (`Loan`)

| Класс | Вид | Поля |
|---|---|---|
| `Loan` | корень, сущность | `id: int \| None`, `reader_id: int` (ссылка на `Reader`), `copy_id: int` (ссылка на `Copy`), `period: LoanPeriod`, `returned_at: date \| None = None`, `extensions: list[Extension]` |
| `LoanPeriod` | объект-значение, frozen | `start: date` (дата выдачи), `due: date` |
| `Extension` | объект-значение, frozen | `extended_at: date`, `new_due: date` |

Срок выдачи - 14 дней (`Loan.TERM_DAYS: ClassVar`), продлений не больше 2 (`Loan.MAX_EXTENSIONS: ClassVar`).

Инварианты:
- `period.due` > `period.start` (`LoanPeriodInvalid`);
- продлений не больше 2 (`TooManyExtensions(loan_id)`);
- каждое продление сдвигает срок вперёд относительно предыдущего (`ExtensionNotForward(loan_id)`);
- `returned_at` не раньше `period.start` (`LoanReturnedBeforeIssue(loan_id)`).

Поведение:
- `extend(on, days)` - сдвигает `period.due` на `days` дней и добавляет `Extension`.
  Возвращённую выдачу продлить нельзя (`LoanAlreadyReturned(loan_id)`), просроченную - тоже (`LoanOverdue(loan_id)`).
  Проверки - вызовом критериев на инстансе: `self.returned()`, `self.overdue(on=on)`;
- `close(on)` - ставит `returned_at`; повторный возврат - `LoanAlreadyReturned(loan_id)`.

Критерии:
- `overdue(on: date)`;
- `returned()`;
- `due_within(on: date, days)`;
- `of_reader(reader_id)`.

Ошибки репозитория: `LoanNotFound(id)`.

### Агрегат «Уведомление» (`Notification`)

Уведомление - запись для читателя, которую позже отправит внешний канал (вне рамок демо).

| Класс | Вид | Поля |
|---|---|---|
| `Notification` | корень, сущность | `id: int \| None`, `reader_id: int` (ссылка на `Reader`), `loan_id: int` (ссылка на `Loan`), `kind: NotificationKind`, `created_at: date` |
| `NotificationKind` | перечисление (`Enum`) | `loan_issued`, `loan_overdue` |

Критерии:
- `about_loan(loan_id)`;
- `of_kind(kind)`.

Ошибки репозитория: `NotificationNotFound(id)`.

### Сигналы

Контракты сигналов - в `app/commands/signals.py`:
- `LoanIssued(loan_id: int, reader_id: int)` - выдача оформлена. Домен сигналов не знает:
  сигнал испускает команда `IssueLoan` после вызова доменного `BorrowCopy`.

### Доменные usecase (работают с несколькими агрегатами)

`BorrowCopy` выдаёт экземпляр читателю. Зависимости: `ReadersRepo`, `CopiesRepo`, `LoansRepo`.
`run(reader_id, copy_id, on) -> Loan`.

Проверки:
- `reader.membership_active(on=on) and reader.not_blocked()`, иначе `ReaderCannotBorrow(reader_id)`;
- число активных выдач читателя меньше `reader.membership.loan_limit`, иначе `LoanLimitReached(reader_id, limit)`.
  Выдачи берутся из `LoansRepo.find(Loan.of_reader(reader_id=...) & ~Loan.returned())`;
- у читателя нет просроченных выдач (`LoansRepo.find(Loan.of_reader(reader_id=...) & Loan.overdue(on=on))`),
  иначе `ReaderHasOverdueLoans(reader_id)`;
- экземпляр доступен - проверяет `copy.take()` (`CopyNotAvailable`).

Действия:
- `copy.take()`, сохранение экземпляра;
- создаётся и сохраняется `Loan` с `period = LoanPeriod(start=on, due=on + TERM_DAYS)`;
- испускается `LoanIssued(loan_id, reader_id)`.

`ReturnCopy` принимает экземпляр обратно. Зависимости: `LoansRepo`, `CopiesRepo`.
`run(loan_id, on) -> None`.

Действия:
- `loan.close(on)`;
- `copy.give_back()`;
- сохранение обоих агрегатов.

`NotifyOnLoanIssued` - реакция на `LoanIssued`, класс в `app/commands/loans/`. Зависимости: `NotificationsRepo`, `Hub`.
Подписывается в конструкторе, на каждое событие сохраняет `Notification(kind=loan_issued, created_at=date.today())`.
Выполняется синхронно, в транзакции команды, испустившей сигнал.

### Внешняя система: каталог ISBN (integration)

- HTTP-сервис вне контура: `GET {ISBN_CATALOG_URL}/books?isbn=<isbn>`:
  - 200 → `{"isbn": str, "title": str, "authors": [str], "year": int}`;
  - 404 → книги в каталоге нет.
- ABC `IsbnCatalog` с методом `find(isbn) -> CatalogBook | None` нужен одной команде,
  поэтому объявляется в её файле (`commands/books/create_book_from_catalog.py`) вместе
  с датаклассом `CatalogBook(isbn, title, authors, year)`.
- `integrations/isbn_catalog/`:
  - `client.py` - датакласс контракта ответа `CatalogBookPayload` и клиент `IsbnCatalogClient(IsbnCatalog)`
    на `urllib3`. Ответ разбирается `pydantic.TypeAdapter(CatalogBookPayload)` и переводится в `CatalogBook`;
    404 → `None`; прочие коды и невалидный ответ → `IsbnCatalogUnavailable` (исключение интеграции);
  - `settings.py` - `IsbnCatalogSettings`: `ISBN_CATALOG_URL` (чувствительная, без дефолта),
    `ISBN_CATALOG_TIMEOUT` (обычная, дефолт 5 секунд).
- Вызов `find` клиента оборачивается в композите аспектом повтора (`tenacity.retry(...)` напрямую в `composites/integrations/isbn_catalog/client.py`).

### Уведомления

- О выдаче: реакция `NotifyOnLoanIssued` на сигнал `LoanIssued`.
- О просрочке: команда `RemindOverdueLoans`, её запускает планировщик (см. «Процессы»).

## Сценарии

### Права и пользователь

Аутентификация и авторизация будут вынесены в отдельный модуль. Пока его нет, для демо
они описаны здесь и реализуются внутри проекта:
- `app/roles.py`:
  - класс `Permissions` с константами прав;
  - датакласс `Account(login, permissions)`;
  - ошибка доступа `PermissionDenied(login, permission)` - наследник `AuthError` (не `AppError`).
- `app/errors.py`: базовые классы `AppError` (ошибки приложения) и `AuthError` (ошибки авторизации).
  `AuthError` не наследуется от `AppError`: отказ в доступе - не ошибка бизнеса, и HTTP отдаёт
  на него 403, а не 422.
- Usecase с правами имеет сигнатуру `run(params: <UseCase>Params, account: Account)` и проверяет право
  первой строкой `run`, до обращений к хранилищу.
- HTTP: middleware в `interfaces/web_api` строит `Account` из заголовка `X-User` по статической таблице
  пользователей из настроек (демо-аутентификация). Результат кладётся в `req.context.account`.

### Команды (`app/commands/`)

Ошибки, объявленные в домене, - `DomainError`; ошибки, объявленные в файле команды, - `AppError`.
Все команды проверяют право в начале `run` (`PermissionDenied`).

| Группа | Usecase | Право | Params | Результат |
|---|---|---|---|---|
| books | `CreateBook` | `books.edit` | `isbn`, `title`, `authors`, `published_year` | `int` (id книги) |
| books | `CreateBookFromCatalog` | `books.edit` | `isbn` | `int` (id книги) |
| books | `AddCopy` | `books.edit` | `book_id`, `inventory_number`, `hall`, `rack`, `shelf` | `int` (id экземпляра) |
| readers | `RegisterReader` | `readers.edit` | `full_name`, `email`, `phone`, `tier`, `valid_until` | `int` (id читателя) |
| readers | `ExtendMembership` | `readers.edit` | `reader_id`, `valid_until` | — |
| readers | `BlockReader` | `readers.edit` | `reader_id` | — |
| readers | `UnblockReader` | `readers.edit` | `reader_id` | — |
| loans | `IssueLoan` | `loans.edit` | `reader_id`, `copy_id` | `int` (id выдачи) |
| loans | `ExtendLoan` | `loans.edit` | `loan_id`, `days` | — |
| loans | `ReturnLoan` | `loans.edit` | `loan_id` | — |
| loans | `RemindOverdueLoans` | — (фоновый, без пользователя) | — | `int` (число новых уведомлений) |

Проверки и действия:
- `CreateBook`: собирает `Book`, сохраняет. Ошибки - инварианты `Book`.
- `CreateBookFromCatalog`: `IsbnCatalog.find(isbn)`; `None` → `BookNotInCatalog(isbn)` (`AppError`,
  в файле команды). Иначе собирает `Book` из `CatalogBook` и сохраняет.
- `AddCopy`: `BooksRepo.get_by_id(book_id)` (`BookNotFound`); инвентарный номер свободен -
  `CopiesRepo.find(Copy.with_inventory_number(...))` пуст, иначе `InventoryNumberTaken(inventory_number)`
  (`AppError`, в файле команды). Собирает `Copy`, сохраняет.
- `RegisterReader`: собирает `Reader`, сохраняет.
- `ExtendMembership`: `get_by_id`, `reader.extend_membership(until)`, сохраняет.
- `BlockReader` / `UnblockReader`: `get_by_id`, `block()` / `unblock()`, сохраняет.
- `IssueLoan`: вызывает доменный `BorrowCopy.run(reader_id, copy_id, on=date.today())`,
  затем испускает `LoanIssued` через `Hub`.
- `ExtendLoan`: `get_by_id`, `loan.extend(on=date.today(), days)`, сохраняет.
- `ReturnLoan`: вызывает доменный `ReturnCopy.run(loan_id, on=date.today())`.
- `RemindOverdueLoans`: `on = date.today()`; находит выдачи `Loan.overdue(on=on)`; для каждой,
  у которой ещё нет уведомления `Notification.about_loan(loan_id) & Notification.of_kind(loan_overdue)`,
  сохраняет `Notification(kind=loan_overdue, created_at=on)`.

Проверки `Params` в `__post_init__` (`ValueError` → 400):
- `CreateBookParams`: список `authors` не пустой;
- `CreateBookFromCatalogParams`, `CreateBookParams`: `isbn` - 13 символов;
- `AddCopyParams`: `rack`, `shelf` ≥ 1;
- `ExtendLoanParams`: `0 < days <= 30` (`MAX_DAYS: ClassVar`).

### Запросы (`app/queries/`)

Каждый запрос - конкретный класс со своими `Params`, DTO, ошибками и ABC гейтвея в одном файле.
Запросы не импортируют ничего из `app/commands`. Запросам, которым нужна текущая дата, её
передаёт в гейтвей сам usecase-запрос (`date.today()`), а не `now()` БД.

| Группа | Query | Params | Описание |
|---|---|---|---|
| books | `FindBooks` | `title__contains`, `author`, `only_available`, `year_from`, `year_to`, `order_by: Literal['title', 'published_year']`, `limit`, `offset` | Подстрока названия не короче 3 символов, `year_from <= year_to`, `0 < limit <= 100`, `offset >= 0` - иначе `ValueError` из `__post_init__` → 400. Сортировка по белому списку. Динамический `.sql.tmpl` |
| books | `GetBook` | `id` | Карточка книги с экземплярами и их местом на полке. Статический `.sql`. Нет книги - `GetBookNotFound(id)` (`AppError`, в файле запроса) → 422 |
| readers | `FindReaders` | `limit`, `offset` | Список читателей с числом активных и просроченных на сегодня выдач |
| loans | `FindLoans` | `reader_id`, `only_overdue`, `only_active`, `limit`, `offset` | Выдачи; «просрочена» - на сегодняшнюю дату |

## HTTP API (falcon + waitress)

Префикс `/library`, без параметров в URL:
- `/library/books` - `GET` (FindBooks), `POST` (CreateBook → 201);
- `/library/book` - `GET ?id=` (GetBook);
- `/library/catalog_books` - `POST` (CreateBookFromCatalog → 201);
- `/library/copies` - `POST` (AddCopy → 201);
- `/library/readers` - `GET` (FindReaders), `POST` (RegisterReader → 201);
- `/library/memberships` - `PUT` (ExtendMembership);
- `/library/reader_blocks` - `POST` (BlockReader), `DELETE ?reader_id=` (UnblockReader);
- `/library/loans` - `GET` (FindLoans), `POST` (IssueLoan → 201);
- `/library/loan_extensions` - `POST` (ExtendLoan);
- `/library/returns` - `POST` (ReturnLoan).

Ответ на создание - `{"id": int}` (DTO ответа в файле ресурса).

Ошибки (тело - `[{"type", "msg", "ctx"}]`):
- `pydantic.ValidationError` → 400;
- `AuthError` (`PermissionDenied`) → 403;
- `AppError` / `DomainError` → 422, в том числе `<Aggregate>NotFound`, `GetBookNotFound`, `BookNotInCatalog`;
- 404 - только неизвестный URL (нет маршрута).

## Хранилище

- PostgreSQL, драйвер `psycopg`, `classic-db-tools`, миграции `classic-migrations`.
- Своя схема БД `library`.
- Таблицы:
  - `books`, `book_authors` (`book_id`, `position`, `name`);
  - `copies` (`inventory_number` - уникальный индекс);
  - `readers`;
  - `loans`, `loan_extensions` (`loan_id`, `position`, `extended_at`, `new_due`);
  - `notifications`.
- Внешние ключи - с `ON DELETE CASCADE`: `book_authors → books`, `copies → books`,
  `loans → readers`, `loans → copies`, `loan_extensions → loans`,
  `notifications → readers`, `notifications → loans`.
- Миграций минимум две, чтобы было видно `-- depends:`:
  - `0001.init`;
  - `0002.add_notifications`.
- `sql/schema/DDL.sql` всегда актуален. Ограничений CHECK нет.
- Вложенные коллекции (`book_authors`, `loan_extensions`) - объекты-значения без собственного id.
  При сохранении агрегата они перезаписываются целиком (delete + insert); `position` хранит порядок
  элементов в списке.
- Каждый агрегат - свой каталог `sql/aggregates/<aggregate>/` с `criteria.sql.tmpl`;
  каждый критерий агрегата имеет SQL-макрос.

## Процессы (точки входа в `composites/interfaces/`)

- `web_api` - `python -m library.composites.interfaces.web_api`. Импортирует реакцию
  `NotifyOnLoanIssued`, иначе сигнал `LoanIssued` потеряется.
- `overdue_scheduler` - `classic-scheduler` по cron (`0 9 * * *`) вызывает `remind_overdue_loans.run`
  (инстанс из композита).

Транзакции навешиваются в композите на `run` каждой команды и на `run` команды в задаче планировщика.
Доменные usecase и реакции (классы в `commands/`) работают в транзакции вызвавшей команды и отдельно не оборачиваются.
Запросы работают в автокоммите.

## Окружение для разработки и тестов

- Тесты запускаются в WSL против виндового PostgreSQL: адрес хоста Windows из WSL (шлюз из `ip route show default`), порт 5432, пользователь `test`, пароль `test`, БД `test`.
- Виртуальное окружение создаётся в WSL через `uv` на системном Python 3.10.
- Тестовые значения настроек - в `.env.test` (в `.gitignore`), загружаются корневым `tests/conftest.py`.

## Тесты (`tests/`)

По `references/testing.md` навыков:
- `tests/unit/domain/` - по файлу на агрегат и доменный usecase: инварианты, поведение,
  критерии в обеих формах (на инстансе и `is_satisfied_by` у ленивой формы, комбинации `&`, `|`, `~`),
  hypothesis и «почти валидные» входы; время, если нужно, замораживается `freezegun`;
- `tests/unit/app/` - по файлу на usecase: команды и запросы с in-memory репозиториями, гейтвеями
  и `FakeIsbnCatalog` (реализует ABC из app), без БД и сети; время - `freezegun`; проверки `Params`
  на границах, права (`PermissionDenied`), испущенные сигналы;
- `tests/adapters/infra/db/` - репозитории, гейтвеи на тестовой PostgreSQL с миграциями через
  `classic.migrations`; каждый SQL-макрос критерия даёт ту же выборку, что `is_satisfied_by`;
  контрактные тесты репозиториев, параметризованные DB- и in-memory-реализацией;
- `tests/adapters/interfaces/web_api/` - ресурсы через `falcon.testing.TestClient` и `create_app` с `FakeUseCase`:
  разбор запроса в `Params`, коды 200/201, 400, 403, 422, 404 на неизвестный URL;
- `tests/adapters/integrations/isbn_catalog/` - клиент против `pytest-httpserver`: перевод ответа в
  `CatalogBook`, 404 → `None`, ошибка HTTP и невалидный ответ → `IsbnCatalogUnavailable`, отправленный запрос;
- `tests/composites/` - e2e на тестовой PostgreSQL со stub-сервером каталога (`pytest-httpserver`):
  по одному сценарию на маршрут, откат транзакции, реакция `NotifyOnLoanIssued` зарегистрирована,
  retry каталога, задача планировщика;
- фабрики данных (параметров, агрегатов) - функции с дефолтами и `**overrides` в `conftest.py`.

Мутационное тестирование домена и app по навыку `python-classic-mutation-testing`.

## Ограничения

- Python ≥ 3.10, пакет `library` в `src/`, namespace-пакеты без `__init__.py`.
- Зависимости:
  - `falcon`, `waitress`, `pydantic`, `pydantic-settings`, `psycopg[binary]`;
  - `classic-db-tools`, `classic-migrations`, `classic-criteria`, `classic-signals`, `classic-scheduler`;
  - `urllib3`, `tenacity`;
  - dev: `pytest`, `pytest-httpserver`, `hypothesis`, `freezegun`, `python-dotenv`, `mutmut`,
    `pyright`, `ruff`, `vulture`.

## Вне рамок

- Отправка уведомлений во внешний канал.
- Права на запросы и поведение при отсутствующем/неизвестном `X-User`.
