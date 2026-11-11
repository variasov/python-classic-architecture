from typing import Any, cast

import psycopg
from classic.db_tools import Engine
from classic.db_tools.dbapi import Connection

from library.composites.infra.db.settings import db_settings
from library.infra.db.constants import SQL_DIR_PATH

Row = tuple[Any, ...]


def _connect() -> Connection[Row]:
    # psycopg возвращает Connection[TupleRow]; протокол classic-db-tools описывает
    # курсор без параметров row_factory, поэтому типы приводим явно.
    return cast(
        'Connection[Row]',
        psycopg.connect(conninfo=db_settings.DB_CONN_INFO),
    )


engine: Engine[Row] = Engine(
    psycopg,
    _connect,
    templates_dirs=[SQL_DIR_PATH],
)
