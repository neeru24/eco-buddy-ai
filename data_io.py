import sqlite3
import json
import csv
import io
import zipfile
import streamlit as st
from database import DB_NAME
import database
from cache import cached
from cache_config import CACHE_CATEGORY_SESSION
from invalidation import invalidate_all_db_caches, invalidate_export_caches


def _dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def _get_all_table_data(table_name):
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
def export_data_json():
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
def export_data_csv_zip():
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


def import_data_json(json_str, strategy='merge'):
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
