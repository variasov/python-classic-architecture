from collections.abc import Callable
from typing import Any, cast

import psycopg
from classic.db_tools import Engine
from classic.db_tools.dbapi import Connection

from library.composites.infra.db.settings import settings
from library.infra.db.constants import SQL_DIR_PATH

_factory = cast(
    Callable[[], Connection[Any]],
    lambda: psycopg.connect(conninfo=settings.DB_CONN_INFO),
)

engine: Engine[Any] = Engine(
    psycopg,
    _factory,
    templates_dirs=[SQL_DIR_PATH],
)
