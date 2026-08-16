"""Tests for marginal (consequential) emissions accounting."""
import os
import tempfile

import pytest

# Deliberately no ECO_BUDDY_DB assignment here. Setting it at import time
# applies to the whole process, and every module imported afterwards would
# capture it — which in a full-suite run leaves other modules' storage tests
# looking for tables in a database that was never created. The autouse
# fixture below isolates this module's tests without touching anything else.
import marginal_emissions
from marginal_emissions import (
    AVAILABILITY_SHAPES,
    DECARBONISATION_RATES,
    DEFAULT_STACK,
    DEMAND_SHAPE,
    DIVERGENCE_THRESHOLD,
    FOOD_FACTORS,
    GENERATION_STACKS,
    HOURS_IN_DAY,
    MATERIAL_FACTORS,
    annualise,
    attributional_delta,
    availability,
    average_curve,
    clean_demand_shape,
    clean_stack,
    compare_shift,
    consequential_delta,
    curtailment_hours,
    curve_divergence,
    delete_comparison,
    describe_divergence,
    dispatch_day,
    dispatch_hour,
    food_comparison,
    get_comparisons,
    get_marginal_tips,
    get_stack,
    lifetime_comparison,
    list_foods,
    list_materials,
    list_stacks,
    long_run_factor,
    marginal_curve,
    material_comparison,
    rank_actions,
    rank_hours,
    rank_movement,
    ranking_changes,
    save_comparison,
    shift_load,
)


