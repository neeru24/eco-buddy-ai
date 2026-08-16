"""
Unit tests for data processing pipeline optimization and minimal change analysis.
"""
import pytest
from impact_analyzer import analyze_minimal_change
from emissions import calculate_footprint

def test_analyze_minimal_change_reuses_data_and_returns_ranked_candidates():
    total, contributors = calculate_footprint("Car", 20.0, 300.0, "Non-Vegetarian", 2, "US")
    candidates = analyze_minimal_change("Car", 20.0, 300.0, "Non-Vegetarian", 2, "US", total)
    
    assert isinstance(candidates, list)
    assert len(candidates) > 0
    for c in candidates:
        assert "change" in c
        assert "effort" in c
        assert "savings" in c
        assert "impact_ratio" in c
        assert c["savings"] > 0
    
    # Assert sorted by impact_ratio descending
    impact_ratios = [c["impact_ratio"] for c in candidates]
    assert impact_ratios == sorted(impact_ratios, reverse=True)
