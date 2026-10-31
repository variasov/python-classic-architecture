---
name: python-classic-adapters-sql-db
description: SQL DB адаптер (infra/db, classic-db-tools, classic-migrations) для приложения на Python в "классической" архитектуре - схема и миграции, запросы, маппинг, репозитории, гейтвеи, тестирование с тестовой БД. Использовать вместе с python-classic-architecture.
license: MIT
compatibility: opencode
---

# Python SQL DB adapter in "Classic" Architecture 

## Описание

В этом навыке описывается адаптер к SQL DB для приложений на Python,
соответствующих шаблону "Классической" архитектуры. Это адаптер группы `infra`.
Общая идея слоёв и правила группы infra описаны в навыке `python-classic-architecture`,
абстрактные репозитории - в `python-classic-domain`, гейтвеи - в `python-classic-app`.

## Когда использовать
- Во время разработки новых фич в Python-приложении с "Классической" архитектурой, требующих доступа к SQL DB.
- При настройке тестовой БД и фикстур.
- При падении интеграционных тестов из-за рассинхрона БД и кода.

## Структура пакета
- Адаптер размещается в `infra/`. Если внутренняя БД одна, пакет должен называться `db`. Если БД несколько, то названия должны соответствовать назначению БД.
- Структура пакета:
  ```
  infra/db/
    constants.py        # пути к каталогам sql
    settings.py         # настройки подключения (pydantic-settings)
    repos/              # реализации репозиториев агрегатов
    gateways/           # реализации гейтвеев usecase-запросов
    subscribers/        # подписчики на сигналы, работающие с БД
    sql/
      schema/           # DDL целевого состояния БД
      migrations/       # миграции
      aggregates/<aggregate>/   # запросы репозиториев + criteria.sql.tmpl
      gateways/<group>/         # запросы гейтвеев
      subscribers/              # запросы подписчиков
  ```
- Пути к каталогам задаются в `constants.py`, а не вычисляются в разных местах:
  ```python
  # infra/db/constants.py
  SQL_DIR_PATH = Path(__file__).parent / 'sql'
  SCHEMA_DIR_PATH = SQL_DIR_PATH / 'schema'
  MIGRATIONS_DIR_PATH = SQL_DIR_PATH / 'migrations'
  AGGREGATES_DIR_PATH = SQL_DIR_PATH / 'aggregates'
  GATEWAYS_DIR_PATH = SQL_DIR_PATH / 'gateways'
  ```
- В пакете размещается файл settings.py, в котором содержится класс, читающий переменные окружения и предоставляющий настройки для адаптера. Для настроек используется pydantic-settings. Класс отдаёт готовую строку подключения (например, свойство `DB_CONN_INFO`). Инстанс настроек создаётся в композите.

## Схема и миграции
- В sql/schema размещаются .sql файлы, содержащие DDL-запросы, описывающие целевое состояние БД. Это снапшот текущего состояния: при любом добавлении или изменении миграции его обязательно нужно актуализировать. В снапшот переносится только финальное состояние, без временных `DEFAULT` и промежуточных `ALTER`.
- В sql/migrations размещаются файлы миграций, так же содержащие DDL, но отражающие уже историю изменений БД.
- Для применения/отката миграций используется Python-пакет classic-migrations.
- Файлы миграций именуются `NNNN.description.sql` (`0001.init.sql`, `0002.add_deleted_status.sql`) и начинаются с заголовков:
  ```sql
  -- transactional: true
  -- depends: 0001.init
  ```
- `-- depends:` указывает на предыдущую миграцию этого же модуля по имени файла без расширения. Зависимость на миграции чужих модулей не ставится.
- Объекты модуля размещаются в собственной схеме БД, а не в `public`.
- Ограничения CHECK не используются: инварианты проверяются только в домене.
- Внешние ключи от вложенных таблиц агрегата к корню и от зависимых агрегатов объявляются с `ON DELETE CASCADE`, чтобы удаление корня (в том числе в тестах) не требовало перечислять связанные таблицы.

