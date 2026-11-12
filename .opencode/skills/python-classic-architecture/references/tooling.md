# Конфигурация инструментов

Правила типизации и статического анализа - в разделе "Типизация и статический анализ" навыка `python-classic-architecture`. Здесь - эталонная конфигурация.

## pyproject.toml
Инструменты ставятся в группу зависимостей `dev` и настраиваются в `pyproject.toml`:
```toml
[dependency-groups]
dev = [
    "pyright[nodejs]~=1.1.411",
    "ruff~=0.16.4",
    "vulture~=2.16",
    "import-linter",
    "freezegun",  # заморозка времени в тестах (date.today/datetime.now)
    # pytest и прочее
]

[tool.pyright]
include = ["src", "tests"]
exclude = [
    "**/__pycache__",
    "**/.pytest_cache",
    ".venv",
]
typeCheckingMode = "strict"
reportMissingTypeStubs = "none"

[[tool.pyright.executionEnvironments]]
root = "tests"
reportPrivateUsage = "none"
extraPaths = ["."]

[tool.ruff]
target-version = "py310"

[tool.ruff.lint]
select = ["ALL"]
ignore = [
    "D203",     # keeps D211: no blank line before class docstring
    "D213",     # keeps D212: multi-line summary on first line
    "EM",       # error-message style is overly prescriptive
    "TRY003",   # long exception messages are an API concern
    "ANN401",   # DB driver objects are dynamically typed
    "N802",     # Settings properties mirror environment variable names
    "N818",     # exception names are part of the public API
    "INP001",   # namespace packages without __init__.py by design
    "D1",       # docstrings only where they explain a contract, not everywhere
    "CPY001",   # no copyright headers
    "A002",     # `id` argument in repositories and DTO is part of the API
    "TC",       # dataclasses and TypeAdapter need annotation types at runtime
    "RUF001",   # Cyrillic in strings is intended
    "RUF002",   # Cyrillic in docstrings is intended
    "RUF003",   # Cyrillic in comments is intended
]

[tool.ruff.lint.flake8-quotes]
inline-quotes = "single"

[tool.ruff.format]
quote-style = "single"

[tool.ruff.lint.per-file-ignores]
"tests/**" = [
    "SLF001",
    "S101",     # `assert` is idiomatic in pytest
    "D",        # tests do not need docstrings
    "ANN",      # test annotations are optional
    "FBT",      # boolean positional args in test helpers
    "PLR2004",  # magic values are acceptable in assertions
    "PLR0913",  # many-argument test helpers
    "PT011",    # broad pytest.raises is acceptable in tests
    "PT012",    # pytest.raises blocks may legitimately hold several statements
    "ARG",      # unused fixture/helper args
    "CPY001",   # tests do not carry copyright headers
    "S608",     # SQL strings in tests are not injection vectors
]

[tool.vulture]
paths = ["src", "tests", "vulture_whitelist.py"]
min_confidence = 80

[tool.pytest.ini_options]
addopts = "--import-mode=importlib"

[tool.importlinter]
root_packages = ["<package>", "classic"]
include_external_packages = true

[[tool.importlinter.contracts]]
name = "Layers: composites -> adapters -> app"
type = "layers"
layers = [
    "<package>.composites",
    "<package>.interfaces | <package>.infra | <package>.integrations",
    "<package>.app",
]

[[tool.importlinter.contracts]]
name = "Domain imports only stdlib minimum and allowed classic packages"
type = "forbidden"
source_modules = ["<package>.app.commands.domain"]
forbidden_modules = ["*", "<package>.app.*", "<package>.app.commands.*"]
unmatched_ignore_imports_alerting = "none"
ignore_imports = [
    "<package>.app.commands.domain.** -> abc",
    "<package>.app.commands.domain.** -> collections",
    "<package>.app.commands.domain.** -> dataclasses",
    "<package>.app.commands.domain.** -> datetime",
    "<package>.app.commands.domain.** -> enum",
    "<package>.app.commands.domain.** -> typing",
    "<package>.app.commands.domain.** -> classic.criteria",
    "<package>.app.commands.domain.** -> classic.criteria.**",
    "<package>.app.commands.domain.** -> classic.signals",
    "<package>.app.commands.domain.** -> classic.signals.**",
]

[[tool.importlinter.contracts]]
name = "Queries do not import commands"
type = "forbidden"
source_modules = ["<package>.app.queries"]
forbidden_modules = ["<package>.app.commands"]

[[tool.importlinter.contracts]]
name = "App imports only allowed libraries"
type = "forbidden"
source_modules = ["<package>.app"]
forbidden_modules = ["*"]
unmatched_ignore_imports_alerting = "none"
ignore_imports = [
    "<package>.app.** -> abc",
    "<package>.app.** -> collections",
    "<package>.app.** -> dataclasses",
    "<package>.app.** -> datetime",
    "<package>.app.** -> enum",
    "<package>.app.** -> logging",
    "<package>.app.** -> typing",
    "<package>.app.** -> classic.criteria",
    "<package>.app.** -> classic.criteria.**",
    "<package>.app.** -> classic.signals",
    "<package>.app.** -> classic.signals.**",
    # библиотеки для технической логики app (отчёты и т.п.), например:
    # "<package>.app.** -> openpyxl",
]
```

