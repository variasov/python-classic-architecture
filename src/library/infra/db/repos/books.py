from typing import Any

from classic.criteria import Criteria
from classic.db_tools import Engine, Entity

from library.app.commands.domain.book import Book, BookNotFound, BooksRepo


class DbBooksRepo(BooksRepo):
    """Репозиторий книг поверх PostgreSQL"""

    def __init__(self, db: Engine[Any]) -> None:
        self._db = db

    def get_by_id(self, id: int) -> Book:
        book: Book | None = (
            self._db.query_from('aggregates/books/get_by_id.sql')
            .map_to(Book, Book=Entity(Book, 'id'))
            .one(id=id)
        )
        if book is None:
            raise BookNotFound(id=id)
        return book

    def save(self, book: Book) -> Book:
        book.check()
        if book.id is None:
            book.id = self._db.query_from('aggregates/books/insert.sql').scalar(
                **book.__dict__
            )
        else:
            updated = self._db.query_from('aggregates/books/update.sql').scalar(
                **book.__dict__
            )
            if updated is None:
                raise BookNotFound(id=book.id)
        self._sync_authors(book)
        return book

    def find(self, criteria: Criteria[Book]) -> list[Book]:
        books: list[Book] = (
            self._db.query_from('aggregates/books/find.sql.tmpl')
            .map_to(Book, Book=Entity(Book, 'id'))
            .all(criteria=criteria)
        )
        return books

    def _sync_authors(self, book: Book) -> None:
        assert book.id is not None
        self._db.query_from('aggregates/books/delete_authors.sql').execute(
            book_id=book.id
        )
        rows = [
            {'book_id': book.id, 'position': position, 'name': name}
            for position, name in enumerate(book.authors)
        ]
        self._db.query_from('aggregates/books/insert_authors.sql').executemany(rows)
