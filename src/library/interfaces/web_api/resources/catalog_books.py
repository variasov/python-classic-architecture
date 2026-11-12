import falcon

from library.app.commands.use_cases.books.create_book_from_catalog import (
    CreateBookFromCatalog,
)


class CatalogBooksResource:
    def __init__(self, create_book_from_catalog: CreateBookFromCatalog) -> None:
        self._create_book_from_catalog = create_book_from_catalog

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        resp.media = self._create_book_from_catalog.run(
            req.media,
            req.context.account,
        )
        resp.status = falcon.HTTP_201
