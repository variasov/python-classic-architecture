from datetime import date
from typing import Any

from classic.db_tools import Engine, Entity

from library.app.queries.readers.find_readers import (
    FindReadersGateway,
    FindReadersParams,
    ReaderListItemDTO,
)


class DbFindReadersGateway(FindReadersGateway):
    """Список читателей из PostgreSQL."""

    def __init__(self, db: Engine[Any]) -> None:
        self._db = db

    def run(
        self,
        params: FindReadersParams,
        on: date,
    ) -> list[ReaderListItemDTO]:
        readers: list[ReaderListItemDTO] = (
            self._db.query_from('gateways/readers/find_readers.sql.tmpl')
            .map_to(
                ReaderListItemDTO,
                ReaderListItemDTO=Entity(ReaderListItemDTO, 'id'),
            )
            .all(
                on=on,
                limit=params.limit,
                offset=params.offset,
            )
        )
        return readers
