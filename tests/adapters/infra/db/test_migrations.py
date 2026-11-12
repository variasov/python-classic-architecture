import re
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from classic.migrations import MigrationsCollection, Migrator
from psycopg import sql

from library.infra.db.constants import MIGRATIONS_DIR_PATH
from library.infra.db.settings import DBSettings

CHECK_SCHEMA = 'library_migration_check'
CHECK_HISTORY_SCHEMA = 'library_migration_check_history'


def _drop_check_schemas(settings: DBSettings) -> None:
    with psycopg.connect(conninfo=settings.DB_CONN_INFO) as connection:
        with connection.cursor() as cursor:
            for schema in (CHECK_SCHEMA, CHECK_HISTORY_SCHEMA):
                cursor.execute(
                    sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(
                        sql.Identifier(schema),
                    ),
                )
        connection.commit()


@pytest.fixture
def check_migrations_dir(
    migrated_db: DBSettings,
    tmp_path: Path,
) -> Iterator[Path]:
    """Копия миграций, перенацеленная на отдельную схему тестовой БД.

    Миграции жёстко называют схему `library`, а в ней уже работают остальные
    тесты, поэтому цикл откатов выполняется на копии с другим именем схемы.
    """
    _drop_check_schemas(migrated_db)
    for source in MIGRATIONS_DIR_PATH.glob('*.sql'):
        text = source.read_text(encoding='utf-8')
        (tmp_path / source.name).write_text(
            re.sub(r'\blibrary\b', CHECK_SCHEMA, text),
            encoding='utf-8',
            newline='\n',
        )
    yield tmp_path
    _drop_check_schemas(migrated_db)


def _tables(settings: DBSettings) -> set[str]:
    with psycopg.connect(conninfo=settings.DB_CONN_INFO) as connection:
        rows = connection.execute(
            'SELECT table_name FROM information_schema.tables WHERE table_schema = %s',
            (CHECK_SCHEMA,),
        ).fetchall()
    return {row[0] for row in rows}


def test_every_migration_has_transactional_rollback() -> None:
    migrations = [
        path
        for path in MIGRATIONS_DIR_PATH.glob('*.sql')
        if not path.name.endswith('.rollback.sql')
    ]

    assert migrations
    for path in migrations:
        rollback = path.with_name(f'{path.stem}.rollback.sql')
        assert rollback.exists(), f'нет отката для {path.name}'
        first_line = rollback.read_text(encoding='utf-8').splitlines()[0]
        assert first_line == '-- transactional: true'


def test_apply_rollback_all_apply_again(
    migrated_db: DBSettings,
    check_migrations_dir: Path,
) -> None:
    collection = MigrationsCollection(sources=[str(check_migrations_dir)])
    with Migrator(
        driver='psycopg',
        db_host=migrated_db.DB_HOST,
        db_port=migrated_db.DB_PORT,
        db_name=migrated_db.DB_NAME,
        db_user=migrated_db.DB_USER,
        db_pass=migrated_db.DB_PASS,
        migration_schema=CHECK_HISTORY_SCHEMA,
    ) as migrator:
        hooks, migrations = collection.to_apply(migrator.history())
        migrator.apply(migrations, hooks)
        applied = _tables(migrated_db)
        assert 'notifications' in applied

        hooks, migrations = collection.to_rollback(migrator.history())
        migrator.rollback(migrations, hooks)
        assert _tables(migrated_db) == set()

        hooks, migrations = collection.to_apply(migrator.history())
        migrator.apply(migrations, hooks)
        assert _tables(migrated_db) == applied
