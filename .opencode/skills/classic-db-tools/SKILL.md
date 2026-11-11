---
name: classic-db-tools
description: Справка по API библиотеки classic-db-tools (classic.db_tools) - Engine, транзакции, запросы из файлов, статические и динамические (Jinja) шаблоны, автобиндинг параметров, трансляция критериев traverse, маппинг Entity/Value/Append/Assign. Загружать перед написанием кода с classic.db_tools. Как библиотека применяется в архитектуре - в python-classic-adapters-sql-db.
license: MIT
compatibility: opencode
---

# classic-db-tools: API

Только API, сверенный с версией 3.3. Правила применения (раскладка `sql/`, репозитории, где создаётся Engine) - в `python-classic-adapters-sql-db`.

## Engine
```python
import psycopg
from classic.db_tools import Engine, Entity, Value, Append, Assign, Add

engine = Engine(
    psycopg,                                      # драйвер DB API 2.0, позиционно
    lambda: psycopg.connect(conninfo=conninfo),   # фабрика соединений, позиционно
    templates_dirs=[SQL_DIR_PATH],                # str | PathLike | список
)
```
- Первые два аргумента только позиционные (`/` в сигнатуре).
- Создание Engine не открывает соединение: соединения берутся из встроенного пула при первом запросе.
- Вне `transaction()`/`conn()` каждый запрос выполняется в автокоммите.

## Транзакции и соединения
```python
with engine.transaction():          # commit при выходе, rollback при исключении
    ...
usecase.run = engine.transaction(usecase.run)   # то же как обёртка функции
with engine.transaction(commit=False): ...      # rollback всегда
with engine.conn(): ...                          # одно соединение без commit/rollback
```
- Вложенный `transaction()` создаёт SAVEPOINT.
- Все запросы внутри блока идут через одно соединение текущего потока - передавать соединение/курсор в репозитории не нужно.

## Запросы
```python
engine.query_from('aggregates/readers/get_by_id.sql')     # путь относительно templates_dirs
engine.query('SELECT 1', static=True)                      # из строки; по умолчанию static=False
```
- Файл `.sql` - статический: уходит в драйвер как есть, параметры - `%(name)s`.
- Файл `.sql.tmpl` - динамический: Jinja2-шаблон, собирается при каждом выполнении.
- Другое расширение у `query_from` - `ValueError`.
- Файлы загружаются лениво и кешируются.

### Динамические шаблоны
- Каждое `{{ expr }}` автоматически оборачивается в фильтр `bind`: значение уходит параметром запроса, а не текстом. Явно писать `|bind` не нужно.
- Не оборачиваются выражения, оканчивающиеся на `bind`, `inclause`, `sqlsafe`; результат Jinja-макроса (`Markup`) тоже вставляется как SQL.
- `{{ name | identifier }}` - идентификатор в кавычках (`"col"`); значение - только из белого списка.
- `{{ values | inclause }}` - список для `IN (...)`.
- `{{ text | sqlsafe }}` - вставить как есть. Только для доверенного SQL.
- Шаблон проходит через `%`-форматирование драйвера: литеральный `%` пишется `%%` (`ILIKE '%%' || {{ q }} || '%%'`).
- Доступны глобальные функции `traverse` и `contains` (ниже).

### Критерии в SQL: traverse
```sql
{# criteria.sql.tmpl #}
{% macro overdue(criteria) -%}
    (l.returned_at IS NULL AND l.due < {{ criteria.on }})
{%- endmacro %}
```
```sql
{% import 'aggregates/loans/criteria.sql.tmpl' as macros %}
SELECT ... FROM library.loans l
WHERE {{ traverse(criteria, macros) | safe }}
```
- `traverse(criteria, macros)` раскрывает `&`/`|`/`~` в `AND`/`OR`/`NOT`, для листа вызывает макрос с именем класса критерия. У критерия из `@criteria` имя класса = имя метода (`Loan.overdue(on=...)` → класс `overdue`), поэтому макрос называется как метод.
- Макрос получает ОДИН аргумент - объект критерия; параметры читаются атрибутами (`criteria.on`) и биндятся автоматически.
- Результат `traverse` - SQL из макросов, автобиндингом не превращается в параметр; `| safe` не обязателен, но допустим и принят в шаблонах.
- Нет макроса с нужным именем - `KeyError` при рендере.
- `AND`/`OR` не оборачиваются в скобки: если внутри макроса есть `OR`, оберни тело макроса в скобки.
- `contains(criteria, 'overdue', 'returned')` - есть ли в дереве критерий с одним из имён (для `{% if %}`).

## Выполнение и результаты
Параметры передаются kwargs или dict (оба можно вместе, kwargs приоритетнее); объект с `__dict__` - через `**obj.__dict__`.

| Метод | Возвращает |
|---|---|
| `.execute(**params)` | курсор (`.fetchone()`, `.fetchall()`) |
| `.executemany([...])` | пакетное выполнение |
| `.one(**params)` | первая строка или `None` |
| `.all(**params)` | список строк |
| `.iter(batch=500, **params)` | итератор строк |
| `.scalar(**params)` | первое значение первой строки или `None`; `raising=True` - `IndexError` |
| `.scalars(**params)` | итератор значений первого столбца |
| `.rowcount(**params)` | число затронутых строк |

Без маппинга строки - кортежи драйвера.

`INSERT ... RETURNING id`: `engine.query_from(...).execute(**params).fetchone()[0]`.

## Маппинг
```python
.map_to(Reader, Reader=Entity(Reader, 'id')).one(reader_id=1)       # -> Reader | None
.map_to(
    Loan,
    loan=Entity(Loan, 'id', extensions=Append('extension')),
    extension=Entity(Extension, 'id'),
).all()                                                             # -> list[Loan]
```
- Колонки называются `<prefix>__<field>` (`r.id AS Reader__id`). Регистр не важен: имена приводятся к нижнему.
- `map_to(Cls)` без kwargs - префикс = имя класса, конфигурация - `default_mapping` Engine. С kwargs - kwargs заменяют конфигурацию, первый аргумент задаёт тип результата и префикс (`map_to(Cls, 'prefix', ...)` - явный префикс).
- `Entity(Cls, 'id')` или `Entity(Cls, ('a', 'b'))` - объект с идентификатором; строки с одинаковым id схлопываются в один объект.
- `Value(Cls)` - объект-значение, создаётся на каждую строку; все поля `NULL` → `None` (`Value(Cls, False)` - создать всё равно).
- Связи: `Append('prefix')` - `.append` в список (one-to-many), `Add('prefix')` - `.add` в set, `Assign('prefix')` - присвоение атрибута (one-to-one). Связи по аннотациям полей часто распознаются автоматически, явные имеют приоритет.
- После `map_to` доступны `.one()`, `.all()`, `.iter()`; `.sources()` - текст сгенерированного маппера для отладки.

## Ошибки
- `classic.db_tools.pool.ConnectionLimitError` - пул исчерпан (`pool_kwargs={'limit': N, 'timeout': s}`).
- Ошибки драйвера (`psycopg.errors.*`) пробрасываются как есть.
- Ошибка синтаксиса шаблона - `jinja2.TemplateError`.
