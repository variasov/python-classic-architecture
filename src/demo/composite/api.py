import sqlite3
from pathlib import Path

from classic.db_tools import Engine
from waitress import serve

from demo.app.commands.create_cat import CreateCat
from demo.infrastructure.db.queries.find_cats import FindCatsImpl
from demo.infrastructure.db.queries.get_cat import GetCatImpl
from demo.infrastructure.db.repos.cat_repository import SqliteCatRepository
from demo.interfaces.api.cats_collection import CatsCollection
from demo.interfaces.api.get_cat import GetCatResource

DB_PATH = Path(__file__).parent.parent.parent.parent / 'demo.db'

_SCHEMA_PATH = (
    Path(__file__).parent.parent / 'infrastructure' / 'db' / 'sql' / 'schema' / '001_initial.sql'
)


def create_engine(db_path: str | None = None) -> Engine:
    target = db_path or str(DB_PATH)

    def factory() -> sqlite3.Connection:
        conn = sqlite3.connect(target)
        conn.execute('PRAGMA foreign_keys = ON')
        return conn

    queries_dir = Path(__file__).parent.parent / 'infrastructure' / 'db' / 'sql' / 'queries'

    return Engine(sqlite3, factory, templates_dirs=[str(queries_dir)])


def _init_schema(engine: Engine) -> None:
    ddl = _SCHEMA_PATH.read_text()
    for statement in ddl.split(';'):
        stmt = statement.strip()
        if stmt:
            engine.query(stmt).execute()


def create_app(db_path: str | None = None) -> 'falcon.App':
    import falcon

    engine = create_engine(db_path)
    _init_schema(engine)

    repository = SqliteCatRepository(engine)
    create_cat = CreateCat(repository)
    get_cat = GetCatImpl(engine)
    find_cats = FindCatsImpl(engine)

    app = falcon.App()

    app.add_route('/cats', CatsCollection(create_cat, find_cats))
    app.add_route('/cats/{cat_id}', GetCatResource(get_cat))

    return app


def main() -> None:
    app = create_app()
    serve(app, host='0.0.0.0', port=8080)


if __name__ == '__main__':
    main()
