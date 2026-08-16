"""Read-only SQLite schema and migration integrity checks for EcoBuddy AI."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
import sqlite3
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from migrations import CURRENT_VERSION


MIGRATION_FILE_PATTERN = re.compile(
    r"^migrate_v(?P<version>\d+)(?:_[A-Za-z0-9_-]+)?\.py$"
)


# This declarative schema contains the tables, columns, and indexes required by
# the current application and migrations. Extra tables, columns, and indexes
# are allowed so feature modules can extend the database independently.
EXPECTED_TABLES: Mapping[str, Mapping[str, str]] = {
    "users": {
        "id": "INTEGER",
        "username": "TEXT",
        "email": "TEXT",
        "password_hash": "TEXT",
        "anonymous_leaderboard": "INTEGER",
        "created_at": "TIMESTAMP",
    },
    "assessments": {
        "id": "INTEGER",
        "user_id": "INTEGER",
        "date": "TIMESTAMP",
        "created_at": "TIMESTAMP",
        "transport": "TEXT",
        "distance": "REAL",
        "electricity": "REAL",
        "diet": "TEXT",
        "flights": "INTEGER",
        "footprint": "REAL",
        "eco_score": "INTEGER",
        "trip_id": "TEXT",
        "factor_version": "TEXT",
    },
    "assessment_drafts": {
        "user_id": "INTEGER",
        "transport": "TEXT",
        "distance": "REAL",
        "electricity": "REAL",
        "diet": "TEXT",
        "flights": "INTEGER",
        "region": "TEXT",
        "updated_at": "TIMESTAMP",
    },
    "appliances": {
        "id": "INTEGER",
        "user_id": "INTEGER",
        "name": "TEXT",
        "category": "TEXT",
        "quantity": "INTEGER",
        "power_rating_watts": "REAL",
        "hours_used_per_day": "REAL",
        "standby_draw_watts": "REAL",
        "usage_schedule": "TEXT",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
    },
    "solar_configs": {
        "id": "INTEGER",
        "user_id": "INTEGER",
        "roof_space_m2": "REAL",
        "peak_sun_hours": "REAL",
        "utility_rate_per_kwh": "REAL",
        "panel_efficiency": "REAL",
        "installation_cost_per_kw": "REAL",
        "maintenance_cost_per_year": "REAL",
        "annual_rate_increase": "REAL",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
    },
    "user_challenges": {
        "id": "INTEGER",
        "user_id": "INTEGER",
        "challenge_id": "TEXT",
        "progress_value": "REAL",
        "status": "TEXT",
        "enrolled_at": "TIMESTAMP",
        "completed_at": "TIMESTAMP",
        "xp_awarded": "BOOLEAN",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
    },
    "unlocked_badges": {
        "id": "INTEGER",
        "user_id": "INTEGER",
        "badge_id": "TEXT",
        "unlocked_at": "TIMESTAMP",
        "xp_awarded": "BOOLEAN",
        "created_at": "TIMESTAMP",
    },
    "xp_transactions": {
        "id": "INTEGER",
        "user_id": "INTEGER",
        "source_type": "TEXT",
        "source_id": "TEXT",
        "xp_amount": "INTEGER",
        "description": "TEXT",
        "created_at": "TIMESTAMP",
    },
    "skill_tree_progress": {
        "id": "INTEGER",
        "user_id": "INTEGER",
        "node_id": "TEXT",
        "status": "TEXT",
        "completed_at": "TIMESTAMP",
        "created_at": "TIMESTAMP",
    },
    "journey_profiles": {
        "id": "INTEGER",
        "user_id": "INTEGER",
        "name": "TEXT",
        "distance_km": "REAL",
        "transport_mode": "TEXT",
        "passenger_count": "INTEGER",
        "trips_per_week": "INTEGER",
        "is_commute": "BOOLEAN",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
    },
    "offset_transactions": {
        "id": "INTEGER",
        "user_id": "INTEGER",
        "project_id": "TEXT",
        "project_name": "TEXT",
        "offset_tonnes": "REAL",
        "cost_per_tonne": "REAL",
        "total_cost": "REAL",
        "transaction_status": "TEXT",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
    },
    "water_consumption": {
        "id": "INTEGER",
        "user_id": "INTEGER",
        "shower_mins_per_day": "REAL",
        "laundry_loads_per_week": "REAL",
        "dishwasher_runs_per_week": "REAL",
        "garden_mins_per_week": "REAL",
        "diet": "TEXT",
        "total_liters": "REAL",
        "created_at": "TIMESTAMP",
    },
    "dashboard_widget_preferences": {
        "user_id": "INTEGER",
        "widgets_json": "TEXT",
        "updated_at": "TIMESTAMP",
    },
    "environmental_milestones": {
        "id": "INTEGER",
        "user_id": "INTEGER",
        "milestone_type": "TEXT",
        "title": "TEXT",
        "description": "TEXT",
        "icon": "TEXT",
        "achieved_at": "TIMESTAMP",
        "metadata_json": "TEXT",
    },
    "freeze_token_balances": {
        "user_id": "INTEGER",
        "balance": "INTEGER",
        "total_earned": "INTEGER",
        "total_used": "INTEGER",
    },
    "freeze_token_transactions": {
        "id": "INTEGER",
        "user_id": "INTEGER",
        "amount": "INTEGER",
        "reason": "TEXT",
        "created_at": "TIMESTAMP",
    },
    "streak_freezes": {
        "id": "INTEGER",
        "user_id": "INTEGER",
        "frozen_date": "TEXT",
        "created_at": "TIMESTAMP",
    },
    "time_capsules": {
        "id": "INTEGER",
        "user_id": "INTEGER",
        "title": "TEXT",
        "promise_text": "TEXT",
        "category": "TEXT",
        "unlock_date": "TEXT",
        "is_unlocked": "INTEGER",
        "unlocked_at": "TIMESTAMP",
        "progress_notes": "TEXT",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
    },
    "carbon_credits": {
        "id": "INTEGER",
        "user_id": "INTEGER",
        "serial_no": "TEXT",
        "project_id": "TEXT",
        "project_name": "TEXT",
        "vintage_year": "INTEGER",
        "quantity": "REAL",
        "status": "TEXT",
        "source": "TEXT",
        "issued_at": "TIMESTAMP",
        "retired_at": "TIMESTAMP",
        "retired_for": "TEXT",
    },
    "credit_trades": {
        "id": "INTEGER",
        "credit_id": "INTEGER",
        "seller_id": "INTEGER",
        "buyer_id": "INTEGER",
        "quantity": "REAL",
        "price_per_tonne": "REAL",
        "total_value": "REAL",
        "status": "TEXT",
        "created_at": "TIMESTAMP",
    },
    "market_state": {
        "id": "INTEGER",
        "price_per_tonne": "REAL",
        "volatility": "REAL",
        "total_supply": "REAL",
        "total_demand": "REAL",
        "trading_volume": "REAL",
        "updated_at": "TIMESTAMP",
    },
    "user_eco_balance": {
        "user_id": "INTEGER",
        "balance": "REAL",
        "lifetime_earned": "REAL",
        "lifetime_spent": "REAL",
        "updated_at": "TIMESTAMP",
    },
}

EXPECTED_INDEXES: Mapping[str, tuple[str, tuple[str, ...]]] = {
    "idx_assessments_trip_id": (
        "assessments",
        ("trip_id",),
    ),
    "idx_xp_user": (
        "xp_transactions",
        ("user_id",),
    ),
    "idx_environmental_milestones_user_date": (
        "environmental_milestones",
        ("user_id", "achieved_at"),
    ),
    "idx_streak_freezes_user_date": (
        "streak_freezes",
        ("user_id", "frozen_date"),
    ),
    "idx_assessments_factor_version": (
        "assessments",
        ("user_id", "factor_version"),
    ),
    "idx_time_capsules_user": (
        "time_capsules",
        ("user_id", "unlock_date"),
    ),
    "idx_credits_user": (
        "carbon_credits",
        ("user_id", "status"),
    ),
    "idx_trades_seller": (
        "credit_trades",
        ("seller_id",),
    ),
    "idx_trades_buyer": (
        "credit_trades",
        ("buyer_id",),
    ),
}


@dataclass(frozen=True)
class MigrationInventory:
    """Versions discovered in the migration directory."""

    versions: tuple[int, ...]
    duplicate_versions: tuple[int, ...]
    missing_versions: tuple[int, ...]
    unexpected_future_versions: tuple[int, ...]


@dataclass
class IntegrityReport:
    """Complete, human-readable database validation result."""

    database_path: str
    expected_version: int
    actual_version: int | None = None
    integrity_check: str | None = None
    foreign_key_violations: int = 0
    tables_checked: int = 0
    indexes_checked: int = 0
    migration_inventory: MigrationInventory | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def render(self) -> str:
        heading = (
            "Database integrity check passed"
            if self.is_valid
            else "Database integrity check failed"
        )
        lines = [
            heading,
            f"Database: {self.database_path}",
            (
                f"Schema version: {self.actual_version}"
                f" (expected {self.expected_version})"
            ),
            f"Tables checked: {self.tables_checked}",
            f"Indexes checked: {self.indexes_checked}",
            f"Foreign-key violations: {self.foreign_key_violations}",
        ]

        if self.integrity_check is not None:
            lines.append(f"SQLite integrity check: {self.integrity_check}")

        if self.migration_inventory is not None:
            versions = ", ".join(
                str(version)
                for version in self.migration_inventory.versions
            )
            lines.append(f"Migration files: {versions or 'none'}")

        for warning in self.warnings:
            lines.append(f"Warning: {warning}")
        for error in self.errors:
            lines.append(f"- {error}")

        return "\n".join(lines)


def _quote_identifier(identifier: str) -> str:
    """Quote a trusted SQLite identifier."""
    return '"' + identifier.replace('"', '""') + '"'


def _normalise_type(value: object) -> str:
    return str(value or "").strip().upper()


def discover_migrations(
    migration_directory: str | Path,
    expected_version: int = CURRENT_VERSION,
) -> MigrationInventory:
    """Inspect migration filenames for duplicates, gaps, and future versions."""
    directory = Path(migration_directory)
    version_counts: dict[int, int] = {}

    if directory.exists():
        for path in directory.iterdir():
            if not path.is_file():
                continue
            match = MIGRATION_FILE_PATTERN.fullmatch(path.name)
            if not match:
                continue
            version = int(match.group("version"))
            version_counts[version] = version_counts.get(version, 0) + 1

    versions = tuple(sorted(version_counts))
    duplicate_versions = tuple(
        version
        for version, count in sorted(version_counts.items())
        if count > 1
    )
    expected_versions = set(range(1, expected_version + 1))
    missing_versions = tuple(sorted(expected_versions - set(versions)))
    unexpected_future_versions = tuple(
        version for version in versions if version > expected_version
    )

    return MigrationInventory(
        versions=versions,
        duplicate_versions=duplicate_versions,
        missing_versions=missing_versions,
        unexpected_future_versions=unexpected_future_versions,
    )


def _table_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        """
    ).fetchall()
    return {str(row[0]) for row in rows}


