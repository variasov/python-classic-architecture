import falcon

from library.app.commands.use_cases.books.create_book import CreateBook
from library.app.queries.books.find_books import FindBooks


class BooksResource:
    def __init__(self, create_book: CreateBook, find_books: FindBooks) -> None:
        self._create_book = create_book
        self._find_books = find_books

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        resp.media = self._find_books.run(req.params)  # pyright: ignore[reportArgumentType]

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        resp.media = self._create_book.run(req.media, req.context.account)
        resp.status = falcon.HTTP_201
