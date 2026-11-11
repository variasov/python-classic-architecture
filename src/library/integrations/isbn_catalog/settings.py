from pydantic_settings import BaseSettings, SettingsConfigDict


class IsbnCatalogSettings(BaseSettings):
    """Настройки клиента внешнего каталога ISBN"""

    ISBN_CATALOG_URL: str
    ISBN_CATALOG_TIMEOUT: float = 5.0

    model_config = SettingsConfigDict(extra='ignore')
