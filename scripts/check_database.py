#!/usr/bin/env python3
"""Command-line entry point for EcoBuddy database integrity checks."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database_integrity import inspect_database


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate EcoBuddy's SQLite schema, migrations, indexes, "
            "foreign keys, and integrity without modifying the database."
        )
    )
    parser.add_argument(
        "database",
        nargs="?",
        default=str(PROJECT_ROOT / "eco_buddy.db"),
        help="SQLite database path (default: eco_buddy.db)",
    )
    parser.add_argument(
        "--migrations",
        default=str(PROJECT_ROOT / "migrations"),
        help="Migration directory path",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        report = inspect_database(
            args.database,
            migration_directory=args.migrations,
        )
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"Database integrity check could not run: {exc}")
        return 2

    print(report.render())
    return 0 if report.is_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
