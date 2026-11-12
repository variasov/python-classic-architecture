import falcon

from library.app.queries.books.get_book import GetBook


class BookResource:
    def __init__(self, get_book: GetBook) -> None:
        self._get_book = get_book

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        resp.media = self._get_book.run(req.params)  # pyright: ignore[reportArgumentType]
