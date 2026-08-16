"""
Tests for calculation audit logs (Issue #276).

Tests:
1. calculate_footprint with return_audit=True
2. calculate_eco_score with return_audit=True
3. generate_full_audit_log structure and contents
4. export_audit_log_json formatting
5. Plugin audit log integration (CarbonFootprintPlugin)
"""

import pytest
import json
from emissions import (
    calculate_footprint,
    calculate_eco_score,
    generate_full_audit_log,
    export_audit_log_json,
)
from plugins import get_plugin


def test_calculate_footprint_audit():
    total, contributors, audit = calculate_footprint(
        transport="Car",
        distance=20.0,
        electricity=250.0,
        diet="Vegetarian",
        flights=2,
        region="Global",
        return_audit=True,
    )
    assert isinstance(total, float)
    assert isinstance(contributors, dict)
    assert isinstance(audit, dict)
    assert "timestamp" in audit
    assert "intermediate_calculations" in audit
    assert "Transport" in audit["intermediate_calculations"]
    assert "Electricity" in audit["intermediate_calculations"]
    assert "Diet" in audit["intermediate_calculations"]
    assert "Flights" in audit["intermediate_calculations"]


def test_calculate_eco_score_audit():
    total, contributors, _ = calculate_footprint(
        transport="Car",
        distance=20.0,
        electricity=250.0,
        diet="Vegetarian",
        flights=2,
        return_audit=True,
    )
    score, audit = calculate_eco_score(total, contributors, return_audit=True)
    assert isinstance(score, int)
    assert isinstance(audit, dict)
    assert "baseline" in audit
    assert "category_scores" in audit
    assert "Transport" in audit["category_scores"]


def test_generate_full_audit_log():
    audit = generate_full_audit_log("Car", 15.0, 200.0, "Vegetarian", 1)
    assert "footprint_audit" in audit
    assert "eco_score_audit" in audit
    assert "summary" in audit
    assert audit["summary"]["total_footprint_kg_co2"] > 0
    assert audit["summary"]["eco_score"] >= 0


def test_export_audit_log_json():
    audit = generate_full_audit_log("Public Transport", 10.0, 150.0, "Vegetarian", 0)
    json_str = export_audit_log_json(audit)
    assert isinstance(json_str, str)
    parsed = json.loads(json_str)
    assert "summary" in parsed
    assert parsed["summary"]["eco_score"] == audit["summary"]["eco_score"]


def test_carbon_footprint_plugin_audit():
    plugin = get_plugin("carbon_footprint")
    assert plugin is not None
    res = plugin.calculate({
        "transport": "Car",
        "distance": 20.0,
        "electricity": 250.0,
        "diet": "Vegetarian",
        "flights": 2,
        "region": "Global",
    })
    assert "audit_log" in res.metadata
    audit_log = res.metadata["audit_log"]
    assert "footprint_audit" in audit_log
