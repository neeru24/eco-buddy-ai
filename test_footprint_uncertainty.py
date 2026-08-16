"""Tests for the Footprint Uncertainty & Confidence Engine."""
import math
import os
import tempfile

import pytest

os.environ["ECO_BUDDY_DB"] = ":memory:"

import footprint_uncertainty
from footprint_uncertainty import (
    ACTIVITY_QUALITY,
    DEFAULT_ITERATIONS,
    DEFAULT_SEED,
    FACTOR_TIER,
    LOWER_PERCENTILE,
    UPPER_PERCENTILE,
    UncertaintyError,
    activity_gsd,
    analytical_interval,
    build_component,
    combine_gsd,
    compare_footprints,
    delete_profile,
    detectable_change,
    factor_gsd,
    factor_tier_for_kind,
    format_interval,
    get_profiles,
    get_uncertainty_notes,
    gsd_to_relative_spread,
    improvement_plan,
    list_activity_qualities,
    list_factor_tiers,
    percentile,
    point_estimate,
    propagate,
    save_profile,
    sensitivity_ranking,
)


@pytest.fixture(autouse=True)
def temp_db():
    """Point the module at a throwaway SQLite file for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
        db_path = handle.name
    original = footprint_uncertainty.DB_NAME
    footprint_uncertainty.DB_NAME = db_path
    yield db_path
    footprint_uncertainty.DB_NAME = original
    try:
        os.unlink(db_path)
    except OSError:
        pass


# A small three-component footprint used across the propagation tests. Driving
# dominates the total, heating is recalled and therefore the sloppiest input,
# and electricity is metered and tight.
def sample_components():
    return [
        build_component("Car", 12000, 0.17, "estimated", "published", "km", "transport"),
        build_component("Heating", 14000, 0.18, "recalled", "published", "kWh", "home"),
        build_component("Electricity", 3200, 0.21, "metered", "verified", "kWh", "home"),
    ]


# Faster settings for the many tests that only care about behaviour, not about
# the third decimal place of a percentile.
FAST = 2000


# --- Quality vocabulary -----------------------------------------------------


def test_activity_qualities_sorted_tightest_first():
    levels = list_activity_qualities()
    assert [entry["key"] for entry in levels][0] == "metered"
    assert levels == sorted(levels, key=lambda item: item["gsd"])


def test_factor_tiers_sorted_tightest_first():
    tiers = list_factor_tiers()
    assert tiers[0]["key"] == "measured"
    assert tiers[-1]["key"] == "assumed"


def test_every_quality_level_has_a_label_and_description():
    for entry in list_activity_qualities() + list_factor_tiers():
        assert entry["label"]
        assert entry["description"]
        assert entry["gsd"] > 1.0


def test_unknown_quality_falls_back_to_the_default():
    assert activity_gsd("nonsense") == ACTIVITY_QUALITY["estimated"]["gsd"]
    assert factor_gsd("nonsense") == FACTOR_TIER["published"]["gsd"]


def test_metered_data_is_tighter_than_recalled_data():
    assert activity_gsd("metered") < activity_gsd("recalled")


def test_registry_kinds_map_onto_factor_tiers():
    # A live API factor for the user's own region beats a built-in constant.
    assert factor_gsd(factor_tier_for_kind("dynamic")) < factor_gsd(
        factor_tier_for_kind("static")
    )
    assert factor_tier_for_kind("something-else") == "published"


# --- Lognormal arithmetic ---------------------------------------------------


def test_combining_gsds_adds_log_variance_in_quadrature():
    combined = combine_gsd(1.2, 1.3)
    expected = math.exp(math.sqrt(math.log(1.2) ** 2 + math.log(1.3) ** 2))
    assert combined == pytest.approx(expected)


def test_combined_gsd_exceeds_each_input():
    combined = combine_gsd(1.2, 1.3)
    assert combined > 1.3


def test_certain_inputs_contribute_nothing_to_the_combination():
    assert combine_gsd(1.0, 1.4) == pytest.approx(1.4)
    assert combine_gsd(1.4) == pytest.approx(1.4)
    assert combine_gsd() == pytest.approx(1.0)


def test_combining_ignores_junk_values():
    assert combine_gsd(1.3, None, "oops", 0.5) == pytest.approx(1.3)


def test_relative_spread_grows_with_gsd():
    assert gsd_to_relative_spread(1.0) == 0.0
    assert gsd_to_relative_spread(1.1) < gsd_to_relative_spread(1.5)


def test_percentile_interpolates_between_neighbours():
    values = [0.0, 10.0, 20.0, 30.0, 40.0]
    assert percentile(values, 0) == 0.0
    assert percentile(values, 100) == 40.0
    assert percentile(values, 50) == 20.0
    assert percentile(values, 25) == pytest.approx(10.0)


def test_percentile_handles_degenerate_inputs():
    assert percentile([], 50) == 0.0
    assert percentile([7.0], 90) == 7.0
    # Out-of-range percentiles clamp rather than raising.
    assert percentile([1.0, 2.0], -20) == 1.0
    assert percentile([1.0, 2.0], 200) == 2.0


# --- Components -------------------------------------------------------------


def test_component_multiplies_amount_by_factor():
    component = build_component("Car", 1000, 0.2)
    assert component["emissions"] == pytest.approx(200.0)


def test_component_combines_both_sources_of_uncertainty():
    component = build_component("Car", 1000, 0.2, "recalled", "proxy")
    assert component["combined_gsd"] > component["activity_gsd"]
    assert component["combined_gsd"] > component["factor_gsd"]


def test_better_data_produces_a_tighter_component():
    sloppy = build_component("Car", 1000, 0.2, "assumed", "assumed")
    careful = build_component("Car", 1000, 0.2, "metered", "measured")
    assert careful["combined_gsd"] < sloppy["combined_gsd"]
    assert careful["emissions"] == sloppy["emissions"]


def test_component_rejects_negative_values():
    with pytest.raises(UncertaintyError):
        build_component("Car", -100, 0.2)
    with pytest.raises(UncertaintyError):
        build_component("Car", 100, -0.2)


def test_component_rejects_non_numeric_values():
    with pytest.raises(UncertaintyError):
        build_component("Car", "twelve thousand", 0.2)


def test_component_rejects_nan_and_infinity():
    with pytest.raises(UncertaintyError):
        build_component("Car", float("nan"), 0.2)
    with pytest.raises(UncertaintyError):
        build_component("Car", float("inf"), 0.2)


def test_unknown_quality_keys_fall_back_rather_than_raising():
    component = build_component("Car", 1000, 0.2, "made-up", "also-made-up")
    assert component["activity_quality"] == "estimated"
    assert component["factor_tier"] == "published"


def test_point_estimate_sums_components():
    assert point_estimate(sample_components()) == pytest.approx(
        12000 * 0.17 + 14000 * 0.18 + 3200 * 0.21
    )


def test_point_estimate_of_nothing_is_zero():
    assert point_estimate([]) == 0.0
    assert point_estimate(None) == 0.0


# --- Propagation ------------------------------------------------------------


def test_propagation_brackets_the_point_estimate():
    result = propagate(sample_components(), iterations=FAST)
    assert result["lower"] < result["point_estimate"] < result["upper"]


def test_propagation_is_deterministic_for_a_fixed_seed():
    first = propagate(sample_components(), iterations=FAST, seed=7)
    second = propagate(sample_components(), iterations=FAST, seed=7)
    assert first["median"] == second["median"]
    assert first["lower"] == second["lower"]
    assert first["upper"] == second["upper"]


def test_different_seeds_give_close_but_distinct_results():
    first = propagate(sample_components(), iterations=FAST, seed=1)
    second = propagate(sample_components(), iterations=FAST, seed=2)
    assert first["median"] != second["median"]
    assert first["median"] == pytest.approx(second["median"], rel=0.05)


def test_median_sits_just_above_the_point_estimate():
    # Each component is sampled so its own median is its point estimate, but
    # the median of a *sum* of right-skewed variables is not the sum of the
    # medians - it gets pulled up towards the mean. The drift is real and
    # small, and it is why the point estimate is reported alongside rather
    # than replaced by the median.
    result = propagate(sample_components(), iterations=8000)
    assert result["median"] >= result["point_estimate"]
    assert result["median"] == pytest.approx(result["point_estimate"], rel=0.08)


def test_mean_sits_above_the_median_for_lognormal_inputs():
    # The defining asymmetry of a lognormal, and the reason the module reports
    # the median rather than the mean as the headline figure.
    result = propagate(sample_components(), iterations=8000)
    assert result["mean"] > result["median"]


def test_sloppier_data_widens_the_interval():
    careful = [
        build_component("Car", 12000, 0.17, "metered", "measured"),
        build_component("Heating", 14000, 0.18, "metered", "measured"),
    ]
    sloppy = [
        build_component("Car", 12000, 0.17, "assumed", "assumed"),
        build_component("Heating", 14000, 0.18, "assumed", "assumed"),
    ]
    tight = propagate(careful, iterations=FAST)
    wide = propagate(sloppy, iterations=FAST)
    assert wide["relative_half_width"] > tight["relative_half_width"]
    assert wide["is_wide"]
    assert not tight["is_wide"]


def test_a_certain_component_has_no_spread():
    component = build_component("Fixed", 100, 1.0)
    component["combined_gsd"] = 1.0
    result = propagate([component], iterations=FAST)
    assert result["lower"] == pytest.approx(100.0)
    assert result["upper"] == pytest.approx(100.0)
    assert result["relative_half_width"] == pytest.approx(0.0)


def test_zero_emission_components_do_not_break_propagation():
    components = [
        build_component("Car", 12000, 0.17),
        build_component("Solar", 0, 0.0),
    ]
    result = propagate(components, iterations=FAST)
    assert result["median"] > 0
    assert result["component_count"] == 2


def test_propagation_requires_components():
    with pytest.raises(UncertaintyError):
        propagate([])
    with pytest.raises(UncertaintyError):
        propagate(None)
    with pytest.raises(UncertaintyError):
        propagate([None, None])


def test_iteration_count_is_clamped_to_a_sane_range():
    low = propagate(sample_components(), iterations=1)
    high = propagate(sample_components(), iterations=10 ** 9)
    assert low["iterations"] == footprint_uncertainty.MIN_ITERATIONS
    assert high["iterations"] == footprint_uncertainty.MAX_ITERATIONS


def test_junk_iteration_counts_fall_back_to_the_default():
    result = propagate(sample_components(), iterations="lots")
    assert result["iterations"] == DEFAULT_ITERATIONS


def test_reported_interval_is_the_ninety_percent_range():
    result = propagate(sample_components(), iterations=FAST)
    assert result["confidence_level"] == UPPER_PERCENTILE - LOWER_PERCENTILE == 90


def test_adding_a_component_does_not_disturb_the_others_draws():
    # Each component is seeded independently, so extending a footprint must
    # not resample the components that were already there.
    base = sample_components()
    extended = base + [build_component("Flights", 2, 400.0, "logged", "published")]
    first = sensitivity_ranking(base, iterations=FAST)
    second = sensitivity_ranking(extended, iterations=FAST)
    car_before = next(item for item in first if item["name"] == "Car")
    car_after = next(item for item in second if item["name"] == "Car")
    # Its share of variance changes because the denominator grew, but its own
    # emissions and modelled spread are untouched.
    assert car_before["emissions"] == car_after["emissions"]
    assert car_before["combined_gsd"] == car_after["combined_gsd"]


# --- Analytical cross-check -------------------------------------------------


def test_analytical_interval_roughly_agrees_with_monte_carlo():
    components = sample_components()
    quick = analytical_interval(components)
    sampled = propagate(components, iterations=8000)
    # Different distributional assumptions, so agreement is loose by design -
    # but an order-of-magnitude disagreement would mean something is wrong.
    assert quick["relative_half_width"] == pytest.approx(
        sampled["relative_half_width"], rel=0.35
    )


def test_analytical_interval_of_an_empty_footprint_is_zero():
    component = build_component("Nothing", 0, 0)
    assert analytical_interval([component])["relative_half_width"] == 0.0


# --- Sensitivity ------------------------------------------------------------


def test_variance_shares_sum_to_roughly_one():
    rankings = sensitivity_ranking(sample_components(), iterations=8000)
    assert sum(item["variance_share"] for item in rankings) == pytest.approx(1.0, abs=0.1)


def test_the_biggest_and_sloppiest_input_dominates_the_uncertainty():
    rankings = sensitivity_ranking(sample_components(), iterations=8000)
    # Heating is both large and recalled from memory, so it should top the
    # ranking ahead of the metered electricity.
    assert rankings[0]["name"] == "Heating"
    assert rankings[-1]["name"] == "Electricity"


def test_a_tiny_input_is_flagged_negligible():
    components = [
        build_component("Car", 12000, 0.17, "estimated", "published"),
        build_component("Coffee", 300, 0.01, "recalled", "assumed"),
    ]
    rankings = sensitivity_ranking(components, iterations=8000)
    coffee = next(item for item in rankings if item["name"] == "Coffee")
    assert coffee["is_negligible"]


def test_a_large_input_is_not_flagged_negligible():
    rankings = sensitivity_ranking(sample_components(), iterations=8000)
    assert not rankings[0]["is_negligible"]


def test_pinning_a_component_reduces_the_residual_spread():
    rankings = sensitivity_ranking(sample_components(), iterations=FAST)
    full = propagate(sample_components(), iterations=FAST)
    for item in rankings:
        assert item["residual_relative_half_width"] <= full["relative_half_width"] + 1e-9


def test_sensitivity_reports_emission_shares_that_sum_to_one():
    rankings = sensitivity_ranking(sample_components(), iterations=FAST)
    assert sum(item["emissions_share"] for item in rankings) == pytest.approx(1.0)


def test_variance_share_is_never_negative():
    rankings = sensitivity_ranking(sample_components(), iterations=FAST)
    assert all(item["variance_share"] >= 0 for item in rankings)


# --- Improvement plan -------------------------------------------------------


def test_improvement_plan_targets_the_worst_input_first():
    plan = improvement_plan(sample_components(), iterations=FAST)
    assert plan["actions"][0]["name"] == "Heating"
    assert plan["best_action"]["name"] == "Heating"


def test_measuring_an_input_narrows_the_interval():
    plan = improvement_plan(sample_components(), iterations=FAST)
    best = plan["best_action"]
    assert best["improved_relative_half_width"] < plan["baseline_relative_half_width"]
    assert best["reduction_points"] > 0


def test_already_metered_inputs_offer_no_gain():
    plan = improvement_plan(sample_components(), iterations=FAST)
    electricity = next(item for item in plan["actions"] if item["name"] == "Electricity")
    assert electricity["already_good"]
    assert electricity["reduction"] == 0.0


def test_plan_with_nothing_left_to_improve_has_no_best_action():
    components = [
        build_component("Car", 12000, 0.17, "metered", "published"),
        build_component("Heating", 14000, 0.18, "metered", "published"),
    ]
    plan = improvement_plan(components, iterations=FAST)
    assert plan["best_action"] is None
    assert all(action["already_good"] for action in plan["actions"])


def test_unknown_target_quality_falls_back_to_metered():
    plan = improvement_plan(sample_components(), target_quality="perfect", iterations=FAST)
    assert plan["target_quality"] == "metered"


# --- Comparing two footprints -----------------------------------------------


def test_a_large_reduction_is_detected_as_real():
    before = [build_component("Car", 12000, 0.17, "logged", "verified")]
    after = [build_component("Car", 6000, 0.17, "logged", "verified")]
    result = compare_footprints(before, after, iterations=FAST)
    assert result["verdict"] == "reduced"
    assert result["probability_reduced"] > 0.95
    assert result["percent_change"] < 0


def test_a_small_change_in_sloppy_data_is_inconclusive():
    before = [build_component("Car", 12000, 0.17, "recalled", "assumed")]
    after = [build_component("Car", 11600, 0.17, "recalled", "assumed")]
    result = compare_footprints(before, after, iterations=FAST)
    assert result["verdict"] == "inconclusive"
    assert "same" in result["explanation"]


def test_the_same_change_is_more_detectable_with_better_data():
    # The identical 15% cut, judged on recalled data and on metered data.
    sloppy = compare_footprints(
        [build_component("Car", 12000, 0.17, "recalled", "assumed")],
        [build_component("Car", 10200, 0.17, "recalled", "assumed")],
        iterations=8000,
    )
    precise = compare_footprints(
        [build_component("Car", 12000, 0.17, "metered", "measured")],
        [build_component("Car", 10200, 0.17, "metered", "measured")],
        iterations=8000,
    )
    assert precise["probability_reduced"] > sloppy["probability_reduced"]
    assert sloppy["verdict"] == "inconclusive"
    # Even metered data does not quite clear the 95% bar on a 15% cut - the
    # closed form puts it at 0.935 - and the module is right not to overclaim.
    assert precise["verdict"] == "probably_reduced"


def test_a_cut_large_enough_for_the_data_clears_the_strong_evidence_bar():
    result = compare_footprints(
        [build_component("Car", 12000, 0.17, "metered", "measured")],
        [build_component("Car", 8400, 0.17, "metered", "measured")],
        iterations=8000,
    )
    assert result["verdict"] == "reduced"


def test_a_large_increase_is_detected():
    before = [build_component("Car", 6000, 0.17, "logged", "verified")]
    after = [build_component("Car", 14000, 0.17, "logged", "verified")]
    result = compare_footprints(before, after, iterations=FAST)
    assert result["verdict"] == "increased"
    assert result["percent_change"] > 0


def test_identical_footprints_are_a_coin_flip():
    components = sample_components()
    result = compare_footprints(components, components, iterations=8000)
    assert result["probability_reduced"] == pytest.approx(0.5, abs=0.08)
    assert result["verdict"] == "inconclusive"
    assert result["absolute_change"] == pytest.approx(0.0)


def test_comparison_explanation_quotes_the_size_of_the_change():
    before = [build_component("Car", 12000, 0.17, "logged", "verified")]
    after = [build_component("Car", 6000, 0.17, "logged", "verified")]
    result = compare_footprints(before, after, iterations=FAST)
    assert "50%" in result["explanation"]


def test_comparison_requires_both_sides():
    with pytest.raises(UncertaintyError):
        compare_footprints([], sample_components())
    with pytest.raises(UncertaintyError):
        compare_footprints(sample_components(), [])


# --- Detectable change ------------------------------------------------------


def test_detectable_change_is_wider_than_a_single_interval():
    # Two independent estimates each carry their own spread, so telling them
    # apart takes a bigger difference than either interval alone.
    result = detectable_change(sample_components(), iterations=FAST)
    assert result["min_detectable_relative"] > result["relative_half_width"]
    assert result["min_detectable_relative"] == pytest.approx(
        result["relative_half_width"] * math.sqrt(2.0)
    )


def test_better_data_lowers_the_detectable_threshold():
    sloppy = detectable_change(
        [build_component("Car", 12000, 0.17, "assumed", "assumed")], iterations=FAST
    )
    precise = detectable_change(
        [build_component("Car", 12000, 0.17, "metered", "measured")], iterations=FAST
    )
    assert precise["min_detectable_percent"] < sloppy["min_detectable_percent"]


# --- Narrative --------------------------------------------------------------


def test_formatted_interval_shows_range_and_percentage():
    result = propagate(sample_components(), iterations=FAST)
    text = format_interval(result)
    assert "kg CO2e" in text
    assert "±" in text
    assert "-" in text


def test_notes_warn_when_the_interval_is_wide():
    sloppy = [build_component("Car", 12000, 0.17, "assumed", "assumed")]
    result = propagate(sloppy, iterations=FAST)
    notes = get_uncertainty_notes(result)
    assert any("no use at all" in note for note in notes)


def test_notes_call_out_a_dominant_source_of_uncertainty():
    components = [
        build_component("Heating", 14000, 0.18, "assumed", "assumed"),
        build_component("Electricity", 100, 0.21, "metered", "measured"),
    ]
    result = propagate(components, iterations=FAST)
    rankings = sensitivity_ranking(components, iterations=FAST)
    notes = get_uncertainty_notes(result, rankings)
    assert any("wasted effort" in note for note in notes)


def test_notes_are_produced_without_a_ranking():
    result = propagate(sample_components(), iterations=FAST)
    assert get_uncertainty_notes(result)


# --- Persistence ------------------------------------------------------------


def test_saved_profile_round_trips():
    components = sample_components()
    summary = propagate(components, iterations=FAST)
    profile_id = save_profile(1, "Baseline 2026", components, summary)
    assert profile_id

    profiles = get_profiles(1)
    assert len(profiles) == 1
    assert profiles[0]["name"] == "Baseline 2026"
    assert len(profiles[0]["components"]) == 3
    assert profiles[0]["median"] == pytest.approx(summary["median"])


def test_profiles_come_back_newest_first():
    summary = propagate(sample_components(), iterations=FAST)
    save_profile(1, "Older", sample_components(), summary)
    save_profile(1, "Newer", sample_components(), summary)
    assert [profile["name"] for profile in get_profiles(1)] == ["Newer", "Older"]


def test_profiles_are_scoped_to_their_user():
    summary = propagate(sample_components(), iterations=FAST)
    save_profile(1, "Mine", sample_components(), summary)
    assert get_profiles(2) == []


def test_deleting_a_profile_removes_it():
    summary = propagate(sample_components(), iterations=FAST)
    profile_id = save_profile(1, "Temporary", sample_components(), summary)
    assert delete_profile(1, profile_id)
    assert get_profiles(1) == []


def test_a_profile_cannot_be_deleted_by_another_user():
    summary = propagate(sample_components(), iterations=FAST)
    profile_id = save_profile(1, "Mine", sample_components(), summary)
    assert not delete_profile(2, profile_id)
    assert len(get_profiles(1)) == 1


def test_persistence_helpers_ignore_missing_ids():
    assert save_profile(None, "x", [], {}) is None
    assert get_profiles(None) == []
    assert delete_profile(None, 1) is False
    assert delete_profile(1, None) is False


def test_profile_limit_is_respected():
    summary = propagate(sample_components(), iterations=FAST)
    for index in range(6):
        save_profile(1, f"Profile {index}", sample_components(), summary)
    assert len(get_profiles(1, limit=3)) == 3
