# 06. Абонемент и блокировка читателя

`PUT /library/memberships` продлевает абонемент; `POST`/`DELETE /library/reader_blocks`
блокирует и разблокирует читателя.

## Спецификация
- `Reader` - поведение `extend_membership`, `block`, `unblock`;
  команды `ExtendMembership`, `BlockReader`, `UnblockReader`; маршруты `/library/memberships`,
  `/library/reader_blocks`.

## Скиллы
`python-classic-domain`, `python-classic-app`, `python-classic-adapters-http-api`,
`python-classic-composite`.

## Сделать
- Домен: поведение `Reader` и его ошибки.
- App: `commands/readers/extend_membership.py`, `block_reader.py`, `unblock_reader.py`.
- HTTP: `PUT /library/memberships`, `POST /library/reader_blocks`, `DELETE /library/reader_blocks?reader_id=`.
- Композит: сборка, транзакции, ресурсы.

## Критерии приёмки
- Unit домена: каждое поведение и его ошибка (`MembershipNotExtended`, `ReaderAlreadyBlocked`, `ReaderNotBlocked`).
- Unit app: каждая команда, `ReaderNotFound`, права.
- HTTP: успешные коды, 400, 403, 422.
- E2E: регистрация → продление → блокировка → разблокировка; повторная блокировка → 422.
