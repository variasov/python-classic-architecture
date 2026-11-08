from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    DB_SCHEMA: str = 'library'

    @property
    def DB_CONN_INFO(self) -> str:
        return (
            f'host={self.DB_HOST} port={self.DB_PORT} '
            f'dbname={self.DB_NAME} user={self.DB_USER} '
            f'password={self.DB_PASS}'
        )


class TestDBSettings(DBSettings):
    model_config = SettingsConfigDict(
        env_prefix='TEST_',
        env_file='.env',
        extra='ignore',
    )

    DB_HOST: str = 'localhost'
    DB_PORT: int = 5432
    DB_USER: str = 'test'
    DB_PASS: str = 'test'  # noqa: S105
    DB_NAME: str = 'test'
    TEST_MIGRATIONS_SCHEMA: str = 'library_migrations_test'
