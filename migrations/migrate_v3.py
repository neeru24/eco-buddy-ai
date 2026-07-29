"""
Migration v3: Add water_consumption table if missing.

This migration ensures the water_consumption table exists.
It's idempotent (uses IF NOT EXISTS) so it can be re-run safely.
"""

import sqlite3


def migrate(conn):
    """
    Apply migration v3: Create water_consumption table.
    """
    cursor = conn.cursor()
    
    # Create water_consumption table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_consumption (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            shower_mins_per_day REAL,
            laundry_loads_per_week REAL,
            dishwasher_runs_per_week REAL,
            garden_mins_per_week REAL,
            diet TEXT,
            total_liters REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
