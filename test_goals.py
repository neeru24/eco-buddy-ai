import datetime

import pytest

from goals import (
    AT_RISK_THRESHOLD,
    DAYS_PER_MONTH,
    GOAL_ACTIVE,
    REDUCTION_CEILINGS,
    STATUS_ACHIEVED,
    STATUS_AHEAD,
    STATUS_AT_RISK,
    STATUS_OFF_TRACK,
    STATUS_ON_TRACK,
    GoalValidationError,
    allocate_reduction,
    build_pathway,
    classify_status,
    create_goal,
    evaluate_progress,
    expected_footprint_at,
    goal_to_dict,
    latest_footprint,
    months_between,
    observed_pace,
    pathway_to_series,
    project_final_footprint,
    reduction_percentage,
    required_daily_reduction,
    required_monthly_reduction,
    suggest_feasible_target,
    summarize_goal,
    total_reduction_required,
    validate_goal,
)

START = datetime.date(2026, 1, 1)
END = datetime.date(2027, 1, 1)


def make_goal(baseline=5000.0, target=3500.0, start=START, end=END):
    return create_goal(baseline, target, start, end, user_id=1)


def assessment_row(record_date, footprint):
    """Build a row shaped exactly like database.get_assessments() returns."""
    return (1, record_date.isoformat(), "Car", 10.0, 300.0, "Vegetarian", 2, footprint, 60)


# --- Goal construction and validation ---------------------------------------

def test_create_goal_returns_normalized_record():
    goal = make_goal()
    assert goal["baseline_kg"] == 5000.0
    assert goal["target_kg"] == 3500.0
    assert goal["start_date"] == START
    assert goal["target_date"] == END
    assert goal["status"] == GOAL_ACTIVE


def test_create_goal_accepts_iso_strings():
    goal = create_goal(5000, 3500, "2026-01-01", "2027-01-01")
    assert goal["start_date"] == START
    assert goal["target_date"] == END


def test_create_goal_accepts_sqlite_timestamp_strings():
    goal = create_goal(5000, 3500, "2026-01-01 00:00:00", "2027-01-01 12:30:00")
    assert goal["start_date"] == START
    assert goal["target_date"] == END


def test_create_goal_accepts_datetime_objects():
    goal = create_goal(
        5000, 3500,
        datetime.datetime(2026, 1, 1, 8, 0),
        datetime.datetime(2027, 1, 1, 8, 0),
    )
    assert goal["start_date"] == START


def test_target_above_baseline_is_rejected():
    with pytest.raises(GoalValidationError, match="must be below"):
        create_goal(3000, 4000, START, END)


def test_target_equal_to_baseline_is_rejected():
    with pytest.raises(GoalValidationError):
        create_goal(3000, 3000, START, END)


def test_target_date_before_start_is_rejected():
    with pytest.raises(GoalValidationError, match="after start_date"):
        create_goal(5000, 3500, END, START)


def test_window_shorter_than_one_month_is_rejected():
    with pytest.raises(GoalValidationError, match="shorter than one month"):
        create_goal(5000, 3500, START, START + datetime.timedelta(days=10))


def test_non_numeric_baseline_is_rejected():
    with pytest.raises(GoalValidationError, match="must be a number"):
        create_goal("not-a-number", 3500, START, END)


def test_zero_baseline_is_rejected():
    with pytest.raises(GoalValidationError, match="greater than zero"):
        create_goal(0, 0, START, END)


def test_malformed_date_string_is_rejected():
    with pytest.raises(GoalValidationError, match="ISO-8601"):
        create_goal(5000, 3500, "01/01/2026", END)


def test_validate_goal_accepts_a_valid_goal():
    assert validate_goal(make_goal()) is True


# --- Pace arithmetic --------------------------------------------------------

def test_total_reduction_required():
    assert total_reduction_required(make_goal()) == 1500.0


def test_reduction_percentage():
    assert reduction_percentage(make_goal()) == pytest.approx(30.0)


def test_required_monthly_reduction_over_a_year():
    # 1500 kg spread over ~12 months
    pace = required_monthly_reduction(make_goal())
    assert pace == pytest.approx(1500.0 / (365 / DAYS_PER_MONTH), rel=1e-6)
    assert 120 < pace < 130


def test_required_daily_reduction_is_monthly_over_month_length():
    goal = make_goal()
    assert required_daily_reduction(goal) == pytest.approx(
        required_monthly_reduction(goal) / DAYS_PER_MONTH
    )


def test_months_between_is_symmetric_in_sign():
    assert months_between(START, END) == pytest.approx(-months_between(END, START))


