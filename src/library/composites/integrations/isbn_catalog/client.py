from library.composites.aspects.retry import retry_on_failure
from library.composites.integrations.isbn_catalog.settings import (
    isbn_catalog_settings,
)
from library.integrations.isbn_catalog.client import IsbnCatalogClient

isbn_catalog_client = IsbnCatalogClient(settings=isbn_catalog_settings)
isbn_catalog_client.find = retry_on_failure(  # pyright: ignore[reportAttributeAccessIssue]
    isbn_catalog_client.find,
)