@pytest.fixture(autouse=True)
def temp_db():
    """Point the module at a throwaway SQLite file for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
        db_path = handle.name
    original = marginal_emissions.DB_NAME
    marginal_emissions.DB_NAME = db_path
    yield db_path
    marginal_emissions.DB_NAME = original
    try:
        os.unlink(db_path)
    except OSError:
        pass


# A deliberately tiny stack: one must-run renewable that only runs in the
# middle of the day, and two thermal units. Every dispatch assertion against
# it can be checked by hand.
TOY_STACK = [
    {"name": "Sun", "capacity": 1.0, "intensity": 40.0,
     "variable": "solar", "must_run": True},
    {"name": "Mid", "capacity": 0.5, "intensity": 300.0,
     "variable": None, "must_run": False},
    {"name": "Peak", "capacity": 0.5, "intensity": 600.0,
     "variable": None, "must_run": False},
]

FLAT_DEMAND = [0.6] * HOURS_IN_DAY


# ---------------------------------------------------------------------------
# Stack handling
# ---------------------------------------------------------------------------

def test_list_stacks_returns_all_archetypes():
    assert set(list_stacks()) == set(GENERATION_STACKS.keys())


def test_get_stack_falls_back_to_default():
    assert get_stack("Not a real grid") == get_stack(DEFAULT_STACK)


def test_get_stack_returns_a_copy():
    stack = get_stack("Gas-balanced")
    stack[0]["intensity"] = 9999.0
    assert GENERATION_STACKS["Gas-balanced"][0]["intensity"] != 9999.0


def test_every_stack_has_must_run_and_dispatchable_units():
    for name, stack in GENERATION_STACKS.items():
        assert any(unit["must_run"] for unit in stack), name
        assert any(not unit["must_run"] for unit in stack), name


def test_every_stack_can_meet_peak_demand():
    for name, stack in GENERATION_STACKS.items():
        total = sum(unit["capacity"] for unit in stack)
        assert total >= max(DEMAND_SHAPE), name


def test_clean_stack_drops_zero_capacity_units():
    stack = clean_stack([
        {"name": "Real", "capacity": 1.0, "intensity": 100.0},
        {"name": "Ghost", "capacity": 0.0, "intensity": 100.0},
    ])
    assert [unit["name"] for unit in stack] == ["Real"]


def test_clean_stack_drops_negative_intensity():
    stack = clean_stack([{"name": "Impossible", "capacity": 1.0, "intensity": -5.0}])
    assert stack == []


def test_clean_stack_drops_unnamed_units():
    assert clean_stack([{"name": "  ", "capacity": 1.0, "intensity": 10.0}]) == []


def test_clean_stack_ignores_unknown_availability_shape():
    stack = clean_stack([
        {"name": "X", "capacity": 1.0, "intensity": 10.0, "variable": "tides"},
    ])
    assert stack[0]["variable"] is None


def test_clean_stack_handles_junk_entries():
    assert clean_stack(["not a dict", None, 42]) == []


def test_clean_demand_shape_rejects_wrong_length():
    assert clean_demand_shape([0.5, 0.5]) == list(DEMAND_SHAPE)


def test_clean_demand_shape_rejects_all_zero():
    assert clean_demand_shape([0.0] * HOURS_IN_DAY) == list(DEMAND_SHAPE)


def test_clean_demand_shape_accepts_valid_shape():
    assert clean_demand_shape(FLAT_DEMAND) == FLAT_DEMAND


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------

def test_availability_is_one_for_firm_plant():
    unit = {"name": "Nuclear", "capacity": 1.0, "intensity": 12.0, "variable": None}
    assert availability(unit, 3) == 1.0


def test_solar_availability_is_zero_at_night():
    unit = {"name": "Sun", "capacity": 1.0, "intensity": 40.0, "variable": "solar"}
    assert availability(unit, 2) == 0.0


def test_solar_availability_peaks_at_noon():
    unit = {"name": "Sun", "capacity": 1.0, "intensity": 40.0, "variable": "solar"}
    noon = availability(unit, 12)
    assert noon == max(AVAILABILITY_SHAPES["solar"])
    assert noon == 1.0


def test_availability_wraps_hours():
    unit = {"name": "Sun", "capacity": 1.0, "intensity": 40.0, "variable": "solar"}
    assert availability(unit, 26) == availability(unit, 2)


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def test_dispatch_at_night_uses_mid_merit_thermal():
    # No sun, demand 0.6, Mid has 0.5 of capacity so Peak must cover 0.1.
    result = dispatch_hour(TOY_STACK, 2, 0.6)
    assert result["marginal_unit"] == "Peak"
    assert result["marginal_intensity"] == 600.0
    assert result["generation"]["Sun"] == 0.0
    assert result["generation"]["Mid"] == pytest.approx(0.5)
    assert result["generation"]["Peak"] == pytest.approx(0.1)


def test_dispatch_average_is_energy_weighted():
    result = dispatch_hour(TOY_STACK, 2, 0.6)
    expected = (0.5 * 300.0 + 0.1 * 600.0) / 0.6
    assert result["average_intensity"] == pytest.approx(expected)


def test_marginal_exceeds_average_when_thermal_sets_margin():
    result = dispatch_hour(TOY_STACK, 2, 0.6)
    assert result["marginal_intensity"] > result["average_intensity"]


def test_dispatch_stops_at_first_unit_that_covers_demand():
    result = dispatch_hour(TOY_STACK, 2, 0.4)
    assert result["marginal_unit"] == "Mid"
    assert result["generation"]["Peak"] == 0.0


def test_curtailment_collapses_the_marginal_factor():
    # At noon the toy stack has 1.0 of solar against 0.6 of demand.
    result = dispatch_hour(TOY_STACK, 12, 0.6)
    assert result["curtailed"] is True
    assert result["curtailed_energy"] == pytest.approx(0.4)
    assert result["marginal_intensity"] == 40.0
    assert result["marginal_unit"] == "Sun"


def test_curtailed_hour_dispatches_no_thermal():
    result = dispatch_hour(TOY_STACK, 12, 0.6)
    assert result["generation"]["Mid"] == 0.0
    assert result["generation"]["Peak"] == 0.0


def test_curtailed_must_run_scales_down_to_demand():
    result = dispatch_hour(TOY_STACK, 12, 0.6)
    assert result["generation"]["Sun"] == pytest.approx(0.6)


def test_unserved_demand_is_reported_not_hidden():
    result = dispatch_hour(TOY_STACK, 2, 2.0)
    assert result["unserved"] == pytest.approx(1.0)
    assert result["marginal_unit"] == "Peak"


def test_zero_demand_returns_zero_average():
    result = dispatch_hour(TOY_STACK, 12, 0.0)
    assert result["average_intensity"] == 0.0
    assert result["curtailed"] is True


def test_dispatch_day_covers_every_hour():
    day = dispatch_day(stack=TOY_STACK, demand_shape=FLAT_DEMAND)
    assert len(day) == HOURS_IN_DAY
    assert [row["hour"] for row in day] == list(range(HOURS_IN_DAY))


def test_dispatch_day_defaults_to_named_stack():
    day = dispatch_day("Coal-heavy")
    assert len(day) == HOURS_IN_DAY
    assert all(row["marginal_intensity"] > 0 for row in day)


def test_empty_custom_stack_falls_back_to_named_stack():
    day = dispatch_day("Coal-heavy", stack=[{"bad": "entry"}])
    assert len(day) == HOURS_IN_DAY


# ---------------------------------------------------------------------------
# Curves
# ---------------------------------------------------------------------------

def test_curves_have_24_values():
    assert len(average_curve("Gas-balanced")) == HOURS_IN_DAY
    assert len(marginal_curve("Gas-balanced")) == HOURS_IN_DAY


def test_marginal_and_average_curves_differ():
    average = average_curve("Gas-balanced")
    marginal = marginal_curve("Gas-balanced")
    assert average != marginal


def test_baseload_grid_has_clean_average_and_dirty_margin_overnight():
    # The error that points the opposite way to curtailment: at 3am the grid
    # average is genuinely low while the responding plant is still thermal.
    average = average_curve("Nuclear baseload")
    marginal = marginal_curve("Nuclear baseload")
    assert average[3] < 100.0
    assert marginal[3] > 300.0


def test_solar_grid_curtails_around_midday():
    hours = curtailment_hours("Solar-heavy")
    assert 12 in hours
    assert 3 not in hours


def test_coal_grid_never_curtails():
    assert curtailment_hours("Coal-heavy") == []


def test_curve_divergence_flags_material_gaps():
    rows = curve_divergence("Nuclear baseload")
    assert any(row["material"] for row in rows)


def test_curve_divergence_reports_marginal_unit():
    rows = curve_divergence("Gas-balanced")
    assert all(row["marginal_unit"] for row in rows)


def test_curve_divergence_relative_gap_matches_threshold_flag():
    for row in curve_divergence("Gas-balanced"):
        assert row["material"] == (abs(row["relative_gap"]) >= DIVERGENCE_THRESHOLD)


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------

def test_rank_hours_orders_cleanest_first():
    curve = [float(hour) for hour in range(HOURS_IN_DAY)]
    ranked = rank_hours(curve)
    assert ranked[0] == (0, 0.0)
    assert ranked[-1] == (23, 23.0)


def test_rank_hours_can_order_dirtiest_first():
    curve = [float(hour) for hour in range(HOURS_IN_DAY)]
    assert rank_hours(curve, cleanest_first=False)[0] == (23, 23.0)


def test_rank_hours_rejects_wrong_length():
    with pytest.raises(ValueError):
        rank_hours([1.0, 2.0])


def test_ranking_changes_is_empty_for_identical_curves():
    curve = [float(hour) for hour in range(HOURS_IN_DAY)]
    assert ranking_changes(curve, curve) == []


def test_ranking_changes_detects_reordering():
    average = [float(hour) for hour in range(HOURS_IN_DAY)]
    marginal = list(reversed(average))
    changes = ranking_changes(average, marginal)
    assert changes
    assert changes[0]["movement"] != 0


def test_ranking_changes_respects_top_n():
    average = [float(hour) for hour in range(HOURS_IN_DAY)]
    marginal = list(reversed(average))
    assert len(ranking_changes(average, marginal, top_n=3)) == 3


def test_real_grid_reorders_hours_between_accountings():
    changes = ranking_changes(
        average_curve("Solar-heavy"), marginal_curve("Solar-heavy")
    )
    assert changes, "the two accountings should not agree on hour order"


# ---------------------------------------------------------------------------
# Deltas and load shifting
# ---------------------------------------------------------------------------

def test_shift_load_conserves_energy():
    vector = shift_load(4.0, 18, 3)
    assert sum(vector) == pytest.approx(0.0)


def test_shift_load_spreads_over_duration():
    vector = shift_load(4.0, 18, 2, duration_hours=2)
    assert vector[2] == pytest.approx(2.0)
    assert vector[3] == pytest.approx(2.0)
    assert vector[18] == pytest.approx(-2.0)
    assert vector[19] == pytest.approx(-2.0)


def test_shift_load_wraps_past_midnight():
    vector = shift_load(2.0, 23, 0, duration_hours=2)
    assert vector[23] == pytest.approx(-1.0)
    assert vector[0] == pytest.approx(-1.0 + 1.0)
    assert vector[1] == pytest.approx(1.0)


def test_attributional_delta_is_energy_times_curve():
    energy = [0.0] * HOURS_IN_DAY
    energy[5] = 2.0
    curve = [500.0] * HOURS_IN_DAY
    assert attributional_delta(energy, curve) == pytest.approx(1.0)


def test_consequential_delta_uses_the_curve_it_is_given():
    energy = [0.0] * HOURS_IN_DAY
    energy[5] = 2.0
    assert consequential_delta(energy, [250.0] * HOURS_IN_DAY) == pytest.approx(0.5)


def test_delta_rejects_wrong_length_inputs():
    with pytest.raises(ValueError):
        attributional_delta([1.0], [100.0] * HOURS_IN_DAY)
    with pytest.raises(ValueError):
        attributional_delta([1.0] * HOURS_IN_DAY, [100.0])


def test_compare_shift_reports_both_accountings():
    result = compare_shift(5.0, 18, 12, stack_name="Solar-heavy")
    assert "attributional_kg" in result
    assert "consequential_kg" in result
    assert result["attributional_kg"] < 0
    assert result["consequential_kg"] < 0


def test_shifting_into_curtailment_saves_more_than_averages_suggest():
    # Moving load into a curtailed hour is undersold by the average curve,
    # because the average cannot see that the extra energy was free.
    result = compare_shift(10.0, 18, 12, stack_name="Solar-heavy")
    assert abs(result["consequential_kg"]) > abs(result["attributional_kg"])
    assert result["material"] is True


def test_shifting_within_one_marginal_unit_saves_nothing_real():
    # Both hours have coal on the margin, so moving load between them changes
    # nothing at all - while the average curve still reports a saving, because
    # the generation *mix* differs even though the responding plant does not.
    # This is the sharpest illustration of why the two curves are not
    # interchangeable, and average-factor tools cannot express it.
    result = compare_shift(1.0, 2, 3, stack_name="Coal-heavy")
    assert result["consequential_kg"] == pytest.approx(0.0)
    assert result["attributional_kg"] != pytest.approx(0.0)
    assert result["material"] is True


# ---------------------------------------------------------------------------
# Divergence reporting
# ---------------------------------------------------------------------------

def test_describe_divergence_detects_sign_flip():
    result = describe_divergence(-5.0, 2.0)
    assert result["sign_flip"] is True
    assert "not" in result["reading"]


def test_describe_divergence_detects_reverse_sign_flip():
    result = describe_divergence(2.0, -5.0)
    assert result["sign_flip"] is True


def test_describe_divergence_agrees_within_noise():
    result = describe_divergence(-10.0, -10.5)
    assert result["material"] is False
    assert "agree" in result["reading"]


def test_describe_divergence_flags_understatement():
    result = describe_divergence(-10.0, -30.0)
    assert result["material"] is True
    assert "understate" in result["reading"]


def test_describe_divergence_flags_flattery():
    result = describe_divergence(-30.0, -10.0)
    assert result["material"] is True
    assert "flatter" in result["reading"]


def test_describe_divergence_handles_zero_baseline():
    result = describe_divergence(0.0, -4.0)
    assert result["material"] is True
    assert result["relative_gap"] == 0.0


def test_describe_divergence_zero_on_both_sides_is_not_material():
    assert describe_divergence(0.0, 0.0)["material"] is False


# ---------------------------------------------------------------------------
# Long run
# ---------------------------------------------------------------------------

def test_long_run_factor_equals_base_for_one_year():
    assert long_run_factor(400.0, 1, "Central") == pytest.approx(400.0)


def test_long_run_factor_falls_below_base_over_time():
    assert long_run_factor(400.0, 15, "Central") < 400.0


def test_stalled_trajectory_stays_near_base():
    stalled = long_run_factor(400.0, 15, "Stalled")
    rapid = long_run_factor(400.0, 15, "Rapid")
    assert stalled > rapid
    assert stalled > 380.0


def test_long_run_factor_accepts_explicit_rate():
    assert long_run_factor(100.0, 2, rate=0.5) == pytest.approx((100.0 + 50.0) / 2)


def test_long_run_factor_clamps_negative_rate():
    assert long_run_factor(100.0, 3, rate=-1.0) == pytest.approx(100.0)


def test_long_run_factor_unknown_trajectory_uses_default():
    assert long_run_factor(300.0, 10, "Wishful") == pytest.approx(
        long_run_factor(300.0, 10, "Central")
    )


def test_every_trajectory_is_a_fraction():
    for name, rate in DECARBONISATION_RATES.items():
        assert 0.0 <= rate < 1.0, name


def test_lifetime_comparison_shows_static_overstatement():
    result = lifetime_comparison(2500.0, 15, 380.0, "Central")
    assert result["static_lifetime_kg"] > result["declining_lifetime_kg"]
    assert result["overstatement_pct"] > 0


def test_lifetime_comparison_includes_embodied_in_both():
    result = lifetime_comparison(2500.0, 15, 380.0, "Central", embodied_kg=1200.0)
    assert result["embodied_kg"] == 1200.0
    assert result["static_lifetime_kg"] > 1200.0
    assert result["declining_lifetime_kg"] > 1200.0


def test_lifetime_comparison_handles_zero_use():
    result = lifetime_comparison(0.0, 15, 380.0)
    assert result["overstatement_pct"] == 0.0


# ---------------------------------------------------------------------------
# Materials and food
# ---------------------------------------------------------------------------

def test_list_materials_matches_table():
    assert set(list_materials()) == set(MATERIAL_FACTORS.keys())


def test_every_material_marginal_exceeds_average():
    for name, entry in MATERIAL_FACTORS.items():
        assert entry["marginal"] > entry["average"], name


def test_material_comparison_credits_more_than_the_average():
    result = material_comparison("Aluminium", 10.0)
    assert abs(result["consequential_kg"]) > abs(result["attributional_kg"])
    assert result["ratio"] > 1.0


def test_aluminium_gap_is_the_largest():
    ratios = {
        name: entry["marginal"] / entry["average"]
        for name, entry in MATERIAL_FACTORS.items()
    }
    assert max(ratios, key=ratios.get) == "Aluminium"


def test_material_comparison_raises_on_unknown_material():
    with pytest.raises(KeyError):
        material_comparison("Unobtainium", 1.0)


def test_material_comparison_handles_zero_mass():
    result = material_comparison("Glass", 0.0)
    assert result["attributional_kg"] == 0.0
    assert result["consequential_kg"] == 0.0


def test_material_comparison_carries_the_note():
    assert material_comparison("Aluminium", 1.0)["note"]


def test_list_foods_matches_table():
    assert set(list_foods()) == set(FOOD_FACTORS.keys())


def test_short_run_food_response_is_smaller_than_average():
    for name, entry in FOOD_FACTORS.items():
        assert entry["short_run"] <= entry["average"], name


def test_long_run_food_response_is_at_least_average():
    for name, entry in FOOD_FACTORS.items():
        assert entry["long_run"] >= entry["average"], name


def test_food_comparison_short_run_understates_the_saving():
    result = food_comparison("Beef", 10.0, "short_run")
    assert abs(result["consequential_kg"]) < abs(result["attributional_kg"])


def test_food_comparison_long_run_exceeds_the_saving():
    result = food_comparison("Beef", 10.0, "long_run")
    assert abs(result["consequential_kg"]) > abs(result["attributional_kg"])


def test_food_comparison_rejects_bad_horizon():
    with pytest.raises(ValueError):
        food_comparison("Beef", 1.0, "next tuesday")


def test_food_comparison_raises_on_unknown_food():
    with pytest.raises(KeyError):
        food_comparison("Ambrosia", 1.0)


# ---------------------------------------------------------------------------
# Action ranking
# ---------------------------------------------------------------------------

def test_rank_actions_puts_biggest_saving_first():
    actions = [
        {"label": "small", "attributional_kg": -1.0, "consequential_kg": -1.0},
        {"label": "big", "attributional_kg": -9.0, "consequential_kg": -9.0},
    ]
    assert rank_actions(actions)[0]["label"] == "big"


def test_rank_actions_rejects_unknown_key():
    with pytest.raises(ValueError):
        rank_actions([], key="vibes")


def test_rank_actions_ignores_non_dict_entries():
    assert rank_actions(["nope", {"label": "ok", "consequential_kg": -1.0}])


def test_rank_movement_is_empty_when_orders_agree():
    actions = [
        {"label": "a", "attributional_kg": -1.0, "consequential_kg": -1.0},
        {"label": "b", "attributional_kg": -2.0, "consequential_kg": -2.0},
    ]
    assert rank_movement(actions) == []


def test_rank_movement_detects_a_swap():
    actions = [
        {"label": "recycle", "attributional_kg": -1.0, "consequential_kg": -9.0},
        {"label": "shift load", "attributional_kg": -5.0, "consequential_kg": -2.0},
    ]
    movements = rank_movement(actions)
    assert {move["label"] for move in movements} == {"recycle", "shift load"}
    up = [move for move in movements if move["direction"] == "up"]
    assert up[0]["label"] == "recycle"


def test_rank_movement_handles_duplicate_labels():
    actions = [
        {"label": "same", "attributional_kg": -1.0, "consequential_kg": -9.0},
        {"label": "same", "attributional_kg": -5.0, "consequential_kg": -2.0},
    ]
    assert len(rank_movement(actions)) == 2


def test_annualise_scales_a_daily_figure():
    assert annualise(2.0, 365) == pytest.approx(730.0)


def test_annualise_handles_junk():
    assert annualise("not a number") == 0.0


# ---------------------------------------------------------------------------
# Tips
# ---------------------------------------------------------------------------

def test_tips_lead_with_sign_flips():
    tips = get_marginal_tips([describe_divergence(-5.0, 2.0)])
    assert "changes sign" in tips[0]


def test_tips_mention_understatement():
    tips = get_marginal_tips([describe_divergence(-10.0, -30.0)])
    assert any("Recycling" in tip for tip in tips)


def test_tips_handle_no_actions():
    tips = get_marginal_tips([])
    assert any("Add an action" in tip for tip in tips)


def test_tips_respect_the_limit():
    assert len(get_marginal_tips([], limit=2)) == 2


def test_tips_always_explain_the_two_questions():
    tips = get_marginal_tips([])
    assert any("different questions" in tip for tip in tips)


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def test_save_and_read_back_a_comparison():
    comparison = compare_shift(5.0, 18, 12, stack_name="Solar-heavy")
    row_id = save_comparison(7, "Evening wash", comparison, "Solar-heavy")
    assert row_id is not None

    saved = get_comparisons(7)
    assert len(saved) == 1
    assert saved[0]["comparison_name"] == "Evening wash"
    assert saved[0]["stack_name"] == "Solar-heavy"
    assert saved[0]["detail"]["label"] == comparison["label"]


def test_saved_comparisons_are_scoped_to_the_user():
    comparison = compare_shift(1.0, 18, 12)
    save_comparison(1, "Mine", comparison)
    save_comparison(2, "Theirs", comparison)
    assert len(get_comparisons(1)) == 1
    assert get_comparisons(1)[0]["comparison_name"] == "Mine"


def test_blank_comparison_name_gets_a_default():
    save_comparison(3, "   ", compare_shift(1.0, 18, 12))
    assert get_comparisons(3)[0]["comparison_name"] == "Comparison"


def test_sign_flip_survives_the_round_trip():
    save_comparison(4, "Flip", describe_divergence(-5.0, 2.0))
    assert get_comparisons(4)[0]["sign_flip"] is True


def test_delete_comparison_removes_it():
    row_id = save_comparison(5, "Temp", compare_shift(1.0, 18, 12))
    assert delete_comparison(row_id) is True
    assert get_comparisons(5) == []


def test_delete_missing_comparison_returns_false():
    assert delete_comparison(999999) is False


def test_get_comparisons_respects_limit():
    for index in range(5):
        save_comparison(6, f"Run {index}", compare_shift(1.0, 18, 12))
    assert len(get_comparisons(6, limit=2)) == 2


def test_get_comparisons_for_unknown_user_is_empty():
    assert get_comparisons(4242) == []
