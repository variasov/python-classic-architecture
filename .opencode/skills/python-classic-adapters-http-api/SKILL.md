---
name: python-classic-adapters-http-api
description: HTTP API адаптер (interfaces/api, falcon) для приложения на Python в "классической" архитектуре - ресурсы, парсинг, сериализация, ошибки, тестирование. Использовать вместе с python-classic-architecture.
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
- За основу адаптера берется веб-фреймворк falcon, остальные запрещены.
- В качестве WSGI-сервера используется waitress.
- Адаптер размещается в `interfaces/api/`: классы-ресурсы и DTO их ответов в `interfaces/api/resources/<resource>.py`, класс настроек в `interfaces/api/settings.py` (pydantic-settings).
- Сборка falcon-приложения размещается в композите (см. Точка входа).

### Ресурсы
- На каждую URL в приложении делать отдельный класс-Resource. Действие задаётся HTTP-методом (`on_get`, `on_post`, `on_put`, `on_patch`, `on_delete`), а не URL.
  ❌ `/api/create_book`, `/api/delete_book`
  ✅ `/books` с `on_post` и `on_delete`
- URL - существительное во множественном числе, общий префикс модуля: `/library/books`. Исключение - отдельный ресурс для одного объекта по `?id=` (карточка), он называется существительным в единственном числе: `/library/book?id=1`.
- Действие над агрегатом, которое не укладывается в CRUD, оформляется отдельным ресурсом-существительным, обозначающим результат действия: `POST /loan_extensions` (продлить), `POST /returns` (вернуть), `POST /reader_blocks` (заблокировать).
- Все параметры запроса должны передаваться в параметрах запроса (query string), заголовках и теле. Нельзя размещать параметры в URL (`/books/{id}`). Идентификатор передаётся query-параметром для GET или полем тела для PUT/PATCH.
- Классы-ресурcы отвечают за разбор параметров запроса, парсинг данных из нагрузки,
  упаковку ответа пользователю, работу с заголовками.
- Классы-ресурсы НЕ ДОЛЖНЫ содержать бизнес-логику напрямую,
  а только обращаться к UseCase с уровня приложения. Usecase передаются в конструктор ресурса.
- `resp.status = falcon.HTTP_200` не ставится - это значение по умолчанию. `falcon.HTTP_201` ставится явно, только когда POST создаёт новый агрегат и возвращает его `id`. Действия над существующим агрегатом (продление, возврат, блокировка) возвращают 200.

### Парсинг
- Адаптер НЕ создаёт собственных Pydantic-моделей (наследников BaseModel) и не дублирует DTO для запросов.
  TypeAdapter инстанцируется напрямую на `Params`, импортированных с уровня приложения,
  и размещается как ClassVar на классе-ресурсе. Каждый TypeAdapter инстанцируется лишь единожды
  за запуск программы.
  ❌ class CreateBookRequest(BaseModel): ...       # не надо
  ✅ _create_validator: ClassVar = TypeAdapter(CreateBookParams)
- Query string парсится через `validate_python(req.params)`, тело - через `validate_json(req.bounded_stream.read())`.
- `TypeAdapter` вызывает `__post_init__` датакласса при разборе и превращает `ValueError` из него в `pydantic.ValidationError`. Поэтому и нарушение структуры и типов, и нарушение семантики параметров дают 400 без отдельной обработки.

### Сериализация
- Ответ упаковывается тоже через `TypeAdapter`, сразу в JSON: `dump_json(...)` кладётся в `resp.data`. `resp.media` и JSON-обработчик falcon для ответов не используются.
- TypeAdapter ответа, как и TypeAdapter параметров, - `ClassVar` на классе-ресурсе, создаётся один раз.
- Если ресурс отдаёт ровно то, что вернул usecase, TypeAdapter строится на результате usecase: `TypeAdapter(list[BookDTO])`.
- Если ответ отличается от результата usecase (usecase вернул простое значение, которое нужно обернуть в объект, поля нужно переименовать, отбросить или собрать из нескольких вызовов), рядом с ресурсом в `interfaces/api/` описывается датакласс-DTO ответа. Он и есть контракт HTTP API, TypeAdapter строится на нём. DTO ответа объявляется в файле ресурса и называется по смыслу ответа (`BookCreated`), без суффикса `Response`.
- Даты, перечисления и вложенные датаклассы сериализует сам TypeAdapter, ручной перевод в `dict` не нужен.

