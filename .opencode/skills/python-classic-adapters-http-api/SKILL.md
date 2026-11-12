---
name: python-classic-adapters-http-api
description: HTTP API адаптер (interfaces/<name>_api, falcon) для приложения на Python в "классической" архитектуре - ресурсы, парсинг, сериализация, ошибки, тестирование. Использовать вместе с python-classic-architecture.
license: MIT
compatibility: opencode
---

# Python HTTP API adapter in "Classic" Architecture 

## Описание

В этом навыке описывается HTTP API адаптер к приложению на Python,
соответствующий шаблону "Классической" архитектуры. Это адаптер группы `interfaces`.
Общая идея слоёв и правила группы interfaces описаны в навыке `python-classic-architecture`,
общие правила композита - в навыке `python-classic-composite`.

## Когда использовать
- Во время разработки новых фич в Python-приложении, требующих доступа по HTTP.
- При написании тестов на HTTP-ресурсы.

## Instructions

### Стек и размещение
- За основу адаптера берется веб-фреймворк falcon, остальные запрещены: единый зафиксированный стек - все проекты устроены одинаково, а falcon - минималистичный WSGI-фреймворк без магии, сборка приложения остаётся явной.
- В качестве WSGI-сервера используется waitress.
- Адаптер размещается в `interfaces/<name>_api/`, где `<name>` - назначение API, то есть кто и зачем к нему обращается: `web_api` (фронтенд), `integrations_api` (внешние партнёры), `s2s_api` (другие сервисы). В одном приложении таких адаптеров может быть несколько: у API с разными клиентами разные контракты, аутентификация и темп изменений, поэтому они не смешиваются в одном пакете, а безликое `api` не говорит, какой это из них. Имя пишется через подчёркивание (`web_api`, не `web-api`): это имя Python-пакета.
- Внутри адаптера: классы-ресурсы в `interfaces/<name>_api/resources/<resource>.py`, класс настроек в `interfaces/<name>_api/settings.py` (pydantic-settings), обработчики ошибок в `interfaces/<name>_api/errors.py`. Хост и порт - чувствительные настройки и объявляются без дефолтов (см. «Настройки» в `python-classic-architecture`).
- Сборка falcon-приложения размещается в композите (см. Точка входа).

### Ресурсы
- На каждую URL в приложении делать отдельный класс-Resource. Действие задаётся HTTP-методом (`on_get`, `on_post`, `on_put`, `on_patch`, `on_delete`), а не URL: URL - имя ресурса, метод - действие, иначе URL плодятся под каждое действие и теряется единообразие REST.
  ❌ `/api/create_book`, `/api/delete_book`
  ✅ `/books` с `on_post` и `on_delete`
- URL - существительное во множественном числе, общий префикс модуля: `/library/books`. Исключение - отдельный ресурс для одного объекта по `?id=` (карточка), он называется существительным в единственном числе: `/library/book?id=1`.
- Действие над агрегатом, которое не укладывается в CRUD, оформляется отдельным ресурсом-существительным, обозначающим результат действия: `POST /loan_extensions` (продлить), `POST /returns` (вернуть), `POST /reader_blocks` (заблокировать). Так действие становится созданием результата: сохраняется правило «URL - существительное, действие - метод» и не появляются гибридные URL-глаголы.
- Все параметры запроса должны передаваться в параметрах запроса (query string), заголовках и теле. Нельзя размещать параметры в URL (`/books/{id}`): все входы ресурса передаются единообразно - `req.params` или тело целиком уходят в usecase, а path-параметры приходят в falcon отдельными аргументами метода и размазывают разбор по сигнатуре. Идентификатор передаётся query-параметром для GET или полем тела для PUT/PATCH.
- Ресурс - тонкий перевод протокола: берёт данные запроса, передаёт их usecase и кладёт результат в ответ, работает с заголовками и кодом ответа. Остальное распределено так: валидацию входа выполняет аспект, навешанный на usecase в композите (см. `python-classic-aspects-validation`), сериализацию - JSON-обработчик приложения (см. «JSON-обработчик»), контракт ответа задаёт результат usecase.
- Классы-ресурсы НЕ ДОЛЖНЫ содержать бизнес-логику напрямую,
  а только обращаться к UseCase с уровня приложения. Usecase передаются в конструктор ресурса.
