from pathlib import Path

from classic.db_tools import Engine

from demo.app.queries.get_cat import CatDTO, GetCat
from demo.infrastructure.db.sql.mapper import build_movement

_QUERIES_DIR = (
    Path(__file__).parent.parent / 'sql' / 'queries'
)


class GetCatImpl(GetCat):

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def run(self, cat_id: str) -> CatDTO | None:
        row = self._engine.query_from(
            str(_QUERIES_DIR / 'get_cat.sql'),
        ).one(id=cat_id)
        if row is None:
            return None
        movements = self._get_movements(cat_id)
        return CatDTO(
            id=row[0],
            name=row[1],
            age=row[2],
            mood=row[3],
            movements=movements,
        )

    def _get_movements(self, cat_id: str) -> list:
        rows = self._engine.query_from(
            str(_QUERIES_DIR / 'get_movements.sql'),
        ).all(cat_id=cat_id)
        return [build_movement(row) for row in rows]
