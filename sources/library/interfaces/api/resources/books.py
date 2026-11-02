from dataclasses import dataclass
from typing import ClassVar

import falcon
from library.app.commands.use_cases.books.add_copy import AddCopy, AddCopyParams
from library.app.commands.use_cases.books.create_book import (
    CreateBook,
    CreateBookParams,
)
from library.app.commands.use_cases.books.create_book_from_catalog import (
    CreateBookFromCatalog,
    CreateBookFromCatalogParams,
)
from library.app.queries.books.find_books import (
    FindBooks,
    FindBooksParams,
    FoundBook,
)
from library.app.queries.books.get_book import BookCard, GetBook, GetBookParams
from library.interfaces.api.middleware import get_account
from pydantic import TypeAdapter


@dataclass(frozen=True)
class BookCreated:
    """Контракт ответа на создание книги: usecase возвращает только id."""

    id: int


class BooksResource:
    _query_validator: ClassVar = TypeAdapter(FindBooksParams)
    _create_validator: ClassVar = TypeAdapter(CreateBookParams)
    _books_serializer: ClassVar = TypeAdapter(list[FoundBook])
    _created_serializer: ClassVar = TypeAdapter(BookCreated)

    def __init__(self, find_books: FindBooks, create_book: CreateBook) -> None:
        self._find_books = find_books
        self._create_book = create_book

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._query_validator.validate_python(req.params)
        books = self._find_books.run(params)
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._books_serializer.dump_json(books)

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._create_validator.validate_json(req.bounded_stream.read())
        book_id = self._create_book.run(params, get_account(req))
        resp.status = falcon.HTTP_201
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._created_serializer.dump_json(BookCreated(id=book_id))


class BookResource:
    _query_validator: ClassVar = TypeAdapter(GetBookParams)
    _card_serializer: ClassVar = TypeAdapter(BookCard)

    def __init__(self, get_book: GetBook) -> None:
        self._get_book = get_book

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._query_validator.validate_python(req.params)
        card = self._get_book.run(params)
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._card_serializer.dump_json(card)


class CatalogBooksResource:
    _create_validator: ClassVar = TypeAdapter(CreateBookFromCatalogParams)
    _created_serializer: ClassVar = TypeAdapter(BookCreated)

    def __init__(self, create_book_from_catalog: CreateBookFromCatalog) -> None:
        self._create_book_from_catalog = create_book_from_catalog

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._create_validator.validate_json(req.bounded_stream.read())
        book_id = self._create_book_from_catalog.run(params, get_account(req))
        resp.status = falcon.HTTP_201
        resp.content_type = falcon.MEDIA_JSON
        resp.data = self._created_serializer.dump_json(BookCreated(id=book_id))


class CopiesResource:
    _create_validator: ClassVar = TypeAdapter(AddCopyParams)

    def __init__(self, add_copy: AddCopy) -> None:
        self._add_copy = add_copy

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        params = self._create_validator.validate_json(req.bounded_stream.read())
        self._add_copy.run(params, get_account(req))
