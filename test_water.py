"""Unit tests for water footprint calculations, daily activities, categories, and savings."""

import pytest
from water import (
    calculate_water_footprint,
    validate_water_inputs,
    get_activity_categories,
    calculate_water_efficiency_score,
    calculate_potential_water_savings,
    liters_to_gallons,
    gallons_to_liters,
    GLOBAL_WATER_AVERAGE_LITERS,
    DIET_VIRTUAL_WATER,
)


# --- Backwards compatibility tests ---

def test_calculate_water_footprint_vegan():
    total, contributors = calculate_water_footprint(
        shower_mins_per_day=10,
        laundry_loads_per_week=2,
        dishwasher_runs_per_week=3,
        garden_mins_per_week=14,
        diet="Vegan",
    )
    
    assert total > 0
    assert contributors["Shower"] == 100
    assert contributors["Laundry"] == pytest.approx((2 * 50) / 7.0)
    assert contributors["Dishwasher"] == pytest.approx((3 * 15) / 7.0)
    assert contributors["Garden"] == pytest.approx((14 * 20) / 7.0)
    assert contributors["Diet"] == DIET_VIRTUAL_WATER["Vegan"]


def test_calculate_water_footprint_omnivore():
    total, contributors = calculate_water_footprint(
        shower_mins_per_day=5,
        laundry_loads_per_week=0,
        dishwasher_runs_per_week=0,
        garden_mins_per_week=0,
        diet="Omnivore",
    )
    
    assert contributors["Shower"] == 50
    assert contributors["Diet"] == DIET_VIRTUAL_WATER["Omnivore"]
    assert total == 50 + DIET_VIRTUAL_WATER["Omnivore"]


# --- Granular daily activities tests ---

def test_calculate_water_footprint_with_extended_activities():
    total, contributors = calculate_water_footprint(
        shower_mins_per_day=8,
        laundry_loads_per_week=3,
        dishwasher_runs_per_week=4,
        garden_mins_per_week=20,
        diet="Vegetarian",
        baths_per_week=2,
        teeth_handwash_mins_per_day=3,
        tap_running_while_brushing=True,
        toilet_flushes_per_day=6,
        low_flow_fixtures=False,
        cooking_drinking_liters_per_day=12,
        car_washes_per_month=2,
        cleaning_liters_per_day=6,
    )

    assert "Baths" in contributors
    assert "Sink & Hygiene" in contributors
    assert "Toilet Flushes" in contributors
    assert "Cooking & Drinking" in contributors
    assert "Car Wash" in contributors
    assert "House Cleaning" in contributors

    assert contributors["Baths"] == pytest.approx((2 * 120.0) / 7.0)
    assert contributors["Sink & Hygiene"] == pytest.approx(3 * 8.0)
    assert contributors["Toilet Flushes"] == pytest.approx(6 * 9.0)
    assert contributors["Cooking & Drinking"] == 12.0
    assert contributors["Car Wash"] == pytest.approx((2 * 150.0) / 30.0)
    assert contributors["House Cleaning"] == 6.0
    assert total == sum(contributors.values())


def test_calculate_water_footprint_low_flow_fixtures():
    total_std, _ = calculate_water_footprint(
        shower_mins_per_day=10,
        laundry_loads_per_week=4,
        toilet_flushes_per_day=6,
        low_flow_fixtures=False,
    )
    total_low, _ = calculate_water_footprint(
        shower_mins_per_day=10,
        laundry_loads_per_week=4,
        toilet_flushes_per_day=6,
        low_flow_fixtures=True,
    )

    assert total_low < total_std


# --- Activity categorization tests ---

def test_get_activity_categories():
    _, contributors = calculate_water_footprint(
        shower_mins_per_day=10,
        laundry_loads_per_week=2,
        dishwasher_runs_per_week=3,
        garden_mins_per_week=15,
        diet="Omnivore",
        baths_per_week=1,
        toilet_flushes_per_day=5,
    )

    categories = get_activity_categories(contributors)

    assert "Personal Hygiene" in categories
    assert "Kitchen & Laundry" in categories
    assert "Outdoor & Cleaning" in categories
    assert "Dietary Virtual Water" in categories
    assert sum(categories.values()) == pytest.approx(sum(contributors.values()))


