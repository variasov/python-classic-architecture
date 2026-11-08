from dataclasses import dataclass
from typing import ClassVar, cast

import falcon
from pydantic import TypeAdapter

from library.app.commands.use_cases.books.create_book import (
    CreateBook,
    CreateBookParams,
)
from library.app.queries.books.find_books import (
    BookDTO,
    FindBooks,
    FindBooksParams,
)
from library.app.roles import Account


@dataclass(frozen=True)
class BookCreated:
    id: int


class BooksResource:
    _find_validator: ClassVar[TypeAdapter[FindBooksParams]] = TypeAdapter(
        FindBooksParams,
    )
    _create_validator: ClassVar[TypeAdapter[CreateBookParams]] = TypeAdapter(
        CreateBookParams,
    )
    _books_serializer: ClassVar[TypeAdapter[list[BookDTO]]] = TypeAdapter(
        list[BookDTO],
    )
    _created_serializer: ClassVar[TypeAdapter[BookCreated]] = TypeAdapter(
        BookCreated,
    )

    def __init__(
        self,
        find_books: FindBooks,
        create_book: CreateBook,
    ) -> None:
        self._find_books = find_books
        self._create_book = create_book

    def on_get(
        self,
        req: falcon.Request,
        resp: falcon.Response,
    ) -> None:
        params = self._find_validator.validate_python(req.params)
        books = self._find_books.run(params)
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._books_serializer.dump_json(books)

    def on_post(
        self,
        req: falcon.Request,
        resp: falcon.Response,
    ) -> None:
        params = self._create_validator.validate_json(
            req.bounded_stream.read(),
        )
        account = cast('Account', req.context.account)
        book_id = self._create_book.run(account, params)
        resp.status = falcon.HTTP_201
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._created_serializer.dump_json(
            BookCreated(id=book_id),
        )