# --- Pathway ----------------------------------------------------------------

def test_pathway_starts_at_baseline_and_ends_exactly_on_target():
    pathway = build_pathway(make_goal())
    assert pathway[0]["target_kg"] == 5000.0
    assert pathway[0]["date"] == START
    assert pathway[-1]["target_kg"] == 3500.0
    assert pathway[-1]["date"] == END


def test_pathway_is_monotonically_decreasing():
    values = [point["target_kg"] for point in build_pathway(make_goal())]
    assert all(a >= b for a, b in zip(values, values[1:]))


def test_pathway_respects_explicit_point_count():
    assert len(build_pathway(make_goal(), points=5)) == 5


def test_pathway_never_returns_fewer_than_two_points():
    assert len(build_pathway(make_goal(), points=1)) == 2


def test_pathway_to_series_splits_into_parallel_lists():
    pathway = build_pathway(make_goal(), points=4)
    dates, values = pathway_to_series(pathway)
    assert len(dates) == len(values) == 4
    assert dates[0] == START


def test_expected_footprint_is_clamped_before_start():
    assert expected_footprint_at(make_goal(), START - datetime.timedelta(days=30)) == 5000.0


def test_expected_footprint_is_clamped_after_end():
    assert expected_footprint_at(make_goal(), END + datetime.timedelta(days=30)) == 3500.0


def test_expected_footprint_at_midpoint_is_halfway():
    midpoint = START + datetime.timedelta(days=182)
    expected = expected_footprint_at(make_goal(), midpoint)
    assert expected == pytest.approx(4250.0, abs=15)


# --- Observed pace ----------------------------------------------------------

def test_observed_pace_is_zero_without_enough_data():
    assert observed_pace([]) == 0.0
    assert observed_pace([assessment_row(START, 5000)]) == 0.0


def test_observed_pace_is_positive_when_footprint_falls():
    records = [
        assessment_row(START, 5000),
        assessment_row(START + datetime.timedelta(days=30), 4900),
        assessment_row(START + datetime.timedelta(days=60), 4800),
    ]
    pace = observed_pace(records)
    assert pace > 0
    assert pace == pytest.approx(100.0, rel=0.05)


def test_observed_pace_is_negative_when_footprint_rises():
    records = [
        assessment_row(START, 4000),
        assessment_row(START + datetime.timedelta(days=30), 4200),
    ]
    assert observed_pace(records) < 0


def test_observed_pace_handles_identical_dates():
    records = [assessment_row(START, 5000), assessment_row(START, 4000)]
    assert observed_pace(records) == 0.0


def test_observed_pace_ignores_unusable_rows():
    records = [
        assessment_row(START, 5000),
        (2, None, "Car", 1, 1, "Vegan", 0, 4000, 50),
        (3, START.isoformat(), "Car", 1, 1, "Vegan", 0, None, 50),
        assessment_row(START + datetime.timedelta(days=30), 4900),
    ]
    assert observed_pace(records) == pytest.approx(100.0, rel=0.05)


def test_records_are_sorted_before_use():
    unsorted_records = [
        assessment_row(START + datetime.timedelta(days=60), 4800),
        assessment_row(START, 5000),
    ]
    assert latest_footprint(unsorted_records) == 4800


def test_latest_footprint_is_none_for_empty_history():
    assert latest_footprint([]) is None


def test_dict_records_are_accepted():
    records = [
        {"date": START, "footprint": 5000},
        {"date": START + datetime.timedelta(days=30), "footprint": 4900},
    ]
    assert observed_pace(records) == pytest.approx(100.0, rel=0.05)


# --- Projection -------------------------------------------------------------

def test_projection_extends_the_observed_pace():
    records = [
        assessment_row(START, 5000),
        assessment_row(START + datetime.timedelta(days=30), 4900),
    ]
    as_of = START + datetime.timedelta(days=30)
    projected = project_final_footprint(make_goal(), records, as_of=as_of)
    # ~11 months left at ~100 kg/month off 4900
    assert projected == pytest.approx(3800, abs=120)


def test_projection_never_goes_below_zero():
    records = [
        assessment_row(START, 5000),
        assessment_row(START + datetime.timedelta(days=30), 500),
    ]
    assert project_final_footprint(make_goal(), records, as_of=START + datetime.timedelta(days=30)) >= 0.0


def test_projection_falls_back_to_baseline_without_history():
    goal = make_goal()
    assert project_final_footprint(goal, [], as_of=END) == goal["baseline_kg"]


# --- Status classification --------------------------------------------------

