# Database Integrity Checker

EcoBuddy AI includes a read-only command for validating the SQLite database
before application startup, migration work, or deployment.

## Run the checker

From the repository root:

```powershell
python scripts/check_database.py
```

The default database is:

```text
eco_buddy.db
```

Inspect another database:

```powershell
python scripts/check_database.py path\to\database.db
```

Use another migration directory:

```powershell
python scripts/check_database.py `
  path\to\database.db `
  --migrations path\to\migrations
```

## Checks performed

The command validates:

- `PRAGMA integrity_check`;
- `PRAGMA foreign_key_check`;
- `PRAGMA user_version`;
- the expected migration version;
- required tables;
- required columns and SQLite column types;
- required named indexes and indexed columns;
- missing migration versions;
- duplicate migration versions;
- migration files newer than `CURRENT_VERSION`.

The checker allows additional feature tables, columns, and indexes. It only
fails when a required object is absent or incompatible.

## Exit codes

```text
0  Database is valid
1  Database was inspected but integrity problems were found
2  The checker could not run, for example because the file does not exist
```

This allows CI and deployment scripts to stop when schema drift is detected.

## Read-only behaviour

`inspect_database()` opens the file using SQLite URI mode:

```text
mode=ro
```

The checker does not run migrations, create tables, update `user_version`, or
write application data.

## Example success

```text
Database integrity check passed
Database: eco_buddy.db
Schema version: 8 (expected 8)
Tables checked: 22
Indexes checked: 9
Foreign-key violations: 0
SQLite integrity check: ok
Migration files: 1, 2, 3, 4, 5, 6, 7, 8
```

## Example failure

```text
Database integrity check failed
Database: eco_buddy.db
Schema version: 7 (expected 8)
Tables checked: 22
Indexes checked: 9
Foreign-key violations: 0
SQLite integrity check: ok
Migration files: 1, 2, 3, 4, 5, 6, 7, 8
- Schema version mismatch: found 7, expected 8
- Missing table: environmental_milestones
- Missing index: idx_assessments_factor_version
```

## Extending the expected schema

Update these constants in `database_integrity.py` when a migration introduces
a required object:

```python
EXPECTED_TABLES
EXPECTED_INDEXES
```

Then increment `CURRENT_VERSION`, add the next `migrate_vN.py`, and update the
integrity tests.

## Tests

```powershell
python -m pytest test_database_integrity.py -v
```

The focused suite creates temporary SQLite databases and covers valid schemas,
missing tables, missing columns, type mismatches, missing indexes, outdated
versions, foreign-key violations, migration gaps, duplicates, future
migrations, read-only behaviour, and command exit codes.
