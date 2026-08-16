import sqlite3
import json
import csv
import io
import zipfile
from typing import Any
import streamlit as st
from database import DB_NAME
import database
from cache import cached
from cache_config import CACHE_CATEGORY_SESSION
from invalidation import invalidate_all_db_caches, invalidate_export_caches


def _dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def _get_all_table_data(table_name: str) -> list[dict[str, Any]]:
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = _dict_factory
        cursor = conn.cursor()
        # Ensure table exists first to avoid errors if db is empty
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            return []
        cursor.execute(f"SELECT * FROM {table_name}")
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error reading table {table_name}: {e}")
        return []
    finally:
        if conn:
            conn.close()


@cached(category=CACHE_CATEGORY_SESSION)
def export_data_json() -> str:
    """Exports all user data as a JSON string."""
    tables = [
        "assessments",
        "appliances",
        "solar_configs",
        "user_challenges",
        "unlocked_badges",
        "xp_transactions",
        "journey_profiles",
        "offset_transactions"
    ]
    data = {}
    for table in tables:
        data[table] = _get_all_table_data(table)
    return json.dumps(data, indent=4)


@cached(category=CACHE_CATEGORY_SESSION)
def export_data_csv_zip() -> bytes:
    """Exports assessments, appliances, and offset_transactions as CSVs in a ZIP archive."""
    tables_to_export = ["assessments", "appliances", "offset_transactions"]
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for table in tables_to_export:
            data = _get_all_table_data(table)
            if not data:
                continue
            
            csv_buffer = io.StringIO()
            writer = csv.DictWriter(csv_buffer, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            
            zip_file.writestr(f"{table}.csv", csv_buffer.getvalue())
            
    return zip_buffer.getvalue()


def import_data_json(json_str: str, strategy: str = 'merge') -> tuple[bool, str]:
    """Imports JSON data back into the database. Strategy can be 'merge' or 'replace'."""
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return False, "Invalid JSON file format."

    # Validate schema loosely
    expected_tables = [
        "assessments", "appliances", "solar_configs", 
        "user_challenges", "unlocked_badges", "xp_transactions", 
        "journey_profiles", "offset_transactions"
    ]
    if not isinstance(data, dict):
        return False, "Invalid JSON data structure."
        
    for table, rows in data.items():
        if table not in expected_tables:
            continue
        if not isinstance(rows, list):
            return False, f"Invalid data format for table {table}."
            
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("BEGIN TRANSACTION")
        
        for table, rows in data.items():
            if table not in expected_tables:
                continue
                
            if strategy == 'replace':
                cursor.execute(f"DELETE FROM {table}")
                
            for row in rows:
                if not row:
                    continue
                
                # Check for duplicates by timestamp in merge strategy
                if strategy == 'merge':
                    ts_col = None
                    if 'created_at' in row:
                        ts_col = 'created_at'
                    elif 'date' in row:
                        ts_col = 'date'
                    elif 'enrolled_at' in row:
                        ts_col = 'enrolled_at'
                    elif 'unlocked_at' in row:
                        ts_col = 'unlocked_at'
                        
                    if ts_col:
                        cursor.execute(f"SELECT 1 FROM {table} WHERE {ts_col} = ?", (row[ts_col],))
                        if cursor.fetchone():
                            continue # Skip duplicate
                            
                columns = ', '.join(row.keys())
                placeholders = ', '.join(['?' for _ in row.keys()])
                values = tuple(row.values())
                
                try:
                    cursor.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values)
                except sqlite3.IntegrityError:
                    # Ignore unique constraint violations during merge
                    continue

        conn.commit()

        invalidate_export_caches()
        invalidate_all_db_caches()

        return True, "Data imported successfully!"
    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"Import failed: {str(e)}"
    finally:
        if conn:
            conn.close()


def import_assessments_bulk(
    file_content: str,
    file_type: str,
    user_id: int,
) -> dict[str, Any]:
    """
    Bulk-imports historical assessments from CSV or JSON content.
    Validates each record, skips duplicates and invalid rows, and
    returns a summary dict instead of failing the whole import.
    """
    required_fields = ["transport", "distance", "electricity", "diet", "flights", "footprint", "eco_score"]
    summary = {"imported": 0, "duplicates": 0, "invalid": 0, "errors": []}

    try:
        if file_type == "csv":
            rows = list(csv.DictReader(io.StringIO(file_content)))
        elif file_type == "json":
            parsed = json.loads(file_content)
            rows = parsed if isinstance(parsed, list) else parsed.get("assessments", [])
        else:
            summary["errors"].append("Unsupported file type. Please upload a .csv or .json file.")
            return summary
    except (json.JSONDecodeError, csv.Error) as e:
        summary["errors"].append(f"Could not parse file: {e}")
        return summary

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for i, row in enumerate(rows, start=1):
        missing = [f for f in required_fields if not row.get(f)]
        if missing:
            summary["invalid"] += 1
            summary["errors"].append(f"Row {i}: missing field(s) {', '.join(missing)}")
            continue

        try:
            transport = str(row["transport"])
            distance = float(row["distance"])
            electricity = float(row["electricity"])
            diet = str(row["diet"])
            flights = int(row["flights"])
            footprint = float(row["footprint"])
            eco_score = int(row["eco_score"])
        except (ValueError, TypeError):
            summary["invalid"] += 1
            summary["errors"].append(f"Row {i}: invalid data type in one or more fields")
            continue

        cursor.execute(
            """SELECT 1 FROM assessments
               WHERE user_id = ? AND transport = ? AND distance = ?
               AND footprint = ? AND eco_score = ?""",
            (user_id, transport, distance, footprint, eco_score),
        )
        if cursor.fetchone():
            summary["duplicates"] += 1
            continue

        if database.save_assessment(user_id, transport, distance, electricity, diet, flights, footprint, eco_score):
            summary["imported"] += 1
        else:
            summary["invalid"] += 1
            summary["errors"].append(f"Row {i}: failed to save to database")

    conn.close()
    invalidate_export_caches()
    invalidate_all_db_caches()
    return summary