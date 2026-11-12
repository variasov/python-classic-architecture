---
name: python-classic-aspects-validation
description: Аспект валидации входных параметров usecase (pydantic.validate_call) в "классической" архитектуре на Python - навешивание в композите, требования к сигнатуре run, ошибки, тестирование. Использовать вместе с python-classic-composite.
license: MIT
compatibility: opencode
---

# Validation Aspect in "Classic" Architecture

## Описание

В этом навыке описывается аспект валидации: превращение данных, пришедших в адаптер-интерфейс,
в датаклассы `Params` usecase. Общие правила аспектов и порядок обёрток описаны в навыке
`python-classic-composite`, сами `Params` - в навыке `python-classic-app`.

## Когда использовать
- При добавлении usecase, который вызывается из адаптера-интерфейса (HTTP API, чат-бот, обработчик очереди).
- При изменении сигнатуры `run` или датаклассов `Params`.
- При написании тестов композита на невалидный ввод.

## Instructions

### Назначение
- Валидация входных параметров usecase - аспект `pydantic.validate_call`, навешанный в композите на `run`. Адаптер-интерфейс передаёт в `run` данные как есть (словарь), аспект по аннотациям `run` создаёт из них датаклассы `Params`, вызывая их `__post_init__`. Так разбор входа описан один раз - аннотациями `run` и `Params`, - адаптеры его не повторяют, а ни usecase, ни адаптер не привязаны к pydantic.
- Нарушение структуры и типов, как и `ValueError` из `__post_init__`, аспект превращает в `pydantic.ValidationError`. Её обрабатывает адаптер-интерфейс (например, HTTP API отвечает 400, см. `python-classic-adapters-http-api`).
- Аспект навешивается на каждый usecase, который адаптеры-интерфейсы вызывают с внешними данными.

### Навешивание
- `pydantic.validate_call` применяется напрямую, файл в `composites/aspects/` для него не заводится.
- Валидация - самая внешняя обёртка: невалидный ввод отсекается до повторов и до открытия транзакции (порядок обёрток и их форматирование - в `python-classic-composite`).
  ```python
  # composites/app/queries/books/find_books.py
  find_books = FindBooks(gateway=find_books_gateway)
  find_books.run = pydantic.validate_call(find_books.run)  # pyright: ignore[reportAttributeAccessIssue]
  ```
  ```python
  # composites/app/commands/books/create_book.py
  create_book = CreateBook(books=books_repo, logger=logger)
  # fmt: off
  create_book.run = (
      pydantic.validate_call(
      engine.transaction(
      create_book.run
  )))  # pyright: ignore[reportAttributeAccessIssue]
  # fmt: on
  ```

### Требования к сигнатуре `run`
- Все типы в сигнатуре `run` поддерживаются pydantic: датаклассы, примитивы, `date`/`datetime`, перечисления, конкретные коллекции (`list`, `tuple`, `dict`). Абстрактные `collections.abc.Collection` и произвольные классы pydantic не валидирует, и импорт композита падает при навешивании аспекта. Поэтому поля датаклассов, которые передаются в `run` (в том числе `Account`), объявляются конкретными типами: права в `Account` - `tuple[str, ...]`.
- Уже созданный инстанс датакласса (`Account`, готовые `Params`) pydantic принимает без повторной валидации, поэтому usecase с аспектом вызывается и с готовыми объектами (из тестов, планировщика, других адаптеров).
- Аспект работает в нестрогом режиме: строки приводятся к типам полей (`'5'` -> `5`, `'true'` -> `True`, `'2026-03-01'` -> `date`). Поэтому данные, где все значения - строки (query string, переменные окружения, аргументы командной строки), передаются без предварительного приведения.

## Тестирование
- Варианты невалидного ввода проверяются в unit-тестах app созданием `Params` (см. `python-classic-app`): аспект только вызывает `__post_init__` и проверки типов.
- Тесты композита проверяют, что аспект навешан: на каждый вход с валидацией - один невалидный запрос, который даёт ошибку валидации (в HTTP - 400), без перебора вариантов.
- В тестах адаптеров-интерфейсов аспекта нет: фейковые usecase получают данные как есть.
