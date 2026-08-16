"""
Database migrations for EcoBuddy AI.

Migration files are named sequentially: migrate_v{version}.py
Each migration file must contain a migrate(conn) function that applies
schema changes and sets the database version.
"""

import importlib
import os
import sqlite3
from database_connection import database_connection


def get_db_name() -> str:
    """Get the current database name (read at runtime to support test DB switching)."""
    import database
    return database.DB_NAME


def get_current_version(conn: sqlite3.Connection) -> int:
    """Get the current database schema version using PRAGMA user_version."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA user_version")
    return cursor.fetchone()[0]


def set_version(conn: sqlite3.Connection, version: int) -> None:
    """Set the database schema version using PRAGMA user_version."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA user_version = {version}")
    conn.commit()


CURRENT_VERSION = 9


def migrate() -> tuple[bool, str]:
    """Apply all pending database migrations."""
    try:
        db_name = get_db_name()

        with database_connection(db_name) as conn:
            current_version = get_current_version(conn)

            if current_version >= CURRENT_VERSION:
                return True, (
                    f"Database is already at version {current_version}"
                )

            migrations_to_apply = range(
                current_version + 1,
                CURRENT_VERSION + 1,
            )
            for version in migrations_to_apply:
                migration_file = f"migrations/migrate_v{version}.py"
                if os.path.exists(migration_file):
                    module = importlib.import_module(
                        f"migrations.migrate_v{version}"
                    )
                    if hasattr(module, "migrate"):
                        module.migrate(conn)
                        set_version(conn, version)
                        print(f"Applied migration v{version}")

        return True, f"Database migrated to version {CURRENT_VERSION}"
    except Exception as exc:
        return False, f"Migration failed: {exc}"
