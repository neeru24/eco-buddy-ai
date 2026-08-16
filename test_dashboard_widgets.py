import os
import sqlite3

import pytest

import database as db
from dashboard_widgets import DEFAULT_WIDGETS, normalize_widget_preferences

TEST_DB = "test_dashboard_widgets.db"


@pytest.fixture(autouse=True)
def isolated_database():
    original = db.DB_NAME
    db.DB_NAME = TEST_DB
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    conn = sqlite3.connect(TEST_DB)
    conn.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "INSERT INTO users (id, username, email, password_hash) VALUES (1, 'tester', 'test@example.com', 'hash')"
    )
    conn.commit()
    conn.close()

    yield

    db.DB_NAME = original
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_normalize_filters_unknown_and_duplicate_widgets():
    assert normalize_widget_preferences(
        ["trend", "summary", "trend", "unknown"]
    ) == ["summary", "trend"]


def test_normalize_preserves_canonical_dashboard_order():
    assert normalize_widget_preferences(reversed(DEFAULT_WIDGETS)) == list(DEFAULT_WIDGETS)


def test_preferences_are_saved_and_restored_for_user():
    assert db.get_dashboard_widget_preferences(1) is None

    assert db.save_dashboard_widget_preferences(1, ["summary", "trend"]) is True

    assert db.get_dashboard_widget_preferences(1) == ["summary", "trend"]


def test_preferences_can_hide_all_widgets():
    assert db.save_dashboard_widget_preferences(1, []) is True
    assert db.get_dashboard_widget_preferences(1) == []


def test_preferences_upsert_replaces_previous_layout():
    assert db.save_dashboard_widget_preferences(1, ["summary"]) is True
    assert db.save_dashboard_widget_preferences(1, ["eco_score", "quick_tips"]) is True

    assert db.get_dashboard_widget_preferences(1) == ["eco_score", "quick_tips"]
