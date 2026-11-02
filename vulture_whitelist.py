"""Белый список vulture: имена, которые используются через фреймворки."""
# ruff: noqa: B018, F821

# Фикстуры pytest, подключаемые через цепочку зависимостей, а не использованием значения
migrated_db
test_env

# Методы ресурсов и middleware falcon вызываются фреймворком
on_get
on_post
on_put
process_request
content_type
