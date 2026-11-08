from typing import Any

from classic.criteria import Criteria
from classic.db_tools import Append, Assign, Engine, Entity, Value

from library.app.commands.domain.book import (
    Book,
    BookNotFound,
    BooksRepo,
    Copy,
    ShelfLocation,
)


class BooksRepository(BooksRepo):
    def __init__(self, db: Engine[Any]) -> None:
        self._db = db

    def get_by_id(self, id: int) -> Book:
        book = (
            self._db.query_from('aggregates/books/get_by_id.sql')
            .map_to(
                Book,
                book=Entity(Book, 'id', copies=Append(Copy)),
                copy=Entity(
                    Copy,
                    'inventory_number',
                    shelf=Assign('shelf'),
                ),
                shelf=Value(ShelfLocation),
            )
            .one(id=id)
        )
        if book is None:
            raise BookNotFound(id=id)
        return book

    def save(self, book: Book) -> Book:
        book.check()
        book_id = book.id
        if book_id is None:
            book_id = int(
                self._db.query_from('aggregates/books/insert.sql').scalar(
                    isbn=book.isbn,
                    title=book.title,
                    authors=book.authors,
                    published_year=book.published_year,
                ),
            )
            book.id = book_id
        else:
            row = (
                self._db.query_from('aggregates/books/update.sql')
                .execute(
                    id=book_id,
                    isbn=book.isbn,
                    title=book.title,
                    authors=book.authors,
                    published_year=book.published_year,
                )
                .fetchone()
            )
            if row is None:
                raise BookNotFound(id=book_id)
        self._sync_copies(book_id, book)
        return book

    def find(self, criteria: Criteria[Book]) -> list[Book]:
        books: list[Book] = (
            self._db.query_from('aggregates/books/find.sql.tmpl')
            .map_to(
                Book,
                book=Entity(Book, 'id', copies=Append(Copy)),
                copy=Entity(
                    Copy,
                    'inventory_number',
                    shelf=Assign('shelf'),
                ),
                shelf=Value(ShelfLocation),
            )
            .all(criteria=criteria)
        )
        return books

    def _sync_copies(self, book_id: int, book: Book) -> None:
        for copy in book.copies:
            self._db.query_from('aggregates/books/upsert_copy.sql').execute(
                book_id=book_id,
                inventory_number=copy.inventory_number,
                hall=copy.shelf.hall,
                rack=copy.shelf.rack,
                shelf=copy.shelf.shelf,
                is_available=copy.is_available,
            )
        self._db.query_from(
            'aggregates/books/delete_missing_copies.sql',
        ).execute(
            book_id=book_id,
            inventory_numbers=[copy.inventory_number for copy in book.copies],
        )