## import-linter
- Запуск: `lint-imports` (через `uv run lint-imports`). Проверяется установленный пакет, поэтому проект ставится в режиме редактирования (`pip install -e` / `uv sync`).
- Контракты зеркалят правила слоёв из `python-classic-architecture`, `python-classic-app` и `python-classic-domain`:
  - `layers` с тремя адаптерами через `|` - адаптеры одного уровня, зависят только от app и не знают друг о друге;
  - домен импортирует только минимум стандартной библиотеки и `classic.criteria`, `classic.signals`, а из проекта - только сам домен;
  - запросы не импортируют ничего из `app/commands` (CQRS);
  - остальной app импортирует только разрешённые библиотеки.
- Зависимости задаются белыми списками: контракт `forbidden` с маской `*` в `forbidden_modules` запрещает любые импорты, а `ignore_imports` перечисляет разрешённые - по строке на модуль. Новая библиотека в проекте сразу запрещена и в домене, и в app, без правки конфига, а технологии из стандартной библиотеки (`json`, `sqlite3`, `http`, `os`) тоже не проходят. `unmatched_ignore_imports_alerting = "none"` нужен, чтобы не используемые пока разрешения не считались ошибкой.
- Маска `*` закрывает только внешние модули: модули проекта, содержащие источник (`<package>`, `<package>.app`), import-linter пропускает. Поэтому в контракте домена к ней добавлены `<package>.app.*` и `<package>.app.commands.*`: они запрещают домену `errors.py`, `roles.py`, `queries`, `use_cases` и любые другие модули app, а сам домен из запрета выпадает, так как содержит источник.
- Требования к домену и к остальному app различаются:
  - белый список домена фиксирован и минимален: домен - модель предметной области, ему не нужны ни библиотеки, ни логирование;
  - белый список app начинается с того же минимума и расширяется по необходимости. В app, кроме домена, размещается логика, которая удовлетворяет требования бизнеса, но носит технический характер, например генерация отчёта Excel. Библиотека для такой логики (`openpyxl`) добавляется в белый список app. Фреймворки, драйверы, клиенты внешних систем и библиотеки парсинга и сериализации входа/выхода в него не добавляются: это технологии адаптеров.
- Модуль стандартной библиотеки добавляется в белый список домена, только когда он нужен доменной логике и не привязывает её к технологии (например, `decimal`, `uuid`, `itertools`).
- Если домена нет, контракт домена не добавляется.
- Внешний пакет (`include_external_packages = true`) import-linter схлопывает в один узел по первому сегменту имени: `classic.criteria` и `classic.db_tools` для него - один и тот же `classic`. Пакет, у которого разрешена только часть подпакетов, объявляется в `root_packages`: тогда import-linter анализирует его код и видит подпакеты. Так `classic` разрешается в app только частично - `classic.criteria` и `classic.signals`, а `classic.db_tools`, `classic.migrations`, `classic.scheduler` запрещены.
- Разрешённый подпакет корневого пакета указывается двумя строками - `-> classic.signals` и `-> classic.signals.**`: импорты идут и в сам пакет (`from classic.signals import Hub`), и в его модули (`classic.criteria.criteria`), а маска `**` сам пакет не включает.
- Имена контрактов пишутся по-английски: вывод `lint-imports` в консоли Windows искажает кириллицу.

## vulture_whitelist.py
Vulture не знает о вызовах через фреймворки (методы `on_get`/`on_post` ресурсов falcon, фикстуры pytest, `__post_init__`). Ложные срабатывания подавляются белым списком `vulture_whitelist.py` в корне проекта, который передаётся vulture вместе с исходниками (см. `paths` выше), а не понижением `min_confidence`.

## pytest
В пакете нет `__init__.py`, в том числе в `tests/`, поэтому одноимённые файлы тестов в разных каталогах разрешаются режимом импорта `--import-mode=importlib` (см. `[tool.pytest.ini_options]` выше).
