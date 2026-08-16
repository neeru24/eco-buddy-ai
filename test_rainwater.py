"""Tests for the Rainwater Harvesting Planner."""
import os
import tempfile

import pytest

os.environ["ECO_BUDDY_DB"] = ":memory:"

import rainwater
from rainwater import (
    CLIMATE_ZONES,
    DAYS_IN_MONTH,
    DEFAULT_CLIMATE_ZONE,
    DEFAULT_TREATMENT_INTENSITY,
    LITRES_PER_PERSON_PER_DAY,
    MONTHS,
    ROOF_MATERIALS,
    SYSTEM_EFFICIENCY,
    TANK_COST_PER_LITRE,
    TANK_SIZES,
    annual_harvest_potential,
    build_plan,
    co2_savings,
    delete_harvest_plan,
    demand_coverage,
    demand_from_water_assessment,
    estimate_household_demand,
    get_climate_profile,
    get_harvest_plans,
    get_harvesting_tips,
    get_runoff_coefficient,
    list_roof_materials,
    monthly_harvest,
    recommend_tank_size,
    save_harvest_plan,
    savings_estimate,
    simulate_storage,
)


@pytest.fixture(autouse=True)
def temp_db():
    """Point the module at a throwaway SQLite file for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
        db_path = handle.name
    original = rainwater.DB_NAME
    rainwater.DB_NAME = db_path
    yield db_path
    rainwater.DB_NAME = original
    try:
        os.unlink(db_path)
    except OSError:
        pass


FLAT_RAINFALL = [50.0] * 12


# --------------------------------------------------------------------------
# Reference data
# --------------------------------------------------------------------------

def test_every_roof_material_has_a_sane_runoff_coefficient():
    for name, info in ROOF_MATERIALS.items():
        assert 0 < info["runoff"] <= 1.0, name
        assert info["note"], name


def test_metal_is_the_best_harvesting_surface():
    assert list_roof_materials()[0]["name"] == "Metal / corrugated sheet"


def test_green_roof_is_the_worst_harvesting_surface():
    assert list_roof_materials()[-1]["name"] == "Green roof"


def test_unknown_roof_material_falls_back_to_concrete():
    assert get_runoff_coefficient("Thatch") == ROOF_MATERIALS["Concrete / RCC"]["runoff"]
    assert get_runoff_coefficient(None) == ROOF_MATERIALS["Concrete / RCC"]["runoff"]


def test_every_climate_zone_has_twelve_months():
    for zone, profile in CLIMATE_ZONES.items():
        assert len(profile) == 12, zone
        assert all(value >= 0 for value in profile), zone


def test_unknown_climate_zone_falls_back_to_the_default():
    assert get_climate_profile("Martian") == CLIMATE_ZONES[DEFAULT_CLIMATE_ZONE]


def test_climate_profiles_are_returned_as_copies():
    profile = get_climate_profile("Semi-arid")
    profile[0] = 9999
    assert CLIMATE_ZONES["Semi-arid"][0] != 9999


# --------------------------------------------------------------------------
# Harvest maths
# --------------------------------------------------------------------------

def test_annual_harvest_matches_the_design_formula():
    expected = 100 * 600 * ROOF_MATERIALS["Metal / corrugated sheet"]["runoff"] * SYSTEM_EFFICIENCY
    assert annual_harvest_potential(100, 600, "Metal / corrugated sheet") == pytest.approx(
        expected, abs=0.1
    )


def test_one_mm_over_one_square_metre_is_one_litre_before_losses():
    # 1 mm of rain over 1 m2 is 1 litre, less the runoff and system losses.
    litres_per_m2 = annual_harvest_potential(1000, 1, "Metal / corrugated sheet") / 1000
    assert litres_per_m2 == pytest.approx(
        ROOF_MATERIALS["Metal / corrugated sheet"]["runoff"] * SYSTEM_EFFICIENCY, abs=0.001
    )


def test_harvest_scales_linearly_with_roof_area():
    small = annual_harvest_potential(50, 800, "Concrete / RCC")
    large = annual_harvest_potential(100, 800, "Concrete / RCC")
    assert large == pytest.approx(small * 2, abs=0.1)


def test_a_better_roof_harvests_more():
    metal = annual_harvest_potential(100, 800, "Metal / corrugated sheet")
    green = annual_harvest_potential(100, 800, "Green roof")
    assert metal > green


def test_zero_and_negative_inputs_harvest_nothing():
    assert annual_harvest_potential(0, 800, "Concrete / RCC") == 0.0
    assert annual_harvest_potential(-50, 800, "Concrete / RCC") == 0.0
    assert annual_harvest_potential(100, -800, "Concrete / RCC") == 0.0


def test_garbage_inputs_harvest_nothing():
    assert annual_harvest_potential("big", 800, "Concrete / RCC") == 0.0
    assert annual_harvest_potential(100, None, "Concrete / RCC") == 0.0


def test_monthly_harvest_has_twelve_months_summing_to_the_annual_figure():
    series = monthly_harvest(100, FLAT_RAINFALL, "Metal / corrugated sheet")
    assert len(series) == 12
    assert sum(series) == pytest.approx(
        annual_harvest_potential(100, sum(FLAT_RAINFALL), "Metal / corrugated sheet"),
        abs=1.0,
    )


def test_short_rainfall_series_is_padded():
    series = monthly_harvest(100, [50, 50, 50], "Concrete / RCC")
    assert len(series) == 12
    assert series[5] == 0.0


def test_long_rainfall_series_is_truncated():
    assert len(monthly_harvest(100, [50] * 20, "Concrete / RCC")) == 12


def test_missing_rainfall_series_harvests_nothing():
    assert monthly_harvest(100, None, "Concrete / RCC") == [0.0] * 12


# --------------------------------------------------------------------------
# Demand
# --------------------------------------------------------------------------

def test_household_demand_scales_with_people():
    one = estimate_household_demand(1)
    four = estimate_household_demand(4)
    assert sum(four) == pytest.approx(sum(one) * 4, abs=1.0)


def test_household_demand_matches_the_per_person_baseline():
    demand = estimate_household_demand(2)
    assert demand[0] == pytest.approx(
        2 * LITRES_PER_PERSON_PER_DAY * DAYS_IN_MONTH[0], abs=0.5
    )


def test_a_garden_increases_demand():
    assert sum(estimate_household_demand(2, 50)) > sum(estimate_household_demand(2, 0))


def test_a_seasonal_garden_profile_shifts_demand_between_months():
    profile = [0.0] * 5 + [3.0] * 3 + [0.0] * 4
    demand = estimate_household_demand(2, 100, profile)
    assert demand[6] > demand[0]
    assert len(demand) == 12


def test_an_invalid_garden_profile_is_ignored():
    assert estimate_household_demand(2, 50, [1.0, 2.0]) == estimate_household_demand(2, 50)


def test_demand_from_a_saved_water_assessment():
    demand = demand_from_water_assessment({"total_liters": 300}, people=2)
    assert demand[0] == pytest.approx(300 * DAYS_IN_MONTH[0], abs=0.5)
    assert len(demand) == 12


def test_demand_falls_back_when_no_assessment_exists():
    assert demand_from_water_assessment(None, people=2) == estimate_household_demand(2)
    assert demand_from_water_assessment({}, people=2) == estimate_household_demand(2)


# --------------------------------------------------------------------------
# Storage simulation invariants
# --------------------------------------------------------------------------

def test_storage_never_goes_negative_or_exceeds_capacity():
    simulation = simulate_storage(2000, monthly_harvest(100, FLAT_RAINFALL, "Concrete / RCC"),
                                  estimate_household_demand(3))
    for month in simulation["months"]:
        assert 0 <= month["stored_l"] <= 2000 + 0.01


def test_the_water_balance_is_conserved():
    harvest = monthly_harvest(120, CLIMATE_ZONES["Temperate maritime"], "Metal / corrugated sheet")
    simulation = simulate_storage(3000, harvest, estimate_household_demand(3, 20))
    final_stored = simulation["months"][-1]["stored_l"]
    accounted = (
        simulation["total_supplied_l"] + simulation["total_overflow_l"] + final_stored
    )
    assert accounted == pytest.approx(simulation["total_harvest_l"], abs=1.0)


def test_supplied_never_exceeds_demand():
    simulation = simulate_storage(50000, monthly_harvest(500, FLAT_RAINFALL, "Metal / corrugated sheet"),
                                  estimate_household_demand(1))
    assert simulation["total_supplied_l"] <= simulation["total_demand_l"] + 0.01
    for month in simulation["months"]:
        assert month["supplied_l"] <= month["demand_l"] + 0.01


def test_supplied_plus_shortfall_equals_demand():
    simulation = simulate_storage(1000, monthly_harvest(60, FLAT_RAINFALL, "Concrete / RCC"),
                                  estimate_household_demand(4))
    assert simulation["total_supplied_l"] + simulation["total_shortfall_l"] == pytest.approx(
        simulation["total_demand_l"], abs=1.0
    )


def test_coverage_is_bounded_between_zero_and_one_hundred():
    generous = simulate_storage(50000, monthly_harvest(1000, FLAT_RAINFALL, "Metal / corrugated sheet"),
                                estimate_household_demand(1))
    meagre = simulate_storage(500, monthly_harvest(5, FLAT_RAINFALL, "Green roof"),
                              estimate_household_demand(6))
    assert 0 <= meagre["coverage_pct"] <= 100
    assert 0 <= generous["coverage_pct"] <= 100
    assert generous["coverage_pct"] > meagre["coverage_pct"]


def test_a_tiny_tank_overflows():
    simulation = simulate_storage(100, monthly_harvest(200, FLAT_RAINFALL, "Metal / corrugated sheet"),
                                  [0.0] * 12)
    assert simulation["total_overflow_l"] > 0
    assert simulation["overflow_months"]


def test_no_demand_means_no_supply_and_no_shortfall():
    simulation = simulate_storage(5000, monthly_harvest(100, FLAT_RAINFALL, "Concrete / RCC"),
                                  [0.0] * 12)
    assert simulation["total_supplied_l"] == 0.0
    assert simulation["total_shortfall_l"] == 0.0
    assert simulation["coverage_pct"] == 0.0


def test_no_harvest_means_a_total_shortfall():
    demand = estimate_household_demand(2)
    simulation = simulate_storage(5000, [0.0] * 12, demand)
    assert simulation["total_supplied_l"] == 0.0
    assert simulation["total_shortfall_l"] == pytest.approx(sum(demand), abs=1.0)
    assert len(simulation["shortfall_months"]) == 12


def test_a_zero_capacity_tank_still_supplies_same_month_rain():
    simulation = simulate_storage(0, [1000.0] * 12, [500.0] * 12)
    assert simulation["total_supplied_l"] == pytest.approx(6000.0, abs=1.0)
    assert simulation["total_overflow_l"] == pytest.approx(6000.0, abs=1.0)


def test_simulation_always_reports_twelve_named_months():
    simulation = simulate_storage(1000, None, None)
    assert [month["month"] for month in simulation["months"]] == MONTHS


def test_negative_harvest_and_demand_are_treated_as_zero():
    simulation = simulate_storage(1000, [-500.0] * 12, [-200.0] * 12)
    assert simulation["total_harvest_l"] == 0.0
    assert simulation["total_demand_l"] == 0.0


# --------------------------------------------------------------------------
# Tank sizing
# --------------------------------------------------------------------------

def test_recommendation_picks_a_real_candidate():
    harvest = monthly_harvest(120, CLIMATE_ZONES["Mediterranean"], "Metal / corrugated sheet")
    result = recommend_tank_size(harvest, estimate_household_demand(3, 20))
    assert result["recommended"]["tank_litres"] in TANK_SIZES
    assert len(result["options"]) == len(TANK_SIZES)


def test_bigger_tanks_never_cover_less():
    harvest = monthly_harvest(120, CLIMATE_ZONES["Tropical monsoon"], "Metal / corrugated sheet")
    options = recommend_tank_size(harvest, estimate_household_demand(4, 30))["options"]
    values = [option["coverage_pct"] for option in options]
    assert values == sorted(values)


def test_the_recommendation_is_close_to_the_best_achievable_coverage():
    harvest = monthly_harvest(150, CLIMATE_ZONES["Continental"], "Glazed tile")
    result = recommend_tank_size(harvest, estimate_household_demand(3, 15))
    assert result["recommended"]["coverage_pct"] >= result["best_coverage_pct"] - 2.0


def test_the_recommendation_is_the_smallest_tank_that_qualifies():
    harvest = monthly_harvest(150, CLIMATE_ZONES["Continental"], "Glazed tile")
    result = recommend_tank_size(harvest, estimate_household_demand(3, 15))
    recommended = result["recommended"]["tank_litres"]
    smaller = [
        option for option in result["options"]
        if option["tank_litres"] < recommended
        and option["coverage_pct"] >= result["best_coverage_pct"] - 2.0
    ]
    assert smaller == []


def test_recommendation_with_no_candidates():
    result = recommend_tank_size([100.0] * 12, [100.0] * 12, candidates=[])
    assert result["recommended"] is None
    assert result["options"] == []


# --------------------------------------------------------------------------
# Coverage, savings and carbon
# --------------------------------------------------------------------------

def test_demand_coverage_percentage():
    assert demand_coverage(500, 1000) == 50.0
    assert demand_coverage(1500, 1000) == 100.0
    assert demand_coverage(0, 1000) == 0.0


def test_demand_coverage_with_no_demand():
    assert demand_coverage(500, 0) == 0.0
    assert demand_coverage(None, None) == 0.0


def test_savings_and_payback_maths():
    result = savings_estimate(50000, water_price_per_kl=2.0, tank_litres=2000, install_cost=400)
    assert result["annual_saving"] == pytest.approx(100.0, abs=0.01)
    assert result["tank_cost"] == pytest.approx(2000 * TANK_COST_PER_LITRE, abs=0.01)
    assert result["setup_cost"] == pytest.approx(result["tank_cost"] + 400, abs=0.01)
    assert result["payback_years"] == pytest.approx(
        result["setup_cost"] / result["annual_saving"], abs=0.05
    )


def test_no_saving_means_no_payback():
    assert savings_estimate(0, 2.0, 2000, 400)["payback_years"] is None
    assert savings_estimate(50000, 0.0, 2000, 400)["payback_years"] is None


def test_a_free_system_pays_back_immediately():
    result = savings_estimate(50000, 2.0, tank_litres=0, install_cost=0)
    assert result["setup_cost"] == 0.0
    assert result["payback_years"] == 0.0


def test_ten_year_net_reflects_the_setup_cost():
    result = savings_estimate(50000, 2.0, 2000, 400)
    assert result["ten_year_net"] == pytest.approx(
        result["annual_saving"] * 10 - result["setup_cost"], abs=0.05
    )


def test_carbon_savings_scale_with_water():
    small = co2_savings(10000)
    large = co2_savings(100000)
    assert large["annual_kg"] == pytest.approx(small["annual_kg"] * 10, abs=0.05)
    assert large["ten_year_kg"] == pytest.approx(large["annual_kg"] * 10, abs=0.05)
    assert large["tree_equivalent"] > 0


def test_carbon_savings_with_no_water():
    assert co2_savings(0)["annual_kg"] == 0.0
    assert co2_savings(None)["annual_kg"] == 0.0


def test_treatment_intensity_can_be_overridden():
    assert co2_savings(10000, 0.001)["annual_kg"] > co2_savings(10000, DEFAULT_TREATMENT_INTENSITY)["annual_kg"]


# --------------------------------------------------------------------------
# Full plan
# --------------------------------------------------------------------------

def test_build_plan_produces_a_complete_result():
    plan = build_plan(100, "Metal / corrugated sheet", "Temperate maritime", people=3, garden_m2=20)
    assert plan["annual_harvest_l"] > 0
    assert plan["tank_litres"] in TANK_SIZES
    assert len(plan["monthly_harvest_l"]) == 12
    assert len(plan["monthly_demand_l"]) == 12
    assert plan["simulation"]["coverage_pct"] >= 0
    assert plan["savings"]["setup_cost"] > 0
    assert plan["carbon"]["annual_kg"] >= 0


def test_build_plan_honours_a_chosen_tank_size():
    plan = build_plan(100, "Concrete / RCC", tank_litres=5000)
    assert plan["tank_litres"] == 5000
    assert plan["simulation"]["tank_litres"] == 5000


def test_build_plan_uses_custom_rainfall_when_given():
    default_plan = build_plan(100, "Concrete / RCC", "Semi-arid")
    custom_plan = build_plan(100, "Concrete / RCC", "Semi-arid", monthly_rainfall_mm=[200.0] * 12)
    assert custom_plan["annual_rainfall_mm"] == pytest.approx(2400.0, abs=0.5)
    assert custom_plan["annual_harvest_l"] > default_plan["annual_harvest_l"]


def test_build_plan_normalises_invalid_inputs():
    plan = build_plan(100, "Thatch", "Martian")
    assert plan["roof_material"] == "Concrete / RCC"
    assert plan["climate_zone"] == DEFAULT_CLIMATE_ZONE


def test_a_wetter_climate_harvests_more():
    monsoon = build_plan(100, "Metal / corrugated sheet", "Tropical monsoon")
    arid = build_plan(100, "Metal / corrugated sheet", "Semi-arid")
    assert monsoon["annual_harvest_l"] > arid["annual_harvest_l"]


# --------------------------------------------------------------------------
# Tips
# --------------------------------------------------------------------------

def test_tips_call_out_a_dry_season_shortfall():
    plan = build_plan(30, "Green roof", "Mediterranean", people=6, garden_m2=100)
    assert any("run dry" in tip for tip in get_harvesting_tips(plan))


def test_tips_call_out_heavy_overflow():
    plan = build_plan(400, "Metal / corrugated sheet", "Tropical monsoon",
                      people=1, garden_m2=0, tank_litres=500)
    assert any("overflowing" in tip for tip in get_harvesting_tips(plan))


def test_tips_always_include_the_first_flush_advice():
    plan = build_plan(100, "Metal / corrugated sheet", "Temperate maritime")
    assert any("first-flush" in tip for tip in get_harvesting_tips(plan, limit=10))


def test_tips_for_a_plan_with_no_demand():
    plan = build_plan(100, "Concrete / RCC", people=0, garden_m2=0)
    tips = get_harvesting_tips(plan)
    assert len(tips) == 1
    assert "Enter your roof size" in tips[0]


def test_tip_limit_is_respected():
    plan = build_plan(100, "Metal / corrugated sheet", "Temperate maritime")
    assert len(get_harvesting_tips(plan, limit=2)) == 2


# --------------------------------------------------------------------------
# Persistence
# --------------------------------------------------------------------------

def test_save_and_load_a_plan():
    plan = build_plan(100, "Metal / corrugated sheet", "Temperate maritime", people=3)
    plan_id = save_harvest_plan(1, "Back roof", plan)
    assert plan_id

    saved = get_harvest_plans(1)
    assert len(saved) == 1
    assert saved[0]["plan_name"] == "Back roof"
    assert saved[0]["roof_material"] == "Metal / corrugated sheet"
    assert saved[0]["annual_harvest_l"] == pytest.approx(plan["annual_harvest_l"], abs=0.1)
    assert len(saved[0]["series"]["monthly_harvest_l"]) == 12


def test_plans_are_scoped_per_user():
    plan = build_plan(100, "Concrete / RCC")
    save_harvest_plan(1, "Mine", plan)
    save_harvest_plan(2, "Theirs", plan)
    assert len(get_harvest_plans(1)) == 1
    assert get_harvest_plans(99) == []


def test_an_unnamed_plan_gets_a_default_name():
    save_harvest_plan(1, "", build_plan(100, "Concrete / RCC"))
    assert get_harvest_plans(1)[0]["plan_name"] == "My roof"


def test_the_plan_limit_is_respected():
    plan = build_plan(100, "Concrete / RCC")
    for index in range(4):
        save_harvest_plan(1, f"Plan {index}", plan)
    assert len(get_harvest_plans(1, limit=2)) == 2


def test_delete_a_plan():
    plan_id = save_harvest_plan(1, "Temp", build_plan(100, "Concrete / RCC"))
    assert delete_harvest_plan(plan_id) is True
    assert get_harvest_plans(1) == []
    assert delete_harvest_plan(plan_id) is False


def test_a_plan_with_no_payback_saves_cleanly():
    plan = build_plan(100, "Concrete / RCC", water_price_per_kl=0.0)
    assert plan["savings"]["payback_years"] is None
    save_harvest_plan(1, "Free water", plan)
    assert get_harvest_plans(1)[0]["payback_years"] is None
