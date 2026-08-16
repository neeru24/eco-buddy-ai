import pytest
import sqlite3
import os
from database import DB_NAME, init_db, init_gamification_db, get_skill_tree_progress, update_skill_node_status, award_xp, get_total_xp
from gamification import evaluate_skill_tree, complete_skill_node
from skill_tree_data import SKILL_TREE_NODES

TEST_DB = "test_eco_buddy_skill.db"

@pytest.fixture(autouse=True)
def setup_db():
    import database as db
    old_db = db.DB_NAME
    db.DB_NAME = TEST_DB
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    db.init_db()
    db.init_gamification_db()
    
    get_skill_tree_progress.clear()
    get_total_xp.clear()
    
    yield
    
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    db.DB_NAME = old_db

def test_initial_evaluation():
    node_status = evaluate_skill_tree(1)
    
    # Since start_composting and zero_waste_grocery have no prereqs, they should be 'Unlocked'
    assert node_status.get('start_composting') == 'Unlocked'
    assert node_status.get('zero_waste_grocery') == 'Unlocked'
    
    # Prereqs not met
    assert node_status.get('grow_herbs', 'Locked') == 'Locked'
    assert node_status.get('solar_panels', 'Locked') == 'Locked'

def test_completing_node_unlocks_child():
    # Evaluate first to unlock roots
    evaluate_skill_tree(1)
    
    # Complete start_composting
    success = complete_skill_node(1, 'start_composting')
    assert success == True
    
    node_status = evaluate_skill_tree(1)
    assert node_status.get('start_composting') == 'Completed'
    
    # grow_herbs should now be unlocked since its prereq is start_composting
    assert node_status.get('grow_herbs') == 'Unlocked'
    
    # Check XP awarded
    xp = get_total_xp(1)
    assert xp == SKILL_TREE_NODES['start_composting']['xp_reward']

def test_multiple_prerequisites():
    evaluate_skill_tree(1)
    
    # Complete grow_herbs prereq
    complete_skill_node(1, 'start_composting')
    complete_skill_node(1, 'grow_herbs')
    
    node_status = evaluate_skill_tree(1)
    
    # plant_based_diet needs both grow_herbs and zero_waste_grocery
    assert node_status.get('plant_based_diet', 'Locked') == 'Locked'
    
    # complete the second prereq
    complete_skill_node(1, 'zero_waste_grocery')
    
    node_status = evaluate_skill_tree(1)
    assert node_status.get('plant_based_diet') == 'Unlocked'
def test_successful_node_completion():
    evaluate_skill_tree(1)

    success = complete_skill_node(1, "start_composting")

    assert success is True

    node_status = evaluate_skill_tree(1)

    assert node_status["start_composting"] == "Completed"
def test_cannot_complete_locked_node():
    evaluate_skill_tree(1)

    success = complete_skill_node(1, "solar_panels")

    assert success is False

    node_status = evaluate_skill_tree(1)

    assert node_status.get("solar_panels", "Locked") == "Locked"
def test_complete_invalid_node():
    success = complete_skill_node(1, "invalid_node")

    assert success is False
def test_xp_awarded_after_completion():
    evaluate_skill_tree(1)

    complete_skill_node(1, "start_composting")

    xp = get_total_xp(1)

    assert xp == SKILL_TREE_NODES["start_composting"]["xp_reward"]
def test_child_remains_locked_without_prerequisites():
    evaluate_skill_tree(1)

    node_status = evaluate_skill_tree(1)

    assert node_status.get("grow_herbs") == "Locked"