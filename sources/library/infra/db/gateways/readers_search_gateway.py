from dataclasses import asdict
from datetime import date
from typing import cast

from classic.db_tools import Engine, Entity
from library.app.queries.readers.find_readers import (
    FindReadersParams,
    FoundReader,
    ReadersSearchGateway,
)


class DbReadersSearchGateway(ReadersSearchGateway):
    def __init__(self, engine: Engine) -> None:
        self._db = engine

    def find(self, params: FindReadersParams, today: date) -> list[FoundReader]:
        return cast(
            'list[FoundReader]',
            list(
                self._db.query_from('gateways/readers/find.sql')
                .map_to(FoundReader, FoundReader=Entity(FoundReader, 'id'))
                .all({**asdict(params), 'today': today}),
            ),
        )
