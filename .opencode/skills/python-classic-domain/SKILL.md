---
name: python-classic-domain
description: Модель домена в "классической" архитектуре на Python - агрегаты, сущности, объекты-значения, инварианты, критерии, абстрактные репозитории, доменные ошибки, доменные usecase и события. Использовать вместе с python-classic-architecture и python-classic-app.
license: MIT
compatibility: opencode
---

# Python Domain Model in "Classic" Architecture

## Описание

В этом навыке описывается модель домена - опциональная часть слоя app.
Общая идея слоёв описана в навыке `python-classic-architecture`,
правила слоя app (команды, запросы, сигналы) - в навыке `python-classic-app`.

## Когда использовать
- Когда у предметной области есть объекты с собственными правилами: состояние, инварианты, переходы.
- Во время разработки или ревью агрегатов, репозиториев, критериев и доменных ошибок.

Если команды сводятся к сохранению данных без правил, домен не вводится.

## Размещение
- Модель домена размещается в `app/commands/domain`. Она принадлежит командам: запросы (`app/queries`) домен не импортируют.
- Домен - нижележащий подслой внутри app. Остальной app (usecase-команды, `clock.py`, `errors.py`, `signals.py`) знает о домене, а домен об остальном app не знает: из домена запрещено импортировать что-либо из `app`, кроме самого `app/commands/domain`.
  ❌ `from library.app.errors import AppError` в `domain/loan.py`
  ✅ `from library.app.commands.domain.errors import DomainError`
- Всё, что нужно домену, объявляется в самом домене: базовый класс ошибок, контракты доменных событий, ABC внешних систем.
- Каждый агрегат описывается в своём файле `domain/<aggregate>.py` вместе с его объектами-значениями, вложенными сущностями, абстрактным репозиторием и доменными ошибками.
- Доменный usecase - в своём файле `domain/<usecase>.py`.
- ABC внешней системы, нужной самому домену, объявляется в `domain/<system>.py` вместе с DTO её ответа (чистыми датаклассами). ABC, нужные только командам, в домен не кладутся (см. `python-classic-app`).
- Домен тем более не импортирует ничего из адаптеров и композита, не знает о БД, HTTP, транзакциях, правах пользователя и текущем времени.

## Строительные блоки
- Модель домена содержит классы, отражающие понятия из предметной области, и логику, связанную с этими понятиями.
- Состоит из объектов-значений, сущностей, инвариантов, агрегатов, критериев, доменных usecase и доменных событий.
- Объекты-значения описываются датаклассами, зачастую с frozen=True. Такие объекты не имеют id, и являются подчиненными по отношению к сущностям. Может содержать логику, связанную со своими данными, инварианты и критерии.
- Сущности описываются датаклассами, и всегда имеют идентификатор. Идентификатор может быть простым типом данных, кортежем простых данных, и даже объектом-значением. Может содержать логику, связанную со своими данными, инварианты и критерии. Если идентификатор выдаёт хранилище, до сохранения он равен `None`.
- Агрегат - иерархия сущностей и объектов-значений, а так же логики, инвариантов и критериев. В корне иерархии всегда находится сущность.
- Части агрегатов могут содержать ссылки на корни других агрегатов. Нельзя сослаться из одного агрегата на что-то внутри другого агрегата напрямую, только на корень.
- Агрегаты не должны содержать логику управления другими агрегатами. При необходимости работы с несколькими разными агрегатами пишутся доменные usecase.
- Пример агрегата: корень `Loan`, объект-значение `LoanPeriod`, вложенная сущность `Extension`, ссылки на корни других агрегатов, рекурсивный `check()` и методы, меняющие состояние по правилам:
  ```python
  # app/commands/domain/loan.py
  @dataclass(frozen=True)
  class LoanPeriod:
      """Объект-значение: срок выдачи"""

      start: date
      due: date

      def check(self) -> None:
          if self.due <= self.start:
              raise LoanPeriodInvalid(start=self.start, due=self.due)

      def extended(self, days: int) -> 'LoanPeriod':
          return LoanPeriod(start=self.start, due=self.due + timedelta(days=days))


  @dataclass
  class Extension:
      """Вложенная сущность: имеет id, но живёт только внутри выдачи"""

      extended_on: date
      days: int
      id: int | None = None

      def check(self) -> None:
          if self.days <= 0:
              raise ExtensionDaysNotPositive


  @dataclass
  class Loan:
      """Корень агрегата"""

      MAX_EXTENSIONS: ClassVar[int] = 2

      reader_id: int  # ссылка на корень агрегата Reader
      copy_id: int  # ссылка на корень агрегата Copy
      period: LoanPeriod
      extensions: list[Extension] = field(default_factory=list)
      returned_at: date | None = None
      id: int | None = None

      def check(self) -> None:
          self.period.check()
          if len(self.extensions) > self.MAX_EXTENSIONS:
              raise TooManyExtensions(loan_id=self.id)
          for extension in self.extensions:
              extension.check()

      def extend(self, days: int, on: date) -> None:
          if self.returned_at is not None:
              raise LoanAlreadyReturned(loan_id=self.id)
          self.extensions.append(Extension(extended_on=on, days=days))
          self.period = self.period.extended(days)

      def return_on(self, on: date) -> None:
          if self.returned_at is not None:
              raise LoanAlreadyReturned(loan_id=self.id)
          self.returned_at = on
  ```
  Методы изменяют состояние и проверяют правила перехода (нельзя продлить возвращённую выдачу). Инварианты всего агрегата (не больше двух продлений) проверяет `check()`, его вызывает репозиторий при сохранении.
