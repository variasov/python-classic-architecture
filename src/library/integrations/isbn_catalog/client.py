from dataclasses import dataclass
from typing import ClassVar
from urllib.parse import urlencode

import pydantic
import urllib3
from pydantic import TypeAdapter

from library.app.commands.use_cases.books.create_book_from_catalog import (
    CatalogBook,
    IsbnCatalog,
)
from library.integrations.isbn_catalog.settings import IsbnCatalogSettings


@dataclass(frozen=True)
class CatalogBookPayload:
    """Контракт ответа внешнего каталога на запрос книги."""

    isbn: str
    title: str
    authors: list[str]
    year: int


class IsbnCatalogUnavailable(Exception):
    """Каталог ISBN недоступен или вернул неожиданный ответ."""


class IsbnCatalogClient(IsbnCatalog):
    """Клиент внешнего каталога ISBN поверх urllib3."""

    _payload_adapter: ClassVar = TypeAdapter(CatalogBookPayload)

    def __init__(self, settings: IsbnCatalogSettings) -> None:
        self._settings = settings
        self._http = urllib3.PoolManager()

    def find(self, isbn: str) -> CatalogBook | None:
        base_url = self._settings.ISBN_CATALOG_URL.rstrip('/')
        url = f'{base_url}/books?{urlencode({"isbn": isbn})}'
        try:
            response = self._http.request(
                'GET',
                url,
                timeout=self._settings.ISBN_CATALOG_TIMEOUT,
            )
        except (urllib3.exceptions.HTTPError, OSError) as error:
            raise IsbnCatalogUnavailable(
                f'Каталог ISBN недоступен: {error}',
            ) from error
        if response.status == 404:
            return None
        if response.status != 200:
            raise IsbnCatalogUnavailable(
                f'Каталог ISBN вернул код {response.status}',
            )
        try:
            payload = self._payload_adapter.validate_json(response.data)
        except pydantic.ValidationError as error:
            raise IsbnCatalogUnavailable(
                'Каталог ISBN вернул некорректный ответ',
            ) from error
        return CatalogBook(
            isbn=payload.isbn,
            title=payload.title,
            authors=list(payload.authors),
            year=payload.year,
        )