## Запросы
- Для работы с SQL-запросами в Python используется classic-db-tools + драйвер для БД. Запросы загружаются из файлов: `engine.query_from('aggregates/readers/get_by_id.sql')`.
- `Engine` создаётся в композите, `templates_dirs` указывает на `SQL_DIR_PATH`. Драйвер и фабрика соединений передаются позиционно: `Engine(psycopg, lambda: psycopg.connect(conninfo=settings.DB_CONN_INFO), templates_dirs=[SQL_DIR_PATH])`. Репозитории и гейтвеи получают `Engine` через конструктор.
- Запросы репозитория лежат в `sql/aggregates/<aggregate>/`, запросы гейтвея - в `sql/gateways/<group>/`.
- Статические запросы (`.sql`) предпочтительнее, чем динамические.
- Динамические запросы предпочтительны, когда у запроса меняется форма в зависимости от входных параметров,
  например, добавляются условия в WHERE, добавляются JOIN, меняется ORDER BY и т.д. Динамические запросы - Jinja2-шаблоны с расширением `.sql.tmpl`, лежат рядом со статическими:
  ```sql
  SELECT id AS BookDTO__id, title AS BookDTO__title
  FROM library.books
  WHERE TRUE
  {% if title_like %} AND title ILIKE '%%' || {{ title_like }} || '%%' {% endif %}
  ORDER BY title
  ```
- Значения в шаблоне подставляются только через `{{ value }}` (автобиндинг в параметр запроса). Идентификаторы подставляются через фильтр `identifier` и только из белого списка. Собирать SQL конкатенацией строк в Python запрещено.
- Критерии из classic-criteria транслируются в SQL функцией `traverse(criteria, macros)` в шаблоне (доступна глобально). На каждый класс критерия описывается Jinja-макрос с тем же именем, что у метода-критерия. Макрос принимает ОДИН аргумент - сам объект критерия, параметры критерия читаются его атрибутами. `traverse` сам собирает `&`, `|`, `~` в `AND`, `OR`, `NOT`; результат выводится с `| safe`.
  Макросы агрегата лежат в `sql/aggregates/<aggregate>/criteria.sql.tmpl`, запрос импортирует их и обращается к таблице через алиас, оговорённый в комментарии файла макросов:
  ```sql
  {# sql/aggregates/loans/criteria.sql.tmpl. Таблица loans - алиас l #}
  {% macro overdue(criteria) -%}
      (l.returned_at IS NULL AND l.due < {{ criteria.on }})
  {%- endmacro %}

  {% macro returned(criteria) -%}
      l.returned_at IS NOT NULL
  {%- endmacro %}
  ```
  ```sql
  {# sql/aggregates/loans/find.sql.tmpl #}
  {% import 'aggregates/loans/criteria.sql.tmpl' as macros %}
  SELECT ... FROM library.loans l
  WHERE {{ traverse(criteria, macros) | safe }}
  ```

## Маппинг
- Для маппинга результатов запроса используй Entity и Value из classic-db-tools.
- Колонки в SQL обязательно именуются с префиксом `ClassName__`:
  ```sql
  SELECT
      r.id   AS Reader__id,
      r.name AS Reader__name
  FROM library.readers r
  WHERE r.id = %(reader_id)s
  ```
  ```python
  reader = (
      self._db.query_from('aggregates/readers/get_by_id.sql')
      .map_to(Reader, Reader=Entity(Reader, 'id'))
      .one(reader_id=reader_id)
  )
  ```
- Вложенные коллекции агрегата собираются одним запросом с JOIN через `Append`:
  ```python
  .map_to(
      Loan,
      loan=Entity(Loan, 'id', extensions=Append('extension')),
      extension=Entity(Extension, 'id'),
  )
  ```
