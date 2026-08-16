"""
Unit tests for Undo & Restore Last Assessment (#441).
"""

import pytest
from database import (
    init_db,
    save_assessment,
    get_assessments,
    undo_last_assessment,
    restore_last_deleted_assessment,
    get_last_undone_assessment,
    get_assessment_activity_history,
)


@pytest.fixture(autouse=True)
def setup_test_database():
    """Ensure database schema is initialized before tests."""
    init_db()


def test_undo_and_restore_assessment():
    test_user_id = 999
    
    # 1. Save an assessment
    saved = save_assessment(
        user_id=test_user_id,
        transport="Car",
        distance=50.0,
        electricity=100.0,
        diet="Vegetarian",
        flights=0,
        footprint=120.5,
        eco_score=80
    )
    assert saved is True
    
    assessments_before = get_assessments(user_id=test_user_id)
    assert len(assessments_before) >= 1
    latest_id = assessments_before[0][0]
    
    # 2. Undo assessment
    success, msg, undone_data = undo_last_assessment(user_id=test_user_id)
    assert success is True
    assert undone_data["id"] == latest_id
    
    assessments_after_undo = get_assessments(user_id=test_user_id)
    assert len(assessments_after_undo) == len(assessments_before) - 1
    
    # 3. Check undone record preview
    last_undone = get_last_undone_assessment(user_id=test_user_id)
    assert last_undone is not None
    assert last_undone["original_id"] == latest_id
    
    # 4. Restore assessment
    res_success, res_msg, restored_data = restore_last_deleted_assessment(user_id=test_user_id)
    assert res_success is True
    assert restored_data["footprint"] == 120.5
    
    assessments_after_restore = get_assessments(user_id=test_user_id)
    assert len(assessments_after_restore) == len(assessments_before)
    
    # 5. Verify Activity Log
    history = get_assessment_activity_history(user_id=test_user_id)
    assert len(history) >= 2
    actions = [h["action"] for h in history]
    assert "UNDO" in actions
    assert "RESTORE" in actions
