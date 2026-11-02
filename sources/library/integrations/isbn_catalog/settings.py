from pydantic_settings import BaseSettings


class IsbnCatalogSettings(BaseSettings):
    ISBN_CATALOG_URL: str = 'http://localhost:8081'
    ISBN_CATALOG_TIMEOUT: float = 5.0
