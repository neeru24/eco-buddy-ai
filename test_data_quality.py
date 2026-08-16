import datetime

import pytest

from data_quality import (
    CODE_DUPLICATE,
    CODE_DUPLICATE_TIMESTAMP,
    CODE_FUTURE_DATE,
    CODE_IMPLAUSIBLE_JUMP,
    CODE_MISSING_FIELD,
    CODE_OUTLIER,
    CODE_SMALL_SAMPLE,
    CODE_STALE_DATA,
    CODE_ZERO_FOOTPRINT,
    MIN_MEANINGFUL_SAMPLE,
    SEVERITY_CRITICAL,
    SEVERITY_INFO,
    SEVERITY_WARNING,
    audit_assessments,
    calculate_confidence_score,
    detect_duplicates,
    detect_implausible_jumps,
    detect_missing_fields,
    detect_out_of_order,
    detect_outliers,
    detect_small_sample,
    detect_staleness,
    detect_timestamp_issues,
    filter_clean_records,
    group_issues_by_severity,
    make_issue,
    modified_z_scores,
    normalize_records,
    quality_grade,
    summarize_report,
    to_dict,
)

NOW = datetime.datetime(2026, 7, 30, 12, 0, 0)


def row(record_id, when, footprint, transport="Car", distance=10.0,
        electricity=300.0, diet="Vegetarian", flights=2, eco_score=60):
    """A row shaped exactly like database.get_assessments() returns."""
    when_text = when.isoformat() if hasattr(when, "isoformat") else when
    return (record_id, when_text, transport, distance, electricity, diet,
            flights, footprint, eco_score)


def days_ago(days, hours=0):
    return NOW - datetime.timedelta(days=days, hours=hours)


def healthy_history(count=8, footprint=5000.0):
    """A clean series, one entry a week, with mild natural variation."""
    return [
        row(index + 1, days_ago(7 * (count - index)), footprint + index * 20)
        for index in range(count)
    ]


# --- Normalisation ----------------------------------------------------------

def test_tuple_rows_are_normalized():
    records = normalize_records([row(1, days_ago(1), 5000)])
    assert records[0]["id"] == 1
    assert records[0]["footprint"] == 5000.0
    assert records[0]["transport"] == "Car"
    assert isinstance(records[0]["timestamp"], datetime.datetime)


def test_dict_rows_are_normalized():
    records = normalize_records([
        {"id": 7, "date": "2026-01-01", "transport": "Bike", "distance": 5,
         "electricity": 100, "diet": "Vegan", "flights": 0,
         "footprint": 1200, "eco_score": 90}
    ])
    assert records[0]["id"] == 7
    assert records[0]["diet"] == "Vegan"


def test_unparseable_dates_become_none_rather_than_raising():
    records = normalize_records([row(1, "not-a-date", 5000)])
    assert records[0]["timestamp"] is None
    assert records[0]["raw_date"] == "not-a-date"


def test_sqlite_timestamp_format_is_parsed():
    records = normalize_records([row(1, "2026-01-01 08:30:00", 5000)])
    assert records[0]["timestamp"] == datetime.datetime(2026, 1, 1, 8, 30)


def test_non_numeric_footprint_becomes_none():
    records = normalize_records([row(1, days_ago(1), "lots")])
    assert records[0]["footprint"] is None


def test_short_and_malformed_rows_are_skipped():
    assert normalize_records([(1, "2026-01-01")]) == []
    assert normalize_records(["nonsense"]) == []


def test_empty_input_normalizes_to_empty():
    assert normalize_records([]) == []
    assert normalize_records(None) == []


# --- Modified Z-score -------------------------------------------------------

def test_z_scores_need_at_least_three_values():
    assert modified_z_scores([1.0, 2.0]) == []


def test_z_score_flags_a_lone_extreme_value():
    scores = modified_z_scores([100, 102, 98, 101, 99, 5000])
    assert abs(scores[-1]) > 3.5
    assert all(abs(score) < 3.5 for score in scores[:-1])


def test_z_score_handles_identical_values_via_mad_fallback():
    """
    With more than half the values identical the MAD is zero. A naive
    implementation divides by zero here; the mean-deviation fallback still
    separates the odd value out.
    """
    scores = modified_z_scores([100, 100, 100, 100, 5000])
    assert abs(scores[-1]) > 3.5


