import os
import sqlite3
import pytest
from waste_classifier import classify_waste_image
import database as db
import gamification as gf

# Use a test database
TEST_DB = "test_eco_buddy.db"

@pytest.fixture(autouse=True)
def setup_teardown():
    db.DB_NAME = TEST_DB
    db.init_gamification_db()
    db.init_squads_db()
    
    # Add c6 & b7 custom setup if required (they are loaded dynamically from CHALLENGES and BADGES dictionary)
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_waste_classifier_fallback():
    # Setup mock image bytes with specific lengths to test local heuristic logic
    img_recyclable = b"abc"  # len = 3 (3 % 3 == 0) -> Recyclable
    img_compost = b"abcd"   # len = 4 (4 % 3 == 1) -> Compost
    img_landfill = b"abcde" # len = 5 (5 % 3 == 2) -> Landfill
    
    res1 = classify_waste_image(img_recyclable)
    assert res1["category"] == "Recyclable"
    assert "PET Bottle" in res1["type"]
    assert res1["confidence"] == 0.92
    
    res2 = classify_waste_image(img_compost)
    assert res2["category"] == "Compost"
    assert "Apple Core" in res2["type"]
    assert res2["confidence"] == 0.89
    
    res3 = classify_waste_image(img_landfill)
    assert res3["category"] == "Landfill"
    assert "Styrofoam" in res3["type"]
    assert res3["confidence"] == 0.85

def test_waste_scanning_gamification_progress():
    user_id = db.get_or_create_user("ScannerTestUser")
    
    # Enroll in waste sorting challenge (c6)
    success = db.enroll_challenge(user_id, 'c6')
    assert success is True
    
    # Make 1 scan progress
    db.update_challenge_progress(user_id, 'c6', progress_increment=1.0)
    challenges = db.get_user_challenges(user_id)
    c6_data = [c for c in challenges if c['challenge_id'] == 'c6'][0]
    assert c6_data['progress_value'] == 1.0
    assert c6_data['status'] == 'enrolled'
    
    # Ensure badge is still locked
    unlocked_badges = db.get_unlocked_badges(user_id)
    assert not any(b['badge_id'] == 'b7' for b in unlocked_badges)
    
    # Make 2 more scans (total 3.0)
    db.update_challenge_progress(user_id, 'c6', progress_increment=2.0)
    
    # Validate progress and complete challenge
    is_complete = gf.validate_challenge_progress(user_id, 'c6')
    assert is_complete is True
    
    # Challenge should now be completed
    challenges = db.get_user_challenges(user_id)
    c6_data = [c for c in challenges if c['challenge_id'] == 'c6'][0]
    assert c6_data['status'] == 'completed'
    
    # XP should be awarded for the challenge completion
    total_xp = gf.get_total_xp(user_id)
    assert total_xp >= gf.CHALLENGES['c6']['xp']
    
    # Check that badge eligibility unlocked the Waste Sorting Guru (b7) badge
    gf.check_badge_eligibility(user_id)
    unlocked_badges = db.get_unlocked_badges(user_id)
    assert any(b['badge_id'] == 'b7' for b in unlocked_badges)