- `resp.status = falcon.HTTP_200` не ставится - это значение по умолчанию. `falcon.HTTP_201` ставится явно, только когда POST создаёт новый агрегат и возвращает его `id`. Действия над существующим агрегатом (продление, возврат, блокировка) возвращают 200.

### Входные данные
- Query string (`req.params`) или тело (`req.media`) передаются в `run` usecase как есть, словарём:
  ```python
  self._create_book.run(req.media, req.context.account)
  ```
  В `Params` словарь превращает аспект валидации, навешанный на `run` в композите (см. `python-classic-aspects-validation`). Ошибки валидации он бросает как `pydantic.ValidationError`, которая даёт 400 (см. «Обработка ошибок»).
- `Params` usecase - единственный контракт входа. Адаптер не описывает собственных моделей запроса: вторая модель того же входа неизбежно разошлась бы с `Params`.
- Значения query string - строки, к типам `Params` их приводит аспект валидации. Повторяющийся параметр приходит списком.
- Аккаунт берётся из `req.context.account`: middleware аутентификации кладёт его в каждый запрос (для неизвестного пользователя - аккаунт без прав), поэтому ресурс не проверяет его наличие.
- Статически ресурс передаёт словарь туда, где аннотирован `Params`. `req.media` типизирован как `Any` и пометок не требует, а для `req.params` (`Mapping[str, ...]`) pyright сообщает о несовпадении типа - такая строка помечается `# pyright: ignore[reportArgumentType]`.

### Ответ
- Результат usecase кладётся прямо в `resp.media`, сериализует его JSON-обработчик приложения.
- Контракт ответа - результат usecase: DTO, объявленные рядом с usecase в app (см. «Параметры и результат» в `python-classic-app`). Тело ответа - JSON-объект, поэтому usecase, результат которого уходит клиенту, возвращает датакласс: команда создания возвращает `BookCreated(id=...)`, и клиент получает `{"id": 1}`.
- Если usecase ничего не возвращает (действие над существующим агрегатом), `resp.media` не ставится.

### JSON-обработчик
- В `create_app` стандартный JSON-обработчик falcon заменяется на `orjson` - и для запросов, и для ответов:
  ```python
  orjson_handler = falcon.media.JSONHandler(dumps=orjson.dumps, loads=orjson.loads)
  app.req_options.media_handlers[falcon.MEDIA_JSON] = orjson_handler
  app.resp_options.media_handlers[falcon.MEDIA_JSON] = orjson_handler
  ```
- orjson быстрее стандартного `json` и сам сериализует датаклассы (в том числе вложенные), `date`/`datetime` (ISO 8601), перечисления (значением), `UUID`. Поэтому DTO usecase отдаются в `resp.media` без перевода в `dict`. Типы, которые orjson не сериализует (например, `Decimal`), в DTO, уходящих в HTTP, не используются или поддерживаются через `default=` в `dumps`.
- `orjson` - зависимость проекта наравне с falcon.

### Пример ресурса
```python
class BooksResource:
    def __init__(self, create_book: CreateBook, find_books: FindBooks) -> None:
        self._create_book = create_book
        self._find_books = find_books

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        resp.media = self._find_books.run(req.params)  # pyright: ignore[reportArgumentType]

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        resp.media = self._create_book.run(req.media, req.context.account)
        resp.status = falcon.HTTP_201
```
- Метод ресурса - одна-две строки: вызов usecase с данными запроса и, если нужно, код ответа или заголовки.
- Если в методе появляется разбор, преобразование данных или сборка ответа из нескольких вызовов - логика просится в usecase и его DTO, а не в ресурс.

### Точка входа
- Точка входа HTTP API - пакет `composites/interfaces/<name>_api/` с тем же именем, что у адаптера; на каждый HTTP API - своя точка входа (свой процесс):
  ```
  composites/interfaces/<name>_api/
    __main__.py              # waitress.serve(app, ...)
    wsgi.py                  # create_app(...) и модульный app
    settings.py              # инстанс настроек
    resources/<resource>.py  # инстанс ресурса с внедрёнными usecase
  ```