def _table_columns(
    connection: sqlite3.Connection,
    table_name: str,
) -> dict[str, str]:
    rows = connection.execute(
        f"PRAGMA table_info({_quote_identifier(table_name)})"
    ).fetchall()
    return {
        str(row[1]): _normalise_type(row[2])
        for row in rows
    }


def _index_details(
    connection: sqlite3.Connection,
) -> dict[str, tuple[str, tuple[str, ...]]]:
    rows = connection.execute(
        """
        SELECT name, tbl_name
        FROM sqlite_master
        WHERE type = 'index'
          AND name NOT LIKE 'sqlite_autoindex_%'
        """
    ).fetchall()

    result: dict[str, tuple[str, tuple[str, ...]]] = {}
    for index_name, table_name in rows:
        column_rows = connection.execute(
            f"PRAGMA index_info({_quote_identifier(str(index_name))})"
        ).fetchall()
        columns = tuple(str(row[2]) for row in column_rows)
        result[str(index_name)] = (str(table_name), columns)
    return result


def inspect_connection(
    connection: sqlite3.Connection,
    *,
    database_path: str = "<connection>",
    migration_directory: str | Path = "migrations",
    expected_version: int = CURRENT_VERSION,
    expected_tables: Mapping[str, Mapping[str, str]] = EXPECTED_TABLES,
    expected_indexes: Mapping[
        str,
        tuple[str, tuple[str, ...]],
    ] = EXPECTED_INDEXES,
) -> IntegrityReport:
    """Inspect one SQLite connection without modifying its schema or data."""
    report = IntegrityReport(
        database_path=database_path,
        expected_version=expected_version,
        tables_checked=len(expected_tables),
        indexes_checked=len(expected_indexes),
    )

    integrity_rows = connection.execute("PRAGMA integrity_check").fetchall()
    integrity_messages = [str(row[0]) for row in integrity_rows]
    report.integrity_check = ", ".join(integrity_messages)
    if integrity_messages != ["ok"]:
        for message in integrity_messages:
            report.errors.append(f"SQLite integrity error: {message}")

    foreign_key_rows = connection.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()
    report.foreign_key_violations = len(foreign_key_rows)
    for table, rowid, parent, foreign_key_id in foreign_key_rows:
        report.errors.append(
            "Foreign-key violation: "
            f"table={table}, rowid={rowid}, parent={parent}, "
            f"constraint={foreign_key_id}"
        )

    version_row = connection.execute("PRAGMA user_version").fetchone()
    report.actual_version = int(version_row[0])
    if report.actual_version != expected_version:
        report.errors.append(
            "Schema version mismatch: "
            f"found {report.actual_version}, expected {expected_version}"
        )

    actual_tables = _table_names(connection)
    for table_name, expected_columns in expected_tables.items():
        if table_name not in actual_tables:
            report.errors.append(f"Missing table: {table_name}")
            continue

        actual_columns = _table_columns(connection, table_name)
        for column_name, expected_type in expected_columns.items():
            if column_name not in actual_columns:
                report.errors.append(
                    f"Missing column: {table_name}.{column_name}"
                )
                continue

            actual_type = actual_columns[column_name]
            if actual_type != _normalise_type(expected_type):
                report.errors.append(
                    "Column type mismatch: "
                    f"{table_name}.{column_name} is {actual_type or '<none>'}, "
                    f"expected {_normalise_type(expected_type)}"
                )

    actual_indexes = _index_details(connection)
    for index_name, expected_details in expected_indexes.items():
        if index_name not in actual_indexes:
            report.errors.append(f"Missing index: {index_name}")
            continue

        actual_table, actual_columns = actual_indexes[index_name]
        expected_table, expected_columns = expected_details
        if actual_table != expected_table:
            report.errors.append(
                "Index table mismatch: "
                f"{index_name} belongs to {actual_table}, "
                f"expected {expected_table}"
            )
        if actual_columns != expected_columns:
            report.errors.append(
                "Index column mismatch: "
                f"{index_name} has {actual_columns}, "
                f"expected {expected_columns}"
            )

    inventory = discover_migrations(
        migration_directory,
        expected_version,
    )
    report.migration_inventory = inventory

    for version in inventory.duplicate_versions:
        report.errors.append(
            f"Duplicate migration version: v{version}"
        )
    for version in inventory.missing_versions:
        report.errors.append(
            f"Missing migration file: migrate_v{version}.py"
        )
    for version in inventory.unexpected_future_versions:
        report.errors.append(
            "Migration version exceeds CURRENT_VERSION: "
            f"v{version} > v{expected_version}"
        )

    return report


def open_read_only(database_path: str | Path) -> sqlite3.Connection:
    """Open an existing SQLite database in read-only URI mode."""
    path = Path(database_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Database file does not exist: {path}")

    connection = sqlite3.connect(
        f"{path.as_uri()}?mode=ro",
        uri=True,
    )
    connection.row_factory = sqlite3.Row
    return connection


def inspect_database(
    database_path: str | Path,
    *,
    migration_directory: str | Path = "migrations",
    expected_version: int = CURRENT_VERSION,
) -> IntegrityReport:
    """Open and inspect a database without modifying it."""
    connection = open_read_only(database_path)
    try:
        return inspect_connection(
            connection,
            database_path=str(Path(database_path)),
            migration_directory=migration_directory,
            expected_version=expected_version,
        )
    finally:
        connection.close()