def test_z_score_of_completely_identical_values_is_zero():
    assert modified_z_scores([100, 100, 100, 100]) == [0.0, 0.0, 0.0, 0.0]


def test_z_scores_ignore_none_values():
    assert len(modified_z_scores([100, None, 102, 98])) == 3


# --- Outliers ---------------------------------------------------------------

def test_outlier_is_detected():
    records = normalize_records(healthy_history(6) + [row(99, days_ago(1), 60000)])
    issues = detect_outliers(records)
    assert any(issue["code"] == CODE_OUTLIER for issue in issues)
    assert 99 in issues[0]["record_ids"]


def test_clean_history_produces_no_outliers():
    assert detect_outliers(normalize_records(healthy_history(8))) == []


def test_outlier_detection_needs_three_records():
    assert detect_outliers(normalize_records(healthy_history(2))) == []


def test_a_low_outlier_is_flagged_too():
    records = normalize_records(healthy_history(6) + [row(99, days_ago(1), 5)])
    assert any(issue["code"] == CODE_OUTLIER for issue in detect_outliers(records))


def test_outlier_message_names_the_direction():
    records = normalize_records(healthy_history(6) + [row(99, days_ago(1), 60000)])
    assert "far above" in detect_outliers(records)[0]["message"]


def test_a_single_outlier_does_not_mask_itself():
    """
    The reason this module uses MAD rather than standard deviation: at n=6 a
    mean/stdev test lets an extreme value inflate the deviation enough to hide
    behind it. This asserts the extreme value is actually caught.
    """
    records = normalize_records(healthy_history(5) + [row(99, days_ago(1), 40000)])
    assert detect_outliers(records)


# --- Duplicates -------------------------------------------------------------

def test_double_submission_is_detected():
    when = days_ago(1)
    records = normalize_records([
        row(1, when, 5000),
        row(2, when + datetime.timedelta(seconds=20), 5000),
    ])
    issues = detect_duplicates(records)
    assert len(issues) == 1
    assert issues[0]["code"] == CODE_DUPLICATE
    assert issues[0]["record_ids"] == [1, 2]


def test_identical_inputs_far_apart_are_not_duplicates():
    records = normalize_records([
        row(1, days_ago(30), 5000),
        row(2, days_ago(1), 5000),
    ])
    assert detect_duplicates(records) == []


def test_different_inputs_close_together_are_not_duplicates():
    when = days_ago(1)
    records = normalize_records([
        row(1, when, 5000, transport="Car"),
        row(2, when + datetime.timedelta(seconds=20), 1200, transport="Bike"),
    ])
    assert detect_duplicates(records) == []


def test_different_diet_prevents_a_duplicate_match():
    when = days_ago(1)
    records = normalize_records([
        row(1, when, 5000, diet="Vegetarian"),
        row(2, when + datetime.timedelta(seconds=20), 5000, diet="Non-Vegetarian"),
    ])
    assert detect_duplicates(records) == []


def test_tiny_numeric_differences_still_count_as_duplicates():
    when = days_ago(1)
    records = normalize_records([
        row(1, when, 5000.00),
        row(2, when + datetime.timedelta(seconds=5), 5000.01),
    ])
    assert len(detect_duplicates(records)) == 1


def test_duplicate_detection_needs_two_records():
    assert detect_duplicates(normalize_records([row(1, days_ago(1), 5000)])) == []


def test_duplicate_window_is_configurable():
    records = normalize_records([
        row(1, days_ago(1), 5000),
        row(2, days_ago(1) + datetime.timedelta(minutes=30), 5000),
    ])
    assert detect_duplicates(records, time_window_minutes=5) == []
    assert detect_duplicates(records, time_window_minutes=60)


# --- Implausible jumps ------------------------------------------------------

def test_sudden_spike_is_flagged():
    records = normalize_records([
        row(1, days_ago(10), 1000),
        row(2, days_ago(5), 50000),
    ])
    issues = detect_implausible_jumps(records)
    assert issues and issues[0]["code"] == CODE_IMPLAUSIBLE_JUMP
    assert "increased" in issues[0]["message"]


def test_sudden_collapse_is_flagged():
    records = normalize_records([
        row(1, days_ago(10), 50000),
        row(2, days_ago(5), 1000),
    ])
    issues = detect_implausible_jumps(records)
    assert issues and "dropped" in issues[0]["message"]


