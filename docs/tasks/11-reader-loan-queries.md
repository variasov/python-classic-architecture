# 11. Списки читателей и выдач

`GET /library/readers` и `GET /library/loans`.

## Спецификация
- «Запросы» - `FindReaders`, `FindLoans` (текущую дату передаёт usecase-запрос);
  маршруты `/library/readers` `GET`, `/library/loans` `GET`.

## Скиллы
`python-classic-app` (запросы, гейтвеи), `python-classic-adapters-sql-db` + `classic-db-tools`,
`python-classic-adapters-http-api`, `python-classic-composite`.

## Сделать
- App: `queries/readers/find_readers.py`, `queries/loans/find_loans.py` - Params с проверками
  пагинации, DTO, ABC гейтвеев.
- БД: гейтвеи и их SQL.
- HTTP: `GET` на `/library/readers` и `/library/loans`.
- Композит: сборка без транзакций.

## Критерии приёмки
- Unit app: in-memory гейтвеи, дата передаётся в гейтвей, границы `limit`/`offset`.
- БД: число активных и просроченных выдач у читателя; фильтры `reader_id`, `only_overdue`,
  `only_active`; пагинация.
- HTTP: 200, 400.
- E2E: после выдач и возвратов списки отражают текущее состояние.
