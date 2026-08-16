"""Migration v7: record which emission factor set produced each assessment."""

import sqlite3


def migrate(conn: sqlite3.Connection) -> None:
    """
    Add assessments.factor_version so a stored footprint can be reproduced.

    Existing rows stay NULL and are read as 'static-v1' by
    emission_factors.normalize_version(), which is exactly the factor set they
    were computed with, so no historical value changes meaning.
    """
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(assessments)")
    columns = {row[1] for row in cursor.fetchall()}

    if "factor_version" not in columns:
        cursor.execute("ALTER TABLE assessments ADD COLUMN factor_version TEXT")

    # Queries that ask "which versions are mixed into this user's history?"
    # scan by user and version, so index that pair.
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_assessments_factor_version
        ON assessments(user_id, factor_version)
        """
    )
    conn.commit()
