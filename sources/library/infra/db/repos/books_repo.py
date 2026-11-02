from typing import Any, cast

from classic.criteria import Criteria
from classic.db_tools import Append, Engine, Entity
from library.app.commands.domain.book import (
    Book,
    BookNotFound,
    BooksRepo,
    Copy,
    ShelfLocation,
)


def _make_copy(
    *,
    inventory_number: str,
    is_available: bool,
    hall: str,
    rack: int,
    shelf: int,
) -> Copy:
    return Copy(
        inventory_number=inventory_number,
        shelf=ShelfLocation(hall=hall, rack=rack, shelf=shelf),
        is_available=is_available,
    )


class DbBooksRepo(BooksRepo):
    def __init__(self, engine: Engine) -> None:
        self._db = engine

    def get_by_id(self, id: int) -> Book:
        book = cast(
            'Book | None',
            self._db.query_from('aggregates/books/get_by_id.sql')
            .map_to(
                Book,
                Book=Entity(Book, 'id', copies=Append('copy')),
                # Фабрика вызывается с именованными аргументами, а типы библиотеки
                # допускают только класс или Callable[[Any], Any]
                Copy=Entity(cast('Any', _make_copy), 'inventory_number'),
            )
            .one(id=id),
        )
        if book is None:
            raise BookNotFound(id=id)
        return book

    def save(self, book: Book) -> Book:
        book.check()
        if book.id is None:
            book.id = self._db.query_from('aggregates/books/insert.sql').scalar(
                isbn=book.isbn,
                title=book.title,
                authors=book.authors,
                published_year=book.published_year,
            )
        else:
            updated_id = self._db.query_from('aggregates/books/update.sql').scalar(
                id=book.id,
                isbn=book.isbn,
                title=book.title,
                authors=book.authors,
                published_year=book.published_year,
            )
            if updated_id is None:
                raise BookNotFound(id=book.id)
        self._sync_copies(cast('int', book.id), book)
        return book

    def find(self, criteria: Criteria[Book]) -> list[Book]:
        ids = self._db.query_from('aggregates/books/find_ids.sql.tmpl').scalars(
            criteria=criteria,
        )
        return [self.get_by_id(book_id) for book_id in ids]

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
        self._db.query_from('aggregates/books/delete_missing_copies.sql').execute(
            book_id=book_id,
            inventory_numbers=[c.inventory_number for c in book.copies],
        )
