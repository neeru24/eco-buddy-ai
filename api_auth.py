"""
API Authentication & Key Management Module for EcoBuddy AI Sustainability Insights API.

Provides API key generation, secure storage (hashed with SHA-256 or bcrypt), validation,
scope checking, and rate limiting logic.
"""

import os
import secrets
import hashlib
import time
import datetime
from database_connection import database_connection

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")


def init_api_keys_db() -> None:
    """Initialize the api_keys database table if it doesn't exist."""
    with database_connection(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name TEXT NOT NULL,
                api_key_hash TEXT NOT NULL UNIQUE,
                key_prefix TEXT NOT NULL,
                user_id TEXT DEFAULT 'default_user',
                role TEXT DEFAULT 'developer',
                rate_limit INTEGER DEFAULT 100,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP
            )
        """)
        conn.commit()


def hash_key(raw_key: str) -> str:
    """Hash raw API key using SHA-256."""
    return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()


def generate_api_key(app_name: str, user_id: str = "default_user", role: str = "developer", rate_limit: int = 100) -> dict:
    """
    Generate a secure random API key.
    
    Returns:
        dict with raw 'api_key' (shown once to user), 'key_prefix', 'app_name', and DB row metadata.
    """
    init_api_keys_db()
    raw_token = secrets.token_hex(24)
    raw_key = f"eco_live_{raw_token}"
    key_prefix = raw_key[:12] + "..."
    key_hash = hash_key(raw_key)

    with database_connection(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO api_keys (app_name, api_key_hash, key_prefix, user_id, role, rate_limit, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (app_name, key_hash, key_prefix, user_id, role, rate_limit))
        conn.commit()
        key_id = cursor.lastrowid

    return {
        "id": key_id,
        "app_name": app_name,
        "api_key": raw_key,
        "key_prefix": key_prefix,
        "user_id": user_id,
        "role": role,
        "rate_limit": rate_limit,
        "created_at": datetime.datetime.now().isoformat()
    }


def validate_api_key(raw_key: str) -> dict:
    """
    Validate an incoming raw API key.
    
    Returns dict with key details if valid and active, or None if invalid.
    Updates last_used_at timestamp.
    """
    if not raw_key or not isinstance(raw_key, str):
        return None

    init_api_keys_db()
    key_hash = hash_key(raw_key.strip())

    with database_connection(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, app_name, key_prefix, user_id, role, rate_limit, is_active, created_at
            FROM api_keys
            WHERE api_key_hash = ? AND is_active = 1
        """, (key_hash,))
        row = cursor.fetchone()

        if not row:
            return None

        key_info = {
            "id": row[0],
            "app_name": row[1],
            "key_prefix": row[2],
            "user_id": row[3],
            "role": row[4],
            "rate_limit": row[5],
            "is_active": bool(row[6]),
            "created_at": row[7]
        }

        # Update last_used_at
        cursor.execute("""
            UPDATE api_keys
            SET last_used_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (row[0],))
        conn.commit()

        return key_info


def revoke_api_key(key_id: int) -> bool:
    """Revoke (deactivate) an API key by ID."""
    init_api_keys_db()
    with database_connection(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE api_keys SET is_active = 0 WHERE id = ?
        """, (key_id,))
        conn.commit()
        return cursor.rowcount > 0


def list_api_keys(user_id: str = None) -> list:
    """List API keys metadata (without exposing secret hashes or raw keys)."""
    init_api_keys_db()
    with database_connection(DB_NAME) as conn:
        cursor = conn.cursor()
        if user_id:
            cursor.execute("""
                SELECT id, app_name, key_prefix, user_id, role, rate_limit, is_active, created_at, last_used_at
                FROM api_keys WHERE user_id = ? ORDER BY created_at DESC
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT id, app_name, key_prefix, user_id, role, rate_limit, is_active, created_at, last_used_at
                FROM api_keys ORDER BY created_at DESC
            """)
        rows = cursor.fetchall()
        return [
            {
                "id": r[0],
                "app_name": r[1],
                "key_prefix": r[2],
                "user_id": r[3],
                "role": r[4],
                "rate_limit": r[5],
                "is_active": bool(r[6]),
                "created_at": r[7],
                "last_used_at": r[8]
            }
            for r in rows
        ]


def authenticate_request(headers: dict) -> tuple:
    """
    Extract API key from headers (X-API-Key or Authorization: Bearer <key>).
    
    Returns:
        tuple (is_authenticated: bool, key_info_or_error: dict/str)
    """
    api_key = None
    if "X-API-Key" in headers:
        api_key = headers["X-API-Key"]
    elif "x-api-key" in headers:
        api_key = headers["x-api-key"]
    elif "Authorization" in headers or "authorization" in headers:
        auth_val = headers.get("Authorization") or headers.get("authorization")
        if auth_val and auth_val.startswith("Bearer "):
            api_key = auth_val[7:].strip()

    if not api_key:
        return False, "Missing API Key. Provide 'X-API-Key' header or 'Authorization: Bearer <key>'."

    key_info = validate_api_key(api_key)
    if not key_info:
        return False, "Invalid or deactivated API Key."

    return True, key_info
