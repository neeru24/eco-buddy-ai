import os
import pytest
import database as db

TEST_DB = "test_eco_buddy_draft.db"

@pytest.fixture(autouse=True)
def setup_teardown():
    original_db_name = db.DB_NAME
    db.DB_NAME = TEST_DB
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    db.init_db()
    yield
    db.DB_NAME = original_db_name
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_save_and_get_draft():
    user_id = 99
    success = db.save_assessment_draft(user_id, "Public Transport", 15.5, 180.0, "Vegetarian", 1, "US")
    assert success is True

    draft = db.get_assessment_draft(user_id)
    assert draft is not None
    assert draft["transport"] == "Public Transport"
    assert draft["distance"] == 15.5
    assert draft["electricity"] == 180.0
    assert draft["diet"] == "Vegetarian"
    assert draft["flights"] == 1
    assert draft["region"] == "US"


def test_save_updates_existing_draft():
    user_id = 99
    db.save_assessment_draft(user_id, "Car", 10.0, 200.0, "Non-Vegetarian", 0, "Global")
    
    # Update draft
    success = db.save_assessment_draft(user_id, "Bike", 5.0, 150.0, "Vegetarian", 0, "EU")
    assert success is True

    draft = db.get_assessment_draft(user_id)
    assert draft is not None
    assert draft["transport"] == "Bike"
    assert draft["distance"] == 5.0
    assert draft["electricity"] == 150.0
    assert draft["diet"] == "Vegetarian"
    assert draft["flights"] == 0
    assert draft["region"] == "EU"


def test_delete_draft():
    user_id = 99
    db.save_assessment_draft(user_id, "Car", 10.0, 200.0, "Vegetarian", 0, "Global")
    
    success = db.delete_assessment_draft(user_id)
    assert success is True

    draft = db.get_assessment_draft(user_id)
    assert draft is None


def test_get_non_existent_draft():
    draft = db.get_assessment_draft(12345)
    assert draft is None
