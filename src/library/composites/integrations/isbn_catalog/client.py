import tenacity

from library.composites.integrations.isbn_catalog.settings import (
    isbn_catalog_settings,
)
from library.integrations.isbn_catalog.client import (
    IsbnCatalogClient,
    IsbnCatalogUnavailable,
)

isbn_catalog_client = IsbnCatalogClient(settings=isbn_catalog_settings)
isbn_catalog_client.find = tenacity.retry(  # pyright: ignore[reportAttributeAccessIssue]
    retry=tenacity.retry_if_exception_type(IsbnCatalogUnavailable),
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=0.1, max=2),
    reraise=True,
)(isbn_catalog_client.find)
