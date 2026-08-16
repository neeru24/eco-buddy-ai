"""Tests for automatic assessment session recovery."""

import sqlite3

import database
import session_recovery

DEFAULTS = {
    "region": "Global",
    "transport": "Car",
    "distance": 10.0,
    "electricity": 200.0,
    "diet": "Vegetarian",
    "flights": 0,
}


def test_normalise_draft_returns_complete_typed_values():
    draft = session_recovery.normalise_draft(
        {
            "transport": "Bike",
            "distance": "12.5",
            "flights": "2",
        },
        DEFAULTS,
    )

    assert draft == {
        "region": "Global",
        "transport": "Bike",
        "distance": 12.5,
        "electricity": 200.0,
        "diet": "Vegetarian",
        "flights": 2,
    }


def test_default_form_is_not_saved(monkeypatch):
    called = []
    monkeypatch.setattr(
        session_recovery,
        "save_assessment_draft",
        lambda *args: called.append(args) or True,
    )

    result = session_recovery.save_draft_if_changed(
        1,
        DEFAULTS,
        DEFAULTS,
    )

    assert result.saved is False
    assert result.reason == "unchanged-defaults"
    assert called == []


def test_changed_draft_is_saved_once(monkeypatch):
    called = []
    monkeypatch.setattr(
        session_recovery,
        "save_assessment_draft",
        lambda *args: called.append(args) or True,
    )
    values = {**DEFAULTS, "transport": "Bike"}

    first = session_recovery.save_draft_if_changed(
        1,
        values,
        DEFAULTS,
    )
    second = session_recovery.save_draft_if_changed(
        1,
        values,
        DEFAULTS,
        first.fingerprint,
    )

    assert first.saved is True
    assert second.saved is False
    assert second.reason == "already-saved"
    assert len(called) == 1


def test_restore_populates_session_state():
    state = {}

    session_recovery.restore_draft_into_session(
        {
            "region": "UK",
            "transport": "Public Transport",
            "distance": 8,
            "electricity": 150,
            "diet": "Vegetarian",
            "flights": 1,
        },
        state,
        DEFAULTS,
    )

    assert state["region"] == "UK"
    assert state["transport"] == "Public Transport"
    assert state["distance"] == 8.0
    assert state["flights"] == 1


def test_database_draft_is_updated_and_user_scoped(tmp_path, monkeypatch):
    db_path = tmp_path / "drafts.db"
    monkeypatch.setattr(database, "DB_NAME", str(db_path))

    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE assessment_drafts (
            user_id INTEGER PRIMARY KEY,
            transport TEXT,
            distance REAL,
            electricity REAL,
            diet TEXT,
            flights INTEGER,
            region TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()

    assert database.save_assessment_draft(
        1,
        "Car",
        10,
        200,
        "Vegetarian",
        0,
        "Global",
    )
    assert database.save_assessment_draft(
        1,
        "Bike",
        4,
        150,
        "Vegetarian",
        0,
        "EU",
    )
    assert database.save_assessment_draft(
        2,
        "Walking",
        2,
        100,
        "Vegetarian",
        0,
        "UK",
    )

    user_one = database.get_assessment_draft(1)
    user_two = database.get_assessment_draft(2)

    assert user_one["transport"] == "Bike"
    assert user_one["region"] == "EU"
    assert user_two["transport"] == "Walking"

    assert database.delete_assessment_draft(1)
    assert database.get_assessment_draft(1) is None
    assert database.get_assessment_draft(2) is not None
