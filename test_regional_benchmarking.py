"""
Tests for the Regional Benchmarking Engine
"""

import math
import pytest

from src.utils.regional_benchmarking import (
    get_region_data, calculate_percentile, calculate_regional_gap,
    compare_categories, identify_weakest_category, generate_insights,
    calculate_monthly_trend, aggregate_community_data, calculate_reduction_pathway,
    generate_benchmarking_summary, REGIONAL_AVERAGES,
)

SAMPLE_CONTRIBUTORS = {"Transport": 2000.0, "Electricity": 1500.0, "Diet": 1000.0, "Flights": 600.0}
SAMPLE_ASSESSMENTS = [{"month": f"2024-0{i}", "footprint": 5200.0 - i * 200} for i in range(1, 7)]
SAMPLE_COMMUNITY = [
    {"user_id": 1, "footprint": 5000.0, "eco_score": 60},
    {"user_id": 2, "footprint": 3500.0, "eco_score": 72},
    {"user_id": 3, "footprint": 7200.0, "eco_score": 45},
    {"user_id": 4, "footprint": 4100.0, "eco_score": 65},
    {"user_id": 5, "footprint": 2800.0, "eco_score": 82},
]


class TestGetRegionData:
    def test_known_region(self):
        assert get_region_data("US")["average_footprint_kg"] == 14900.0

    def test_unknown_region_fallback(self):
        assert get_region_data("Antarctica") == REGIONAL_AVERAGES["Global"]

    def test_all_regions_have_required_keys(self):
        required = {"average_footprint_kg", "target_2030_kg", "target_2050_kg", "category_averages"}
        for r, d in REGIONAL_AVERAGES.items():
            assert required.issubset(d.keys()), f"{r} missing keys"


class TestCalculatePercentile:
    def test_high_footprint_high_percentile(self):
        assert calculate_percentile(20000.0, "Global")["percentile"] > 75

    def test_low_footprint_low_percentile(self):
        assert calculate_percentile(500.0, "Global")["percentile"] < 25

    def test_average_footprint_mid_range(self):
        p = calculate_percentile(4700.0, "Global")["percentile"]
        assert 35 < p < 65

    def test_zero_returns_minimum(self):
        assert calculate_percentile(0.0, "US")["percentile"] == 1.0

    def test_bounded_1_to_99(self):
        for v in [100, 1000, 5000, 15000, 50000]:
            r = calculate_percentile(float(v), "US")
            assert 1.0 <= r["percentile"] <= 99.0

    def test_result_keys(self):
        r = calculate_percentile(4000.0, "EU")
        assert {"percentile", "bracket_label", "bracket_color", "mean_kg", "user_kg", "region"}.issubset(r.keys())


class TestCalculateRegionalGap:
    def test_above_average_positive(self):
        assert calculate_regional_gap(6000.0, "Global")["gap_vs_average_kg"] > 0

    def test_below_average_negative(self):
        assert calculate_regional_gap(20000.0, "Global")["gap_vs_average_kg"] < 0

    def test_gap_calculation(self):
        r = calculate_regional_gap(5000.0, "Global")
        assert abs(r["gap_vs_average_kg"] - 300.0) < 0.1

    def test_zero_gap(self):
        r = calculate_regional_gap(0.0, "Global")
        assert r["gap_vs_average_kg"] == -REGIONAL_AVERAGES["Global"]["average_footprint_kg"]

    def test_result_has_targets(self):
        r = calculate_regional_gap(5000.0, "US")
        assert "target_2030_kg" in r and "target_2050_kg" in r


class TestCompareCategories:
    def test_sorted_by_gap_desc(self):
        gaps = [c["gap_kg"] for c in compare_categories(SAMPLE_CONTRIBUTORS, "US")]
        assert gaps == sorted(gaps, reverse=True)

    def test_all_categories_present(self):
        cats = {c["category"] for c in compare_categories(SAMPLE_CONTRIBUTORS, "Global")}
        assert cats == set(SAMPLE_CONTRIBUTORS.keys())

    def test_above_average_status(self):
        comps = compare_categories({"Transport": 5000.0}, "US")
        assert comps[0]["status"] == "above_average"

    def test_empty_returns_empty(self):
        assert compare_categories({}, "Global") == []


class TestIdentifyWeakestCategory:
    def test_returns_worst(self):
        r = identify_weakest_category(SAMPLE_CONTRIBUTORS, "US")
        assert r is not None and isinstance(r, str)

    def test_returns_none_when_all_low(self):
        low = {"Transport": 100.0, "Electricity": 100.0, "Diet": 100.0, "Flights": 0.0}
        assert identify_weakest_category(low, "US") is None


