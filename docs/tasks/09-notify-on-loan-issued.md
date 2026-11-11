# 09. Уведомление о выдаче

При выдаче экземпляра читателю сохраняется уведомление `loan_issued`.

## Спецификация
- «Агрегат „Уведомление“ (`Notification`)»; доменная реакция `NotifyOnLoanIssued`; «Уведомления»;
  «Хранилище» - таблица `notifications`, миграция `0002.add_notifications`; «Процессы» - `api`
  импортирует реакцию.

## Скиллы
`python-classic-domain` + `classic-criteria`, `classic-signals`, `python-classic-adapters-sql-db`
+ `classic-db-tools` + `classic-migrations`, `python-classic-composite`.

## Сделать
- Домен: `Notification`, `NotificationKind`, критерии, `NotificationsRepo`, `NotificationNotFound`;
  реакция `NotifyOnLoanIssued` (подписка в конструкторе).
- БД: `0002.add_notifications.sql` (`-- depends: 0001.init`), `DDL.sql`, `sql/aggregates/notifications/`
  с макросами, репозиторий.
- Композит: реакция создаётся при сборке на общем `Hub` до первого `notify`.

## Критерии приёмки
- Unit домена: критерии `about_loan`, `of_kind`; реакция на `LoanIssued` сохраняет уведомление
  (свой `Hub` в тесте, замороженное время).
- БД: репозиторий, макросы, контрактные тесты; обе миграции применяются по порядку.
- E2E: `POST /library/loans` создаёт уведомление `loan_issued` в той же транзакции; если сохранение
  уведомления падает, выдача откатывается.
