# 08. Продление и возврат

`POST /library/loan_extensions` продлевает выдачу, `POST /library/returns` принимает экземпляр.

## Спецификация
- `Loan` - поведение `extend`, `close`; доменный usecase `ReturnCopy`; команды `ExtendLoan`
  (и `ExtendLoanParams`), `ReturnLoan`; маршруты `/library/loan_extensions`, `/library/returns`.

## Скиллы
`python-classic-domain`, `python-classic-app`, `python-classic-adapters-http-api`,
`python-classic-composite`.

## Сделать
- Домен: `Loan.extend`, `Loan.close` и их ошибки; доменный usecase `ReturnCopy`.
- App: `use_cases/loans/extend_loan.py`, `return_loan.py`.
- HTTP: ресурсы `/library/loan_extensions`, `/library/returns`.
- Композит: сборка, транзакции на `run` команд.

## Критерии приёмки
- Unit домена: `extend` (сдвиг срока, лимит продлений, возвращённая и просроченная выдача),
  `close` (повторный возврат, дата раньше выдачи); `ReturnCopy` освобождает экземпляр.
- Unit app: обе команды с замороженным временем, границы `days`, права.
- HTTP: успешные коды, 400, 403, 422.
- E2E: выдача → продление → возврат; экземпляр снова доступен; повторный возврат → 422.
