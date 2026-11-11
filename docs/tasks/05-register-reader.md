# 05. Регистрация читателя

`POST /library/readers` регистрирует читателя.

## Спецификация
- «Агрегат „Читатель“ (`Reader`)» - поля, инварианты, критерии, лимиты тарифов;
  команда `RegisterReader`; «Хранилище» - таблица `readers`; маршрут `/library/readers` `POST`.

## Скиллы
`python-classic-domain` + `classic-criteria`, `python-classic-app`,
`python-classic-adapters-sql-db` + `classic-db-tools`, `python-classic-adapters-http-api`,
`python-classic-composite`.

## Сделать
- Домен: `Reader`, `Membership` (с `loan_limit`), `Contact`, инварианты, критерии, `ReadersRepo`, ошибки.
  Поведение `extend_membership`/`block`/`unblock` - в задаче 06.
- App: `use_cases/readers/register_reader.py`.
- БД: таблица, `sql/aggregates/readers/` с макросами всех критериев `Reader`, репозиторий
  (`Membership`, `Contact` - через `Value` + `Assign`).
- HTTP: ресурс `/library/readers` `POST` → 201.
- Композит: сборка, транзакция, ресурс.

## Критерии приёмки
- Unit домена: инварианты, `loan_limit` по тарифам, критерии `membership_active`, `has_tier`,
  `not_blocked` в обеих формах.
- Unit app: регистрация, права.
- БД: репозиторий, макросы, контрактные тесты.
- HTTP: 201, 400, 403, 422.
- E2E: `POST /library/readers` сохраняет читателя.