def test_status_achieved_when_target_reached():
    goal = make_goal()
    assert classify_status(goal, variance_kg=0, current_kg=3400) == STATUS_ACHIEVED


def test_status_ahead_for_large_negative_variance():
    goal = make_goal()
    assert classify_status(goal, variance_kg=-300, current_kg=4000) == STATUS_AHEAD


def test_status_on_track_for_small_variance():
    goal = make_goal()
    assert classify_status(goal, variance_kg=10, current_kg=4000) == STATUS_ON_TRACK


def test_status_at_risk_for_moderate_variance():
    goal = make_goal()
    variance = total_reduction_required(goal) * 0.10
    assert classify_status(goal, variance_kg=variance, current_kg=4600) == STATUS_AT_RISK


def test_status_off_track_beyond_the_at_risk_threshold():
    goal = make_goal()
    variance = total_reduction_required(goal) * (AT_RISK_THRESHOLD + 0.05)
    assert classify_status(goal, variance_kg=variance, current_kg=4900) == STATUS_OFF_TRACK


# --- End-to-end progress evaluation -----------------------------------------

def test_evaluate_progress_without_history_sits_on_baseline():
    goal = make_goal()
    progress = evaluate_progress(goal, [], as_of=START)
    assert progress["has_data"] is False
    assert progress["current_kg"] == 5000.0
    assert progress["percent_complete"] == 0.0
    assert progress["record_count"] == 0


def test_evaluate_progress_reports_percent_complete():
    goal = make_goal()
    records = [assessment_row(START + datetime.timedelta(days=180), 4250)]
    progress = evaluate_progress(goal, records, as_of=START + datetime.timedelta(days=180))
    # Half the 1500 kg reduction achieved
    assert progress["percent_complete"] == pytest.approx(50.0, abs=1.0)


def test_evaluate_progress_percent_complete_is_clamped():
    goal = make_goal()
    over_achieved = [assessment_row(START + datetime.timedelta(days=60), 1000)]
    assert evaluate_progress(goal, over_achieved, as_of=START + datetime.timedelta(days=60))["percent_complete"] == 100.0

    regressed = [assessment_row(START + datetime.timedelta(days=60), 6000)]
    assert evaluate_progress(goal, regressed, as_of=START + datetime.timedelta(days=60))["percent_complete"] == 0.0


def test_evaluate_progress_variance_is_negative_when_ahead():
    goal = make_goal()
    as_of = START + datetime.timedelta(days=180)
    records = [assessment_row(as_of, 3900)]
    progress = evaluate_progress(goal, records, as_of=as_of)
    assert progress["variance_kg"] < 0
    assert progress["status"] in (STATUS_AHEAD, STATUS_ACHIEVED)


def test_evaluate_progress_flags_off_track():
    goal = make_goal()
    as_of = START + datetime.timedelta(days=300)
    records = [assessment_row(as_of, 5000)]
    progress = evaluate_progress(goal, records, as_of=as_of)
    assert progress["status"] == STATUS_OFF_TRACK
    assert progress["projected_shortfall_kg"] > 0


def test_evaluate_progress_reports_achieved():
    goal = make_goal()
    as_of = START + datetime.timedelta(days=200)
    progress = evaluate_progress(goal, [assessment_row(as_of, 3400)], as_of=as_of)
    assert progress["status"] == STATUS_ACHIEVED
    assert progress["remaining_kg"] == 0.0


def test_evaluate_progress_days_remaining_never_negative():
    goal = make_goal()
    progress = evaluate_progress(goal, [], as_of=END + datetime.timedelta(days=60))
    assert progress["days_remaining"] == 0
    assert progress["months_remaining"] == 0.0


def test_evaluate_progress_exposes_both_paces():
    goal = make_goal()
    as_of = START + datetime.timedelta(days=90)
    records = [
        assessment_row(START, 5000),
        assessment_row(as_of, 4700),
    ]
    progress = evaluate_progress(goal, records, as_of=as_of)
    assert progress["required_pace_kg_per_month"] > 0
    assert progress["observed_pace_kg_per_month"] > 0
    assert progress["pace_needed_from_now_kg_per_month"] > 0


def test_evaluate_progress_rejects_an_invalid_goal():
    bad_goal = {
        "baseline_kg": 1000.0,
        "target_kg": 2000.0,
        "start_date": START,
        "target_date": END,
    }
    with pytest.raises(GoalValidationError):
        evaluate_progress(bad_goal, [])


# --- Category allocation ----------------------------------------------------

CONTRIBUTORS = {
    "Transport": 2000.0,
    "Electricity": 1500.0,
    "Diet": 1000.0,
    "Flights": 500.0,
}


