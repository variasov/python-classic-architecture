from dataclasses import asdict
from typing import ClassVar, cast

from classic.db_tools import Engine, Entity
from library.app.queries.books.find_books import (
    BooksSearchGateway,
    FindBooksParams,
    FoundBook,
)


class DbBooksSearchGateway(BooksSearchGateway):
    # Белый список сортировки: значение Literal -> колонка
    _ORDER_COLUMNS: ClassVar[dict[str, tuple[str, str]]] = {
        'title': ('b', 'title'),
        'published_year': ('b', 'published_year'),
        'isbn': ('b', 'isbn'),
    }

    def __init__(self, engine: Engine) -> None:
        self._db = engine

    def find(self, params: FindBooksParams) -> list[FoundBook]:
        query_params = {
            **asdict(params),
            'order_column': self._ORDER_COLUMNS[params.order_by],
        }
        return cast(
            'list[FoundBook]',
            list(
                self._db.query_from('gateways/books/find.sql.tmpl')
                .map_to(FoundBook, FoundBook=Entity(FoundBook, 'id'))
                .all(query_params),
            ),
        )
