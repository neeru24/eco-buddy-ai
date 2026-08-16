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
    db.init_freeze_tokens_db()
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

def test_trading_cards():
    # Unlock a card
    success = gf.unlock_card(1, 'crd_1')
    assert success is True

    # Duplicate should fail
    success_dup = gf.unlock_card(1, 'crd_1')
    assert success_dup is False

    # Verify unlocked
    unlocked = db.get_unlocked_cards(1)
    assert len(unlocked) == 1
    assert unlocked[0]['card_id'] == 'crd_1'

    # Card definitions
    card_def = gf.CARDS.get('crd_1')
    assert card_def is not None
    assert card_def['rarity'] == 'common'
    assert card_def['icon'] == '👣'

    # Rarity colors
    rarity = gf.CARD_RARITIES.get('common')
    assert rarity is not None
    assert rarity['label'] == 'Common'

    # Generate card image
    filepath = gf.generate_trading_card(1, 'crd_1', 'test_trading_card.png')
    assert filepath is not None
    assert os.path.exists(filepath)

    try:
        with Image.open(filepath) as img:
            assert img.width == 500
            assert img.height == 700
    except IOError:
        pytest.fail("Failed to open generated trading card image")

    os.remove(filepath)

def test_card_rarities():
    for r_key, r_def in gf.CARD_RARITIES.items():
        assert 'label' in r_def
        assert 'color_bg' in r_def
        assert 'color_accent' in r_def
        assert 'color_text' in r_def
        assert len(r_def['color_bg']) == 3
        assert len(r_def['color_accent']) == 3
        assert len(r_def['color_text']) == 3

def test_all_cards_have_valid_rarity():
    for c_id, c_def in gf.CARDS.items():
        assert 'name' in c_def, f"Card {c_id} missing name"
        assert 'rarity' in c_def, f"Card {c_id} missing rarity"
        assert c_def['rarity'] in gf.CARD_RARITIES, f"Card {c_id} has invalid rarity {c_def['rarity']}"
        assert 'icon' in c_def, f"Card {c_id} missing icon"
        assert 'desc' in c_def, f"Card {c_id} missing desc"
        assert 'condition' in c_def, f"Card {c_id} missing condition"

def test_trading_card_generation_all_rarities():
    for r_key in gf.CARD_RARITIES:
        card_id = None
        for c_id, c_def in gf.CARDS.items():
            if c_def['rarity'] == r_key:
                card_id = c_id
                break
        assert card_id is not None, f"No card found for rarity {r_key}"

        filepath = gf.generate_trading_card(1, card_id, f"test_{r_key}.png")
        assert filepath is not None
        assert os.path.exists(filepath)
        os.remove(filepath)


def test_freeze_token_balance_initial():
    assert db.get_freeze_token_balance(1) == 0


def test_award_freeze_tokens():
    success = db.award_freeze_tokens(1, 3, "test award")
    assert success is True
    assert db.get_freeze_token_balance(1) == 3
    assert db.get_total_freeze_tokens_earned(1) == 3


def test_redeem_freeze_token():
    db.award_freeze_tokens(1, 2, "test award")
    success = db.redeem_freeze_token(1)
    assert success is True
    assert db.get_freeze_token_balance(1) == 1
    db.redeem_freeze_token(1)
    assert db.redeem_freeze_token(1) is False
    assert db.get_freeze_token_balance(1) == 0


def test_streak_freeze_dates():
    db.use_streak_freeze(1, "2026-07-28")
    db.use_streak_freeze(1, "2026-07-27")
    dates = db.get_streak_freeze_dates(1)
    assert "2026-07-28" in dates
    assert "2026-07-27" in dates
    db.use_streak_freeze(1, "2026-07-28")
    assert len(db.get_streak_freeze_dates(1)) == 2


def test_calculate_streak_with_freeze_dates():
    today = datetime.date.today()
    d1 = today - datetime.timedelta(days=2)
    d2 = today - datetime.timedelta(days=1)
    d_broken = today - datetime.timedelta(days=4)
    dates = [d_broken, d2]
    assert gf.calculate_streak(1, dates, []) == 1
    d3 = today - datetime.timedelta(days=3)
    d4 = today - datetime.timedelta(days=2)
    freeze_dates = [str(d3), str(d4)]
    assert gf.calculate_streak(1, dates, freeze_dates) == 4


def test_award_freeze_tokens_for_milestones():
    today = datetime.date.today()
    d1 = today - datetime.timedelta(days=2)
    d2 = today - datetime.timedelta(days=1)
    db.save_assessment(1, "car", 10, 100, "omnivore", 0, 100, 50, date=str(d1))
    db.save_assessment(1, "car", 10, 100, "omnivore", 0, 100, 50, date=str(d2))
    db.save_assessment(1, "car", 10, 100, "omnivore", 0, 100, 50, date=str(today))
    awarded = gf.award_freeze_tokens_for_streak_milestones(1)
    assert awarded == 0


def test_freeze_token_transactions():
    db.award_freeze_tokens(1, 5, "earn")
    db.redeem_freeze_token(1)
    db.award_freeze_tokens(1, 2, "bonus")
    txs = db.get_freeze_token_transactions(1)
    assert len(txs) == 3
    assert txs[0]['amount'] == 2
    assert txs[1]['amount'] == -1
    assert txs[2]['amount'] == 5
