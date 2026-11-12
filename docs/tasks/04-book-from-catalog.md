# 04. Книга из каталога ISBN

`POST /library/catalog_books` создаёт книгу по ISBN из внешнего каталога.

## Спецификация
- «Внешняя система: каталог ISBN»; команда `CreateBookFromCatalog` и `CreateBookFromCatalogParams`;
  маршрут `/library/catalog_books`.

## Скиллы
`python-classic-app` (ABC внешних систем), `python-classic-architecture` (интеграции, настройки),
`python-classic-adapters-http-api`, `python-classic-composite` (аспекты).

## Сделать
- App: `commands/books/create_book_from_catalog.py` - `CreateBookFromCatalog`, Params,
  `IsbnCatalog` (ABC), `CatalogBook`, `BookNotInCatalog`.
- Интеграция: `integrations/isbn_catalog/client.py` (`CatalogBookPayload`, `IsbnCatalogClient`,
  `IsbnCatalogUnavailable`), `settings.py` (`IsbnCatalogSettings`).
- Композит: `tenacity.retry(...)` на `find` клиента (в `composites/integrations/isbn_catalog/client.py`), сборка, транзакция, ресурс.
- HTTP: ресурс `/library/catalog_books` `POST` → 201.

## Критерии приёмки
- Unit app: `FakeIsbnCatalog`; книга собрана из `CatalogBook`; `BookNotInCatalog`; права; длина `isbn`.
- Интеграция (pytest-httpserver): 200 → `CatalogBook`, 404 → `None`, 500 и невалидный JSON →
  `IsbnCatalogUnavailable`, проверка отправленного запроса (путь, `isbn`).
- HTTP: 201, 400, 403, 422.
- E2E со stub-каталогом: книга создана; временная ошибка каталога повторяется аспектом retry.
