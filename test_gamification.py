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
    db.DB_NAME = TEST_DB
    db.init_gamification_db()
    db.init_squads_db()
    yield
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

    # Broken streak
    d_broken = today - datetime.timedelta(days=3)
    dates_broken = [d_broken, d2, today]
    # diff for d_broken is 3. streak is 2 at that point. diff (3) > streak (2), so breaks.
    assert gf.calculate_streak(1, dates_broken) == 2
    
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


def test_create_and_join_squad():
    # Setup test users
    uid1 = db.get_or_create_user("TestAlice")
    uid2 = db.get_or_create_user("TestBob")
    
    # Create squad
    invite_code = db.create_squad("Test Warriors", "Description", uid1)
    assert invite_code is not None
    assert invite_code.startswith("SQ-")
    
    # Check Alice squad
    sq = db.get_squad_for_user(uid1)
    assert sq['name'] == "Test Warriors"
    
    # Alice can't join another squad
    success, msg = db.join_squad_by_code(uid1, invite_code)
    assert success is False
    
    # Bob joins via code
    success, msg = db.join_squad_by_code(uid2, invite_code)
    assert success is True
    
    # Verify members
    members = db.get_squad_members(sq['id'])
    assert len(members) == 2
    assert any(m['user_id'] == uid1 for m in members)
    assert any(m['user_id'] == uid2 for m in members)
    
    # Leave squad
    assert db.leave_squad(uid2) is True
    members = db.get_squad_members(sq['id'])
    assert len(members) == 1


def test_squad_leaderboard():
    uid1 = db.get_or_create_user("UserL1")
    uid2 = db.get_or_create_user("UserL2")
    
    # Create squads
    code1 = db.create_squad("Squad A", "Desc", uid1)
    code2 = db.create_squad("Squad B", "Desc", uid2)
    
    # Award XP
    db.award_xp(uid1, 'challenge', 'c11', 100, "XP A")
    db.award_xp(uid2, 'challenge', 'c12', 50, "XP B")
    
    leaderboard = db.get_squad_leaderboard()
    assert len(leaderboard) >= 2
    # Squad A should be ahead of Squad B
    filtered = [s for s in leaderboard if s['name'] in ["Squad A", "Squad B"]]
    assert filtered[0]['name'] == "Squad A"
    assert filtered[0]['total_xp'] == 100
    assert filtered[1]['name'] == "Squad B"
    assert filtered[1]['total_xp'] == 50


def test_monthly_challenge_evaluation():
    uid1 = db.get_or_create_user("UserC1")
    
    # Create squad
    code = db.create_squad("Challenge Squad", "Desc", uid1)
    sq = db.get_squad_for_user(uid1)
    
    # Create custom monthly challenge in DB
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO monthly_challenges (id, title, description, target_xp, start_date, end_date, status, reward_badge_id)
        VALUES ('test_mc', 'Test Challenge', 'Goal', 50, '2026-07-01', '2026-07-31', 'active', 'b6')
    """)
    conn.commit()
    conn.close()
    
    # Pre-check
    unlocked = db.get_unlocked_badges(uid1)
    assert not any(b['badge_id'] == 'b6' for b in unlocked)
    
    # Award enough XP to meet the target
    db.award_xp(uid1, 'challenge', 'c13', 60, "XP C")
    
    # Run evaluation
    results = gf.evaluate_monthly_challenges()
    # Check that our test challenge is completed and rewarded
    evaluated = [r for r in results if r['challenge_id'] == 'test_mc']
    assert len(evaluated) == 1
    assert "Challenge Squad" in evaluated[0]['winning_squads']
    
    # Check if Alice got the reward badge b6
    unlocked = db.get_unlocked_badges(uid1)
    assert any(b['badge_id'] == 'b6' for b in unlocked)
