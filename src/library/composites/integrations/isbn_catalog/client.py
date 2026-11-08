from library.composites.integrations.isbn_catalog.settings import settings
from library.integrations.isbn_catalog.client import IsbnCatalogClient

isbn_catalog_client = IsbnCatalogClient(settings=settings)
