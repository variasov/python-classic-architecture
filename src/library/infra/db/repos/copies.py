from typing import Any

from classic.criteria import Criteria
from classic.db_tools import Assign, Engine, Entity, Value

from library.app.commands.domain.copy import (
    CopiesRepo,
    Copy,
    CopyNotFound,
    ShelfLocation,
)


class DbCopiesRepo(CopiesRepo):
    """Репозиторий экземпляров поверх PostgreSQL."""

    def __init__(self, db: Engine[Any]) -> None:
        self._db = db

    def get_by_id(self, id: int) -> Copy:
        copy: Copy | None = (
            self._db.query_from('aggregates/copies/get_by_id.sql')
            .map_to(
                Copy,
                Copy=Entity(Copy, 'id', shelf=Assign('shelf')),
                shelf=Value(ShelfLocation),
            )
            .one(id=id)
        )
        if copy is None:
            raise CopyNotFound(id=id)
        return copy

    def save(self, copy: Copy) -> Copy:
        copy.check()
        params = self._params(copy)
        if copy.id is None:
            copy.id = self._db.query_from('aggregates/copies/insert.sql').scalar(
                **params,
            )
        else:
            updated = self._db.query_from('aggregates/copies/update.sql').scalar(
                **params,
            )
            if updated is None:
                raise CopyNotFound(id=copy.id)
        return copy

    def find(self, criteria: Criteria[Copy]) -> list[Copy]:
        copies: list[Copy] = (
            self._db.query_from('aggregates/copies/find.sql.tmpl')
            .map_to(
                Copy,
                Copy=Entity(Copy, 'id', shelf=Assign('shelf')),
                shelf=Value(ShelfLocation),
            )
            .all(criteria=criteria)
        )
        return copies

    def _params(self, copy: Copy) -> dict[str, Any]:
        return {
            'id': copy.id,
            'book_id': copy.book_id,
            'inventory_number': copy.inventory_number,
            'is_available': copy.is_available,
            'shelf_hall': copy.shelf.hall,
            'shelf_rack': copy.shelf.rack,
            'shelf_shelf': copy.shelf.shelf,
        }
