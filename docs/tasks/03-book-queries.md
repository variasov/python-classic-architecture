# 03. Карточка и поиск книг

`GET /library/book?id=` - карточка книги с экземплярами, `GET /library/books` - поиск.

## Спецификация
- «Запросы» - `GetBook`, `FindBooks` (CQRS: запросы не импортируют `app/commands`);
  маршруты `/library/book` `GET`, `/library/books` `GET`.

## Скиллы
`python-classic-app` (запросы, гейтвеи), `python-classic-adapters-sql-db` + `classic-db-tools`
(гейтвеи, динамические шаблоны, `identifier`), `python-classic-adapters-http-api`, `python-classic-composite`.

## Сделать
- App: `queries/books/get_book.py` (`GetBook`, Params, DTO, `GetBookNotFound`, ABC гейтвея),
  `queries/books/find_books.py` (`FindBooks`, Params с проверками, DTO, ABC гейтвея).
- БД: гейтвеи; `GetBook` - статический `.sql`, `FindBooks` - динамический `.sql.tmpl`,
  сортировка по белому списку через `identifier`.
- HTTP: `GET /library/book`, `GET /library/books`; query-параметры разбираются в Params.
- Композит: сборка гейтвеев и запросов, без транзакции (автокоммит).

## Критерии приёмки
- Unit app: in-memory гейтвеи; `GetBookNotFound`; все проверки `FindBooksParams` на границах.
- БД: гейтвеи на тестовой БД - каждый фильтр (`title__contains`, `author`, `only_available`,
  `year_from`/`year_to`), оба варианта `order_by`, `limit`/`offset`; карточка с местом на полке.
- HTTP: 200, 400 на невалидные параметры, 422 на `GetBookNotFound`.
- E2E: книга + экземпляры → карточка и поиск возвращают их.