def test_allocation_covers_the_full_reduction_when_feasible():
    result = allocate_reduction(make_goal(), CONTRIBUTORS)
    assert result["feasible"] is True
    assert result["total_allocated_kg"] == pytest.approx(1500.0, abs=1.0)
    assert result["unallocated_kg"] == 0.0


def test_allocation_shares_sum_to_one_hundred_percent():
    result = allocate_reduction(make_goal(), CONTRIBUTORS)
    total = sum(item["percent_of_total_reduction"] for item in result["allocations"].values())
    assert total == pytest.approx(100.0, abs=0.5)


def test_allocation_favours_categories_with_more_headroom():
    result = allocate_reduction(make_goal(), CONTRIBUTORS)["allocations"]
    # Transport: 2000 * 0.80 = 1600 headroom; Diet: 1000 * 0.45 = 450.
    assert result["Transport"]["reduce_by_kg"] > result["Diet"]["reduce_by_kg"]


def test_allocation_never_exceeds_a_category_ceiling():
    result = allocate_reduction(make_goal(), CONTRIBUTORS)["allocations"]
    for category, item in result.items():
        ceiling = REDUCTION_CEILINGS[category]
        assert item["reduce_by_kg"] <= item["current_kg"] * ceiling + 0.01


def test_allocation_reports_an_infeasible_goal():
    goal = create_goal(5000, 100, START, END)
    result = allocate_reduction(goal, CONTRIBUTORS)
    assert result["feasible"] is False
    assert result["unallocated_kg"] > 0


def test_allocation_handles_empty_contributors():
    result = allocate_reduction(make_goal(), {})
    assert result["allocations"] == {}
    assert result["unallocated_kg"] == 1500.0


def test_allocation_ignores_non_numeric_contributors():
    contributors = dict(CONTRIBUTORS)
    contributors["Broken"] = "n/a"
    result = allocate_reduction(make_goal(), contributors)
    assert "Broken" not in result["allocations"]


def test_allocation_target_never_goes_negative():
    goal = create_goal(5000, 100, START, END)
    for item in allocate_reduction(goal, CONTRIBUTORS)["allocations"].values():
        assert item["target_kg"] >= 0


def test_allocation_with_all_zero_contributors():
    result = allocate_reduction(make_goal(), {"Transport": 0, "Diet": 0})
    assert result["allocations"] == {}
    assert result["feasible"] is False


# --- Feasible target suggestion ---------------------------------------------

def test_suggest_feasible_target_is_below_baseline():
    suggested = suggest_feasible_target(5000, CONTRIBUTORS)
    assert 0 <= suggested < 5000


def test_suggest_feasible_target_matches_total_headroom():
    # 2000*0.8 + 1500*0.6 + 1000*0.45 + 500*1.0 = 1600 + 900 + 450 + 500 = 3450
    assert suggest_feasible_target(5000, CONTRIBUTORS) == pytest.approx(1550.0)


def test_suggest_feasible_target_falls_back_without_contributors():
    assert suggest_feasible_target(5000, {}) == pytest.approx(2500.0)


def test_suggested_target_produces_a_feasible_goal():
    suggested = suggest_feasible_target(5000, CONTRIBUTORS)
    goal = create_goal(5000, suggested, START, END)
    assert allocate_reduction(goal, CONTRIBUTORS)["feasible"] is True


# --- Presentation helpers ---------------------------------------------------

@pytest.mark.parametrize("current,expected_fragment", [
    (3400, "achieved"),
    (5000, "Off track"),
])
def test_summary_reflects_status(current, expected_fragment):
    goal = make_goal()
    as_of = START + datetime.timedelta(days=300)
    progress = evaluate_progress(goal, [assessment_row(as_of, current)], as_of=as_of)
    assert expected_fragment.lower() in summarize_goal(goal, progress).lower()


def test_summary_prompts_for_data_when_history_is_empty():
    goal = make_goal()
    progress = evaluate_progress(goal, [], as_of=START)
    assert "log an assessment" in summarize_goal(goal, progress).lower()


def test_goal_to_dict_is_json_safe():
    payload = goal_to_dict(make_goal())
    assert payload["start_date"] == "2026-01-01"
    assert payload["target_date"] == "2027-01-01"
    assert isinstance(payload["baseline_kg"], float)


def test_goal_to_dict_round_trips_back_into_create_goal():
    payload = goal_to_dict(make_goal())
    restored = create_goal(
        payload["baseline_kg"],
        payload["target_kg"],
        payload["start_date"],
        payload["target_date"],
    )
    assert restored["start_date"] == START
    assert restored["target_date"] == END
