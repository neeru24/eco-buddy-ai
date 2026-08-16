"""Blockchain-Verified Carbon Credit Portfolio.

Tracks carbon credits users purchase (or earn), records issuance and
retirement events on an immutable, verifiable hash-chain ledger, and
prevents double retirement of the same credit.

This is a transparent educational simulation of a distributed ledger using
a SHA-256 hash chain, not a real blockchain. Every block references the
previous block's hash, so any tampering breaks the chain and is instantly
detectable via verify_ledger().
"""

import os
import json
import hashlib
import sqlite3
import logging
import datetime

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

# Accepted crediting standards (min. permanence 40 years is common for
# forestry projects).
CREDIT_STANDARDS = ["Verra VCS", "Gold Standard", "American Carbon Registry", "ACR Climate Action Reserve", "Puro.earth"]


def sha256_json(payload: dict) -> str:
    """SHA-256 hash of a canonical JSON payload."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _calculate_block_hash(index, previous_hash, timestamp, data) -> str:
    return sha256_json({
        "index": index,
        "previous_hash": previous_hash,
        "timestamp": timestamp,
        "data": data,
    })


def _get_conn():
    return sqlite3.connect(DB_NAME)


def init_ledger_db():
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS credit_ledger_blocks (
                index INTEGER PRIMARY KEY,
                previous_hash TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                data TEXT NOT NULL,
                block_hash TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS carbon_credit_portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                serial_number TEXT UNIQUE NOT NULL,
                project_id TEXT NOT NULL,
                project_name TEXT NOT NULL,
                standard TEXT NOT NULL,
                vintage INTEGER NOT NULL,
                tonnes REAL NOT NULL,
                cost_tonne REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                issued_hash TEXT NOT NULL,
                retired_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Ledger init error: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def generate_serial_number(user_id, project_id, vintage, tonnes):
    """Deterministic, unique serial for a credit batch."""
    token = sha256_json({
        "user_id": user_id,
        "project_id": project_id,
        "vintage": vintage,
        "tonnes": tonnes,
        "nonce": datetime.datetime.now().isoformat(),
    })[:16].upper()
    return f"CR-{vintage}-{token}"


def _append_block(data: dict):
    """Append a block to the ledger, returning its hash."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT index, block_hash FROM credit_ledger_blocks ORDER BY index DESC LIMIT 1"
        ).fetchone()
        index = (row[0] + 1) if row else 0
        previous_hash = row[1] if row else ("0" * 64)
        timestamp = datetime.datetime.now().isoformat()
        block_hash = _calculate_block_hash(index, previous_hash, timestamp, data)
        conn.execute(
            "INSERT INTO credit_ledger_blocks (index, previous_hash, timestamp, data, block_hash) "
            "VALUES (?, ?, ?, ?, ?)",
            (index, previous_hash, timestamp, json.dumps(data), block_hash),
        )
        conn.commit()
        return block_hash
    finally:
        conn.close()


