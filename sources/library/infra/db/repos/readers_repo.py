from datetime import date
from typing import Any, cast

from classic.criteria import Criteria
from classic.db_tools import Engine, Entity
from library.app.commands.domain.reader import (
    Contact,
    Membership,
    Reader,
    ReaderNotFound,
    ReadersRepo,
)


def _make_reader(  # noqa: PLR0913 - фабрика маппера, поля задаёт запрос
    *,
    id: int,
    full_name: str,
    is_blocked: bool,
    email: str,
    phone: str | None,
    tier: str,
    valid_until: date,
) -> Reader:
    return Reader(
        id=id,
        full_name=full_name,
        contact=Contact(email=email, phone=phone),
        membership=Membership(tier=tier, valid_until=valid_until),
        is_blocked=is_blocked,
    )


class DbReadersRepo(ReadersRepo):
    def __init__(self, engine: Engine) -> None:
        self._db = engine

    def get_by_id(self, id: int) -> Reader:
        reader = cast(
            'Reader | None',
            self._db.query_from('aggregates/readers/get_by_id.sql')
            .map_to(
                Reader,
                # Фабрика вызывается с именованными аргументами, а типы библиотеки
                # допускают только класс или Callable[[Any], Any]
                Reader=Entity(cast('Any', _make_reader), 'id'),
            )
            .one(id=id),
        )
        if reader is None:
            raise ReaderNotFound(id=id)
        return reader

    def save(self, reader: Reader) -> Reader:
        reader.check()
        params: dict[str, Any] = {
            'full_name': reader.full_name,
            'email': reader.contact.email,
            'phone': reader.contact.phone,
            'tier': reader.membership.tier,
            'valid_until': reader.membership.valid_until,
            'is_blocked': reader.is_blocked,
        }
        if reader.id is None:
            reader.id = self._db.query_from('aggregates/readers/insert.sql').scalar(
                params,
            )
        else:
            updated_id = self._db.query_from('aggregates/readers/update.sql').scalar(
                {'id': reader.id, **params},
            )
            if updated_id is None:
                raise ReaderNotFound(id=reader.id)
        return reader

    def find(self, criteria: Criteria[Reader]) -> list[Reader]:
        ids = self._db.query_from('aggregates/readers/find_ids.sql.tmpl').scalars(
            criteria=criteria,
        )
        return [self.get_by_id(reader_id) for reader_id in ids]
