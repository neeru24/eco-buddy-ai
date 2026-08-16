"""Tests for the Digital Carbon Footprint tracker."""
import os
import tempfile

import pytest

os.environ["ECO_BUDDY_DB"] = ":memory:"

import digital_footprint
from digital_footprint import (
    DAYS_PER_YEAR,
    DEFAULT_GRID_INTENSITY,
    DEFAULT_STREAMING_QUALITY,
    DIGITAL_ACTIVITIES,
    GRID_INTENSITY_BY_REGION,
    REDUCTION_ACTIONS,
    STAGES,
    STREAMING_QUALITY_FACTORS,
    activity_emissions,
    build_summary_text,
    calculate_digital_footprint,
    compare_to_physical,
    default_usage,
    delete_digital_assessment,
    estimate_savings,
    get_digital_assessments,
    get_digital_tips,
    get_digital_trend,
    get_grid_intensity,
    get_streaming_quality_factor,
    list_activities,
    recommend_actions,
    save_digital_assessment,
    usage_from_assessment,
)


@pytest.fixture(autouse=True)
def temp_db():
    """Point the module at a throwaway SQLite file for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
        db_path = handle.name
    original = digital_footprint.DB_NAME
    digital_footprint.DB_NAME = db_path
    yield db_path
    digital_footprint.DB_NAME = original
    try:
        os.unlink(db_path)
    except OSError:
        pass


# --------------------------------------------------------------------------
# Catalogue integrity
# --------------------------------------------------------------------------

def test_every_activity_declares_all_required_fields():
    required = {
        "label", "icon", "unit", "periodicity", "kwh_per_unit",
        "quality_sensitive", "default", "max", "source",
    }
    for key, info in DIGITAL_ACTIVITIES.items():
        assert required <= set(info), f"{key} is missing fields"
        assert info["periodicity"] in ("daily", "annual")
        assert set(info["kwh_per_unit"]) == set(STAGES)
        assert all(v >= 0 for v in info["kwh_per_unit"].values())
        assert 0 <= info["default"] <= info["max"]


def test_only_streaming_is_quality_sensitive():
    sensitive = [k for k, v in DIGITAL_ACTIVITIES.items() if v["quality_sensitive"]]
    assert sensitive == ["video_streaming"]


def test_list_activities_includes_keys():
    activities = list_activities()
    assert len(activities) == len(DIGITAL_ACTIVITIES)
    assert {item["key"] for item in activities} == set(DIGITAL_ACTIVITIES)


def test_default_usage_matches_catalogue_defaults():
    usage = default_usage()
    assert usage == {k: v["default"] for k, v in DIGITAL_ACTIVITIES.items()}


def test_every_reduction_action_targets_a_real_activity():
    for key, action in REDUCTION_ACTIONS.items():
        assert action["activity"] in DIGITAL_ACTIVITIES, key
        assert 0 < action["reduction"] <= 1


# --------------------------------------------------------------------------
# Grid intensity and quality factors
# --------------------------------------------------------------------------

def test_get_grid_intensity_known_and_unknown_regions():
    assert get_grid_intensity("UK") == GRID_INTENSITY_BY_REGION["UK"]
    assert get_grid_intensity("Atlantis") == DEFAULT_GRID_INTENSITY
    assert get_grid_intensity(None) == DEFAULT_GRID_INTENSITY


def test_streaming_quality_factor_ordering():
    factors = [STREAMING_QUALITY_FACTORS[q] for q in STREAMING_QUALITY_FACTORS]
    assert factors == sorted(factors), "quality tiers must increase with resolution"
    assert get_streaming_quality_factor("4K (2160p)") > get_streaming_quality_factor("SD (480p)")
    assert get_streaming_quality_factor("nonsense") == STREAMING_QUALITY_FACTORS[DEFAULT_STREAMING_QUALITY]
    assert get_streaming_quality_factor(None) == STREAMING_QUALITY_FACTORS[DEFAULT_STREAMING_QUALITY]


# --------------------------------------------------------------------------
# Per activity maths
# --------------------------------------------------------------------------

def test_activity_emissions_matches_hand_calculation():
    # 1 hour/day of web browsing at a 0.5 kg/kWh grid.
    info = DIGITAL_ACTIVITIES["web_browsing"]
    expected_kwh = sum(info["kwh_per_unit"].values()) * DAYS_PER_YEAR
    result = activity_emissions("web_browsing", 1.0, grid_intensity=0.5)
    assert result["annual_kwh"] == pytest.approx(expected_kwh, rel=1e-6)
    assert result["annual_kg"] == pytest.approx(expected_kwh * 0.5, rel=1e-6)


def test_annual_unit_activity_is_not_multiplied_by_days():
    info = DIGITAL_ACTIVITIES["cloud_storage"]
    assert info["periodicity"] == "annual"
    result = activity_emissions("cloud_storage", 100.0, grid_intensity=1.0)
    expected = 100.0 * sum(info["kwh_per_unit"].values())
    assert result["annual_kwh"] == pytest.approx(expected, rel=1e-6)
    assert result["annual_units"] == 100.0


def test_stage_split_sums_to_total():
    result = activity_emissions("video_streaming", 3.0, grid_intensity=0.4)
    assert sum(result["stages"].values()) == pytest.approx(result["annual_kg"], abs=0.01)


def test_streaming_quality_changes_the_result():
    sd = activity_emissions("video_streaming", 2.0, 0.475, "SD (480p)")
    uhd = activity_emissions("video_streaming", 2.0, 0.475, "4K (2160p)")
    assert uhd["annual_kg"] > sd["annual_kg"]
    ratio = STREAMING_QUALITY_FACTORS["4K (2160p)"] / STREAMING_QUALITY_FACTORS["SD (480p)"]
    assert uhd["annual_kg"] / sd["annual_kg"] == pytest.approx(ratio, rel=1e-3)


def test_quality_is_ignored_for_non_streaming_activities():
    sd = activity_emissions("email", 50, 0.475, "SD (480p)")
    uhd = activity_emissions("email", 50, 0.475, "4K (2160p)")
    assert sd["annual_kg"] == uhd["annual_kg"]
    assert sd["quality_multiplier"] == 1.0


def test_negative_and_garbage_amounts_are_clamped_to_zero():
    assert activity_emissions("email", -500)["annual_kg"] == 0.0
    assert activity_emissions("email", None)["annual_kg"] == 0.0
    assert activity_emissions("email", "not a number")["annual_kg"] == 0.0


def test_amount_is_capped_at_the_activity_maximum():
    info = DIGITAL_ACTIVITIES["video_streaming"]
    result = activity_emissions("video_streaming", 9999.0)
    assert result["amount"] == info["max"]


def test_unknown_activity_raises():
    with pytest.raises(KeyError):
        activity_emissions("telepathy", 1.0)


def test_zero_grid_intensity_produces_zero_emissions_but_real_energy():
    result = activity_emissions("online_gaming", 4.0, grid_intensity=0.0)
    assert result["annual_kg"] == 0.0
    assert result["annual_kwh"] > 0


# --------------------------------------------------------------------------
# Full footprint
# --------------------------------------------------------------------------

def test_total_equals_sum_of_activities():
    usage = default_usage()
    result = calculate_digital_footprint(usage)
    parts = sum(item["annual_kg"] for item in result["breakdown"].values())
    assert result["annual_kg"] == pytest.approx(parts, abs=0.05)


def test_stage_totals_sum_to_annual_total():
    result = calculate_digital_footprint(default_usage())
    assert sum(result["stage_totals"].values()) == pytest.approx(
        result["annual_kg"], abs=0.1
    )


def test_shares_add_up_to_one_hundred_percent():
    result = calculate_digital_footprint(default_usage())
    total_share = sum(item["share_pct"] for item in result["breakdown"].values())
    assert total_share == pytest.approx(100.0, abs=0.5)


def test_empty_usage_produces_a_zero_footprint():
    result = calculate_digital_footprint({})
    assert result["annual_kg"] == 0.0
    assert result["top_activity"] is None
    assert all(item["share_pct"] == 0.0 for item in result["breakdown"].values())


def test_none_usage_is_handled():
    assert calculate_digital_footprint(None)["annual_kg"] == 0.0


def test_unknown_usage_keys_are_ignored():
    result = calculate_digital_footprint({"teleportation": 500.0})
    assert result["annual_kg"] == 0.0
    assert "teleportation" not in result["breakdown"]


def test_ranked_is_ordered_and_top_activity_agrees():
    result = calculate_digital_footprint(default_usage())
    values = [item["annual_kg"] for item in result["ranked"]]
    assert values == sorted(values, reverse=True)
    assert result["top_activity"] == result["ranked"][0]["key"]


def test_monthly_and_daily_totals_are_consistent():
    result = calculate_digital_footprint(default_usage())
    assert result["monthly_kg"] == pytest.approx(result["annual_kg"] / 12, abs=0.05)
    assert result["daily_kg"] == pytest.approx(
        result["annual_kg"] / DAYS_PER_YEAR, abs=0.05
    )


def test_cleaner_grid_lowers_the_footprint():
    usage = default_usage()
    dirty = calculate_digital_footprint(usage, GRID_INTENSITY_BY_REGION["India"])
    clean = calculate_digital_footprint(usage, GRID_INTENSITY_BY_REGION["Nordics"])
    assert clean["annual_kg"] < dirty["annual_kg"]


# --------------------------------------------------------------------------
# Savings simulator
# --------------------------------------------------------------------------

def test_estimate_savings_reduces_the_projected_total():
    usage = default_usage()
    savings = estimate_savings(usage, ["downgrade_streaming", "camera_off"])
    assert savings["total_saved_kg"] > 0
    assert savings["projected_kg"] < savings["baseline_kg"]
    assert savings["projected_kg"] == pytest.approx(
        savings["baseline_kg"] - savings["total_saved_kg"], abs=0.05
    )


def test_savings_never_exceed_the_baseline():
    savings = estimate_savings(default_usage(), list(REDUCTION_ACTIONS))
    assert savings["total_saved_kg"] <= savings["baseline_kg"]
    assert savings["projected_kg"] >= 0
    assert 0 <= savings["reduction_pct"] <= 100


def test_no_actions_means_no_savings():
    savings = estimate_savings(default_usage(), [])
    assert savings["total_saved_kg"] == 0
    assert savings["projected_kg"] == savings["baseline_kg"]
    assert savings["actions"] == []


def test_unknown_actions_are_ignored():
    savings = estimate_savings(default_usage(), ["become_a_hermit"])
    assert savings["actions"] == []


def test_savings_actions_are_sorted_by_impact():
    savings = estimate_savings(default_usage(), list(REDUCTION_ACTIONS))
    values = [item["saved_kg"] for item in savings["actions"]]
    assert values == sorted(values, reverse=True)


def test_savings_on_zero_usage_are_zero():
    savings = estimate_savings({}, list(REDUCTION_ACTIONS))
    assert savings["total_saved_kg"] == 0
    assert savings["reduction_pct"] == 0.0


def test_recommend_actions_skips_unused_activities():
    usage = {key: 0.0 for key in DIGITAL_ACTIVITIES}
    usage["email"] = 100.0
    actions = recommend_actions(calculate_digital_footprint(usage), limit=5)
    assert actions
    assert all(item["activity"] == "email" for item in actions)


def test_recommend_actions_respects_the_limit():
    result = calculate_digital_footprint(default_usage())
    assert len(recommend_actions(result, limit=2)) == 2
    assert recommend_actions(result, limit=0) == []


# --------------------------------------------------------------------------
# Tips and equivalents
# --------------------------------------------------------------------------

def test_tips_lead_with_the_biggest_contributor():
    result = calculate_digital_footprint(default_usage())
    tips = get_digital_tips(result)
    assert tips
    assert tips[0]["activity"] == result["top_activity"]


def test_tips_are_empty_without_usage():
    assert get_digital_tips(calculate_digital_footprint({})) == []


def test_tips_respect_the_limit():
    result = calculate_digital_footprint(default_usage())
    assert len(get_digital_tips(result, limit=3)) == 3


def test_physical_equivalents_scale_with_emissions():
    small = compare_to_physical(10)
    large = compare_to_physical(100)
    assert large["km_driven"] > small["km_driven"]
    assert large["trees_to_offset"] > small["trees_to_offset"]
    assert compare_to_physical(0)["km_driven"] == 0
    assert compare_to_physical(None)["trees_to_offset"] == 0


def test_summary_text_mentions_the_top_activity():
    result = calculate_digital_footprint(default_usage())
    summary = build_summary_text(result)
    assert DIGITAL_ACTIVITIES[result["top_activity"]]["label"] in summary


def test_summary_text_handles_no_activity():
    assert "No digital activity" in build_summary_text(calculate_digital_footprint({}))


# --------------------------------------------------------------------------
# Persistence
# --------------------------------------------------------------------------

def test_save_and_read_back_an_assessment():
    usage = default_usage()
    result = calculate_digital_footprint(usage)
    row_id = save_digital_assessment(7, usage, result)
    assert row_id

    saved = get_digital_assessments(7)
    assert len(saved) == 1
    assert saved[0]["annual_kg"] == pytest.approx(result["annual_kg"], abs=0.01)
    assert saved[0]["usage"]["email"] == usage["email"]
    assert "video_streaming" in saved[0]["breakdown"]


def test_assessments_are_scoped_per_user():
    usage = default_usage()
    result = calculate_digital_footprint(usage)
    save_digital_assessment(1, usage, result)
    save_digital_assessment(2, usage, result)
    assert len(get_digital_assessments(1)) == 1
    assert len(get_digital_assessments(99)) == 0


def test_assessment_limit_is_respected():
    usage = default_usage()
    result = calculate_digital_footprint(usage)
    for _ in range(5):
        save_digital_assessment(3, usage, result)
    assert len(get_digital_assessments(3, limit=2)) == 2


def test_delete_assessment():
    usage = default_usage()
    row_id = save_digital_assessment(4, usage, calculate_digital_footprint(usage))
    assert delete_digital_assessment(row_id) is True
    assert get_digital_assessments(4) == []
    assert delete_digital_assessment(row_id) is False


def test_trend_reports_an_improvement():
    heavy = default_usage()
    light = {key: 0.0 for key in DIGITAL_ACTIVITIES}
    save_digital_assessment(5, heavy, calculate_digital_footprint(heavy))
    save_digital_assessment(5, light, calculate_digital_footprint(light))

    trend = get_digital_trend(5)
    assert trend["entries"] == 2
    assert trend["improving"] is True
    assert trend["change_kg"] < 0


def test_trend_with_a_single_entry_reports_no_change():
    usage = default_usage()
    save_digital_assessment(6, usage, calculate_digital_footprint(usage))
    trend = get_digital_trend(6)
    assert trend["entries"] == 1
    assert trend["change_kg"] == 0.0
    assert trend["change_pct"] == 0.0


def test_trend_for_a_user_with_no_data():
    trend = get_digital_trend(1234)
    assert trend["series"] == []
    assert trend["entries"] == 0


def test_usage_from_assessment_restores_saved_values():
    usage = default_usage()
    usage["email"] = 123.0
    save_digital_assessment(8, usage, calculate_digital_footprint(usage))
    restored = usage_from_assessment(get_digital_assessments(8)[0])
    assert restored["email"] == 123.0
    assert set(restored) == set(DIGITAL_ACTIVITIES)


def test_usage_from_assessment_handles_missing_data():
    restored = usage_from_assessment(None)
    assert restored == default_usage()
