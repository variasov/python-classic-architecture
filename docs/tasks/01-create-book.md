# 01. Создание книги

`POST /library/books` создаёт книгу.

## Спецификация
- «Агрегат „Книга“ (`Book`)»; команда `CreateBook` и проверки `CreateBookParams`;
  «Хранилище» - таблицы `books`, `book_authors`; маршрут `/library/books` `POST`.

## Скиллы
`python-classic-domain` + `classic-criteria`, `python-classic-app`,
`python-classic-adapters-sql-db` + `classic-db-tools`, `python-classic-adapters-http-api`,
`python-classic-composite`.

## Сделать
- Домен: `Book` с инвариантами и критериями, `BooksRepo` (ABC), `BookNotFound` и ошибки инвариантов.
- App: `commands/books/create_book.py` - `CreateBook`, `CreateBookParams`.
- БД: таблицы в `0001.init.sql` и `DDL.sql`; `sql/aggregates/books/` (запросы и `criteria.sql.tmpl`
  с макросами всех критериев `Book`); репозиторий `BooksRepo` (`get_by_id`, `save`, `find`).
- HTTP: ресурс `/library/books` `POST` → 201 `{"id": int}`.
- Композит: сборка репозитория и usecase, транзакция на `run`, регистрация ресурса.

## Критерии приёмки
- Unit домена: каждый инвариант, критерии `published_after`, `written_by` в обеих формах и в комбинациях.
- Unit app: создание, `PermissionDenied` без `books.edit`, границы `CreateBookParams` (`authors`, `isbn`).
- БД: `save`/`get_by_id` (вставка, обновление, авторы в порядке `position`), `BookNotFound`,
  каждый SQL-макрос даёт ту же выборку, что `is_satisfied_by`; контрактные тесты DB/in-memory.
- HTTP: 201, 400 на невалидное тело, 403, 422 на нарушение инварианта.
- E2E: `POST /library/books` на тестовой БД сохраняет книгу; ошибка внутри `run` откатывает транзакцию.
