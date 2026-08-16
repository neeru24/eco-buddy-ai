"""Tests for centralized SQLite connection and retry behavior."""

from __future__ import annotations

import sqlite3

import pytest

from database_connection import (
    create_connection,
    database_connection,
    execute_with_retry,
    is_transient_lock_error,
)


def test_connection_applies_expected_pragmas(tmp_path):
    database_path = tmp_path / "configured.db"

    with database_connection(str(database_path)) as connection:
        foreign_keys = connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]
        busy_timeout = connection.execute(
            "PRAGMA busy_timeout"
        ).fetchone()[0]
        journal_mode = connection.execute(
            "PRAGMA journal_mode"
        ).fetchone()[0]

    assert foreign_keys == 1
    assert busy_timeout == 5_000
    assert str(journal_mode).lower() == "wal"


def test_context_manager_commits_successful_transaction(tmp_path):
    database_path = tmp_path / "commit.db"

    with database_connection(str(database_path)) as connection:
        connection.execute(
            "CREATE TABLE records (id INTEGER PRIMARY KEY, value TEXT)"
        )
        connection.execute(
            "INSERT INTO records (value) VALUES (?)",
            ("saved",),
        )

    with sqlite3.connect(database_path) as verification:
        row = verification.execute(
            "SELECT value FROM records"
        ).fetchone()

    assert row == ("saved",)


def test_context_manager_rolls_back_failed_transaction(tmp_path):
    database_path = tmp_path / "rollback.db"

    with database_connection(str(database_path)) as connection:
        connection.execute(
            "CREATE TABLE records (id INTEGER PRIMARY KEY, value TEXT)"
        )

    with pytest.raises(RuntimeError, match="stop transaction"):
        with database_connection(str(database_path)) as connection:
            connection.execute(
                "INSERT INTO records (value) VALUES (?)",
                ("must-roll-back",),
            )
            raise RuntimeError("stop transaction")

    with sqlite3.connect(database_path) as verification:
        count = verification.execute(
            "SELECT COUNT(*) FROM records"
        ).fetchone()[0]

    assert count == 0


def test_connection_closes_after_success(tmp_path):
    database_path = tmp_path / "closed-success.db"
    captured = None

    with database_connection(str(database_path)) as connection:
        captured = connection
        connection.execute("SELECT 1")

    with pytest.raises(sqlite3.ProgrammingError):
        captured.execute("SELECT 1")


def test_connection_closes_after_failure(tmp_path):
    database_path = tmp_path / "closed-failure.db"
    captured = None

    with pytest.raises(ValueError):
        with database_connection(str(database_path)) as connection:
            captured = connection
            raise ValueError("boom")

    with pytest.raises(sqlite3.ProgrammingError):
        captured.execute("SELECT 1")


@pytest.mark.parametrize(
    "message",
    [
        "database is locked",
        "database table is locked",
        "database schema is locked: main",
    ],
)
def test_transient_lock_detection(message):
    assert is_transient_lock_error(
        sqlite3.OperationalError(message)
    )


def test_temporary_lock_is_retried_with_exponential_backoff():
    attempts = 0
    delays = []

    def operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise sqlite3.OperationalError("database is locked")
        return "completed"

    result = execute_with_retry(
        operation,
        max_attempts=4,
        base_delay=0.1,
        sleep_fn=delays.append,
    )

    assert result == "completed"
    assert attempts == 3
    assert delays == [0.1, 0.2]


def test_retry_stops_after_maximum_attempts():
    attempts = 0
    delays = []

    def operation():
        nonlocal attempts
        attempts += 1
        raise sqlite3.OperationalError("database table is locked")

    with pytest.raises(
        sqlite3.OperationalError,
        match="database table is locked",
    ):
        execute_with_retry(
            operation,
            max_attempts=3,
            base_delay=0.05,
            sleep_fn=delays.append,
        )

    assert attempts == 3
    assert delays == [0.05, 0.1]


def test_permanent_operational_error_is_not_retried():
    attempts = 0
    delays = []

    def operation():
        nonlocal attempts
        attempts += 1
        raise sqlite3.OperationalError("no such table: missing")

    with pytest.raises(
        sqlite3.OperationalError,
        match="no such table",
    ):
        execute_with_retry(
            operation,
            max_attempts=5,
            sleep_fn=delays.append,
        )

    assert attempts == 1
    assert delays == []


def test_integrity_error_is_not_retried():
    attempts = 0

    def operation():
        nonlocal attempts
        attempts += 1
        raise sqlite3.IntegrityError("UNIQUE constraint failed")

    with pytest.raises(sqlite3.IntegrityError):
        execute_with_retry(operation, max_attempts=5)

    assert attempts == 1


def test_create_connection_closes_when_configuration_fails(
    monkeypatch,
):
    class FakeConnection:
        def __init__(self):
            self.closed = False
            self.row_factory = None

        def execute(self, statement):
            raise sqlite3.OperationalError("configuration failed")

        def close(self):
            self.closed = True

    fake = FakeConnection()
    monkeypatch.setattr(
        sqlite3,
        "connect",
        lambda *args, **kwargs: fake,
    )

    with pytest.raises(
        sqlite3.OperationalError,
        match="configuration failed",
    ):
        create_connection("broken.db")

    assert fake.closed is True
