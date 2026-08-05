from pathlib import Path

from classic.db_tools import Engine

from demo.app.commands.domain.aggregates.cat import Movement
from demo.app.queries.find_cats import CatDTO, FindCats
from demo.infrastructure.db.sql.mapper import build_movement

_QUERIES_DIR = (
    Path(__file__).parent.parent / 'sql' / 'queries'
)


class FindCatsImpl(FindCats):

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def run(self, age_from: int, age_to: int) -> list[CatDTO]:
        rows = self._engine.query_from(
            str(_QUERIES_DIR / 'find_cats.sql'),
        ).all(age_from=age_from, age_to=age_to)
        if not rows:
            return []
        cat_ids = [row[0] for row in rows]
        movements_map = self._get_movements_bulk(cat_ids)
        return [
            CatDTO(
                id=row[0],
                name=row[1],
                age=row[2],
                mood=row[3],
                movements=movements_map.get(row[0], []),
            )
            for row in rows
        ]

    def _get_movements_bulk(self, cat_ids: list[str]):
        placeholders = ','.join(['?'] * len(cat_ids))
        sql = (
            'SELECT cat_id, timestamp, latitude, longitude '
            'FROM movements '
            f'WHERE cat_id IN ({placeholders}) '
            'ORDER BY cat_id, timestamp'
        )
        rows = self._engine.query(sql, static=True).all(tuple(cat_ids))

        result: dict[str, list[Movement]] = {}
        for row in rows:
            cat_id = row[0]
            if cat_id not in result:
                result[cat_id] = []
            result[cat_id].append(build_movement(row[1:]))
        return result
