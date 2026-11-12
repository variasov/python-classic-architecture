# 07. Выдача экземпляра

`POST /library/loans` выдаёт экземпляр читателю.

## Спецификация
- «Агрегат „Выдача“ (`Loan`)» - поля, инварианты, критерии (поведение `extend`/`close` - задача 08);
  «Сигналы» - `LoanIssued`; доменный usecase `BorrowCopy`; команда `IssueLoan` (испускает `LoanIssued`);
  «Хранилище» - таблицы `loans`, `loan_extensions`; маршрут `/library/loans` `POST`.

## Скиллы
`python-classic-domain` + `classic-criteria` (доменные usecase), `python-classic-app`
+ `classic-signals`, `python-classic-adapters-sql-db` + `classic-db-tools`,
`python-classic-adapters-http-api`, `python-classic-composite`.

## Сделать
- Домен: `Loan`, `LoanPeriod`, `Extension`, инварианты, критерии, `LoansRepo`, ошибки;
  доменный usecase `BorrowCopy` (без `Hub`).
- App: `commands/signals.py` (`LoanIssued`), `commands/loans/issue_loan.py` (испускает `LoanIssued` после `BorrowCopy`).
- БД: таблицы, `sql/aggregates/loans/` с макросами всех критериев `Loan`, репозиторий
  (`extensions` - `Append`, перезапись delete+insert с `position`).
- HTTP: ресурс `/library/loans` `POST` → 201.
- Композит: сборка `BorrowCopy` и `IssueLoan` (с общим `Hub`) (транзакция только на `IssueLoan.run`), ресурс.

## Критерии приёмки
- Unit домена: инварианты `Loan`, критерии в обеих формах и комбинациях; `BorrowCopy` - каждая проверка
  (`ReaderCannotBorrow`, `LoanLimitReached`, `ReaderHasOverdueLoans`, `CopyNotAvailable`), срок выдачи.
- Unit app: `IssueLoan` с замороженным временем, права, испущенный `LoanIssued`.
- БД: репозиторий с продлениями, макросы (`overdue`, `returned`, `due_within`, `of_reader`), контрактные тесты.
- HTTP: 201, 400, 403, 422.
- E2E: книга + экземпляр + читатель → выдача; экземпляр становится недоступен; повторная выдача → 422.