- Приложение собирается функцией-фабрикой `create_app(...)` в `wsgi.py`: middleware, JSON-обработчик, обработчики ошибок, маршруты. Ресурсы передаются ей аргументами, модульный `app` создаётся её вызовом:
  ```python
  # composites/interfaces/<name>_api/wsgi.py
  def create_app(books: BooksResource, ...) -> falcon.App:
      app = falcon.App(middleware=[...])
      # error handlers, add_route
      return app

  app = create_app(books=books_resource, ...)
  ```
- `waitress.serve(app, ...)` вызывается только в `__main__.py`, импорт `wsgi.py` сервер не запускает.
- Тесты ресурсов вызывают `create_app` со своими ресурсами и не дублируют сборку.
- В тестах композита (см. `python-classic-composite`) настоящий `app` импортируется из `wsgi.py` внутри фикстуры, зависящей от `test_env`, и используется через `falcon.testing.TestClient`.

### Обработка ошибок
- Ошибки обрабатываются глобально в `create_app`, а не в ресурсах:
  - `pydantic.ValidationError` -> 400. Её бросает аспект валидации на usecase до входа в `run`;
  - ошибки авторизации (отказ в доступе) -> 403. Отказ в доступе - не ошибка бизнеса: клиенту нужно отличать «нельзя вам» от «нельзя в таком состоянии», поэтому у ошибок авторизации свой обработчик и свой код, отдельно от ошибок приложения и домена;
  - один обработчик на базовые классы ожидаемых ошибок `AppError` (из `app/errors.py`) и `DomainError` (из `app/commands/domain/errors.py`, если домен есть) -> 422. Он покрывает все ошибки приложения и домена, включая `<Aggregate>NotFound`. Отдельные обработчики на каждый тип ошибки не добавляются: все ожидаемые ошибки бизнеса для клиента равнозначны (тело с `type`/`msg`/`ctx` уже различает их), а новая ошибка не требует регистрации.
- 404 отдаёт только сам falcon - когда для URL нет маршрута (нет такого ресурса). Приложение 404 не возвращает никогда: если ресурс есть, но объект по параметрам не найден - в хранилище (`<Aggregate>NotFound`, ошибка запроса) или во внешней системе (`BookNotInCatalog`), - это ошибка в параметрах запроса, то есть 422. Иначе клиент не отличит опечатку в URL от отсутствующего объекта.
  ```python
  # interfaces/<name>_api/errors.py
  @dataclass(frozen=True)
  class ErrorDetail:
      """Контракт тела ответа с ошибкой"""

      type: str
      msg: str
      ctx: dict[str, Any]


  _errors_serializer = TypeAdapter(list[ErrorDetail])


  def serialize_app_error(req, resp, error: AppError | DomainError, params):
      detail = ErrorDetail(type=type(error).__name__, msg=str(error), ctx=vars(error))
      resp.status = falcon.HTTP_422
      resp.content_type = falcon.MEDIA_JSON
      resp.data = _errors_serializer.dump_json([detail])


  app.add_error_handler(pydantic.ValidationError, serialize_pydantic_error)
  app.add_error_handler((AppError, DomainError), serialize_app_error)
  ```
- Тело ошибки: `type` - имя класса ошибки, `msg` - `str(error)`, `ctx` - все поля ошибки (`vars(error)`), то есть поля датакласса для ошибок с параметрами и пустой объект для ошибок без них. Тело описано DTO `ErrorDetail` в `interfaces/<name>_api/errors.py`. Обработчики ошибок тоже размещаются там, `create_app` только регистрирует их.

## Тестирование
Тесты ресурсов проверяют только перевод протокола: `falcon.testing.TestClient`, `create_app(...)` с ресурсами на фейковых usecase, без БД. Валидация навешивается в композите и проверяется тестами композита (см. пирамиду в `python-classic-architecture`).
Подробные правила (`FakeUseCase`, фикстуры, что проверять) - в `references/testing.md` этого навыка. Читай его, когда пишешь или правишь тесты ресурсов.
