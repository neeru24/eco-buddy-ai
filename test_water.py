import pytest
from water import calculate_water_footprint, validate_water_inputs, GLOBAL_WATER_AVERAGE_LITERS, DIET_VIRTUAL_WATER


# --- Normal calculation tests ---

def test_calculate_water_footprint_vegan():
    total, contributors = calculate_water_footprint(
        shower_mins_per_day=10,
        laundry_loads_per_week=2,
        dishwasher_runs_per_week=3,
        garden_mins_per_week=14,
        diet="Vegan"
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
        diet="Omnivore"
    )
    
    assert contributors["Shower"] == 50
    assert contributors["Diet"] == DIET_VIRTUAL_WATER["Omnivore"]
    assert total == 50 + DIET_VIRTUAL_WATER["Omnivore"]


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


def test_validate_water_inputs_multiple_warnings():
    warnings = validate_water_inputs(shower_mins=150, laundry_loads=40, dishwasher_runs=40, garden_mins=400)
    assert len(warnings) >= 2


def test_calculate_clamps_negative_inputs():
    total, contributors = calculate_water_footprint(
        shower_mins_per_day=-10,
        laundry_loads_per_week=-2,
        dishwasher_runs_per_week=-3,
        garden_mins_per_week=-5,
        diet="Vegan"
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
        diet="Vegan"
    )
    assert total == DIET_VIRTUAL_WATER["Vegan"]
