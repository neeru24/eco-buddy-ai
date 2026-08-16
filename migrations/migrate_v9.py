"""Migration v9: persist background task retries and dead letters."""

import sqlite3


def migrate(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS background_task_jobs (
            task_id TEXT PRIMARY KEY,
            task_key TEXT NOT NULL,
            task_type TEXT NOT NULL,
            task_name TEXT NOT NULL,
            status TEXT NOT NULL
                CHECK (
                    status IN (
                        'pending',
                        'running',
                        'retry_scheduled',
                        'completed',
                        'failed',
                        'dead_letter'
                    )
                ),
            attempt_count INTEGER NOT NULL DEFAULT 0,
            max_attempts INTEGER NOT NULL DEFAULT 1,
            last_error TEXT,
            next_retry_at TEXT,
            idempotency_key TEXT,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
        idx_background_task_idempotency
        ON background_task_jobs(idempotency_key)
        WHERE idempotency_key IS NOT NULL
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_background_task_status_updated
        ON background_task_jobs(status, updated_at DESC)
        """
    )

    conn.commit()
