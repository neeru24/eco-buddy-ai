"""Tests for the Grid Carbon Intensity Load Scheduler."""
import os
import tempfile

import pytest

os.environ["ECO_BUDDY_DB"] = ":memory:"

import grid_scheduler
from grid_scheduler import (
    DEFAULT_DAYS_PER_YEAR,
    DEFAULT_GRID_PROFILE,
    DEFAULT_TARIFF,
    GRID_PROFILES,
    HOURS_IN_DAY,
    SHIFTABLE_LOADS,
    TARIFFS,
    allowed_start_hours,
    annual_savings,
    blend_curve,
    build_schedule,
    clean_intensity_curve,
    clean_tariff,
    delete_schedule,
    find_best_window,
    find_worst_window,
    get_intensity_curve,
    get_schedules,
    get_scheduling_tips,
    get_tariff,
    list_grid_profiles,
    list_shiftable_loads,
    peak_and_trough,
    save_schedule,
    schedule_load,
    shift_potential,
    window_average,
    window_hours,
)


@pytest.fixture(autouse=True)
def temp_db():
    """Point the module at a throwaway SQLite file for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
        db_path = handle.name
    original = grid_scheduler.DB_NAME
    grid_scheduler.DB_NAME = db_path
    yield db_path
    grid_scheduler.DB_NAME = original
    try:
        os.unlink(db_path)
    except OSError:
        pass


FLAT_CURVE = [200.0] * HOURS_IN_DAY

# A tiny hand-built curve: hours 3 and 4 are the cleanest pair in the day and
# hours 18 and 19 the dirtiest, which makes every window assertion checkable
# by hand.
TOY_CURVE = [
    300, 280, 240, 100, 100, 260, 320, 360, 340, 330, 320, 310,
    305, 300, 310, 330, 380, 460, 500, 500, 470, 420, 380, 340,
]


class TestReferenceData:
    def test_every_profile_has_24_hours(self):
        for name, curve in GRID_PROFILES.items():
            assert len(curve) == HOURS_IN_DAY, f"{name} is not a full day"
            assert all(value > 0 for value in curve)

    def test_every_tariff_has_24_hours(self):
        for name, prices in TARIFFS.items():
            assert len(prices) == HOURS_IN_DAY, f"{name} is not a full day"
            assert all(price >= 0 for price in prices)

    def test_get_intensity_curve_falls_back_for_unknown_profile(self):
        assert get_intensity_curve("Fusion someday") == GRID_PROFILES[DEFAULT_GRID_PROFILE]

    def test_get_tariff_falls_back_for_unknown_tariff(self):
        assert get_tariff("Barter") == TARIFFS[DEFAULT_TARIFF]

    def test_returned_curve_is_a_copy(self):
        curve = get_intensity_curve("Solar-heavy")
        curve[0] = 9999
        assert GRID_PROFILES["Solar-heavy"][0] != 9999

    def test_list_grid_profiles_sorted_by_average(self):
        profiles = list_grid_profiles()
        averages = [item["average_intensity"] for item in profiles]
        assert averages == sorted(averages)
        assert len(profiles) == len(GRID_PROFILES)

    def test_solar_grid_rewards_shifting_more_than_nuclear(self):
        assert shift_potential(GRID_PROFILES["Solar-heavy"]) > shift_potential(
            GRID_PROFILES["Nuclear baseload"]
        )

    def test_list_shiftable_loads_can_exclude_fixed_loads(self):
        every = list_shiftable_loads()
        flexible = list_shiftable_loads(shiftable_only=True)
        assert len(every) == len(SHIFTABLE_LOADS)
        assert len(flexible) < len(every)
        assert all(item["shiftable"] for item in flexible)

    def test_list_shiftable_loads_sorted_by_energy(self):
        draws = [item["kwh"] for item in list_shiftable_loads()]
        assert draws == sorted(draws, reverse=True)


class TestSeriesCleaning:
    def test_short_series_is_padded_to_a_full_day(self):
        cleaned = clean_intensity_curve([100, 110, 120])
        assert len(cleaned) == HOURS_IN_DAY
        assert cleaned[:3] == [100.0, 110.0, 120.0]

    def test_long_series_is_truncated(self):
        assert len(clean_intensity_curve([150] * 40)) == HOURS_IN_DAY

    def test_garbage_entries_fall_back_to_the_default_curve(self):
        cleaned = clean_intensity_curve(["oops", None, 120] + [200] * 21)
        default = GRID_PROFILES[DEFAULT_GRID_PROFILE]
        assert cleaned[0] == float(default[0])
        assert cleaned[1] == float(default[1])
        assert cleaned[2] == 120.0

    def test_negative_values_are_floored_at_zero(self):
        assert clean_intensity_curve([-50] * HOURS_IN_DAY)[0] == 0.0

    def test_absurd_values_are_capped(self):
        assert clean_intensity_curve([10 ** 9] * HOURS_IN_DAY)[0] == 2000.0

    def test_empty_series_returns_the_default_curve(self):
        assert clean_intensity_curve([]) == [float(v) for v in GRID_PROFILES[DEFAULT_GRID_PROFILE]]

    def test_tariff_cleaning_keeps_prices(self):
        cleaned = clean_tariff([0.1] * HOURS_IN_DAY)
        assert cleaned == [0.1] * HOURS_IN_DAY


class TestSolarBlending:
    def test_blended_curve_never_exceeds_the_original(self):
        base = GRID_PROFILES["Gas-balanced"]
        blended = blend_curve(base, 0.6)
        assert all(blended[hour] <= base[hour] + 1e-9 for hour in range(HOURS_IN_DAY))

    def test_night_hours_are_untouched(self):
        base = GRID_PROFILES["Gas-balanced"]
        blended = blend_curve(base, 0.9)
        assert blended[2] == pytest.approx(float(base[2]))

    def test_midday_is_reduced_the_most(self):
        base = GRID_PROFILES["Gas-balanced"]
        blended = blend_curve(base, 0.5)
        midday_cut = base[12] - blended[12]
        morning_cut = base[7] - blended[7]
        assert midday_cut > morning_cut

    def test_zero_share_is_a_no_op(self):
        base = GRID_PROFILES["Wind-heavy"]
        assert blend_curve(base, 0) == [float(value) for value in base]

    def test_share_is_clamped_and_never_goes_negative(self):
        blended = blend_curve(GRID_PROFILES["Coal-heavy"], 5.0)
        assert all(value >= 0 for value in blended)
        assert blended == blend_curve(GRID_PROFILES["Coal-heavy"], 1.0)

    def test_invalid_share_is_treated_as_none(self):
        base = GRID_PROFILES["Wind-heavy"]
        assert blend_curve(base, "lots") == [float(value) for value in base]


class TestWindows:
    def test_window_hours_wraps_across_midnight(self):
        assert window_hours(22, 4) == [22, 23, 0, 1]

    def test_window_hours_respects_duration_bounds(self):
        assert len(window_hours(0, 0)) == 1
        assert len(window_hours(0, 99)) == HOURS_IN_DAY

    def test_window_average_matches_hand_calculation(self):
        assert window_average(TOY_CURVE, 3, 2) == pytest.approx(100.0)
        assert window_average(TOY_CURVE, 18, 2) == pytest.approx(500.0)

    def test_window_average_wraps(self):
        expected = (TOY_CURVE[23] + TOY_CURVE[0]) / 2
        assert window_average(TOY_CURVE, 23, 2) == pytest.approx(expected)

    def test_best_window_finds_the_hand_picked_trough(self):
        best = find_best_window(TOY_CURVE, 2)
        assert best["start_hour"] == 3
        assert best["average_intensity"] == pytest.approx(100.0)
        assert best["hours"] == [3, 4]

    def test_worst_window_finds_the_hand_picked_peak(self):
        worst = find_worst_window(TOY_CURVE, 2)
        assert worst["start_hour"] == 18
        assert worst["average_intensity"] == pytest.approx(500.0)

    def test_best_is_never_worse_than_worst(self):
        for name, curve in GRID_PROFILES.items():
            for duration in (1, 2, 4, 6):
                best = find_best_window(curve, duration)
                worst = find_worst_window(curve, duration)
                assert best["average_intensity"] <= worst["average_intensity"], name

    def test_best_is_never_worse_than_the_daily_average(self):
        for curve in GRID_PROFILES.values():
            daily_average = sum(curve) / len(curve)
            assert find_best_window(curve, 3)["average_intensity"] <= daily_average + 1e-9

    def test_flat_curve_ties_resolve_to_the_earliest_hour(self):
        assert find_best_window(FLAT_CURVE, 3)["start_hour"] == 0
        assert find_worst_window(FLAT_CURVE, 3)["start_hour"] == 0

    def test_full_day_window_has_the_daily_average(self):
        best = find_best_window(TOY_CURVE, HOURS_IN_DAY)
        assert best["average_intensity"] == pytest.approx(
            sum(TOY_CURVE) / HOURS_IN_DAY, abs=0.01
        )

    def test_search_honours_candidate_hours(self):
        best = find_best_window(TOY_CURVE, 2, candidate_hours=[10, 11, 12])
        assert best["start_hour"] in (10, 11, 12)

    def test_end_hour_wraps(self):
        best = find_best_window(FLAT_CURVE, 3, candidate_hours=[23])
        assert best["start_hour"] == 23
        assert best["end_hour"] == 2


class TestAllowedStartHours:
    def test_equal_bounds_mean_no_constraint(self):
        assert allowed_start_hours(0, 0, 2) == list(range(HOURS_IN_DAY))
        assert allowed_start_hours(9, 9, 2) == list(range(HOURS_IN_DAY))

    def test_daytime_window_leaves_room_for_the_run(self):
        starts = allowed_start_hours(8, 17, 2)
        assert starts[0] == 8
        assert starts[-1] == 15
        assert len(starts) == 8

    def test_overnight_window_wraps(self):
        starts = allowed_start_hours(22, 6, 2)
        assert starts[0] == 22
        assert 0 in starts
        assert starts[-1] == 4

    def test_run_longer_than_the_window_falls_back_to_the_earliest_hour(self):
        assert allowed_start_hours(10, 12, 6) == [10]

    def test_every_start_keeps_the_run_inside_the_window(self):
        earliest, latest, duration = 9, 18, 3
        allowed = set(range(earliest, latest))
        for start in allowed_start_hours(earliest, latest, duration):
            assert set(window_hours(start, duration)).issubset(allowed)

    def test_out_of_range_hours_are_normalised(self):
        assert allowed_start_hours(25, 25, 2) == list(range(HOURS_IN_DAY))


class TestShiftPotential:
    def test_flat_curve_scores_zero(self):
        assert shift_potential(FLAT_CURVE) == 0.0

    def test_score_is_bounded(self):
        for curve in list(GRID_PROFILES.values()) + [TOY_CURVE, FLAT_CURVE]:
            assert 0.0 <= shift_potential(curve) <= 100.0

    def test_zero_curve_does_not_divide_by_zero(self):
        assert shift_potential([0] * HOURS_IN_DAY) == 0.0

    def test_deeper_trough_scores_higher(self):
        shallow = [200] * 12 + [220] * 12
        deep = [80] * 12 + [400] * 12
        assert shift_potential(deep) > shift_potential(shallow)


class TestPeakAndTrough:
    def test_identifies_the_hand_picked_hours(self):
        marks = peak_and_trough(TOY_CURVE)
        assert marks["greenest_hour"] == 3
        assert marks["dirtiest_hour"] == 18
        assert marks["greenest_intensity"] == 100.0
        assert marks["dirtiest_intensity"] == 500.0

    def test_spread_is_zero_for_a_flat_curve(self):
        assert peak_and_trough(FLAT_CURVE)["spread_pct"] == 0.0

    def test_spread_matches_hand_calculation(self):
        assert peak_and_trough(TOY_CURVE)["spread_pct"] == pytest.approx(80.0)


class TestScheduleLoad:
    def test_emissions_match_the_documented_formula(self):
        result = schedule_load("Dishwasher", TOY_CURVE)
        expected = SHIFTABLE_LOADS["Dishwasher"]["kwh"] * 100.0 / 1000.0
        assert result["co2_kg"] == pytest.approx(expected, abs=1e-4)

    def test_chooses_the_cleanest_window(self):
        result = schedule_load("Dishwasher", TOY_CURVE)
        assert result["start_hour"] == 3
        assert result["window_label"] == "03:00-05:00"

    def test_savings_are_never_negative(self):
        for name in SHIFTABLE_LOADS:
            for profile in GRID_PROFILES.values():
                result = schedule_load(name, profile)
                assert result["saving_vs_worst_kg"] >= 0
                assert result["saving_vs_average_kg"] >= 0

    def test_best_is_bounded_by_average_and_worst(self):
        result = schedule_load("EV charge", GRID_PROFILES["Solar-heavy"])
        assert result["co2_kg"] <= result["average_co2_kg"] + 1e-9
        assert result["average_co2_kg"] <= result["worst_co2_kg"] + 1e-9

    def test_flat_curve_yields_no_saving(self):
        result = schedule_load("Tumble dryer", FLAT_CURVE)
        assert result["saving_vs_worst_kg"] == pytest.approx(0.0, abs=1e-6)
        assert result["saving_vs_average_kg"] == pytest.approx(0.0, abs=1e-6)

    def test_constraints_are_honoured(self):
        result = schedule_load("Dishwasher", TOY_CURVE, earliest_hour=9, latest_hour=17)
        assert 9 <= result["start_hour"] <= 15
        assert result["constrained"] is True

    def test_unconstrained_runs_are_flagged_as_such(self):
        assert schedule_load("Dishwasher", TOY_CURVE)["constrained"] is False

    def test_custom_energy_and_duration_override_the_catalogue(self):
        result = schedule_load("Dishwasher", FLAT_CURVE, kwh=10.0, duration_hours=5)
        assert result["kwh"] == 10.0
        assert result["duration_hours"] == 5
        assert result["co2_kg"] == pytest.approx(10.0 * 200.0 / 1000.0)

    def test_unknown_load_still_produces_a_result(self):
        result = schedule_load("Bitcoin rig", TOY_CURVE, kwh=5.0, duration_hours=3)
        assert result["load"] == "Bitcoin rig"
        assert result["co2_kg"] > 0

    def test_negative_energy_is_floored(self):
        assert schedule_load("Dishwasher", TOY_CURVE, kwh=-4)["co2_kg"] == 0.0

    def test_cost_uses_the_tariff(self):
        prices = [1.0] * HOURS_IN_DAY
        result = schedule_load("Dishwasher", FLAT_CURVE, tariff=prices)
        assert result["cost"] == pytest.approx(SHIFTABLE_LOADS["Dishwasher"]["kwh"])

    def test_cost_conflict_is_detected(self):
        # Cheapest at hour 0, greenest at hour 12: the two cannot be satisfied
        # at once and the caller needs to know.
        curve = [500] * 12 + [100] * 12
        prices = [0.05] * 12 + [0.90] * 12
        result = schedule_load("Dishwasher", curve, tariff=prices)
        assert result["cost_conflict"] is True
        assert result["cheapest_start_hour"] == 0
        assert result["start_hour"] >= 12

    def test_no_conflict_when_green_and_cheap_align(self):
        curve = [500] * 12 + [100] * 12
        prices = [0.90] * 12 + [0.05] * 12
        assert schedule_load("Dishwasher", curve, tariff=prices)["cost_conflict"] is False


class TestBuildSchedule:
    def test_totals_equal_the_sum_of_the_parts(self):
        schedule = build_schedule(
            ["Dishwasher", "Washing machine", "EV charge"], GRID_PROFILES["Solar-heavy"]
        )
        assert schedule["total_kwh"] == pytest.approx(
            sum(item["kwh"] for item in schedule["loads"])
        )
        assert schedule["total_co2_kg"] == pytest.approx(
            sum(item["co2_kg"] for item in schedule["loads"]), abs=1e-4
        )

    def test_loads_are_ranked_by_saving(self):
        schedule = build_schedule(
            ["Washing machine", "EV charge", "Dishwasher"], GRID_PROFILES["Solar-heavy"]
        )
        savings = [item["saving_vs_average_kg"] for item in schedule["loads"]]
        assert savings == sorted(savings, reverse=True)

    def test_ev_charge_dominates_the_plan(self):
        schedule = build_schedule(
            ["Washing machine", "EV charge", "Dishwasher"], GRID_PROFILES["Solar-heavy"]
        )
        assert schedule["loads"][0]["load"] == "EV charge"

    def test_daily_savings_are_never_negative(self):
        for profile in GRID_PROFILES.values():
            schedule = build_schedule(list(SHIFTABLE_LOADS), profile)
            assert schedule["daily_saving_vs_average_kg"] >= 0
            assert schedule["daily_saving_vs_worst_kg"] >= 0

    def test_worst_is_never_below_best(self):
        schedule = build_schedule(list(SHIFTABLE_LOADS), GRID_PROFILES["Coal-heavy"])
        assert schedule["worst_co2_kg"] >= schedule["total_co2_kg"]

    def test_empty_plan_is_all_zeroes(self):
        schedule = build_schedule([], GRID_PROFILES["Gas-balanced"])
        assert schedule["loads"] == []
        assert schedule["total_kwh"] == 0
        assert schedule["total_co2_kg"] == 0
        assert schedule["daily_saving_vs_average_kg"] == 0

    def test_none_load_list_is_handled(self):
        assert build_schedule(None, GRID_PROFILES["Gas-balanced"])["loads"] == []

    def test_per_load_constraints_are_applied(self):
        schedule = build_schedule(
            ["Dishwasher"],
            TOY_CURVE,
            constraints={"Dishwasher": {"earliest_hour": 12, "latest_hour": 16}},
        )
        assert 12 <= schedule["loads"][0]["start_hour"] <= 14

    def test_schedule_carries_grid_diagnostics(self):
        schedule = build_schedule(["Dishwasher"], TOY_CURVE)
        assert schedule["shift_potential"] == shift_potential(TOY_CURVE)
        assert schedule["peak_and_trough"]["greenest_hour"] == 3


class TestAnnualSavings:
    def test_scales_the_daily_figure(self):
        schedule = build_schedule(["EV charge"], GRID_PROFILES["Solar-heavy"])
        annual = annual_savings(schedule, days_per_year=100)
        assert annual["co2_saved_kg"] == pytest.approx(
            schedule["daily_saving_vs_average_kg"] * 100, abs=0.01
        )

    def test_defaults_to_the_module_constant(self):
        schedule = build_schedule(["Dishwasher"], GRID_PROFILES["Solar-heavy"])
        assert annual_savings(schedule)["days_per_year"] == DEFAULT_DAYS_PER_YEAR

    def test_zero_days_means_zero_saving(self):
        schedule = build_schedule(["EV charge"], GRID_PROFILES["Solar-heavy"])
        assert annual_savings(schedule, days_per_year=0)["co2_saved_kg"] == 0.0

    def test_invalid_day_count_falls_back(self):
        schedule = build_schedule(["Dishwasher"], GRID_PROFILES["Solar-heavy"])
        assert annual_savings(schedule, days_per_year="soon")["days_per_year"] == (
            DEFAULT_DAYS_PER_YEAR
        )

    def test_negative_day_count_is_floored(self):
        schedule = build_schedule(["Dishwasher"], GRID_PROFILES["Solar-heavy"])
        assert annual_savings(schedule, days_per_year=-5)["days_per_year"] == 0

    def test_cost_penalty_is_never_negative(self):
        curve = [500] * 12 + [100] * 12
        prices = [0.05] * 12 + [0.90] * 12
        schedule = build_schedule(["Dishwasher", "EV charge"], curve, tariff=prices)
        assert annual_savings(schedule)["cost_penalty"] >= 0

    def test_no_penalty_when_green_is_also_cheap(self):
        curve = [500] * 12 + [100] * 12
        prices = [0.90] * 12 + [0.05] * 12
        schedule = build_schedule(["Dishwasher"], curve, tariff=prices)
        assert annual_savings(schedule)["cost_penalty"] == pytest.approx(0.0, abs=1e-6)


class TestTips:
    def test_flat_grid_says_do_not_bother(self):
        schedule = build_schedule(["Dishwasher"], FLAT_CURVE)
        tips = get_scheduling_tips(schedule, FLAT_CURVE)
        assert len(tips) == 1
        assert "flat" in tips[0].lower()

    def test_variable_grid_gets_actionable_advice(self):
        schedule = build_schedule(["EV charge", "Dishwasher"], TOY_CURVE)
        tips = get_scheduling_tips(schedule, TOY_CURVE)
        assert len(tips) > 1
        assert any("greenest" in tip.lower() for tip in tips)

    def test_limit_is_respected(self):
        schedule = build_schedule(list(SHIFTABLE_LOADS), TOY_CURVE)
        assert len(get_scheduling_tips(schedule, TOY_CURVE, limit=2)) <= 2

    def test_zero_limit_returns_nothing(self):
        schedule = build_schedule(["Dishwasher"], TOY_CURVE)
        assert get_scheduling_tips(schedule, TOY_CURVE, limit=0) == []

    def test_cost_conflict_is_mentioned(self):
        curve = [500] * 12 + [100] * 12
        prices = [0.05] * 12 + [0.90] * 12
        schedule = build_schedule(["Dishwasher"], curve, tariff=prices)
        tips = get_scheduling_tips(schedule, curve)
        assert any("cheapest" in tip.lower() for tip in tips)


class TestPersistence:
    def test_save_and_load_round_trip(self):
        schedule = build_schedule(["Dishwasher", "EV charge"], GRID_PROFILES["Solar-heavy"])
        schedule_id = save_schedule(1, "Weekday", schedule, "Solar-heavy", "Flat rate")
        assert schedule_id is not None

        saved = get_schedules(1)
        assert len(saved) == 1
        assert saved[0]["schedule_name"] == "Weekday"
        assert saved[0]["grid_profile"] == "Solar-heavy"
        assert saved[0]["total_co2_kg"] == pytest.approx(schedule["total_co2_kg"])
        assert len(saved[0]["detail"]["loads"]) == 2

    def test_blank_name_gets_a_default(self):
        schedule = build_schedule(["Dishwasher"], GRID_PROFILES["Gas-balanced"])
        save_schedule(2, "   ", schedule)
        assert get_schedules(2)[0]["schedule_name"] == "My day"

    def test_schedules_are_scoped_per_user(self):
        schedule = build_schedule(["Dishwasher"], GRID_PROFILES["Gas-balanced"])
        save_schedule(10, "Mine", schedule)
        save_schedule(11, "Theirs", schedule)
        assert len(get_schedules(10)) == 1
        assert get_schedules(10)[0]["schedule_name"] == "Mine"

    def test_limit_is_applied(self):
        schedule = build_schedule(["Dishwasher"], GRID_PROFILES["Gas-balanced"])
        for index in range(5):
            save_schedule(3, f"Plan {index}", schedule)
        assert len(get_schedules(3, limit=2)) == 2

    def test_delete_removes_only_the_target(self):
        schedule = build_schedule(["Dishwasher"], GRID_PROFILES["Gas-balanced"])
        first = save_schedule(4, "One", schedule)
        save_schedule(4, "Two", schedule)
        assert delete_schedule(first) is True
        remaining = get_schedules(4)
        assert len(remaining) == 1
        assert remaining[0]["schedule_name"] == "Two"

    def test_deleting_a_missing_row_returns_false(self):
        assert delete_schedule(999999) is False

    def test_no_schedules_for_a_new_user(self):
        assert get_schedules(12345) == []