Пример ресурса:
```python
@dataclass(frozen=True)
class BookCreated:
    """Контракт ответа на создание книги: usecase возвращает только id"""

    id: int


class BooksResource:
    _query_validator: ClassVar = TypeAdapter(FindBooksParams)
    _create_validator: ClassVar = TypeAdapter(CreateBookParams)
    _update_validator: ClassVar = TypeAdapter(UpdateBookParams)
    _books_serializer: ClassVar = TypeAdapter(list[BookDTO])
    _created_serializer: ClassVar = TypeAdapter(BookCreated)

    def __init__(
        self, find_books: FindBooks, create_book: CreateBook, update_book: UpdateBook
    ):
        self._find_books = find_books
        self._create_book = create_book
        self._update_book = update_book

    def on_get(self, req: falcon.Request, resp: falcon.Response):
        params = self._query_validator.validate_python(req.params)
        books = self._find_books.run(params)
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._books_serializer.dump_json(books)

    def on_post(self, req: falcon.Request, resp: falcon.Response):
        params = self._create_validator.validate_json(req.bounded_stream.read())
        book_id = self._create_book.run(params)
        resp.status = falcon.HTTP_201
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._created_serializer.dump_json(BookCreated(id=book_id))

    def on_put(self, req: falcon.Request, resp: falcon.Response):
        params = self._update_validator.validate_json(req.bounded_stream.read())
        self._update_book.run(params)
```

### Точка входа
- Точка входа HTTP API - пакет `composites/interfaces/api/`:
  ```
  composites/interfaces/api/
    __main__.py              # waitress.serve(app, ...)
    wsgi.py                  # create_app(...) и модульный app
    settings.py              # инстанс настроек
    resources/<resource>.py  # инстанс ресурса с внедрёнными usecase
  ```
- Приложение собирается функцией-фабрикой `create_app(...)` в `wsgi.py`: middleware, обработчики ошибок, маршруты. Ресурсы передаются ей аргументами, модульный `app` создаётся её вызовом:
  ```python
  # composites/interfaces/api/wsgi.py
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
  - `pydantic.ValidationError` -> 400;
  - один обработчик на базовые классы ожидаемых ошибок `AppError` (из `app/errors.py`) и `DomainError` (из `app/commands/domain/errors.py`, если домен есть) -> 422. Он покрывает все ошибки приложения и домена, включая `<Aggregate>NotFound`. Отдельные обработчики на каждый тип ошибки не добавляются.
  ```python
  # interfaces/api/errors.py
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
- Тело ошибки: `type` - имя класса ошибки, `msg` - `str(error)`, `ctx` - все поля ошибки (`vars(error)`), то есть поля датакласса для ошибок с параметрами и пустой объект для ошибок без них. Тело описано DTO `ErrorDetail` в `interfaces/api/errors.py` и упаковывается через TypeAdapter, как и обычные ответы. Обработчики ошибок тоже размещаются там, `create_app` только регистрирует их.

## Тестирование
Тесты ресурсов проверяют только перевод протокола: `falcon.testing.TestClient`, `create_app(...)` с ресурсами на фейковых usecase, без БД (см. пирамиду в `python-classic-architecture`).
Подробные правила (`FakeUseCase`, фикстуры, что проверять) - в `references/testing.md` этого навыка. Читай его, когда пишешь или правишь тесты ресурсов.
