# Тестирование: python-classic-adapters-http-api
Тесты ресурсов - средний уровень пирамиды (см. `python-classic-architecture`): проверяется только перевод протокола, без БД и настоящих usecase. Сквозная проверка API с настоящими usecase и БД - в тестах композита (см. `python-classic-composite`).

### Подход
- На каждый ресурс - свой файл `tests/adapters/interfaces/<name>_api/test_<resource>.py`, фикстуры - в `tests/adapters/interfaces/<name>_api/conftest.py`.
- HTTP наружу не вызывается: используется `falcon.testing.TestClient`.
- Ресурсу передаются фейковые usecase: классы с методом `run`, которые запоминают полученные параметры и возвращают подготовленный результат или бросают заданную ошибку.
  ```python
  class FakeUseCase:
      def __init__(self, result=None, error: Exception | None = None) -> None:
          self.result = result
          self.error = error
          self.calls: list = []

      def run(self, params, account):
          self.calls.append((params, account))
          if self.error:
              raise self.error
          return self.result
  ```
  Здесь, в отличие от тестов app, проверка полученных параметров допустима: это и есть поведение ресурса - какие данные запроса и какой аккаунт он передал usecase. Фейк получает данные запроса словарём: валидация - аспект, навешанный в композите, и в тестах ресурсов её нет.
- Приложение собирается фабрикой `create_app(...)` из `composites/interfaces/<name>_api/wsgi.py`, в которую передаются ресурсы с фейковыми usecase. Middleware, обработчики ошибок и маршруты в тестах не дублируются: иначе тест не проверит, что ошибка превращается в нужный код ответа.
  ```python
  @pytest.fixture
  def create_book() -> FakeUseCase:
      return FakeUseCase(result=BookCreated(id=1))

  @pytest.fixture
  def client(create_book, ...) -> TestClient:
      books = BooksResource(create_book=create_book, ...)
      return TestClient(create_app(books=books, ...))
  ```

### Что проверять
- Передача запроса: query string или тело попадают в usecase как есть, вместе с аккаунтом из middleware.
- Код ответа и форма тела для успешного запроса (`201` + `id` для создания, `200` для остального): тело - сериализованный результат usecase, даты и перечисления сериализованы.
- Перевод `pydantic.ValidationError` в 400 - поведение обработчика ошибок `create_app`, он проверяется один раз, на тестовом ресурсе. Варианты невалидного ввода проверяются на `Params` в unit-тестах app, а то, что валидация навешена, - в тестах композита.
- Ошибка приложения, которую бросил usecase, в том числе `<Aggregate>NotFound`, - 422, в теле `type` с именем класса ошибки и `ctx` с её полями.
- Ошибка авторизации, которую бросил usecase, - 403 с тем же телом.
- Бизнес-правила здесь не проверяются: они покрыты unit-тестами app.
