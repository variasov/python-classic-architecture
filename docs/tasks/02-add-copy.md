# 02. Экземпляры книг

`POST /library/copies` добавляет экземпляр книги на полку.

## Спецификация
- «Агрегат „Экземпляр“ (`Copy`)»; команда `AddCopy` и проверки `AddCopyParams`;
  «Хранилище» - таблица `copies` (уникальный индекс `inventory_number`); маршрут `/library/copies`.

## Скиллы
`python-classic-domain` + `classic-criteria`, `python-classic-app`,
`python-classic-adapters-sql-db` + `classic-db-tools`, `python-classic-adapters-http-api`,
`python-classic-composite`.

## Сделать
- Домен: `Copy`, `ShelfLocation`, поведение `take()`/`give_back()`, критерии, `CopiesRepo`, ошибки.
- App: `commands/books/add_copy.py` - `AddCopy`, `AddCopyParams`, `InventoryNumberTaken`.
- БД: таблица, `sql/aggregates/copies/` с макросами всех критериев `Copy`, репозиторий
  (`ShelfLocation` маппится через `Value` + `Assign`).
- HTTP: ресурс `/library/copies` `POST` → 201.
- Композит: сборка, транзакция, регистрация ресурса.

## Критерии приёмки
- Unit домена: инварианты, `take`/`give_back` и их ошибки, критерии в обеих формах.
- Unit app: создание, `BookNotFound`, `InventoryNumberTaken`, права, границы `rack`/`shelf`.
- БД: репозиторий и макросы (`available`, `of_book`, `with_inventory_number`), контрактные тесты.
- HTTP: 201, 400, 403, 422.
- E2E: книга (`POST /library/books`) → экземпляр (`POST /library/copies`); повтор инвентарного номера → 422.
