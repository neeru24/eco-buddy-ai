"""Migration v5: add environmental impact milestones."""

import sqlite3

def migrate(conn: sqlite3.Connection) -> None:
    """Create the extensible per-user environmental milestone table."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS environmental_milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            milestone_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            icon TEXT NOT NULL DEFAULT '🌱',
            achieved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            UNIQUE(user_id, milestone_type)
        )
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_environmental_milestones_user_date
        ON environmental_milestones(user_id, achieved_at DESC)
        """
    )
    conn.commit()
