from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    DB_HOST: str = 'localhost'
    DB_PORT: int = 5432
    DB_NAME: str = 'library'
    DB_USER: str = 'library'
    DB_PASS: str = 'library'  # noqa: S105 - демо-значение по умолчанию
    MIGRATIONS_SCHEMA: str = 'public'

    @property
    def DB_CONN_INFO(self) -> str:
        return (
            f'host={self.DB_HOST} port={self.DB_PORT} dbname={self.DB_NAME} '
            f'user={self.DB_USER} password={self.DB_PASS}'
        )


class TestDBSettings(DBSettings):
    """Настройки тестовой БД: переменные окружения с префиксом TEST_."""

    __test__ = False
    model_config = SettingsConfigDict(env_prefix='TEST_')

    DB_HOST: str = 'localhost'
    DB_PORT: int = 5432
    DB_NAME: str = 'test'
    DB_USER: str = 'test'
    DB_PASS: str = 'test'  # noqa: S105 - тестовая БД
    MIGRATIONS_SCHEMA: str = 'library_migrations'
