from typing import Any, ClassVar

from classic.db_tools import Engine, Entity

from library.app.queries.books.find_books import (
    BookListItemDTO,
    FindBooksGateway,
    FindBooksParams,
)


class DbFindBooksGateway(FindBooksGateway):
    """Поиск книг в PostgreSQL"""

    SORT_COLUMNS: ClassVar[dict[str, str]] = {
        'title': 'title',
        'published_year': 'published_year',
    }

    def __init__(self, db: Engine[Any]) -> None:
        self._db = db

    def run(self, params: FindBooksParams) -> list[BookListItemDTO]:
        books: list[BookListItemDTO] = (
            self._db.query_from('gateways/books/find_books.sql.tmpl')
            .map_to(BookListItemDTO, BookListItemDTO=Entity(BookListItemDTO, 'id'))
            .all(
                title_contains=params.title__contains,
                author=params.author,
                only_available=params.only_available,
                year_from=params.year_from,
                year_to=params.year_to,
                column=self.SORT_COLUMNS[params.order_by],
                limit=params.limit,
                offset=params.offset,
            )
        )
        return books
