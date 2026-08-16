"""Tests for the Eco Time Capsule feature."""
import os
import sqlite3
import tempfile
import pytest
from datetime import date, timedelta

os.environ["ECO_BUDDY_DB"] = ":memory:"

from database import (
    DB_NAME, create_time_capsule, get_time_capsules,
    update_time_capsule_unlock, update_time_capsule_progress,
    delete_time_capsule,
)
from time_capsule import CAPSULE_CATEGORIES, get_progress_summary


@pytest.fixture(autouse=True)
def setup_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        test_db = f.name
    os.environ["ECO_BUDDY_DB"] = test_db
    import database
    database.DB_NAME = test_db
    import migrations
    original_get_db_name = migrations.get_db_name
    migrations.get_db_name = lambda: test_db
    _migrate(test_db)
    yield
    migrations.get_db_name = original_get_db_name
    try:
        os.unlink(test_db)
    except OSError:
        pass


def _migrate(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA user_version = 0")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            anonymous_leaderboard INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            transport TEXT,
            distance REAL,
            electricity REAL,
            diet TEXT,
            flights INTEGER,
            footprint REAL,
            eco_score INTEGER,
            trip_id TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS xp_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL,
            xp_amount INTEGER NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, source_type, source_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_capsules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            promise_text TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            unlock_date TEXT NOT NULL,
            is_unlocked INTEGER DEFAULT 0,
            unlocked_at TIMESTAMP,
            progress_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def test_create_and_get_capsule():
    user_id = 1
    future = (date.today() + timedelta(days=30)).isoformat()
    assert create_time_capsule(user_id, "Test Capsule", "I will reduce waste", "waste", future)
    capsules = get_time_capsules(user_id)
    assert len(capsules) == 1
    assert capsules[0]["title"] == "Test Capsule"
    assert capsules[0]["promise_text"] == "I will reduce waste"
    assert capsules[0]["category"] == "waste"
    assert capsules[0]["unlock_date"] == future
    assert not capsules[0]["is_unlocked"]


def test_unlock_capsule():
    user_id = 1
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    assert create_time_capsule(user_id, "Past Capsule", "Test", "general", yesterday)
    capsules = get_time_capsules(user_id)
    assert len(capsules) == 1
    assert update_time_capsule_unlock(capsules[0]["id"])
    capsules = get_time_capsules(user_id)
    assert capsules[0]["is_unlocked"]


def test_update_progress():
    user_id = 1
    future = (date.today() + timedelta(days=30)).isoformat()
    assert create_time_capsule(user_id, "Prog Capsule", "Test", "general", future)
    capsules = get_time_capsules(user_id)
    cap_id = capsules[0]["id"]
    assert update_time_capsule_progress(cap_id, "Made good progress!")
    capsules = get_time_capsules(user_id)
    assert capsules[0]["progress_notes"] == "Made good progress!"


def test_delete_capsule():
    user_id = 1
    future = (date.today() + timedelta(days=30)).isoformat()
    assert create_time_capsule(user_id, "Del Capsule", "Test", "general", future)
    capsules = get_time_capsules(user_id)
    assert len(capsules) == 1
    assert delete_time_capsule(capsules[0]["id"])
    assert len(get_time_capsules(user_id)) == 0


def test_get_progress_summary_empty():
    assert get_progress_summary(1) == {}


def test_multiple_capsules_different_users():
    assert create_time_capsule(1, "User1 Cap", "Test", "general", (date.today() + timedelta(days=10)).isoformat())
    assert create_time_capsule(2, "User2 Cap", "Test", "general", (date.today() + timedelta(days=10)).isoformat())
    assert len(get_time_capsules(1)) == 1
    assert len(get_time_capsules(2)) == 1


def test_capsule_categories():
    for cat in CAPSULE_CATEGORIES:
        assert create_time_capsule(1, f"Cap {cat}", "Test", cat, (date.today() + timedelta(days=10)).isoformat())
    capsules = get_time_capsules(1)
    assert len(capsules) == len(CAPSULE_CATEGORIES)
