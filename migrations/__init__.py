"""
Database migrations for EcoBuddy AI.

Migration files are named sequentially: migrate_v{version}.py
Each migration file must contain a migrate(conn) function that applies
schema changes and sets the database version.
"""

import importlib
import os
import sqlite3


def get_db_name():
    """Get the current database name (read at runtime to support test DB switching)."""
    import database
    return database.DB_NAME


def get_current_version(conn):
    """Get the current database schema version using PRAGMA user_version."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA user_version")
    return cursor.fetchone()[0]


def set_version(conn, version):
    """Set the database schema version using PRAGMA user_version."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA user_version = {version}")
    conn.commit()


CURRENT_VERSION = 3


def migrate():
    """
    Apply all pending database migrations.
    
    This function is called on application startup to ensure the database
    schema is up to date. It reads the current version from the database
    and applies any migrations with higher versions.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        db_name = get_db_name()
        conn = sqlite3.connect(db_name)
        current_version = get_current_version(conn)
        
        if current_version >= CURRENT_VERSION:
            conn.close()
            return True, f"Database is already at version {current_version}"
        
        # Apply migrations sequentially
        migrations_to_apply = range(current_version + 1, CURRENT_VERSION + 1)
        for version in migrations_to_apply:
            migration_file = f"migrations/migrate_v{version}.py"
            if os.path.exists(migration_file):
                module = importlib.import_module(f"migrations.migrate_v{version}")
                if hasattr(module, 'migrate'):
                    module.migrate(conn)
                    set_version(conn, version)
                    print(f"Applied migration v{version}")
        
        conn.close()
        return True, f"Database migrated to version {CURRENT_VERSION}"
        
    except Exception as e:
        return False, f"Migration failed: {str(e)}"
