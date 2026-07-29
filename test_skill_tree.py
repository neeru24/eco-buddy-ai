import pytest
import sqlite3
import os
from database import DB_NAME, init_db, init_gamification_db, get_skill_tree_progress, update_skill_node_status, award_xp, get_total_xp
from gamification import evaluate_skill_tree, complete_skill_node
from skill_tree_data import SKILL_TREE_NODES

@pytest.fixture(autouse=True)
def setup_db():
    # Setup
    init_db()
    init_gamification_db()
    # Ensure fresh state for user 1
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM skill_tree_progress WHERE user_id = 1")
    cursor.execute("DELETE FROM xp_transactions WHERE user_id = 1")
    conn.commit()
    conn.close()
    
    get_skill_tree_progress.clear()
    get_total_xp.clear()
    
    yield
    
    # Teardown
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM skill_tree_progress WHERE user_id = 1")
    cursor.execute("DELETE FROM xp_transactions WHERE user_id = 1")
    conn.commit()
    conn.close()

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
from unittest.mock import patch
from pages.Skill_Tree import load_skill_tree, load_total_xp


@patch("pages.Skill_Tree.evaluate_skill_tree")
def test_load_skill_tree_error(mock_eval):
    mock_eval.side_effect = RuntimeError("Database error")

    result = load_skill_tree(1)

    assert result == {}


@patch("pages.Skill_Tree.get_total_xp")
def test_load_total_xp_error(mock_xp):
    mock_xp.side_effect = RuntimeError("Database error")

    result = load_total_xp(1)

    assert result == 0