# --- Water efficiency rating tests ---

def test_calculate_water_efficiency_score():
    score_low = calculate_water_efficiency_score(1800.0)
    assert score_low["grade"] == "A+"
    assert score_low["score"] >= 90
    assert score_low["diff_pct"] < 0

    score_high = calculate_water_efficiency_score(6500.0)
    assert score_high["grade"] in {"D", "F"}
    assert score_high["diff_pct"] > 0


# --- Potential savings calculations tests ---

def test_calculate_potential_water_savings():
    inputs = {
        "shower_mins": 12.0,
        "low_flow_fixtures": False,
        "tap_running_while_brushing": True,
        "laundry_loads": 3,
        "baths_per_week": 2,
        "diet": "Omnivore",
    }
    savings = calculate_potential_water_savings(inputs)

    assert len(savings) >= 4
    actions = [s["action"] for s in savings]
    assert any("Shower" in a for a in actions)
    assert any("Low-Flow" in a for a in actions)
    assert any("Tap" in a for a in actions)
    assert any("Plant-Based" in a for a in actions)

    for s in savings:
        assert s["daily_liters_saved"] > 0
        assert s["annual_liters_saved"] == pytest.approx(s["daily_liters_saved"] * 365.0)


# --- Conversions tests ---

def test_unit_conversions():
    liters = 378.5411784
    gallons = liters_to_gallons(liters)
    assert gallons == pytest.approx(100.0)
    assert gallons_to_liters(gallons) == pytest.approx(liters)


# --- Input validation tests ---

def test_validate_water_inputs_normal_values():
    warnings = validate_water_inputs(shower_mins=10, laundry_loads=3, dishwasher_runs=5, garden_mins=30)
    assert len(warnings) == 0


def test_validate_water_inputs_high_shower():
    warnings = validate_water_inputs(shower_mins=150, laundry_loads=3, dishwasher_runs=5, garden_mins=30)
    assert any("shower" in w.lower() for w in warnings)


def test_validate_water_inputs_high_laundry():
    warnings = validate_water_inputs(shower_mins=10, laundry_loads=40, dishwasher_runs=5, garden_mins=30)
    assert any("laundry" in w.lower() for w in warnings)


def test_validate_water_inputs_high_dishwasher():
    warnings = validate_water_inputs(shower_mins=10, laundry_loads=3, dishwasher_runs=40, garden_mins=30)
    assert any("dishwasher" in w.lower() for w in warnings)


def test_validate_water_inputs_high_garden():
    warnings = validate_water_inputs(shower_mins=10, laundry_loads=3, dishwasher_runs=5, garden_mins=400)
    assert any("garden" in w.lower() for w in warnings)


def test_validate_water_inputs_extended_activities():
    warnings = validate_water_inputs(
        baths_per_week=25,
        teeth_mins=40,
        toilet_flushes=35,
        car_washes_month=35,
    )
    assert len(warnings) == 4


def test_calculate_clamps_negative_inputs():
    total, contributors = calculate_water_footprint(
        shower_mins_per_day=-10,
        laundry_loads_per_week=-2,
        dishwasher_runs_per_week=-3,
        garden_mins_per_week=-5,
        diet="Vegan",
    )
    assert contributors["Shower"] >= 0
    assert contributors["Laundry"] >= 0
    assert total >= 0


def test_calculate_zero_inputs():
    total, _ = calculate_water_footprint(
        shower_mins_per_day=0,
        laundry_loads_per_week=0,
        dishwasher_runs_per_week=0,
        garden_mins_per_week=0,
        diet="Vegan",
    )
    assert total == DIET_VIRTUAL_WATER["Vegan"]
