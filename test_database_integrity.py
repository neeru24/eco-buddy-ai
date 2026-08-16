"""Tests for the database schema and migration integrity checker."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from database_integrity import (
    EXPECTED_INDEXES,
    EXPECTED_TABLES,
    discover_migrations,
    inspect_connection,
    inspect_database,
)
from migrations import CURRENT_VERSION
from scripts.check_database import main


def create_expected_database(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")

    for table_name, columns in EXPECTED_TABLES.items():
        definitions = []
        for position, (column_name, column_type) in enumerate(
            columns.items()
        ):
            suffix = ""
            if position == 0:
                if column_name == "id":
                    suffix = " PRIMARY KEY"
                elif column_name == "user_id" and table_name in {
                    "assessment_drafts",
                    "dashboard_widget_preferences",
                    "freeze_token_balances",
                    "user_eco_balance",
                }:
                    suffix = " PRIMARY KEY"

            definitions.append(
                f'"{column_name}" {column_type}{suffix}'
            )

        if table_name == "dashboard_widget_preferences":
            definitions.append(
                "FOREIGN KEY (user_id) REFERENCES users(id)"
            )
        if table_name == "credit_trades":
            definitions.append(
                "FOREIGN KEY (credit_id) REFERENCES carbon_credits(id)"
            )

        connection.execute(
            f'CREATE TABLE "{table_name}" ({", ".join(definitions)})'
        )

    for index_name, (table_name, columns) in EXPECTED_INDEXES.items():
        quoted_columns = ", ".join(
            f'"{column}"' for column in columns
        )
        connection.execute(
            f'CREATE INDEX "{index_name}" '
            f'ON "{table_name}" ({quoted_columns})'
        )

    connection.execute(f"PRAGMA user_version = {CURRENT_VERSION}")
    connection.commit()
    return connection


@pytest.fixture
def migration_directory(tmp_path):
    directory = tmp_path / "migrations"
    directory.mkdir()
    for version in range(1, CURRENT_VERSION + 1):
        (directory / f"migrate_v{version}.py").write_text(
            "def migrate(conn):\n    pass\n",
            encoding="utf-8",
        )
    return directory


def test_valid_database_passes(tmp_path, migration_directory):
    database_path = tmp_path / "valid.db"
    connection = create_expected_database(database_path)

    report = inspect_connection(
        connection,
        database_path=str(database_path),
        migration_directory=migration_directory,
    )
    connection.close()

    assert report.is_valid
    assert report.errors == []
    assert report.actual_version == CURRENT_VERSION
    assert report.integrity_check == "ok"
    assert report.foreign_key_violations == 0


def test_missing_table_is_reported(tmp_path, migration_directory):
    database_path = tmp_path / "missing-table.db"
    connection = create_expected_database(database_path)
    connection.execute("DROP TABLE environmental_milestones")
    connection.commit()

    report = inspect_connection(
        connection,
        migration_directory=migration_directory,
    )
    connection.close()

    assert "Missing table: environmental_milestones" in report.errors


def test_missing_column_is_reported(tmp_path, migration_directory):
    database_path = tmp_path / "missing-column.db"
    connection = create_expected_database(database_path)
    connection.execute("ALTER TABLE users RENAME TO users_original")
    connection.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            email TEXT,
            password_hash TEXT,
            created_at TIMESTAMP
        )
        """
    )
    connection.commit()

    report = inspect_connection(
        connection,
        migration_directory=migration_directory,
    )
    connection.close()

    assert (
        "Missing column: users.anonymous_leaderboard"
        in report.errors
    )


def test_column_type_mismatch_is_reported(
    tmp_path,
    migration_directory,
):
    database_path = tmp_path / "wrong-type.db"
    connection = create_expected_database(database_path)
    connection.execute("ALTER TABLE market_state RENAME TO old_market_state")
    connection.execute(
        """
        CREATE TABLE market_state (
            id INTEGER PRIMARY KEY,
            price_per_tonne TEXT,
            volatility REAL,
            total_supply REAL,
            total_demand REAL,
            trading_volume REAL,
            updated_at TIMESTAMP
        )
        """
    )
    connection.commit()

    report = inspect_connection(
        connection,
        migration_directory=migration_directory,
    )
    connection.close()

    assert any(
        error.startswith(
            "Column type mismatch: market_state.price_per_tonne"
        )
        for error in report.errors
    )