def test_gradual_change_is_not_flagged():
    assert detect_implausible_jumps(normalize_records(healthy_history(8))) == []


def test_jump_ratio_is_configurable():
    records = normalize_records([
        row(1, days_ago(10), 1000),
        row(2, days_ago(5), 3000),
    ])
    assert detect_implausible_jumps(records, max_ratio=5.0) == []
    assert detect_implausible_jumps(records, max_ratio=2.0)


def test_zero_footprints_do_not_cause_division_by_zero():
    records = normalize_records([
        row(1, days_ago(10), 0),
        row(2, days_ago(5), 5000),
    ])
    assert detect_implausible_jumps(records) == []


# --- Timestamps -------------------------------------------------------------

def test_future_dates_are_critical():
    records = normalize_records([row(1, NOW + datetime.timedelta(days=5), 5000)])
    issues = detect_timestamp_issues(records, now=NOW)
    future = [issue for issue in issues if issue["code"] == CODE_FUTURE_DATE]
    assert future and future[0]["severity"] == SEVERITY_CRITICAL


def test_unparseable_dates_are_critical():
    records = normalize_records([row(1, "gibberish", 5000)])
    issues = detect_timestamp_issues(records, now=NOW)
    assert any(issue["severity"] == SEVERITY_CRITICAL for issue in issues)


def test_duplicate_timestamps_are_reported():
    when = days_ago(1)
    records = normalize_records([row(1, when, 5000), row(2, when, 4000)])
    issues = detect_timestamp_issues(records, now=NOW)
    assert any(issue["code"] == CODE_DUPLICATE_TIMESTAMP for issue in issues)


def test_clean_timestamps_produce_no_issues():
    assert detect_timestamp_issues(normalize_records(healthy_history(5)), now=NOW) == []


def test_consistent_ordering_is_accepted_in_both_directions():
    ascending = normalize_records(healthy_history(5))
    assert detect_out_of_order(ascending) == []
    assert detect_out_of_order(list(reversed(ascending))) == []


def test_scrambled_ordering_is_reported():
    records = normalize_records([
        row(1, days_ago(5), 5000),
        row(2, days_ago(20), 5000),
        row(3, days_ago(10), 5000),
    ])
    assert detect_out_of_order(records)


# --- Missing fields ---------------------------------------------------------

def test_missing_diet_is_critical():
    records = normalize_records([row(1, days_ago(1), 5000, diet=None)])
    issues = detect_missing_fields(records)
    assert any(
        issue["code"] == CODE_MISSING_FIELD and issue["severity"] == SEVERITY_CRITICAL
        for issue in issues
    )


def test_blank_string_counts_as_missing():
    records = normalize_records([row(1, days_ago(1), 5000, transport="   ")])
    assert detect_missing_fields(records)


def test_zero_footprint_is_a_warning():
    records = normalize_records([row(1, days_ago(1), 0)])
    issues = detect_missing_fields(records)
    zero = [issue for issue in issues if issue["code"] == CODE_ZERO_FOOTPRINT]
    assert zero and zero[0]["severity"] == SEVERITY_WARNING


def test_complete_records_report_nothing_missing():
    assert detect_missing_fields(normalize_records(healthy_history(3))) == []


def test_missing_fields_are_grouped_by_field():
    records = normalize_records([
        row(1, days_ago(1), 5000, diet=None),
        row(2, days_ago(2), 5000, diet=None),
    ])
    issues = [i for i in detect_missing_fields(records) if i["code"] == CODE_MISSING_FIELD]
    assert len(issues) == 1
    assert sorted(issues[0]["record_ids"]) == [1, 2]


# --- Staleness and sample size ----------------------------------------------

def test_old_history_is_flagged_as_stale():
    records = normalize_records([row(1, days_ago(400), 5000)])
    issues = detect_staleness(records, now=NOW)
    assert issues and issues[0]["code"] == CODE_STALE_DATA


def test_recent_history_is_not_stale():
    assert detect_staleness(normalize_records(healthy_history(4)), now=NOW) == []


def test_staleness_threshold_is_configurable():
    records = normalize_records([row(1, days_ago(30), 5000)])
    assert detect_staleness(records, max_age_days=7, now=NOW)


