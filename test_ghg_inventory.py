"""Tests for the GHG Protocol Personal Inventory."""
import os
import tempfile

import pytest

os.environ["ECO_BUDDY_DB"] = ":memory:"

import ghg_inventory
from ghg_inventory import (
    ACTIVITY_CLASSIFICATION,
    CONSOLIDATION_APPROACHES,
    DEFAULT_CONSOLIDATION,
    DEFAULT_GRID_INTENSITY,
    DEFAULT_RESIDUAL_UPLIFT,
    DEFAULT_TARIFF,
    EXPECTED_ACTIVITIES,
    SCOPE_1,
    SCOPE_2,
    SCOPE_3,
    SCOPE_3_CATEGORIES,
    SIGNIFICANCE_THRESHOLD,
    InventoryError,
    assess_completeness,
    boundary_statement,
    build_inventory,
    classify,
    compare_to_base_year,
    delete_inventory,
    explain,
    export_inventory,
    get_inventories,
    get_scope_insights,
    list_activities,
    list_scope_3_categories,
    list_tariffs,
    recalculate_base_year,
    save_inventory,
    scope_2_dual,
    scope_of,
    total_under_method,
)


@pytest.fixture(autouse=True)
def temp_db():
    """Point the module at a throwaway SQLite file for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
        db_path = handle.name
    original = ghg_inventory.DB_NAME
    ghg_inventory.DB_NAME = db_path
    yield db_path
    ghg_inventory.DB_NAME = original
    try:
        os.unlink(db_path)
    except OSError:
        pass


def full_line_items(location_based=630.0, market_based=0.0):
    """A reasonably complete household inventory."""
    return [
        {"activity": "gas_heating", "emissions": 2400.0},
        {"activity": "petrol_vehicle", "emissions": 1800.0},
        {
            "activity": "electricity",
            "emissions": location_based,
            "location_based": location_based,
            "market_based": market_based,
        },
        {"activity": "food", "emissions": 2200.0},
        {"activity": "goods", "emissions": 1500.0},
        {"activity": "flights", "emissions": 900.0},
        {"activity": "waste", "emissions": 180.0},
        {"activity": "upstream_fuel", "emissions": 750.0},
    ]


# --- Classification ---------------------------------------------------------


def test_direct_combustion_is_scope_1():
    for activity in ("gas_heating", "oil_heating", "petrol_vehicle", "wood_burning"):
        assert scope_of(activity) == SCOPE_1


def test_purchased_energy_is_scope_2():
    for activity in ("electricity", "district_heating", "electric_vehicle_charging"):
        assert scope_of(activity) == SCOPE_2


def test_everything_bought_or_travelled_on_is_scope_3():
    for activity in ("food", "goods", "flights", "waste", "public_transport"):
        assert scope_of(activity) == SCOPE_3


def test_a_flight_is_not_scope_1_because_you_do_not_fly_the_plane():
    # The most commonly misfiled item in personal footprinting.
    assert scope_of("flights") == SCOPE_3
    assert "do not operate the aircraft" in classify("flights")["rationale"]


def test_an_electric_car_is_split_across_two_scopes():
    # Charging is purchased energy; the battery is embodied capital. A user
    # should be able to see why the same vehicle appears twice.
    assert scope_of("electric_vehicle_charging") == SCOPE_2
    assert "scope 3 capital goods" in classify("electric_vehicle_charging")["rationale"]


def test_refrigerant_leakage_is_recognised_as_scope_1():
    # Small in mass, large in warming potential, and almost always forgotten.
    assert scope_of("refrigerant_leakage") == SCOPE_1


def test_every_classification_carries_a_rationale():
    for activity in list_activities():
        assert activity["rationale"]
        assert activity["label"]
        assert activity["scope"] in (SCOPE_1, SCOPE_2, SCOPE_3)


def test_every_scope_3_line_has_a_category_and_no_other_scope_does():
    for activity in list_activities():
        if activity["scope"] == SCOPE_3:
            assert activity["category"] in SCOPE_3_CATEGORIES
        else:
            assert activity["category"] is None


def test_activities_can_be_filtered_by_scope():
    assert all(item["scope"] == SCOPE_1 for item in list_activities(scope=SCOPE_1))


def test_scope_3_categories_are_listed():
    categories = list_scope_3_categories()
    assert len(categories) == len(SCOPE_3_CATEGORIES)
    assert all(entry["label"] for entry in categories)


def test_an_unknown_activity_raises_rather_than_defaulting_to_scope_3():
    # Quietly filing an unmapped activity in the largest bucket would hide a
    # gap behind a plausible-looking total.
    with pytest.raises(InventoryError):
        classify("teleportation")
    with pytest.raises(InventoryError):
        scope_of("teleportation")


def test_explanations_are_human_readable():
    text = explain("electricity")
    assert "scope 2" in text
    assert "supplier" in text


# --- Dual scope 2 -----------------------------------------------------------


def test_location_based_uses_the_grid_average():
    result = scope_2_dual(3000, grid_intensity=0.21)
    assert result["location_based"] == pytest.approx(630.0)


def test_a_green_tariff_zeroes_the_market_figure_and_leaves_the_grid_one_alone():
    # The case the app could not previously express at all.
    result = scope_2_dual(3000, 0.21, tariff="Certified renewable tariff")
    assert result["market_based"] == pytest.approx(0.0)
    assert result["location_based"] == pytest.approx(630.0)
    assert "physical grid did not change" in result["explanation"]


def test_a_standard_tariff_is_penalised_by_the_residual_mix():
    # The part green tariff marketing never mentions: if others claim the
    # clean generation, what is left for everyone else is dirtier.
    result = scope_2_dual(3000, 0.21, tariff="Standard tariff")
    assert result["market_based"] > result["location_based"]
    assert result["market_based"] == pytest.approx(630.0 * DEFAULT_RESIDUAL_UPLIFT)
    assert result["uses_residual_mix"]
    assert "never mentions" in result["explanation"]


def test_a_partial_tariff_lands_between_the_two():
    partial = scope_2_dual(3000, 0.21, tariff="Partially renewable tariff")
    green = scope_2_dual(3000, 0.21, tariff="Certified renewable tariff")
    standard = scope_2_dual(3000, 0.21, tariff="Standard tariff")
    assert green["market_based"] < partial["market_based"] < standard["market_based"]


def test_an_explicit_market_intensity_overrides_the_tariff():
    result = scope_2_dual(3000, 0.21, tariff="Standard tariff", market_intensity=0.05)
    assert result["market_based"] == pytest.approx(150.0)
    assert not result["uses_residual_mix"]


def test_the_two_methods_can_agree():
    result = scope_2_dual(3000, 0.21, tariff="Standard tariff", residual_uplift=1.0)
    assert result["market_based"] == pytest.approx(result["location_based"])
    assert "Both methods" in result["explanation"]


def test_an_unknown_tariff_falls_back_to_the_standard_one():
    assert scope_2_dual(3000, 0.21, tariff="Magic tariff")["tariff"] == DEFAULT_TARIFF


def test_using_no_electricity_produces_no_scope_2():
    result = scope_2_dual(0, 0.21)
    assert result["location_based"] == 0.0
    assert result["market_based"] == 0.0


def test_scope_2_rejects_junk():
    with pytest.raises(InventoryError):
        scope_2_dual("lots", 0.21)
    with pytest.raises(InventoryError):
        scope_2_dual(-100, 0.21)
    with pytest.raises(InventoryError):
        scope_2_dual(3000, float("nan"))
    with pytest.raises(InventoryError):
        scope_2_dual(3000, 0.21, residual_uplift=0)


def test_tariffs_are_listed_with_descriptions():
    for tariff in list_tariffs():
        assert tariff["name"]
        assert tariff["description"]


# --- Inventory --------------------------------------------------------------


def test_inventory_sums_each_scope_separately():
    inventory = build_inventory(full_line_items(), reporting_period="2026")
    assert inventory["scope_1"] == pytest.approx(4200.0)
    assert inventory["scope_2"] == pytest.approx(630.0)
    assert inventory["scope_3"] == pytest.approx(5530.0)
    assert inventory["total"] == pytest.approx(10360.0)


def test_scope_shares_sum_to_one():
    inventory = build_inventory(full_line_items())
    assert sum(inventory["shares"].values()) == pytest.approx(1.0)


def test_the_headline_total_follows_the_declared_scope_2_method():
    location = build_inventory(full_line_items(), scope_2_method="location_based")
    market = build_inventory(full_line_items(), scope_2_method="market_based")
    assert location["scope_2"] == pytest.approx(630.0)
    assert market["scope_2"] == pytest.approx(0.0)
    assert market["total"] < location["total"]


def test_both_scope_2_figures_are_always_reported_whichever_is_headline():
    inventory = build_inventory(full_line_items(), scope_2_method="market_based")
    assert inventory["scope_2_location_based"] == pytest.approx(630.0)
    assert inventory["scope_2_market_based"] == pytest.approx(0.0)


def test_a_total_can_be_restated_under_the_other_method_without_rebuilding():
    inventory = build_inventory(full_line_items(), scope_2_method="location_based")
    assert total_under_method(inventory, "market_based") == pytest.approx(
        inventory["total"] - 630.0
    )
    assert total_under_method(inventory, "location_based") == pytest.approx(
        inventory["total"]
    )


def test_an_unrecognised_scope_2_method_defaults_to_location_based():
    inventory = build_inventory(full_line_items(), scope_2_method="vibes")
    assert inventory["scope_2_method"] == "location_based"


def test_scope_3_is_broken_out_by_category_largest_first():
    inventory = build_inventory(full_line_items())
    categories = list(inventory["scope_3_by_category"].items())
    assert categories[0][0] == "food"
    assert [value for _, value in categories] == sorted(
        [value for _, value in categories], reverse=True
    )


def test_lines_are_grouped_by_scope_then_ordered_by_size():
    inventory = build_inventory(full_line_items())
    scopes = [line["scope"] for line in inventory["lines"]]
    assert scopes == sorted(scopes)
    scope_1_lines = [line for line in inventory["lines"] if line["scope"] == SCOPE_1]
    assert scope_1_lines[0]["emissions"] >= scope_1_lines[-1]["emissions"]


def test_an_empty_inventory_is_refused():
    with pytest.raises(InventoryError):
        build_inventory([])
    with pytest.raises(InventoryError):
        build_inventory(None)


def test_an_inventory_with_an_unknown_activity_is_refused():
    with pytest.raises(InventoryError):
        build_inventory([{"activity": "teleportation", "emissions": 100}])


def test_an_inventory_rejects_junk_emissions():
    with pytest.raises(InventoryError):
        build_inventory([{"activity": "food", "emissions": "a lot"}])
    with pytest.raises(InventoryError):
        build_inventory([{"activity": "food", "emissions": -50}])


def test_an_inventory_of_zero_does_not_divide_by_zero():
    inventory = build_inventory([{"activity": "food", "emissions": 0.0}])
    assert inventory["total"] == 0.0
    assert inventory["shares"][SCOPE_3] == 0.0


# --- Boundary ---------------------------------------------------------------


def test_the_boundary_names_its_consolidation_approach_and_period():
    inventory = build_inventory(
        full_line_items(), reporting_period="2026", consolidation="financial_control"
    )
    boundary = inventory["boundary"]
    assert boundary["consolidation_approach"] == "financial_control"
    assert boundary["reporting_period"] == "2026"
    assert "financial control" in boundary["statement"]


def test_an_unstated_period_is_declared_as_unstated_rather_than_hidden():
    inventory = build_inventory(full_line_items())
    assert inventory["boundary"]["reporting_period"] == "not stated"


def test_the_boundary_lists_what_was_left_out():
    partial = [
        {"activity": "gas_heating", "emissions": 2400.0},
        {"activity": "electricity", "emissions": 630.0},
    ]
    boundary = build_inventory(partial)["boundary"]
    assert "Food and diet" in boundary["omitted"]
    assert "Waste and recycling" in boundary["omitted"]


def test_stated_exclusions_are_carried_through():
    inventory = build_inventory(
        full_line_items(), exclusions=["Second home", "Company car"]
    )
    assert "Second home" in inventory["boundary"]["stated_exclusions"]


def test_an_unknown_consolidation_approach_falls_back_to_the_default():
    inventory = build_inventory(full_line_items(), consolidation="vibes")
    assert inventory["consolidation"] == DEFAULT_CONSOLIDATION


def test_every_consolidation_approach_is_described():
    for description in CONSOLIDATION_APPROACHES.values():
        assert len(description) > 20


# --- Completeness -----------------------------------------------------------


def test_a_full_inventory_scores_well():
    completeness = build_inventory(full_line_items())["completeness"]
    assert completeness["rating"] in ("comprehensive", "good")
    assert completeness["score"] >= 0.8
    assert completeness["scopes_covered"] == [SCOPE_1, SCOPE_2, SCOPE_3]


def test_an_electricity_only_inventory_is_called_fragmentary_not_impressive():
    # The failure mode this exists to catch: a low total that means
    # under-reporting, not a small footprint.
    inventory = build_inventory([{"activity": "electricity", "emissions": 630.0}])
    completeness = inventory["completeness"]
    assert completeness["rating"] == "fragmentary"
    # It reports no scope 3 at all, which is the most severe thing wrong with
    # it and so the warning it gets.
    assert "badly understated" in completeness["warning"]


def test_missing_high_impact_categories_are_warned_about_once_scope_3_exists():
    inventory = build_inventory(
        [
            {"activity": "electricity", "emissions": 630.0},
            {"activity": "waste", "emissions": 180.0},
            {"activity": "upstream_fuel", "emissions": 750.0},
        ]
    )
    warning = inventory["completeness"]["warning"]
    assert "incomplete inventory, not a small footprint" in warning
    assert "food" in warning


def test_missing_high_impact_categories_are_named():
    inventory = build_inventory([{"activity": "gas_heating", "emissions": 2400.0}])
    completeness = inventory["completeness"]
    assert "Food and diet" in completeness["missing_high_impact"]
    assert "Purchased electricity" in completeness["missing_high_impact"]


def test_an_inventory_with_no_scope_3_is_flagged_as_badly_understated():
    inventory = build_inventory(
        [
            {"activity": "gas_heating", "emissions": 2400.0},
            {"activity": "electricity", "emissions": 630.0},
            {"activity": "food", "emissions": 2200.0},
            {"activity": "goods", "emissions": 1500.0},
            {"activity": "waste", "emissions": 180.0},
            {"activity": "upstream_fuel", "emissions": 750.0},
        ]
    )
    # This one *does* have scope 3, so it should not be flagged.
    assert "badly understated" not in (inventory["completeness"]["warning"] or "")

    scope_1_and_2_only = assess_completeness(
        [
            {"activity": "gas_heating", "scope": SCOPE_1},
            {"activity": "electricity", "scope": SCOPE_2},
            {"activity": "food", "scope": SCOPE_1},
            {"activity": "goods", "scope": SCOPE_1},
            {"activity": "waste", "scope": SCOPE_1},
            {"activity": "upstream_fuel", "scope": SCOPE_1},
        ]
    )
    assert "badly understated" in scope_1_and_2_only["warning"]


def test_completeness_score_is_bounded():
    assert 0.0 <= build_inventory(full_line_items())["completeness"]["score"] <= 1.0
    assert 0.0 <= assess_completeness([])["score"] <= 1.0


def test_a_complete_inventory_has_no_warning():
    items = full_line_items()
    completeness = build_inventory(items)["completeness"]
    if completeness["rating"] == "comprehensive":
        assert completeness["warning"] == ""


# --- Base year --------------------------------------------------------------


def test_a_significant_methodology_change_restates_the_base_year():
    result = recalculate_base_year(10000.0, 1200.0, reason="Added scope 3 food")
    assert result["is_significant"]
    assert result["restated_base_year"] == pytest.approx(11200.0)
    assert "restated" in result["explanation"]


def test_a_trivial_change_leaves_the_base_year_alone():
    # Restating for every small refinement would produce churn without meaning.
    result = recalculate_base_year(10000.0, 200.0)
    assert not result["is_significant"]
    assert result["restated_base_year"] == pytest.approx(10000.0)
    assert "left alone" in result["explanation"]


def test_the_significance_threshold_is_applied_at_the_boundary():
    exactly_at = recalculate_base_year(10000.0, 10000.0 * SIGNIFICANCE_THRESHOLD)
    assert exactly_at["is_significant"]


def test_a_downward_restatement_is_handled():
    result = recalculate_base_year(10000.0, -1500.0, reason="Removed double count")
    assert result["is_significant"]
    assert result["restated_base_year"] == pytest.approx(8500.0)


def test_recalculation_rejects_junk():
    with pytest.raises(InventoryError):
        recalculate_base_year("lots", 100)
    with pytest.raises(InventoryError):
        recalculate_base_year(10000.0, "some")
    with pytest.raises(InventoryError):
        recalculate_base_year(10000.0, float("inf"))


def test_comparison_to_a_base_year_reports_direction_and_size():
    inventory = build_inventory(full_line_items())
    result = compare_to_base_year(inventory, 12000.0, "2024")
    assert result["reduced"]
    assert result["change"] < 0
    assert result["percent_change"] < 0
    assert result["base_year_label"] == "2024"


def test_comparison_carries_the_like_for_like_caveat():
    # Comparing a market-based total to a location-based one is the classic
    # way to accidentally report a reduction that never happened.
    inventory = build_inventory(full_line_items())
    result = compare_to_base_year(inventory, 12000.0)
    assert "same scope 2 method" in result["caveat"]
    assert result["scope_2_method"] == inventory["scope_2_method"]


def test_comparison_against_a_zero_base_year_does_not_divide_by_zero():
    inventory = build_inventory(full_line_items())
    assert compare_to_base_year(inventory, 0.0)["percent_change"] == 0.0


# --- Export and insights ----------------------------------------------------


def test_export_carries_both_scope_2_figures_and_the_boundary():
    export = export_inventory(build_inventory(full_line_items(), reporting_period="2026"))
    assert export["totals"]["scope_2_location_based"] == pytest.approx(630.0)
    assert export["totals"]["scope_2_market_based"] == pytest.approx(0.0)
    assert export["boundary"]["reporting_period"] == "2026"
    assert export["scope_2_method"] in ("location_based", "market_based")


def test_export_states_its_method_notes():
    export = export_inventory(build_inventory(full_line_items()))
    notes = " ".join(export["method_notes"])
    assert "GHG Protocol" in notes
    assert "location-based and market-based" in notes


def test_export_uses_readable_category_names():
    export = export_inventory(build_inventory(full_line_items()))
    assert "Food and diet" in export["scope_3_by_category"]


def test_export_lines_carry_scope_and_category():
    export = export_inventory(build_inventory(full_line_items()))
    for line in export["lines"]:
        assert line["scope"] in (SCOPE_1, SCOPE_2, SCOPE_3)
        assert "emissions_kgco2e" in line


def test_insights_point_out_that_scope_2_can_be_changed_by_contract():
    inventory = build_inventory(
        [
            {
                "activity": "electricity",
                "emissions": 4000.0,
                "location_based": 4000.0,
                "market_based": 0.0,
            },
            {"activity": "food", "emissions": 2000.0},
        ]
    )
    insights = " ".join(get_scope_insights(inventory))
    assert "switching supplier" in insights.lower() or "renewable tariff" in insights.lower()


def test_insights_flag_an_implausibly_low_scope_3():
    inventory = build_inventory(
        [
            {"activity": "gas_heating", "emissions": 8000.0},
            {"activity": "electricity", "emissions": 600.0},
            {"activity": "food", "emissions": 200.0},
            {"activity": "goods", "emissions": 100.0},
            {"activity": "waste", "emissions": 20.0},
            {"activity": "upstream_fuel", "emissions": 100.0},
        ]
    )
    insights = " ".join(get_scope_insights(inventory))
    assert "unusually low" in insights


def test_insights_note_when_scope_3_dominates_as_it_normally_should():
    insights = " ".join(get_scope_insights(build_inventory(full_line_items())))
    assert insights


# --- Persistence ------------------------------------------------------------


def test_saved_inventory_round_trips_with_its_lines():
    inventory = build_inventory(full_line_items(), reporting_period="2026")
    assert save_inventory(1, "2026 inventory", inventory)

    saved = get_inventories(1)
    assert len(saved) == 1
    assert saved[0]["name"] == "2026 inventory"
    assert saved[0]["total"] == pytest.approx(inventory["total"])
    assert len(saved[0]["lines"]) == len(inventory["lines"])


def test_both_scope_2_figures_survive_a_round_trip():
    inventory = build_inventory(full_line_items(), scope_2_method="market_based")
    save_inventory(1, "Market based", inventory)
    saved = get_inventories(1)[0]
    assert saved["scope_2_location_based"] == pytest.approx(630.0)
    assert saved["scope_2_market_based"] == pytest.approx(0.0)
    assert saved["scope_2_method"] == "market_based"


def test_inventories_come_back_newest_first():
    inventory = build_inventory(full_line_items())
    save_inventory(1, "Older", inventory)
    save_inventory(1, "Newer", inventory)
    assert [item["name"] for item in get_inventories(1)] == ["Newer", "Older"]


def test_inventories_are_scoped_to_their_user():
    save_inventory(1, "Mine", build_inventory(full_line_items()))
    assert get_inventories(2) == []


def test_deleting_an_inventory_removes_it_and_its_lines():
    inventory_id = save_inventory(1, "Temporary", build_inventory(full_line_items()))
    assert delete_inventory(1, inventory_id)
    assert get_inventories(1) == []


def test_an_inventory_cannot_be_deleted_by_another_user():
    inventory_id = save_inventory(1, "Mine", build_inventory(full_line_items()))
    assert not delete_inventory(2, inventory_id)
    # And crucially, the lines must survive the failed attempt too.
    assert len(get_inventories(1)[0]["lines"]) > 0


def test_persistence_helpers_ignore_missing_ids():
    assert save_inventory(None, "x", {}) is None
    assert get_inventories(None) == []
    assert delete_inventory(None, 1) is False
    assert delete_inventory(1, None) is False
