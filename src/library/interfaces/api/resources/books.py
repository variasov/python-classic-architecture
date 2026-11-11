from dataclasses import dataclass
from typing import ClassVar

import falcon
from pydantic import TypeAdapter

from library.app.commands.use_cases.books.create_book import (
    CreateBook,
    CreateBookParams,
)
from library.app.queries.books.find_books import (
    BookListItemDTO,
    FindBooks,
    FindBooksParams,
)
from library.interfaces.api.middleware import current_account


@dataclass(frozen=True)
class BookCreated:
    """Контракт ответа на создание книги."""

    id: int


class BooksResource:
    _query_validator: ClassVar = TypeAdapter(FindBooksParams)
    _books_serializer: ClassVar = TypeAdapter(list[BookListItemDTO])
    _create_validator: ClassVar = TypeAdapter(CreateBookParams)
    _created_serializer: ClassVar = TypeAdapter(BookCreated)

    def __init__(self, create_book: CreateBook, find_books: FindBooks) -> None:
        self._create_book = create_book
        self._find_books = find_books

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._query_validator.validate_python(req.params)
        books = self._find_books.run(params)
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._books_serializer.dump_json(books)

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._create_validator.validate_json(req.bounded_stream.read())
        book_id = self._create_book.run(params, current_account(req))
        resp.status = falcon.HTTP_201
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._created_serializer.dump_json(BookCreated(id=book_id))