def test_staleness_ignores_future_dates():
    """A future-dated row must not make a stale history look fresh."""
    records = normalize_records([
        row(1, days_ago(400), 5000),
        row(2, NOW + datetime.timedelta(days=30), 5000),
    ])
    assert detect_staleness(records, now=NOW)


def test_short_history_is_flagged():
    issues = detect_small_sample(normalize_records(healthy_history(2)))
    assert issues and issues[0]["code"] == CODE_SMALL_SAMPLE


def test_sufficient_history_is_not_flagged():
    assert detect_small_sample(normalize_records(healthy_history(MIN_MEANINGFUL_SAMPLE))) == []


# --- Confidence scoring -----------------------------------------------------

def test_clean_history_scores_full_marks():
    assert calculate_confidence_score([], 20) == 100.0


def test_empty_history_scores_zero():
    assert calculate_confidence_score([], 0) == 0.0


def test_critical_issues_cost_more_than_warnings():
    critical = calculate_confidence_score(
        [make_issue("x", SEVERITY_CRITICAL, "m", [1])], 20)
    warning = calculate_confidence_score(
        [make_issue("x", SEVERITY_WARNING, "m", [1])], 20)
    info = calculate_confidence_score(
        [make_issue("x", SEVERITY_INFO, "m", [1])], 20)
    assert critical < warning < info


def test_the_same_defect_costs_more_in_a_smaller_history():
    """One bad row in three is far more damaging than one bad row in fifty."""
    small = calculate_confidence_score(
        [make_issue("x", SEVERITY_WARNING, "m", [1])], 3)
    large = calculate_confidence_score(
        [make_issue("x", SEVERITY_WARNING, "m", [1])], 50)
    assert small < large


def test_a_tiny_clean_history_is_not_fully_confident():
    """False precision is the failure mode this penalty exists to prevent."""
    assert calculate_confidence_score([], 2) < 100.0


def test_score_is_clamped_to_zero():
    issues = [make_issue("x", SEVERITY_CRITICAL, "m", [i]) for i in range(30)]
    assert calculate_confidence_score(issues, 30) == 0.0


def test_score_never_exceeds_one_hundred():
    assert calculate_confidence_score([], 100) == 100.0


@pytest.mark.parametrize("score,grade", [
    (100.0, "A"), (95.0, "A"), (90.0, "A"),
    (85.0, "B"), (80.0, "B"),
    (75.0, "C"), (70.0, "C"),
    (65.0, "D"), (60.0, "D"),
    (55.0, "F"), (0.0, "F"),
])
def test_grade_bands(score, grade):
    assert quality_grade(score) == grade


# --- End-to-end audit -------------------------------------------------------

def test_clean_history_audits_cleanly():
    report = audit_assessments(healthy_history(10), now=NOW, include_drift=False)
    assert report["record_count"] == 10
    assert report["issues"] == []
    assert report["confidence_score"] == 100.0
    assert report["grade"] == "A"


def test_corrupted_history_is_caught_end_to_end():
    when = days_ago(2)
    corrupted = healthy_history(6) + [
        row(50, when, 5000),
        row(51, when + datetime.timedelta(seconds=15), 5000),   # duplicate
        row(52, days_ago(1), 90000),                            # outlier + jump
        row(53, NOW + datetime.timedelta(days=10), 5000),       # future date
        row(54, days_ago(3), 5000, diet=None),                  # missing field
        row(55, days_ago(4), 0),                                # zero footprint
    ]
    report = audit_assessments(corrupted, now=NOW, include_drift=False)

    codes = {issue["code"] for issue in report["issues"]}
    assert CODE_DUPLICATE in codes
    assert CODE_OUTLIER in codes
    assert CODE_FUTURE_DATE in codes
    assert CODE_MISSING_FIELD in codes
    assert CODE_ZERO_FOOTPRINT in codes
    assert report["confidence_score"] < 100.0
    assert report["grade"] != "A"


def test_audit_of_an_empty_history():
    report = audit_assessments([], now=NOW)
    assert report["record_count"] == 0
    assert report["confidence_score"] == 0.0
    assert "nothing to check" in summarize_report(report).lower()


def test_audit_reports_flagged_record_ids():
    when = days_ago(2)
    records = healthy_history(5) + [
        row(50, when, 5000),
        row(51, when + datetime.timedelta(seconds=10), 5000),
    ]
    report = audit_assessments(records, now=NOW, include_drift=False)
    assert 50 in report["flagged_record_ids"]
    assert 51 in report["flagged_record_ids"]


