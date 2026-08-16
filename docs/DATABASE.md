# Database Connection Policy

EcoBuddy AI uses `database_connection.py` as the shared entry point for new
SQLite operations.

## Standard connection

```python
from database_connection import database_connection

with database_connection(DB_NAME) as connection:
    connection.execute(
        "INSERT INTO records (value) VALUES (?)",
        ("example",),
    )
```

The helper:

- enables `PRAGMA foreign_keys = ON`;
- sets a 5-second SQLite `busy_timeout`;
- attempts to enable WAL mode for file-backed databases;
- configures `sqlite3.Row` for named and positional column access;
- commits successful transactions;
- rolls back failed transactions;
- closes the connection in every case.

WAL setup is best-effort because in-memory databases, read-only filesystems,
and some storage providers may not support it.

## Lock retries

Use `execute_with_retry()` around a complete, idempotent database operation:

```python
from database_connection import execute_with_retry

def save_record():
    with database_connection(DB_NAME) as connection:
        connection.execute(...)

execute_with_retry(save_record)
```

Retries are limited to temporary SQLite lock messages:

- `database is locked`;
- `database table is locked`;
- `database schema is locked`.

Other failures, including invalid SQL, missing tables, and integrity
violations, are raised immediately.

The default retry schedule is:

```text
attempt 1: execute immediately
attempt 2: wait 0.05 seconds
attempt 3: wait 0.10 seconds
```

## Transaction guidance

Place all statements that must succeed together inside the same
`database_connection()` context.

Do not catch an exception inside the context when the transaction must roll
back. Let the exception leave the context and handle it outside.

## Migration scope

Issue #392 migrates a representative set of high-frequency and startup
operations:

- schema initialization;
- application migrations;
- user creation;
- user authentication;
- user lookup.

Remaining direct `sqlite3.connect()` calls can be migrated incrementally in
small, feature-focused pull requests.