- Текущие дата и время не берутся внутри домена (`date.today()`, `datetime.now()` в агрегатах и критериях запрещены): usecase передаёт их в методы агрегатов и критерии явно, параметром.
  ```python
  # ❌
  def overdue(self) -> bool:
      return self.returned_at is None and self.period.due < date.today()


  # ✅
  @criteria
  def overdue(self, on: date) -> bool:
      return self.returned_at is None and self.period.due < on
  ```
  Почему:
  - Детерминизм. Результат метода зависит только от данных агрегата и аргументов, поэтому доменные тесты не требуют подмены времени.
  - Критерии транслируются в SQL. SQL-макрос получает дату из атрибута критерия (`criteria.on`), а не из `now()` сервера БД. Иначе проверка в памяти и выборка в хранилище берут время из разных часов и расходятся.
  - Одно "сейчас" на операцию. Usecase получает время один раз и передаёт во все методы, поэтому проверка и запись внутри одной операции согласованы, в том числе на границе суток.
  - Что считать "сейчас" (часовой пояс, бизнес-календарь), решает сценарий, а не понятие предметной области. Агрегат отвечает на вопрос "на дату X", дату X выбирает usecase.
- Источник текущего времени для usecase - `Clock` (см. `python-classic-app`).

## Репозитории
- На каждый агрегат описывается свой класс-хранилище (репозиторий), умеющий извлекать/искать/сохранять конкретный вид агрегатов. ТОЛЬКО агрегаты имеют репозитории. В пределах модели домена данные можно извлекать только из хранилищ.
- Абстрактный репозиторий содержит `get_by_id` и `save`, при необходимости - методы поиска, возвращающие агрегаты. Не добавлять в репозиторий специализированные методы изменения (`update_status`, `create`, `update(..., sync_x=True)`) в обход агрегата.
  ```python
  class LoansRepo(ABC):
      @abstractmethod
      def get_by_id(self, id: int) -> Loan: ...

      @abstractmethod
      def save(self, loan: Loan) -> Loan: ...
  ```
- `get_by_id` возвращает агрегат или бросает доменную ошибку `<Aggregate>NotFound`, объявленную рядом с агрегатом. Usecase не проверяет результат на `None`.
- Агрегат извлекается из хранилища и сохраняется обратно всегда целиком, и всегда в одной транзакции, чтобы обеспечить целостность. Репозиторий не знает, что именно изменилось, и всегда сохраняет агрегат целиком. При сохранении репозиторий ДОЛЖЕН вызвать `check()` агрегата до записи.
- Реализации репозиториев размещаются в адаптерах (см. `python-classic-adapters-sql-db`).

## Инварианты и доменные ошибки
- Инварианты - требования к сущности/агрегату. Описываются методом `check()`, который ничего не возвращает и не логирует, а при нарушении бросает доменную ошибку. `check()` корня агрегата проверяет весь агрегат, рекурсивно вызывая `check()` вложенных объектов, чтобы из любого места можно было полностью проверить агрегат.
- Инварианты проверяются только в домене. Ограничения CHECK в БД не используются: БД - хранилище, домен - единственный источник правды.
- Так как домен не импортирует app, `AppError` ему недоступен. Доменные ошибки наследуются от собственного базового класса `DomainError` из `domain/errors.py`, который наследуется от `Exception`:
  ```python
  # app/commands/domain/errors.py
  class DomainError(Exception):
      """Базовый класс доменных ошибок"""
  ```
  `DomainError` и `AppError` - два независимых базовых класса. Адаптеры обрабатывают оба одинаково.
- Оформление конкретных ошибок (имена без `Error`, `__str__`, датаклассы не `frozen`, пример `LoanNotFound`) - в разделе "Ошибки" навыка `python-classic-architecture`.