def test_audit_groups_by_severity():
    report = audit_assessments(
        healthy_history(6) + [row(99, NOW + datetime.timedelta(days=5), 5000)],
        now=NOW, include_drift=False,
    )
    grouped = group_issues_by_severity(report["issues"])
    assert grouped[SEVERITY_CRITICAL]


def test_audit_survives_completely_malformed_input():
    """A single unusable row must never take down the whole audit."""
    report = audit_assessments(["nonsense", None, 42], now=NOW, include_drift=False)
    assert report["record_count"] == 0


def test_drift_is_detected_when_stored_value_contradicts_its_inputs():
    """A footprint that its own inputs no longer produce."""
    from data_quality import detect_calculation_drift

    records = normalize_records([row(1, days_ago(5), 9999.0)])
    issues = detect_calculation_drift(records)
    assert issues and issues[0]["severity"] == SEVERITY_INFO
    assert 1 in issues[0]["record_ids"]


def test_no_drift_when_stored_value_matches_its_inputs():
    from data_quality import detect_calculation_drift
    from emissions import calculate_footprint

    expected, _ = calculate_footprint("Car", 10.0, 300.0, "Vegetarian", 2)
    assert detect_calculation_drift(normalize_records([row(1, days_ago(5), expected)])) == []


def test_drift_skips_rows_it_cannot_recompute():
    from data_quality import detect_calculation_drift

    records = normalize_records([row(1, days_ago(5), 5000, transport="Hovercraft")])
    assert detect_calculation_drift(records) == []


def test_drift_detection_can_be_skipped():
    report = audit_assessments(healthy_history(5), now=NOW, include_drift=False)
    assert all(issue["code"] != "calculation_drift" for issue in report["issues"])


# --- Summaries and export ---------------------------------------------------

def test_summary_of_a_clean_report():
    report = audit_assessments(healthy_history(10), now=NOW, include_drift=False)
    assert "no data quality issues" in summarize_report(report).lower()


def test_summary_mentions_critical_issues():
    report = audit_assessments(
        healthy_history(6) + [row(99, NOW + datetime.timedelta(days=5), 5000)],
        now=NOW, include_drift=False,
    )
    assert "critical" in summarize_report(report).lower()


def test_report_exports_as_json_safe_dict():
    report = audit_assessments(healthy_history(6), now=NOW, include_drift=False)
    payload = to_dict(report)
    assert set(payload) >= {"record_count", "confidence_score", "grade", "issues"}
    assert all(isinstance(i, str) for issue in payload["issues"] for i in issue["record_ids"])


# --- Filtering --------------------------------------------------------------

def test_filter_removes_critical_rows_only():
    rows = healthy_history(6) + [row(99, NOW + datetime.timedelta(days=5), 5000)]
    report = audit_assessments(rows, now=NOW, include_drift=False)
    kept = filter_clean_records(rows, report)
    assert all(record[0] != 99 for record in kept)
    assert len(kept) == 6


def test_filter_keeps_outliers_by_default():
    """
    A genuine high-emission month is exactly what the app exists to surface.
    Dropping every flagged row would hide it.
    """
    rows = healthy_history(6) + [row(99, days_ago(1), 60000)]
    report = audit_assessments(rows, now=NOW, include_drift=False)
    assert any(issue["code"] == CODE_OUTLIER for issue in report["issues"])
    assert any(record[0] == 99 for record in filter_clean_records(rows, report))


def test_filter_can_be_asked_to_drop_warnings_too():
    rows = healthy_history(6) + [row(99, days_ago(1), 60000)]
    report = audit_assessments(rows, now=NOW, include_drift=False)
    kept = filter_clean_records(rows, report, severities=(SEVERITY_CRITICAL, SEVERITY_WARNING))
    assert all(record[0] != 99 for record in kept)


def test_filter_on_a_clean_history_returns_everything():
    rows = healthy_history(8)
    assert len(filter_clean_records(rows, audit_assessments(rows, now=NOW, include_drift=False))) == 8


def test_filter_builds_its_own_report_when_not_given_one():
    assert len(filter_clean_records(healthy_history(6))) == 6


def test_filter_handles_an_empty_history():
    assert filter_clean_records([]) == []
