from datetime import date
from typing import Any

from classic.db_tools import Engine, Value

from library.app.queries.readers.find_readers import (
    FindReadersGateway,
    ReaderDTO,
)


class FindReadersGatewayImpl(FindReadersGateway):
    def __init__(self, db: Engine[Any]) -> None:
        self._db = db

    def find(self, on: date) -> list[ReaderDTO]:
        readers: list[ReaderDTO] = (
            self._db.query_from('gateways/readers/find.sql')
            .map_to(ReaderDTO, readerdto=Value(ReaderDTO))
            .all(on=on)
        )
        return readers