def test_missing_index_is_reported(tmp_path, migration_directory):
    database_path = tmp_path / "missing-index.db"
    connection = create_expected_database(database_path)
    connection.execute("DROP INDEX idx_assessments_factor_version")
    connection.commit()

    report = inspect_connection(
        connection,
        migration_directory=migration_directory,
    )
    connection.close()

    assert (
        "Missing index: idx_assessments_factor_version"
        in report.errors
    )


def test_outdated_schema_version_is_reported(
    tmp_path,
    migration_directory,
):
    database_path = tmp_path / "old-version.db"
    connection = create_expected_database(database_path)
    connection.execute(
        f"PRAGMA user_version = {CURRENT_VERSION - 1}"
    )

    report = inspect_connection(
        connection,
        migration_directory=migration_directory,
    )
    connection.close()

    assert any(
        error.startswith("Schema version mismatch:")
        for error in report.errors
    )


def test_foreign_key_violation_is_reported(
    tmp_path,
    migration_directory,
):
    database_path = tmp_path / "foreign-key.db"
    connection = create_expected_database(database_path)
    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute(
        """
        INSERT INTO dashboard_widget_preferences (
            user_id,
            widgets_json
        )
        VALUES (999, '[]')
        """
    )
    connection.commit()

    report = inspect_connection(
        connection,
        migration_directory=migration_directory,
    )
    connection.close()

    assert report.foreign_key_violations == 1
    assert any(
        error.startswith("Foreign-key violation:")
        for error in report.errors
    )


def test_migration_gap_is_reported(tmp_path):
    directory = tmp_path / "migrations"
    directory.mkdir()
    (directory / "migrate_v1.py").write_text("", encoding="utf-8")
    (directory / "migrate_v3.py").write_text("", encoding="utf-8")

    inventory = discover_migrations(
        directory,
        expected_version=3,
    )

    assert inventory.versions == (1, 3)
    assert inventory.missing_versions == (2,)


def test_duplicate_migration_version_is_reported(tmp_path):
    directory = tmp_path / "migrations"
    directory.mkdir()
    (directory / "migrate_v1.py").write_text("", encoding="utf-8")
    (directory / "migrate_v1_retry.py").write_text(
        "",
        encoding="utf-8",
    )

    inventory = discover_migrations(
        directory,
        expected_version=1,
    )

    assert inventory.duplicate_versions == (1,)


def test_future_migration_is_reported(tmp_path):
    directory = tmp_path / "migrations"
    directory.mkdir()
    for version in (1, 2, 3):
        (directory / f"migrate_v{version}.py").write_text(
            "",
            encoding="utf-8",
        )

    inventory = discover_migrations(
        directory,
        expected_version=2,
    )

    assert inventory.unexpected_future_versions == (3,)


def test_read_only_inspection_does_not_modify_database(
    tmp_path,
    migration_directory,
):
    database_path = tmp_path / "read-only.db"
    connection = create_expected_database(database_path)
    connection.close()
    before = database_path.read_bytes()

    report = inspect_database(
        database_path,
        migration_directory=migration_directory,
    )

    after = database_path.read_bytes()
    assert report.is_valid
    assert after == before


def test_cli_returns_zero_for_valid_database(
    tmp_path,
    migration_directory,
    capsys,
):
    database_path = tmp_path / "cli-valid.db"
    connection = create_expected_database(database_path)
    connection.close()

    exit_code = main(
        [
            str(database_path),
            "--migrations",
            str(migration_directory),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Database integrity check passed" in output


def test_cli_returns_one_for_invalid_database(
    tmp_path,
    migration_directory,
    capsys,
):
    database_path = tmp_path / "cli-invalid.db"
    connection = create_expected_database(database_path)
    connection.execute("DROP INDEX idx_time_capsules_user")
    connection.commit()
    connection.close()

    exit_code = main(
        [
            str(database_path),
            "--migrations",
            str(migration_directory),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Database integrity check failed" in output
    assert "Missing index: idx_time_capsules_user" in output


def test_cli_returns_two_when_database_does_not_exist(
    tmp_path,
    migration_directory,
    capsys,
):
    exit_code = main(
        [
            str(tmp_path / "missing.db"),
            "--migrations",
            str(migration_directory),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 2
    assert "could not run" in output
