from pydantic_settings import BaseSettings


class ApiSettings(BaseSettings):
    API_HOST: str = '127.0.0.1'
    API_PORT: int = 8080
    # Демо-аутентификация: статическая таблица login -> права
    API_USERS: dict[str, list[str]] = {
        'admin': ['books.edit', 'readers.edit', 'loans.edit'],
        'guest': [],
    }
