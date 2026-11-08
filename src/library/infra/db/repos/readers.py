from typing import Any

from classic.criteria import Criteria
from classic.db_tools import Assign, Engine, Entity, Value

from library.app.commands.domain.reader import (
    Contact,
    Membership,
    Reader,
    ReaderNotFound,
    ReadersRepo,
)


class ReadersRepository(ReadersRepo):
    def __init__(self, db: Engine[Any]) -> None:
        self._db = db

    def get_by_id(self, id: int) -> Reader:
        reader = (
            self._db.query_from('aggregates/readers/get_by_id.sql')
            .map_to(
                Reader,
                reader=Entity(
                    Reader,
                    'id',
                    contact=Assign('contact'),
                    membership=Assign('membership'),
                ),
                contact=Value(Contact),
                membership=Value(Membership),
            )
            .one(id=id)
        )
        if reader is None:
            raise ReaderNotFound(id=id)
        return reader

    def save(self, reader: Reader) -> Reader:
        reader.check()
        if reader.id is None:
            reader.id = int(
                self._db.query_from('aggregates/readers/insert.sql').scalar(
                    full_name=reader.full_name,
                    email=reader.contact.email,
                    phone=reader.contact.phone,
                    tier=reader.membership.tier,
                    valid_until=reader.membership.valid_until,
                    is_blocked=reader.is_blocked,
                ),
            )
        else:
            row = (
                self._db.query_from('aggregates/readers/update.sql')
                .execute(
                    id=reader.id,
                    full_name=reader.full_name,
                    email=reader.contact.email,
                    phone=reader.contact.phone,
                    tier=reader.membership.tier,
                    valid_until=reader.membership.valid_until,
                    is_blocked=reader.is_blocked,
                )
                .fetchone()
            )
            if row is None:
                raise ReaderNotFound(id=reader.id)
        return reader

    def find(self, criteria: Criteria[Reader]) -> list[Reader]:
        readers: list[Reader] = (
            self._db.query_from('aggregates/readers/find.sql.tmpl')
            .map_to(
                Reader,
                reader=Entity(
                    Reader,
                    'id',
                    contact=Assign('contact'),
                    membership=Assign('membership'),
                ),
                contact=Value(Contact),
                membership=Value(Membership),
            )
            .all(criteria=criteria)
        )
        return readers