## Критерии
- Критерий - функции-предикаты, описывающие разные условия, в которых могут находиться объекты. Для реализации используется classic-criteria. Критерии объявляются методами агрегата с декоратором `@criteria`. Декоратор даёт две формы вызова, и обе используются по назначению:
  - **на инстансе - сразу `bool`.** `loan.returned()`, `reader.membership_active(on=today)`. Это основная форма для проверки одного конкретного объекта в домене и в usecase: в условиях `if`, в методах агрегата (`if self.returned(): ...`). Такой вызов читается как обычный метод.
  - **на классе - ленивый объект критерия.** `Loan.overdue(on=today)` ничего не проверяет, а создаёт объект `Criteria[Loan]`, который можно комбинировать через `&`, `|`, `~`, передать в репозиторий для выборки (`self.loans.find(Loan.overdue(on=today) & ~Loan.returned())`) или применить к объекту позже через `is_satisfied_by`.
  ```python
  # ✅ проверка конкретного объекта - вызов на инстансе
  if loan.returned():
      raise LoanAlreadyReturned(loan_id=loan.id)
  if not (reader.membership_active(on=today) and reader.not_blocked()):
      raise ReaderCannotBorrow(reader_id=reader.id)

  # ✅ комбинация критериев, которую нужно и проверить, и отдать в хранилище - вызов на классе
  can_borrow = Reader.membership_active(on=today) & Reader.not_blocked()
  if not can_borrow.is_satisfied_by(reader):
      ...

  # ❌ ленивая форма там, где достаточно прямого вызова
  if Loan.returned().is_satisfied_by(self):
      ...
  ```
- Ленивая форма на классе нужна, когда критерий передаётся куда-то как значение: в репозиторий, в переменную для повторного использования, в комбинацию с другими критериями. Для однократной проверки одного объекта используется вызов на инстансе.
- У инстанса есть также `.must_be_satisfied(...)`, бросающий `CriteriaNotSatisfied` из classic-criteria. В домене он не используется: нарушение правила - это конкретная доменная ошибка с понятным именем, поэтому проверка пишется явным `if` с `raise`.
  ```python
  @dataclass
  class Loan:
      ...

      @criteria
      def overdue(self, on: date) -> bool:
          return self.returned_at is None and self.period.due < on

      @criteria
      def returned(self) -> bool:
          return self.returned_at is not None


  class LoansRepo(ABC):
      @abstractmethod
      def find(self, criteria: Criteria[Loan]) -> list[Loan]: ...


  # usecase
  overdue_loans = self.loans.find(Loan.overdue(on=today) & ~Loan.returned())
  ```
  Имя класса критерия совпадает с именем метода (`overdue`) - по нему хранилище находит свой транслятор. Параметры, которых нет у агрегата (например, `reader_id`), тоже оформляются критериями, а не отдельными аргументами `find`.

## Доменные usecase
- Доменный usecase - класс с методом `run`, работающий с несколькими агрегатами, когда ни один из агрегатов не управляет другим.
- Получает репозитории через конструктор. Вызывается из usecase-команд, а не из адаптеров.
- Транзакцией не оборачивается: выполняется внутри транзакции вызвавшей его команды.
  ```python
  # app/commands/domain/issue_loan.py
  class IssueLoan:
      """Выдача затрагивает три агрегата: читателя, экземпляр и новую выдачу"""

      def __init__(
          self, readers: ReadersRepo, copies: CopiesRepo, loans: LoansRepo
      ) -> None:
          self.readers = readers
          self.copies = copies
          self.loans = loans

      def run(self, reader_id: int, copy_id: int, on: date) -> Loan:
          reader = self.readers.get_by_id(reader_id)
          copy = self.copies.get_by_id(copy_id)
          reader.ensure_can_borrow(on)
          copy.issue()
          loan = Loan(
              reader_id=reader.id,
              copy_id=copy.id,
              period=LoanPeriod(start=on, due=on + reader.loan_term),
          )
          self.copies.save(copy)
          return self.loans.save(loan)
  ```

## Доменные события
- Доменные события - это события, происходящие во время работы usecase. Описываются с classic-signals (см. раздел "Сигналы" навыка `python-classic-app`). Если на событие реагирует сам домен, контракт события объявляется в домене (`domain/events.py`), а не в `app/commands/signals.py`, чтобы домен не импортировал app.
- Обработчики (reaction) могут располагаться как в модели домена, если нужно запустить еще какое-то действие в домене, так и в адаптерах, если нужен вызов служебной логики. Обработчики события должны работать последовательно, без распараллеливания.

## Тестирование
Доменные тесты - unit-тесты без БД и фикстур: агрегат собирается вручную, вызывается `check()`, метод или критерий (см. пирамиду в `python-classic-architecture`).
Подробные правила (hypothesis, «почти валидные» входы, обе формы критериев) - в `references/testing.md` этого навыка. Читай его, когда пишешь или правишь доменные тесты.
