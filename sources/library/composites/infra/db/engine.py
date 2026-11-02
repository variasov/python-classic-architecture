import psycopg
from classic.db_tools import Engine
from library.composites.infra.db.settings import db_settings
from library.infra.db.constants import SQL_DIR_PATH

engine = Engine(
    psycopg,
    lambda: psycopg.connect(conninfo=db_settings.DB_CONN_INFO),
    templates_dirs=[SQL_DIR_PATH],
)
