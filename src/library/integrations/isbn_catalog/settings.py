from pydantic_settings import BaseSettings, SettingsConfigDict


class IsbnCatalogSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    ISBN_CATALOG_URL: str
