"""Tests for device lifecycle carbon and e-waste guidance."""
import os
import datetime
import tempfile

import pytest

os.environ["ECO_BUDDY_DB"] = ":memory:"

import device_lifecycle
from device_lifecycle import (
    DEFAULT_EFFICIENCY_GAIN,
    DEFAULT_GRID_INTENSITY,
    DEVICE_CONDITIONS,
    DEVICE_TYPES,
    DISPOSAL_ROUTES,
    annualized_footprint,
    delete_device,
    disposal_guidance,
    extension_savings,
    get_device_type,
    get_devices,
    get_lifecycle_tips,
    lifetime_footprint,
    list_device_types,
    operating_emissions,
    portfolio_summary,
    register_device,
    remaining_life,
    repair_vs_replace,
    retire_device,
    update_device,
    upgrade_break_even,
    years_owned,
)

FIXED_TODAY = datetime.date(2026, 8, 1)


@pytest.fixture(autouse=True)
def temp_db():
    """Throwaway database and a frozen 'today' so age maths is deterministic."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
        db_path = handle.name
    original_db = device_lifecycle.DB_NAME
    device_lifecycle.DB_NAME = db_path
    device_lifecycle.TODAY_OVERRIDE = FIXED_TODAY
    yield db_path
    device_lifecycle.DB_NAME = original_db
    device_lifecycle.TODAY_OVERRIDE = None
    try:
        os.unlink(db_path)
    except OSError:
        pass


def laptop(purchase_year=2022, **overrides):
    device = {
        "name": "Work laptop",
        "device_type": "Laptop",
        "purchase_year": purchase_year,
        "quantity": 1,
        "condition": "Working",
    }
    device.update(overrides)
    return device


# --------------------------------------------------------------------------
# Catalogue integrity
# --------------------------------------------------------------------------

def test_every_device_type_has_valid_reference_data():
    for name, info in DEVICE_TYPES.items():
        assert info["embodied_kg"] > 0, name
        assert info["typical_watts"] >= 0, name
        assert 0 < info["daily_hours"] <= 24, name
        assert info["lifespan_years"] > 0, name
        assert info["recyclable_kg"] > 0, name
        assert 1 <= info["repairability"] <= 10, name


def test_list_and_get_device_types():
    types = list_device_types()
    assert len(types) == len(DEVICE_TYPES)
    assert get_device_type("Laptop")["embodied_kg"] == DEVICE_TYPES["Laptop"]["embodied_kg"]
    assert get_device_type("Toaster") is None


def test_disposal_routes_are_all_described():
    for key, route in DISPOSAL_ROUTES.items():
        assert route["label"] and route["detail"] and route["icon"], key


# --------------------------------------------------------------------------
# Age
# --------------------------------------------------------------------------

def test_years_owned_uses_the_frozen_today():
    assert years_owned(2022) == 4.0


def test_a_device_bought_this_year_is_never_zero_years_old():
    assert years_owned(FIXED_TODAY.year) == 0.5


def test_future_and_garbage_purchase_years_are_clamped():
    assert years_owned(3000) == 0.5
    assert years_owned("last Tuesday") == 0.5
    assert years_owned(1800) == float(FIXED_TODAY.year - 1990)


# --------------------------------------------------------------------------
# Operating emissions
# --------------------------------------------------------------------------

def test_operating_emissions_match_a_hand_calculation():
    expected = DEVICE_TYPES["Laptop"]["typical_watts"] / 1000 * 6 * 365 * 0.5
    assert operating_emissions("Laptop", 6, 0.5) == pytest.approx(expected, abs=0.01)


def test_operating_emissions_default_to_catalogue_hours():
    assert operating_emissions("Laptop") == operating_emissions(
        "Laptop", DEVICE_TYPES["Laptop"]["daily_hours"], DEFAULT_GRID_INTENSITY
    )


def test_operating_hours_are_clamped_to_a_day():
    assert operating_emissions("Laptop", 999) == operating_emissions("Laptop", 24)
    assert operating_emissions("Laptop", -5) == 0.0


def test_unknown_device_type_raises():
    with pytest.raises(KeyError):
        operating_emissions("Toaster", 1)


# --------------------------------------------------------------------------
# Annualised footprint
# --------------------------------------------------------------------------

def test_annualized_footprint_amortises_embodied_carbon():
    result = annualized_footprint(laptop(2022))
    expected_amortised = DEVICE_TYPES["Laptop"]["embodied_kg"] / 4.0
    assert result["amortised_embodied_kg"] == pytest.approx(expected_amortised, abs=0.01)
    assert result["annual_kg"] == pytest.approx(
        result["amortised_embodied_kg"] + result["operating_kg"], abs=0.02
    )


def test_keeping_a_device_longer_lowers_its_annual_footprint():
    newer = annualized_footprint(laptop(2025))
    older = annualized_footprint(laptop(2018))
    assert older["annual_kg"] < newer["annual_kg"]


def test_quantity_scales_both_embodied_and_operating():
    single = annualized_footprint(laptop(2022, quantity=1))
    triple = annualized_footprint(laptop(2022, quantity=3))
    assert triple["embodied_kg"] == pytest.approx(single["embodied_kg"] * 3, abs=0.01)
    assert triple["operating_kg"] == pytest.approx(single["operating_kg"] * 3, abs=0.01)


def test_past_lifespan_flag():
    assert annualized_footprint(laptop(2026))["past_lifespan"] is False
    assert annualized_footprint(laptop(2015))["past_lifespan"] is True


def test_embodied_share_is_a_percentage():
    result = annualized_footprint(laptop(2022))
    assert 0 <= result["embodied_share_pct"] <= 100


def test_a_brand_new_device_does_not_divide_by_zero():
    result = annualized_footprint(laptop(FIXED_TODAY.year))
    assert result["years_owned"] == 0.5
    assert result["annual_kg"] > 0


def test_annualized_footprint_rejects_unknown_types():
    with pytest.raises(KeyError):
        annualized_footprint({"device_type": "Toaster", "purchase_year": 2022})


# --------------------------------------------------------------------------
# Lifetime and remaining life
# --------------------------------------------------------------------------

def test_lifetime_footprint_is_embodied_plus_operating_over_the_lifespan():
    result = lifetime_footprint(laptop(2022))
    info = DEVICE_TYPES["Laptop"]
    assert result["embodied_kg"] == info["embodied_kg"]
    assert result["lifetime_total_kg"] == pytest.approx(
        result["embodied_kg"] + result["lifetime_operating_kg"], abs=0.02
    )


def test_manufacturing_dominates_a_smartphone_lifetime():
    result = lifetime_footprint({"device_type": "Smartphone", "purchase_year": 2024})
    assert result["embodied_share_pct"] > 70


def test_remaining_life_counts_down():
    life = remaining_life(laptop(2024))
    assert life["years_remaining"] == pytest.approx(3.0, abs=0.01)
    assert life["past_lifespan"] is False


def test_remaining_life_bottoms_out_at_zero():
    life = remaining_life(laptop(2010))
    assert life["years_remaining"] == 0.0
    assert life["past_lifespan"] is True
    assert life["life_used_pct"] == 100.0


# --------------------------------------------------------------------------
# Repair vs replace
# --------------------------------------------------------------------------

def test_repairing_beats_replacing_for_a_like_for_like_device():
    result = repair_vs_replace(laptop(2021), repair_extends_years=3)
    assert result["verdict"] == "repair"
    assert result["difference_kg"] > 0
    assert "avoids" in result["message"]


def test_replacing_can_win_for_a_very_power_hungry_device():
    result = repair_vs_replace(
        {"device_type": "Desktop PC", "daily_hours": 24},
        repair_extends_years=8,
        replacement_type="Laptop",
        efficiency_gain=0.5,
    )
    assert result["verdict"] == "replace"
    assert result["difference_kg"] < 0


def test_a_longer_horizon_narrows_repairs_advantage():
    # A more efficient replacement gets more time to pay back its
    # manufacturing debt, so repair's lead shrinks as the horizon grows.
    short = repair_vs_replace(laptop(2021), 1)
    long = repair_vs_replace(laptop(2021), 6)
    assert long["difference_kg"] < short["difference_kg"]
    assert short["verdict"] == long["verdict"] == "repair"


def test_a_replacement_with_no_efficiency_gain_never_catches_up():
    short = repair_vs_replace(laptop(2021), 1, efficiency_gain=0.0)
    long = repair_vs_replace(laptop(2021), 20, efficiency_gain=0.0)
    assert short["difference_kg"] == pytest.approx(long["difference_kg"], abs=0.05)


def test_no_efficiency_gain_means_no_break_even():
    result = repair_vs_replace(laptop(2021), 3, efficiency_gain=0.0)
    assert result["break_even_years"] is None


def test_efficiency_gain_is_clamped():
    result = repair_vs_replace(laptop(2021), 3, efficiency_gain=5.0)
    assert result["efficiency_gain"] <= 0.9
    assert repair_vs_replace(laptop(2021), 3, efficiency_gain=-1)["efficiency_gain"] == 0.0


def test_repair_horizon_has_a_floor():
    assert repair_vs_replace(laptop(2021), 0)["horizon_years"] == 0.5
    assert repair_vs_replace(laptop(2021), None)["horizon_years"] == 0.5


def test_repair_vs_replace_rejects_unknown_types():
    with pytest.raises(KeyError):
        repair_vs_replace({"device_type": "Toaster"}, 3)
    with pytest.raises(KeyError):
        repair_vs_replace(laptop(2021), 3, replacement_type="Toaster")


def test_repairability_is_surfaced_in_the_verdict():
    result = repair_vs_replace(laptop(2021), 3)
    assert result["repairability"] == DEVICE_TYPES["Laptop"]["repairability"]


# --------------------------------------------------------------------------
# Upgrade break-even
# --------------------------------------------------------------------------

def test_break_even_years_are_positive_when_the_new_device_is_more_efficient():
    result = upgrade_break_even("Desktop PC", "Laptop", 8, 0.3)
    assert result["break_even_years"] > 0
    assert result["annual_saving_kg"] > 0


def test_no_saving_means_the_upgrade_never_pays_back():
    result = upgrade_break_even("Laptop", "Desktop PC", 6, 0.0)
    assert result["break_even_years"] is None
    assert result["ever_pays_back"] is False
    assert "never repays" in result["message"]


def test_a_slow_payback_is_flagged_as_not_worth_it():
    result = upgrade_break_even("Smart speaker", "Television", 1, 0.05)
    assert result["ever_pays_back"] is False


def test_upgrade_break_even_rejects_unknown_types():
    with pytest.raises(KeyError):
        upgrade_break_even("Toaster", "Laptop")


# --------------------------------------------------------------------------
# Disposal guidance
# --------------------------------------------------------------------------

def test_a_healthy_in_life_device_should_be_kept():
    assert disposal_guidance(laptop(2024, condition="Working"))["route"] == "keep"


def test_a_working_but_old_device_should_be_passed_on():
    assert disposal_guidance(laptop(2015, condition="Working"))["route"] == "resell"


def test_a_degraded_in_life_device_should_be_repaired():
    assert disposal_guidance(laptop(2024, condition="Degraded"))["route"] == "repair"


def test_a_degraded_old_device_should_be_donated():
    assert disposal_guidance(laptop(2012, condition="Degraded"))["route"] == "donate"


def test_a_faulty_repairable_device_goes_to_repair():
    guidance = disposal_guidance(laptop(2024, condition="Faulty"))
    assert guidance["route"] == "repair"
    assert DEVICE_TYPES["Laptop"]["repairability"] >= 5


def test_a_faulty_unrepairable_device_goes_to_recycling():
    guidance = disposal_guidance(
        {"device_type": "Smart speaker", "purchase_year": 2024, "condition": "Faulty"}
    )
    assert guidance["route"] == "recycle"


def test_a_dead_device_always_goes_to_recycling():
    assert disposal_guidance(laptop(2024, condition="Dead"))["route"] == "recycle"


def test_battery_devices_carry_a_hazard_warning():
    assert disposal_guidance(laptop(2024))["warning"] is not None
    router = disposal_guidance(
        {"device_type": "Router", "purchase_year": 2024, "condition": "Dead"}
    )
    assert router["warning"] is None


def test_unknown_condition_falls_back_to_working():
    guidance = disposal_guidance(laptop(2024, condition="Haunted"))
    assert guidance["condition"] == "Working"


def test_disposal_guidance_rejects_unknown_types():
    with pytest.raises(KeyError):
        disposal_guidance({"device_type": "Toaster", "purchase_year": 2020})


# --------------------------------------------------------------------------
# Portfolio and extension savings
# --------------------------------------------------------------------------

def test_portfolio_totals_match_the_individual_devices():
    devices = [laptop(2022), {"device_type": "Smartphone", "purchase_year": 2025}]
    summary = portfolio_summary(devices)
    assert summary["device_count"] == 2
    assert summary["total_annual_kg"] == pytest.approx(
        sum(row["annual_kg"] for row in summary["devices"]), abs=0.05
    )
    assert summary["total_embodied_kg"] == pytest.approx(
        DEVICE_TYPES["Laptop"]["embodied_kg"] + DEVICE_TYPES["Smartphone"]["embodied_kg"],
        abs=0.01,
    )


def test_portfolio_is_ranked_and_shares_add_up():
    summary = portfolio_summary([laptop(2022), {"device_type": "Television", "purchase_year": 2025}])
    values = [row["annual_kg"] for row in summary["devices"]]
    assert values == sorted(values, reverse=True)
    assert sum(row["share_pct"] for row in summary["devices"]) == pytest.approx(100.0, abs=0.5)
    assert summary["heaviest"] == summary["devices"][0]["name"]


def test_portfolio_counts_devices_past_their_lifespan():
    summary = portfolio_summary([laptop(2010), laptop(2025)])
    assert summary["past_lifespan_count"] == 1


def test_portfolio_skips_unknown_device_types():
    summary = portfolio_summary([laptop(2022), {"device_type": "Toaster", "purchase_year": 2020}])
    assert summary["device_count"] == 1


def test_empty_portfolio_is_all_zeros():
    summary = portfolio_summary([])
    assert summary["device_count"] == 0
    assert summary["total_annual_kg"] == 0.0
    assert summary["heaviest"] is None
    assert portfolio_summary(None)["device_count"] == 0


def test_extending_ownership_lowers_the_annualised_total():
    devices = [laptop(2022), {"device_type": "Smartphone", "purchase_year": 2024}]
    extension = extension_savings(devices, 2)
    assert extension["extended_annual_kg"] < extension["current_annual_kg"]
    assert extension["saved_annual_kg"] > 0
    assert 0 < extension["saved_pct"] < 100


def test_extending_by_zero_years_saves_nothing():
    extension = extension_savings([laptop(2022)], 0)
    assert extension["saved_annual_kg"] == pytest.approx(0.0, abs=0.01)


def test_longer_extensions_save_more():
    devices = [laptop(2022)]
    assert (
        extension_savings(devices, 4)["saved_annual_kg"]
        > extension_savings(devices, 1)["saved_annual_kg"]
    )


def test_extension_savings_with_no_devices():
    extension = extension_savings([], 3)
    assert extension["current_annual_kg"] == 0.0
    assert extension["saved_pct"] == 0.0


# --------------------------------------------------------------------------
# Tips
# --------------------------------------------------------------------------

def test_tips_call_out_devices_past_their_lifespan():
    tips = get_lifecycle_tips(portfolio_summary([laptop(2010)]))
    assert any("past their expected lifespan" in tip for tip in tips)


def test_tips_are_helpful_for_an_empty_portfolio():
    tips = get_lifecycle_tips(portfolio_summary([]))
    assert len(tips) == 1
    assert "Register your electronics" in tips[0]


def test_tip_limit_is_respected():
    assert len(get_lifecycle_tips(portfolio_summary([laptop(2022)]), limit=2)) == 2


# --------------------------------------------------------------------------
# Persistence
# --------------------------------------------------------------------------

def test_register_and_list_devices():
    device_id = register_device(1, "Work laptop", "Laptop", 2022, 1, 8.0, "Working")
    assert device_id

    devices = get_devices(1)
    assert len(devices) == 1
    assert devices[0]["name"] == "Work laptop"
    assert devices[0]["daily_hours"] == 8.0
    assert devices[0]["status"] == "active"


def test_registering_an_unknown_type_is_refused():
    assert register_device(1, "Toaster", "Toaster", 2022) is None
    assert get_devices(1) == []


def test_devices_are_scoped_per_user():
    register_device(1, "Mine", "Laptop", 2022)
    register_device(2, "Theirs", "Laptop", 2022)
    assert len(get_devices(1)) == 1
    assert get_devices(99) == []


def test_an_unnamed_device_falls_back_to_its_type():
    register_device(1, "", "Laptop", 2022)
    assert get_devices(1)[0]["name"] == "Laptop"


def test_purchase_year_is_clamped_on_write():
    register_device(1, "Time traveller", "Laptop", 3000)
    assert get_devices(1)[0]["purchase_year"] == FIXED_TODAY.year


def test_quantity_has_a_floor_of_one():
    register_device(1, "Laptop", "Laptop", 2022, quantity=0)
    assert get_devices(1)[0]["quantity"] == 1


def test_unknown_condition_falls_back_on_write():
    register_device(1, "Laptop", "Laptop", 2022, condition="Haunted")
    assert get_devices(1)[0]["condition"] == "Working"


def test_update_a_device():
    device_id = register_device(1, "Laptop", "Laptop", 2022)
    assert update_device(device_id, condition="Faulty", daily_hours=2.0, quantity=2) is True

    device = get_devices(1)[0]
    assert device["condition"] == "Faulty"
    assert device["daily_hours"] == 2.0
    assert device["quantity"] == 2


def test_update_with_nothing_to_change():
    device_id = register_device(1, "Laptop", "Laptop", 2022)
    assert update_device(device_id) is False


def test_update_ignores_an_invalid_condition():
    device_id = register_device(1, "Laptop", "Laptop", 2022)
    assert update_device(device_id, condition="Haunted") is False


def test_retire_a_device_keeps_its_history():
    device_id = register_device(1, "Laptop", "Laptop", 2022)
    assert retire_device(device_id) is True
    assert get_devices(1) == []

    retired = get_devices(1, include_retired=True)
    assert len(retired) == 1
    assert retired[0]["status"] == "retired"
    assert retired[0]["retired_at"] is not None


def test_retiring_twice_is_a_no_op():
    device_id = register_device(1, "Laptop", "Laptop", 2022)
    retire_device(device_id)
    assert retire_device(device_id) is False


def test_delete_a_device():
    device_id = register_device(1, "Laptop", "Laptop", 2022)
    assert delete_device(device_id) is True
    assert get_devices(1, include_retired=True) == []
    assert delete_device(device_id) is False


def test_saved_devices_feed_straight_into_the_portfolio():
    register_device(1, "Work laptop", "Laptop", 2022)
    register_device(1, "Phone", "Smartphone", 2025)
    summary = portfolio_summary(get_devices(1))
    assert summary["device_count"] == 2
    assert summary["total_annual_kg"] > 0


def test_every_condition_is_accepted_on_write():
    for index, condition in enumerate(DEVICE_CONDITIONS):
        register_device(1, f"Device {index}", "Laptop", 2022, condition=condition)
    stored = {device["condition"] for device in get_devices(1)}
    assert stored == set(DEVICE_CONDITIONS)


def test_default_efficiency_gain_is_sensible():
    assert 0 < DEFAULT_EFFICIENCY_GAIN < 1
