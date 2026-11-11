from pathlib import Path

SQL_DIR_PATH = Path(__file__).parent / 'sql'
MIGRATIONS_DIR_PATH = SQL_DIR_PATH / 'migrations'
SCHEMA_DDL_PATH = SQL_DIR_PATH / 'schema' / 'DDL.sql'
