from typing import Any

from classic.criteria import Criteria
from classic.db_tools import Assign, Engine, Entity, Value

from library.app.domain.reader import (
    Contact,
    Membership,
    Reader,
    ReaderNotFound,
    ReadersRepo,
)


class DbReadersRepo(ReadersRepo):
    """Репозиторий читателей поверх PostgreSQL."""

    def __init__(self, db: Engine[Any]) -> None:
        self._db = db

    def get_by_id(self, id: int) -> Reader:
        reader: Reader | None = (
            self._db.query_from('aggregates/readers/get_by_id.sql')
            .map_to(
                Reader,
                Reader=Entity(
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
        params = self._params(reader)
        if reader.id is None:
            reader.id = self._db.query_from('aggregates/readers/insert.sql').scalar(
                **params,
            )
        else:
            updated = self._db.query_from('aggregates/readers/update.sql').scalar(
                **params,
            )
            if updated is None:
                raise ReaderNotFound(id=reader.id)
        return reader

    def find(self, criteria: Criteria[Reader]) -> list[Reader]:
        readers: list[Reader] = (
            self._db.query_from('aggregates/readers/find.sql.tmpl')
            .map_to(
                Reader,
                Reader=Entity(
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

    def _params(self, reader: Reader) -> dict[str, Any]:
        return {
            'id': reader.id,
            'full_name': reader.full_name,
            'is_blocked': reader.is_blocked,
            'contact_email': reader.contact.email,
            'contact_phone': reader.contact.phone,
            'membership_tier': reader.membership.tier,
            'membership_valid_until': reader.membership.valid_until,
        }
