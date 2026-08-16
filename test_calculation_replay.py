"""
Unit tests for Carbon Calculation Replay (#443).
"""

import pytest
from calculation_replay import (
    compare_revisions,
    get_change_highlights,
    build_replay_timeline,
)


def test_compare_revisions():
    rev_a = {
        "transport": "Gasoline Car",
        "distance": 100.0,
        "electricity": 300.0,
        "diet": "Meat-Heavy",
        "flights": 2,
        "footprint": 450.0,
        "eco_score": 50,
    }
    rev_b = {
        "transport": "Electric Vehicle",
        "distance": 60.0,
        "electricity": 200.0,
        "diet": "Vegetarian",
        "flights": 0,
        "footprint": 200.0,
        "eco_score": 85,
    }
    
    diff = compare_revisions(rev_a, rev_b)
    
    assert diff["footprint_delta"] == -250.0
    assert diff["eco_score_delta"] == 35
    assert diff["distance_delta"] == -40.0
    assert diff["electricity_delta"] == -100.0
    assert diff["flights_delta"] == -2
    assert diff["transport_changed"] is True
    assert diff["diet_changed"] is True


def test_get_change_highlights():
    rev_a = {"transport": "Car", "distance": 100.0, "electricity": 200.0, "diet": "Meat", "flights": 1, "footprint": 300.0, "eco_score": 60}
    rev_b = {"transport": "Bus", "distance": 100.0, "electricity": 200.0, "diet": "Vegan", "flights": 1, "footprint": 150.0, "eco_score": 85}
    
    highlights = get_change_highlights(rev_a, rev_b)
    assert len(highlights) >= 2
    fields = [h["field"] for h in highlights]
    assert "Transport" in fields
    assert "Diet" in fields


def test_build_replay_timeline():
    timeline = build_replay_timeline(user_id=1)
    assert isinstance(timeline, list)
    assert len(timeline) >= 2
    assert "revision_num" in timeline[0]
    assert "footprint" in timeline[0]