- `Entity(Cls, 'key')` - для объектов с идентификатором, `Value(Cls)` - для объектов-значений. Вложенный объект (не коллекция) присваивается через `Assign`.
- Методы выборки: `.one()` - одна запись или `None`, `.all()` - список, `.scalar()`/`.scalars()` - значения, `.execute()`/`.executemany()` - без маппинга.
- Гейтвей маппит результат сразу в DTO, объявленные в usecase-запросе.

## Репозитории
- Репозиторий наследует ABC из доменной модели и реализует `get_by_id` и `save`.
- `get_by_id` при отсутствии агрегата бросает доменную ошибку `<Aggregate>NotFound`.
- `save` первым делом вызывает `check()` агрегата, затем сохраняет агрегат целиком. Вставка или обновление определяется ветвлением по наличию `id`:
  ```python
  def save(self, reader: Reader) -> Reader:
      reader.check()
      if reader.id is None:
          row = self._db.query_from('aggregates/readers/insert.sql').execute(**reader.__dict__).fetchone()
          reader.id = row[0]
      else:
          row = self._db.query_from('aggregates/readers/update.sql').execute(**reader.__dict__).fetchone()
          if row is None:
              raise ReaderNotFound(id=reader.id)
      self._sync_associations(reader)
      return reader
  ```
- Вложенные коллекции агрегата синхронизируются upsert-ом с удалением отсутствующих строк, а не через delete+insert.
- Транзакциями репозиторий не управляет: транзакция навешивается в композите на метод, с которого начинается работа, обычно на `run` usecase (`engine.transaction(usecase.run)`).

## Гейтвеи и подписчики
- Гейтвей реализует ABC из usecase-запроса и размещается в `infra/db/gateways/<gateway>.py`. Может использовать внутренние вспомогательные классы, но возвращает только DTO, объявленные в запросе.
- Белый список сортировки из параметров запроса (`Literal`/`Enum`) переводится в имена колонок словарём в гейтвее и подставляется в шаблон через фильтр `identifier`.
- Подписчики на сигналы, работающие с БД, - `infra/db/subscribers/<subscriber>.py`, их SQL - в `sql/subscribers/`.

## Тестирование
Тесты адаптера к БД - средний уровень пирамиды (см. `python-classic-architecture`): каждый репозиторий, гейтвей и подписчик тестируется отдельно, без usecase и композита, против настоящей тестовой БД. Мокать БД нельзя - тогда тест не проверяет ни SQL, ни маппинг, ни миграции.

### Размещение
```
tests/
  conftest.py                  # test_db_settings, migrated_db, db_engine, raw_db - общие с тестами композита
  adapters/infra/db/
    conftest.py                # фикстуры репозиториев, гейтвеев, фабрики данных
    test_<repo>.py
    test_<gateway>.py
    test_<subscriber>.py
```

### Тестовая БД
- Никогда не используется боевая БД. Имя тестовой БД задаётся явно.
- Настройки подключения к тестовой БД читаются отдельным классом (`TestDBSettings`), наследующим общие настройки адаптера и переопределяющим хост, порт, имя БД, пользователя, пароль и имя схемы миграций. Класс объявляется в `infra/db/settings.py` рядом с основным, переменные окружения с префиксом `TEST_`. Тесты композита берут параметры подключения из него же (см. `python-classic-composite`).

### Фикстуры
- Фикстуры БД общие для тестов адаптера и композита, поэтому лежат в корневом `tests/conftest.py`:
  ```
  test_db_settings
    -> migrated_db          # применяет миграции, teardown дропает схемы
      -> db_engine          # classic.db_tools.Engine поверх тестовой БД
        -> raw_db           # прямые SQL-проверки
  ```
