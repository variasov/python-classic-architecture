import urllib3
from library.app.commands.use_cases.books.create_book_from_catalog import (
    CatalogBook,
    IsbnCatalog,
)
from library.integrations.isbn_catalog.settings import IsbnCatalogSettings
from pydantic import BaseModel, ValidationError

HTTP_OK = 200
HTTP_NOT_FOUND = 404


class IsbnCatalogUnavailable(Exception):
    """Каталог ISBN ответил ошибкой или невалидными данными."""


class CatalogBookModel(BaseModel):
    """Контракт ответа каталога ISBN."""

    isbn: str
    title: str
    authors: list[str]
    year: int


class IsbnCatalogClient(IsbnCatalog):
    def __init__(
        self,
        settings: IsbnCatalogSettings,
        http: urllib3.PoolManager | None = None,
    ) -> None:
        self._settings = settings
        self._http = http or urllib3.PoolManager()

    def find(self, isbn: str) -> CatalogBook | None:
        url = f'{self._settings.ISBN_CATALOG_URL.rstrip("/")}/books'
        try:
            response = self._http.request(
                'GET',
                url,
                fields={'isbn': isbn},
                timeout=self._settings.ISBN_CATALOG_TIMEOUT,
                retries=False,
            )
        except urllib3.exceptions.HTTPError as error:
            raise IsbnCatalogUnavailable(str(error)) from error
        if response.status == HTTP_NOT_FOUND:
            return None
        if response.status != HTTP_OK:
            raise IsbnCatalogUnavailable(f'Каталог ответил статусом {response.status}')
        try:
            model = CatalogBookModel.model_validate_json(response.data)
        except ValidationError as error:
            raise IsbnCatalogUnavailable('Каталог вернул невалидный ответ') from error
        return CatalogBook(
            isbn=model.isbn,
            title=model.title,
            authors=model.authors,
            year=model.year,
        )