class TestGenerateInsights:
    def test_returns_three_insights(self):
        insights = generate_insights(4500.0, SAMPLE_CONTRIBUTORS, "Global")
        assert len(insights) == 3 and all(isinstance(i, str) for i in insights)

    def test_excellent_for_very_low(self):
        insights = generate_insights(1000.0, SAMPLE_CONTRIBUTORS, "US")
        assert any("outstanding" in i.lower() or "top" in i.lower() for i in insights)

    def test_critical_for_very_high(self):
        insights = generate_insights(20000.0, SAMPLE_CONTRIBUTORS, "Global")
        assert any("urgent" in i.lower() or "significantly" in i.lower() for i in insights)

    def test_without_contributors(self):
        assert len(generate_insights(5000.0, None, "UK")) == 3


class TestCalculateMonthlyTrend:
    def test_decreasing(self):
        r = calculate_monthly_trend(SAMPLE_ASSESSMENTS)
        assert r["trend_direction"] == "improving" and r["monthly_change_kg"] < 0

    def test_increasing(self):
        inc = [{"month": f"2024-0{i}", "footprint": 2000.0 + i * 1000} for i in range(1, 7)]
        r = calculate_monthly_trend(inc)
        assert r["trend_direction"] == "increasing"

    def test_insufficient_data(self):
        assert calculate_monthly_trend([])["trend_direction"] == "insufficient_data"
        assert calculate_monthly_trend([{"month": "2024-01", "footprint": 4000.0}])["trend_direction"] == "insufficient_data"

    def test_improvement_pct_positive(self):
        assert calculate_monthly_trend(SAMPLE_ASSESSMENTS)["improvement_pct"] > 0

    def test_projected_non_negative(self):
        assert calculate_monthly_trend(SAMPLE_ASSESSMENTS)["projected_next_month_kg"] >= 0


class TestAggregateCommunityData:
    def test_basic_aggregation(self):
        r = aggregate_community_data(SAMPLE_COMMUNITY, user_id=None)
        assert r["peer_count"] == 5 and r["peer_average_kg"] > 0

    def test_excludes_user(self):
        assert aggregate_community_data(SAMPLE_COMMUNITY, user_id=1)["peer_count"] == 4

    def test_median(self):
        r = aggregate_community_data(SAMPLE_COMMUNITY, user_id=None)
        assert r["peer_median_kg"] == sorted(a["footprint"] for a in SAMPLE_COMMUNITY)[2]

    def test_empty(self):
        assert aggregate_community_data([], user_id=1)["peer_count"] == 0


class TestCalculateReductionPathway:
    def test_basic(self):
        r = calculate_reduction_pathway(5000.0, 2500.0, 24)
        assert r["total_reduction_kg"] == 2500.0 and r["monthly_reduction_kg"] > 0

    def test_milestones_count(self):
        assert len(calculate_reduction_pathway(5000.0, 2500.0, 24)["quarterly_milestones"]) == 8

    def test_milestones_decreasing(self):
        ms = calculate_reduction_pathway(8000.0, 2000.0, 36)["quarterly_milestones"]
        targets = [m["target_kg"] for m in ms]
        assert targets == sorted(targets, reverse=True)

    def test_zero_current(self):
        assert calculate_reduction_pathway(0.0, 0.0, 12)["feasible"] is False

    def test_feasibility_levels(self):
        assert calculate_reduction_pathway(5000.0, 4500.0, 120)["feasibility"] == "moderate"
        assert calculate_reduction_pathway(15000.0, 1000.0, 6)["feasibility"] == "aggressive"


class TestGenerateBenchmarkingSummary:
    def test_all_keys_present(self):
        r = generate_benchmarking_summary(4500.0, SAMPLE_CONTRIBUTORS, "US")
        assert {"region", "user_footprint_kg", "regional_gap", "percentile",
                "category_comparisons", "trend", "community", "reduction_pathway",
                "insights", "generated_at"}.issubset(r.keys())

    def test_with_history(self):
        r = generate_benchmarking_summary(4500.0, SAMPLE_CONTRIBUTORS, "Global", assessment_history=SAMPLE_ASSESSMENTS)
        assert r["trend"]["data_points"] == 6

    def test_with_community(self):
        r = generate_benchmarking_summary(4500.0, SAMPLE_CONTRIBUTORS, "EU",
                                          community_assessments=SAMPLE_COMMUNITY, user_id=1)
        assert r["community"]["peer_count"] == 4

    def test_without_contributors(self):
        r = generate_benchmarking_summary(4500.0, None, "UK")
        assert r["category_comparisons"] == [] and len(r["insights"]) > 0


class TestEdgeCases:
    def test_all_regions_valid_percentiles(self):
        for r in REGIONAL_AVERAGES:
            p = calculate_percentile(4000.0, r)["percentile"]
            assert 1.0 <= p <= 99.0

    def test_trend_identical_values(self):
        identical = [{"month": f"2024-0{i}", "footprint": 4000.0} for i in range(1, 7)]
        r = calculate_monthly_trend(identical)
        assert r["trend_direction"] == "stable" and abs(r["monthly_change_kg"]) < 0.01
