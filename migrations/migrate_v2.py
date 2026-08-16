"""
Migration v2: Add trip_id column to assessments table.

This migration adds:
- trip_id TEXT column to assessments table (for deduplication)
- UNIQUE index on trip_id for efficient lookups

The trip_id column was previously added via ALTER TABLE with try/except,
which was inconsistent. This migration handles it cleanly.
"""

import sqlite3


def migrate(conn: sqlite3.Connection) -> None:
    """
    Apply migration v2: Add trip_id column to assessments.
    """
    cursor = conn.cursor()
    
    # Add trip_id column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE assessments ADD COLUMN trip_id TEXT")
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    # Create unique index on trip_id for NULL-safe uniqueness
    # SQLite handles this with WHERE clause in the index
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_assessments_trip_id 
        ON assessments(trip_id) 
        WHERE trip_id IS NOT NULL
    """)
    
    conn.commit()
