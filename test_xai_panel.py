"""
Tests for Explainable AI (XAI) feature importance and transparent recommendation reasoning.
"""
import pytest
from emissions import calculate_footprint, calculate_eco_score, generate_full_audit_log
from recommendations import generate_recommendations

def test_xai_audit_log_contains_feature_importance_breakdown():
    total, contributors, footprint_audit = calculate_footprint(
        transport="Car",
        distance=25.0,
        electricity=350.0,
        diet="Non-Vegetarian",
        flights=3,
        region="US",
        return_audit=True
    )
    assert total > 0
    assert "intermediate_calculations" in footprint_audit
    
    steps = footprint_audit["intermediate_calculations"]
    for cat in ["Transport", "Electricity", "Diet", "Flights"]:
        assert cat in steps
        assert "formula" in steps[cat]
        assert "expression" in steps[cat]
        assert "rounded_result_kg" in steps[cat]

def test_xai_eco_score_audit_transparency():
    total, contributors = calculate_footprint(
        transport="Car",
        distance=20.0,
        electricity=250.0,
        diet="Non-Vegetarian",
        flights=2,
        region="Global"
    )
    score, audit = calculate_eco_score(total, contributors, return_audit=True)
    assert 0 <= score <= 100
    assert "category_scores" in audit
    assert "final_weighted_score" in audit
    assert len(audit["category_scores"]) == 4

def test_xai_full_audit_log_generation():
    full_audit = generate_full_audit_log(
        transport="Car",
        distance=20.0,
        electricity=200.0,
        diet="Vegetarian",
        flights=1,
        region="Global"
    )
    assert "footprint_audit" in full_audit
    assert "eco_score_audit" in full_audit
    assert "summary" in full_audit
    assert full_audit["summary"]["eco_score"] > 0
