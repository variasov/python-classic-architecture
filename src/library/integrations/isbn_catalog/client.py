from dataclasses import dataclass

import urllib3
from pydantic import BaseModel, ValidationError

from library.app.commands.isbn_catalog import CatalogBook, IsbnCatalog
from library.integrations.isbn_catalog.settings import IsbnCatalogSettings

HTTP_OK = 200
HTTP_NOT_FOUND = 404


class IsbnCatalogError(Exception):
    """Базовый класс ошибок интеграции с каталогом ISBN."""


@dataclass
class IsbnCatalogUnavailable(IsbnCatalogError):
    status: int

    def __str__(self) -> str:
        return f'Каталог ISBN ответил статусом {self.status}'


class IsbnCatalogInvalidResponse(IsbnCatalogError):
    def __str__(self) -> str:
        return 'Каталог ISBN вернул некорректный ответ'


class CatalogBookResponse(BaseModel):
    model_config = {'extra': 'ignore'}

    isbn: str
    title: str
    authors: list[str]
    year: int


class IsbnCatalogClient(IsbnCatalog):
    def __init__(self, settings: IsbnCatalogSettings) -> None:
        self._http = urllib3.PoolManager()
        self._base_url = settings.ISBN_CATALOG_URL.rstrip('/')

    def find(self, isbn: str) -> CatalogBook | None:
        response = self._http.request(
            'GET',
            f'{self._base_url}/books',
            fields={'isbn': isbn},
        )
        if response.status == HTTP_NOT_FOUND:
            return None
        if response.status != HTTP_OK:
            raise IsbnCatalogUnavailable(status=response.status)
        try:
            model = CatalogBookResponse.model_validate_json(response.data)
        except ValidationError as error:
            raise IsbnCatalogInvalidResponse from error
        return CatalogBook(
            isbn=model.isbn,
            title=model.title,
            authors=model.authors,
            year=model.year,
        )
