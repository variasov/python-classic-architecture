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
```

## vulture_whitelist.py
Vulture не знает о вызовах через фреймворки (методы `on_get`/`on_post` ресурсов falcon, фикстуры pytest, `__post_init__`). Ложные срабатывания подавляются белым списком `vulture_whitelist.py` в корне проекта, который передаётся vulture вместе с исходниками (см. `paths` выше), а не понижением `min_confidence`.

## pytest
В пакете нет `__init__.py`, в том числе в `tests/`, поэтому одноимённые файлы тестов в разных каталогах разрешаются режимом импорта `--import-mode=importlib` (см. `[tool.pytest.ini_options]` выше).
