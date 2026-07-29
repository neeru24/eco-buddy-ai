import os
import sqlite3
import pytest
import datetime
from PIL import Image

import database as db
import gamification as gf

# Use a test database
TEST_DB = "test_eco_buddy.db"

@pytest.fixture(autouse=True)
def setup_teardown():
    original_db_name = db.DB_NAME
    db.DB_NAME = TEST_DB
    db.init_db()
    db.init_gamification_db()
    yield
    db.DB_NAME = original_db_name
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_xp_and_levels():
    # Initial state
    assert gf.get_total_xp(1) == 0
    assert gf.calculate_level(0) == 1
    
    # Award some XP
    success = db.award_xp(1, 'manual', 'test1', 150, "Test XP")
    assert success is True
    assert gf.get_total_xp(1) == 150
    assert gf.calculate_level(150) == 2
    
    # Prevent duplicate XP
    success_duplicate = db.award_xp(1, 'manual', 'test1', 50, "Test XP duplicate")
    assert success_duplicate is False
    assert gf.get_total_xp(1) == 150

def test_streak_calculation():
    # 3 consecutive days
    today = datetime.date.today()
    d1 = today - datetime.timedelta(days=2)
    d2 = today - datetime.timedelta(days=1)

    dates = [d1, d2, today]
    assert gf.calculate_streak(1, dates) == 3

    # Broken streak (gap between d_broken and d2)
    d_broken = today - datetime.timedelta(days=3)
    dates_broken = [d_broken, d2, today]
    assert gf.calculate_streak(1, dates_broken) == 2

    # Active streak — logged yesterday but NOT today yet (#86 fix)
    dates_active = [d1, d2]
    assert gf.calculate_streak(1, dates_active) == 2

    # Broken streak — last log was 2 days ago, nothing logged since
    d3 = today - datetime.timedelta(days=3)
    dates_broken_old = [d3, d1]
    assert gf.calculate_streak(1, dates_broken_old) == 0

def test_challenges():
    # Enroll
    success = db.enroll_challenge(1, 'c1')
    assert success is True
    
    # Try enrolling again
    success2 = db.enroll_challenge(1, 'c1')
    assert success2 is False
    
    # Update progress
    db.update_challenge_progress(1, 'c1', progress_increment=10.0)
    challenges = db.get_user_challenges(1)
    assert len(challenges) == 1
    assert challenges[0]['progress_value'] == 10.0
    
    # Validate logic (should not complete yet)
    is_complete = gf.validate_challenge_progress(1, 'c1')
    assert is_complete is False
    
    # Complete
    db.update_challenge_progress(1, 'c1', progress_increment=15.0)
    is_complete = gf.validate_challenge_progress(1, 'c1')
    assert is_complete is True
    
    # Verify XP was awarded exactly once
    assert gf.get_total_xp(1) == gf.CHALLENGES['c1']['xp']
    
def test_badges_and_card_generation():
    # Force unlock a badge
    gf.unlock_badge(1, 'b1')
    unlocked = db.get_unlocked_badges(1)
    assert len(unlocked) == 1
    assert unlocked[0]['badge_id'] == 'b1'
    
    # Verify badge XP awarded
    assert gf.get_total_xp(1) == gf.BADGES['b1']['xp']
    
    # Generate image
    filepath = gf.generate_achievement_card(1, 'b1', 'test_badge.png')
    assert filepath is not None
    assert os.path.exists(filepath)
    
    # Check if valid image
    try:
        with Image.open(filepath) as img:
            assert img.width == 600
            assert img.height == 400
    except IOError:
        pytest.fail("Failed to open generated image")
        
    os.remove(filepath)
