from pathlib import Path

from classic.db_tools import Engine

from demo.app.commands.domain.aggregates.cat import Cat, CatRepository

_QUERIES_DIR = (
    Path(__file__).parent.parent / 'sql' / 'queries'
)


class SqliteCatRepository(CatRepository):

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save(self, cat: Cat) -> None:
        with self._engine.transaction():
            self._engine.query_from(
                str(_QUERIES_DIR / 'insert_cat.sql'),
            ).execute(
                id=cat.id,
                name=cat.name,
                age=cat.age,
                mood=cat.mood,
            )
            for m in cat.movements:
                self._engine.query_from(
                    str(_QUERIES_DIR / 'insert_movement.sql'),
                ).execute(
                    cat_id=cat.id,
                    timestamp=m.timestamp,
                    latitude=m.latitude,
                    longitude=m.longitude,
                )
