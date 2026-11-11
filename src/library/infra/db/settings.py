from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    """Настройки подключения к PostgreSQL"""

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    MIGRATIONS_SCHEMA: str = 'library_migrations'

    model_config = SettingsConfigDict(extra='ignore')

    @property
    def DB_CONN_INFO(self) -> str:
        """Строка подключения psycopg"""
        return (
            f'host={_quote_value(self.DB_HOST)} '
            f'port={self.DB_PORT} '
            f'dbname={_quote_value(self.DB_NAME)} '
            f'user={_quote_value(self.DB_USER)} '
            f'password={_quote_value(self.DB_PASS)}'
        )


def _quote_value(value: str) -> str:
    escaped = value.replace('\\', '\\\\').replace("'", "\\'")
    return f"'{escaped}'"