- Сессионный `migrated_db` применяет миграции один раз на прогон и после прогона удаляет схемы `CASCADE` вместе со всеми объектами.
- Миграции применяются программно через `classic.migrations`: `MigrationsCollection` и `Migrator`, путь берётся из `infra/db/constants.py`. Так тесты проверяют именно те миграции, что попадут в бой:
  ```python
  collection = MigrationsCollection(sources=[str(MIGRATIONS_DIR_PATH)])
  with Migrator(
      driver='psycopg', db_host=..., db_port=..., db_name=...,
      db_user=..., db_pass=..., migration_schema=settings.TEST_MIGRATIONS_SCHEMA,
  ) as migrator:
      hooks, migrations = collection.to_apply(migrator.history())
      migrator.apply(migrations, hooks)
  ```
- `db_engine` собирается тем же вызовом `Engine(psycopg, factory, templates_dirs=[SQL_DIR_PATH])`, что и композит, иначе тесты проверяют не тот движок, который работает в бою.
- Репозитории, гейтвеи и подписчики создаются в фикстурах поверх `db_engine`. Тестируемый метод вызывается внутри транзакции `db_engine`, как в бою это делает обёртка из композита.

### Данные и изоляция
- Данные для теста создаются через репозитории (`save` собранного вручную агрегата), а не прямыми INSERT: так данные проходят через инварианты и тот же маппинг, что в бою. Это касается и тестов гейтвеев: гейтвей читает то, что записали репозитории.
- Фабрики агрегатов объявляются в `conftest.py` как функции с дефолтами и `**overrides`.
- Тесты, которые только читают данные, могут работать на общем seed-состоянии (`scope='session'`), созданном через репозитории.
- Тесты, которые меняют данные, обязаны за собой убирать. Фабрика `*_factory` (function-scoped, с `yield`) создаёт записи под конкретный тест и после теста удаляет их. Удаление выполняется после теста, а не до, и затрагивает только созданные тестом записи.
- Каждая запись, созданная фабрикой, получает уникальную метку, по которой teardown удаляет именно её, а не всё подряд.
- Удаление опирается на `ON DELETE CASCADE` в схеме, чтобы не перечислять все связанные таблицы вручную: teardown удаляет через `raw_db` только корни созданных агрегатов. Прямой `DELETE` в teardown допустим, прямой `INSERT` - нет.

### raw_db: прямые SQL-проверки
- Фикстура `raw_db` даёт доступ к `scalar`, `scalars` и `execute` поверх движка и используется для проверок, которые невозможно выразить через репозиторий: общее число строк, наличие записи в справочнике, факт soft-delete, отсутствие записи после откатившейся транзакции.
- Прямые запросы в тесте допустимы только для проверки состояния БД. Создание тестовых данных через raw SQL не допускается - это обходит инварианты и делает тест зависимым от деталей реализации.

### Что проверять
- Репозиторий:
  - агрегат, сохранённый и прочитанный заново, совпадает с исходным, включая вложенные коллекции;
  - обновление, добавление и удаление элементов вложенных коллекций;
  - `get_by_id` несуществующего - `<Aggregate>NotFound`;
  - `save` невалидного агрегата бросает доменную ошибку и ничего не пишет в БД;
  - каждый SQL-макрос критерия и их комбинации (`&`, `|`, `~`) дают ту же выборку, что и `is_satisfied_by` в домене.
- Общий контракт репозитория (сохранить и прочитать, `NotFound`, поиск по критериям) желательно оформить одним набором тестов, параметризованным настоящим и in-memory репозиторием из unit-тестов app. Так fake не расходится с реальной реализацией:
  ```python
  @pytest.fixture(params=['db_loans_repo', 'in_memory_loans_repo'])
  def any_loans_repo(request):
      return request.getfixturevalue(request.param)
  ```
  Фикстура `in_memory_loans_repo` для этого объявляется в корневом `tests/conftest.py` (см. `python-classic-app`).
- Гейтвей: каждый фильтр динамического шаблона по отдельности и в комбинации, сортировка по каждому значению белого списка, пагинация, пустой результат, маппинг в DTO.
- Подписчик: состояние БД после вызова реакции на сигнал.
- Не проверяются количество и текст SQL-запросов.
