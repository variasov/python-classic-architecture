from typing import Any, ClassVar

from classic.db_tools import Engine, Value

from library.app.queries.books.find_books import (
    BookDTO,
    FindBooksGateway,
    FindBooksParams,
)


class FindBooksGatewayImpl(FindBooksGateway):
    _SORT_COLUMNS: ClassVar[dict[str, str]] = {
        'title': 'title',
        'published_year': 'published_year',
        'id': 'id',
    }

    def __init__(self, db: Engine[Any]) -> None:
        self._db = db

    def find(self, params: FindBooksParams) -> list[BookDTO]:
        search = params.title__contains
        title_like = f'%{search}%' if search is not None else None
        books: list[BookDTO] = (
            self._db.query_from('gateways/books/find.sql.tmpl')
            .map_to(BookDTO, bookdto=Value(BookDTO))
            .all(
                title_like=title_like,
                author=params.author,
                only_available=params.only_available,
                year_from=params.year_from,
                year_to=params.year_to,
                sort_column=self._SORT_COLUMNS[params.sort_by],
                sort_direction=params.sort_order.upper(),
                limit=params.limit,
                offset=params.offset,
            )
        )
        return books