def issue_credit(user_id, project, vintage, tonnes, cost_per_tonne, standard="Verra VCS"):
    """Issue a carbon credit for the user and record it on the ledger.

    Returns the credit dict, or None on failure.
    """
    init_ledger_db()
    serial = generate_serial_number(user_id, project["id"], vintage, tonnes)
    issued_hash = _append_block({
        "event": "issue",
        "serial": serial,
        "user_id": user_id,
        "project_id": project["id"],
        "project_name": project["name"],
        "standard": standard,
        "vintage": vintage,
        "tonnes": tonnes,
    })

    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            INSERT INTO carbon_credit_portfolio (
                user_id, serial_number, project_id, project_name, standard,
                vintage, tonnes, cost_tonne, status, issued_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
            """,
            (
                user_id, serial, project["id"], project["name"], standard,
                vintage, tonnes, cost_per_tonne, issued_hash,
            ),
        )
        conn.commit()
        return {
            "serial_number": serial,
            "project_id": project["id"],
            "project_name": project["name"],
            "standard": standard,
            "vintage": vintage,
            "tonnes": tonnes,
            "cost_tonne": cost_per_tonne,
            "issued_hash": issued_hash,
            "status": "active",
        }
    except sqlite3.Error as exc:
        logger.error("Unable to issue credit: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def retire_credit(user_id, credit_id, reason=""):
    """Retire a credit, permanently removing it from circulation (once only).

    Returns (success, message).
    """
    init_ledger_db()
    conn = None
    try:
        conn = _get_conn()
        row = conn.execute(
            "SELECT id, user_id, serial_number, tonnes, status FROM carbon_credit_portfolio "
            "WHERE id = ? AND user_id = ?",
            (credit_id, user_id),
        ).fetchone()
        if not row:
            return False, "Credit not found."
        if row[4] != "active":
            return False, "This credit has already been retired."

        retired_hash = _append_block({
            "event": "retire",
            "serial": row[2],
            "user_id": user_id,
            "tonnes": row[3],
            "reason": reason,
        })
        conn.execute(
            "UPDATE carbon_credit_portfolio SET status = 'retired', retired_hash = ? "
            "WHERE id = ?",
            (retired_hash, credit_id),
        )
        conn.commit()
        return True, f"Credit {row[2][:20]}... retired permanently. ~{row[3]} tCO₂e taken out of circulation."
    except sqlite3.Error as exc:
        logger.error("Unable to retire credit: %s", exc)
        return False, "Could not retire credit."
    finally:
        if conn:
            conn.close()


def get_portfolio(user_id):
    """Return all credits owned by the user."""
    init_ledger_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM carbon_credit_portfolio WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        logger.error("Unable to load portfolio: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def get_portfolio_summary(user_id):
    """Aggregate portfolio metrics."""
    credits = get_portfolio(user_id)
    total_active = sum(c["tonnes"] for c in credits if c["status"] == "active")
    total_retired = sum(c["tonnes"] for c in credits if c["status"] == "retired")
    total_value = sum(c["tonnes"] * c["cost_tonne"] for c in credits)

    projects = {}
    for c in credits:
        key = c["project_name"]
        projects[key] = {
            "project": c["project_name"],
            "tonnes": projects.get(key, {}).get("tonnes", 0) + c["tonnes"],
            "count": projects.get(key, {}).get("count", 0) + 1,
        }

    return {
        "total_credits": len(credits),
        "total_active": round(total_active, 2),
        "total_retired": round(total_retired, 2),
        "total_tonnes": round(total_active + total_retired, 2),
        "total_value_usd": round(total_value, 2),
        "projects": list(projects.values()),
    }


def verify_ledger():
    """Recompute every block hash and confirm the chain is unbroken.

    Returns (is_valid, blocks_count, first_broken_index).
    """
    init_ledger_db()
    conn = None
    try:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT index, previous_hash, timestamp, data, block_hash "
            "FROM credit_ledger_blocks ORDER BY index ASC"
        ).fetchall()
        if not rows:
            return True, 0, None

        expected_prev = "0" * 64
        for index, previous_hash, timestamp, data, stored_hash in rows:
            if previous_hash != expected_prev:
                return False, len(rows), index
            computed = _calculate_block_hash(
                index, previous_hash, timestamp, json.loads(data)
            )
            if computed != stored_hash:
                return False, len(rows), index
            expected_prev = stored_hash
        return True, len(rows), None
    except sqlite3.Error as exc:
        logger.error("Unable to verify ledger: %s", exc)
        return False, 0, None
    finally:
        if conn:
            conn.close()


def lookup_credit(serial_number):
    """Public verification: look up a credit's lifecycle events by serial."""
    init_ledger_db()
    conn = None
    try:
        conn = _get_conn()
        credit = conn.execute(
            "SELECT * FROM carbon_credit_portfolio WHERE serial_number = ?",
            (serial_number,),
        ).fetchone()
        if not credit:
            return None

        events = conn.execute(
            "SELECT data, block_hash, timestamp FROM credit_ledger_blocks "
            "WHERE data LIKE ? ORDER BY index ASC",
            (f"%{serial_number}%",),
        ).fetchall()

        col_names = [d[0] for d in conn.execute("SELECT * FROM carbon_credit_portfolio WHERE serial_number = ?", (serial_number,)).description]
        credit_dict = dict(zip(col_names, credit))
        return {
            "serial_number": serial_number,
            "standard": credit_dict.get("standard"),
            "vintage": credit_dict.get("vintage"),
            "project_name": credit_dict.get("project_name"),
            "tonnes": credit_dict.get("tonnes"),
            "status": credit_dict.get("status"),
            "issued_hash": credit_dict.get("issued_hash"),
            "retired_hash": credit_dict.get("retired_hash"),
            "events": [{"data": json.loads(e[0]), "hash": e[1][:16] + "...", "timestamp": e[2]} for e in events],
        }
    except sqlite3.Error as exc:
        logger.error("Unable to lookup credit: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def get_ledger_height():
    init_ledger_db()
    conn = None
    try:
        conn = _get_conn()
        row = conn.execute("SELECT COUNT(*) FROM credit_ledger_blocks").fetchone()
        return row[0]
    except sqlite3.Error as exc:
        logger.error("Unable to read ledger height: %s", exc)
        return 0
    finally:
        if conn:
            conn.close()