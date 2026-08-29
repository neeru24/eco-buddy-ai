"""
Regional Benchmarking Engine
============================
Compares a user's carbon footprint against regional and global averages,
provides percentile rankings, trend analysis, and community aggregation.
"""

import math
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# ── Regional Average Data (kg CO2/year per capita) ──────────────────────────

REGIONAL_AVERAGES: dict[str, dict[str, Any]] = {
    "Global": {
        "average_footprint_kg": 4700.0, "target_2030_kg": 2500.0, "target_2050_kg": 1500.0,
        "population_billion": 8.0, "description": "World average per-capita carbon footprint",
        "category_averages": {"Transport": 1800.0, "Electricity": 1400.0, "Diet": 950.0, "Flights": 550.0},
    },
    "US": {
        "average_footprint_kg": 14900.0, "target_2030_kg": 8000.0, "target_2050_kg": 3000.0,
        "population_billion": 0.335, "description": "United States per-capita average",
        "category_averages": {"Transport": 4800.0, "Electricity": 4200.0, "Diet": 2500.0, "Flights": 3400.0},
    },
    "UK": {
        "average_footprint_kg": 5500.0, "target_2030_kg": 3000.0, "target_2050_kg": 1500.0,
        "population_billion": 0.067, "description": "United Kingdom per-capita average",
        "category_averages": {"Transport": 1700.0, "Electricity": 1500.0, "Diet": 1200.0, "Flights": 1100.0},
    },
    "EU": {
        "average_footprint_kg": 6400.0, "target_2030_kg": 3500.0, "target_2050_kg": 1800.0,
        "population_billion": 0.447, "description": "European Union weighted average",
        "category_averages": {"Transport": 2100.0, "Electricity": 1700.0, "Diet": 1400.0, "Flights": 1200.0},
    },
}

PERCENTILE_BRACKETS = [
    {"label": "🏆 Top 5% — Climate Leader", "max_percentile": 5, "color": "#15803d"},
    {"label": "🌟 Top 25% — Green Performer", "max_percentile": 25, "color": "#22c55e"},
    {"label": "📊 Average — Room to Improve", "max_percentile": 50, "color": "#eab308"},
    {"label": "⚠️ Below Average — Action Needed", "max_percentile": 75, "color": "#f97316"},
    {"label": "🔴 Bottom 25% — Urgent Change Required", "max_percentile": 100, "color": "#dc2626"},
]

INSIGHT_TEMPLATES = {
    "excellent": [
        "You're among the top performers in your region — keep inspiring others!",
        "Your footprint is significantly below the regional average. Outstanding work!",
        "You're on track to meet the 2030 climate target well ahead of schedule.",
    ],
    "good": [
        "You're doing better than most people in {region}. Keep it up!",
        "Your footprint is below the {region} average. A few small changes could push you into the top 25%.",
        "Great progress — you're beating the regional average by {gap_kg:.0f} kg CO₂/year.",
    ],
    "average": [
        "You're right at the regional average for {region}. Room for improvement!",
        "Switching one high-impact habit could move you into the green performer bracket.",
        "Your footprint matches the typical {region} resident — let's aim higher.",
    ],
    "below_average": [
        "Your footprint is {gap_kg:.0f} kg CO₂ above the {region} average.",
        "Focusing on {weakest_category} could make the biggest difference for your score.",
        "Consider the personalized recommendations to bring your footprint in line with regional targets.",
    ],
    "critical": [
        "Your footprint is significantly above the {region} average — urgent action is recommended.",
        "Your {weakest_category} emissions are the primary driver. Targeting this area first yields the largest reduction.",
        "Set a reduction goal today to start tracking your path toward the 2030 target.",
    ],
}


def get_region_data(region: str) -> dict[str, Any]:
    """Retrieve benchmarking data for a given region, falling back to Global."""
    return REGIONAL_AVERAGES.get(region, REGIONAL_AVERAGES["Global"])


def calculate_percentile(user_footprint: float, region: str = "Global") -> dict[str, Any]:
    """Estimate a user's percentile rank within a region using a log-normal model."""
    data = get_region_data(region)
    mean_kg = data["average_footprint_kg"]
    sigma, mu = 0.6, math.log(mean_kg) - 0.18

    if user_footprint <= 0:
        percentile = 1.0
    else:
        z = (math.log(max(user_footprint, 0.1)) - mu) / sigma
        percentile = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0))) * 100.0
        percentile = max(1.0, min(99.0, percentile))

    bracket = PERCENTILE_BRACKETS[-1]
    for b in PERCENTILE_BRACKETS:
        if percentile <= b["max_percentile"]:
            bracket = b
            break

    return {"percentile": round(percentile, 1), "bracket_label": bracket["label"],
            "bracket_color": bracket["color"], "mean_kg": mean_kg,
            "user_kg": user_footprint, "region": region}


def calculate_regional_gap(user_footprint: float, region: str = "Global") -> dict[str, Any]:
    """Calculate gaps vs regional average, 2030 target, and 2050 target."""
    data = get_region_data(region)
    avg, t2030, t2050 = data["average_footprint_kg"], data["target_2030_kg"], data["target_2050_kg"]
    return {
        "region": region, "user_kg": user_footprint,
        "regional_average_kg": avg, "target_2030_kg": t2030, "target_2050_kg": t2050,
        "gap_vs_average_kg": round(user_footprint - avg, 2),
        "gap_vs_2030_kg": round(user_footprint - t2030, 2),
        "gap_vs_2050_kg": round(user_footprint - t2050, 2),
        "percent_of_average": round((user_footprint / avg * 100) if avg > 0 else 0, 1),
        "percent_of_2030_target": round((user_footprint / t2030 * 100) if t2030 > 0 else 0, 1),
    }


def compare_categories(contributors: dict[str, float], region: str = "Global") -> list[dict[str, Any]]:
    """Compare per-category emissions against regional averages, sorted worst-first."""
    cat_avgs = get_region_data(region)["category_averages"]
    comparisons = []
    for cat, user_val in contributors.items():
        avg = cat_avgs.get(cat, 0.0)
        gap = user_val - avg
        comparisons.append({"category": cat, "user_kg": round(user_val, 2),
                            "regional_average_kg": avg, "gap_kg": round(gap, 2),
                            "percent_of_average": round((user_val / avg * 100) if avg > 0 else 0, 1),
                            "status": "above_average" if gap > 0 else ("below_average" if gap < 0 else "at_average")})
    comparisons.sort(key=lambda c: c["gap_kg"], reverse=True)
    return comparisons


def identify_weakest_category(contributors: dict[str, float], region: str = "Global") -> str | None:
    """Identify the category with the largest excess above regional average."""
    comparisons = compare_categories(contributors, region)
    worst = max(comparisons, key=lambda c: c["gap_kg"])
    return worst["category"] if worst["gap_kg"] > 0 else None


def generate_insights(user_footprint: float, contributors: dict[str, float] | None,
                      region: str = "Global") -> list[str]:
    """Generate contextual benchmarking insights based on footprint data."""
    gap_data = calculate_regional_gap(user_footprint, region)
    percentile_data = calculate_percentile(user_footprint, region)
    gap_vs_avg, gap_kg = gap_data["gap_vs_average_kg"], abs(gap_data["gap_vs_average_kg"])

    if gap_vs_avg < -1000: severity = "excellent"
    elif gap_vs_avg < -200: severity = "good"
    elif gap_vs_avg < 200: severity = "average"
    elif gap_vs_avg < 2000: severity = "below_average"
    else: severity = "critical"

    weakest = identify_weakest_category(contributors, region) if contributors else None
    insights = []
    for template in INSIGHT_TEMPLATES[severity]:
        try:
            insights.append(template.format(region=region, gap_kg=gap_kg,
                                            weakest_category=weakest or "overall lifestyle",
                                            percentile=percentile_data["percentile"]))
        except (KeyError, TypeError):
            insights.append(template)
    return insights


def calculate_monthly_trend(assessments: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze monthly footprint trend with linear regression."""
    if not assessments or len(assessments) < 2:
        return {"trend_direction": "insufficient_data", "monthly_change_kg": 0.0,
                "trend_description": "Not enough data — complete at least two monthly assessments.",
                "projected_next_month_kg": None, "improvement_pct": 0.0, "data_points": len(assessments)}

    sorted_data = sorted(assessments, key=lambda a: a["month"])
    footprints = [a["footprint"] for a in sorted_data]
    n = len(footprints)
    x_mean, y_mean = sum(range(n)) / n, sum(footprints) / n
    num = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(footprints))
    den = sum((i - x_mean) ** 2 for i in range(n))
    slope = num / den if den else 0.0

    projected = max(0.0, slope * n + (y_mean - slope * x_mean))
    improvement_pct = ((footprints[0] - footprints[-1]) / footprints[0] * 100) if footprints[0] > 0 else 0

    if slope < -50: direction, desc = "improving", f"Your footprint is decreasing by ~{abs(slope):.0f} kg/month. Excellent!"
    elif slope < 50: direction, desc = "stable", "Your footprint has been relatively stable."
    else: direction, desc = "increasing", f"Your footprint is increasing by ~{slope:.0f} kg/month."

    return {"trend_direction": direction, "monthly_change_kg": round(slope, 2),
            "trend_description": desc, "projected_next_month_kg": round(projected, 2),
            "improvement_pct": round(improvement_pct, 1), "data_points": n,
            "first_footprint_kg": round(footprints[0], 2), "last_footprint_kg": round(footprints[-1], 2)}


def aggregate_community_data(assessments: list[dict[str, Any]], user_id: int | None = None) -> dict[str, Any]:
    """Aggregate anonymized community data, excluding the calling user."""
    peers = [a for a in assessments if user_id is None or a.get("user_id") != user_id]
    if not peers:
        return {"peer_count": 0, "peer_average_kg": 0.0, "peer_median_kg": 0.0,
                "peer_best_kg": 0.0, "peer_worst_kg": 0.0, "peer_average_score": 0,
                "summary": "No peer data available."}

    fps = sorted(a["footprint"] for a in peers)
    scores = [a.get("eco_score", 0) for a in peers]
    n = len(fps)
    return {"peer_count": n, "peer_average_kg": round(sum(fps) / n, 2),
            "peer_median_kg": round(fps[n // 2] if n % 2 else (fps[n // 2 - 1] + fps[n // 2]) / 2, 2),
            "peer_best_kg": round(fps[0], 2), "peer_worst_kg": round(fps[-1], 2),
            "peer_average_score": round(sum(scores) / n, 1) if scores else 0,
            "summary": f"Compared against {n} community members."}


def calculate_reduction_pathway(current_kg: float, target_kg: float, months: int = 24) -> dict[str, Any]:
    """Calculate a monthly reduction pathway with quarterly milestones."""
    if current_kg <= 0:
        return {"feasible": False, "message": "Current footprint is zero or negative."}

    total_reduction = current_kg - target_kg
    monthly = total_reduction / months if months > 0 else 0
    milestones = []
    for q in range(1, months // 3 + 1):
        m = q * 3
        t = max(target_kg, current_kg - monthly * m)
        milestones.append({"quarter": q, "month": m, "target_kg": round(t, 2),
                           "reduction_from_start_kg": round(current_kg - t, 2)})

    pct_per_month = (monthly / current_kg * 100) if current_kg > 0 else 0
    if pct_per_month > 10: feas, msg = "aggressive", "Aggressive — consider extending timeline."
    elif pct_per_month > 5: feas, msg = "ambitious", "Ambitious but achievable with consistent effort."
    elif pct_per_month > 2: feas, msg = "realistic", "Realistic and achievable reduction pathway."
    else: feas, msg = "moderate", "Moderate pace — easy to sustain long-term."

    return {"current_kg": current_kg, "target_kg": target_kg, "total_reduction_kg": round(total_reduction, 2),
            "monthly_reduction_kg": round(monthly, 2), "timeline_months": months,
            "feasibility": feas, "feasibility_message": msg, "quarterly_milestones": milestones}


def generate_benchmarking_summary(user_footprint: float, contributors: dict[str, float] | None,
                                  region: str = "Global", user_id: int | None = None,
                                  assessment_history: list[dict] | None = None,
                                  community_assessments: list[dict] | None = None) -> dict[str, Any]:
    """Generate a comprehensive benchmarking summary — main entry point."""
    gap = calculate_regional_gap(user_footprint, region)
    cat_comps = compare_categories(contributors, region) if contributors else []
    trend = calculate_monthly_trend(assessment_history) if assessment_history else {"trend_direction": "insufficient_data", "data_points": 0}
    community = aggregate_community_data(community_assessments, user_id) if community_assessments else {"peer_count": 0, "summary": "No community data available."}

    return {"region": region, "user_footprint_kg": user_footprint, "regional_gap": gap,
            "percentile": calculate_percentile(user_footprint, region),
            "category_comparisons": cat_comps, "trend": trend, "community": community,
            "reduction_pathway": calculate_reduction_pathway(user_footprint, gap["target_2030_kg"], 48),
            "insights": generate_insights(user_footprint, contributors, region),
            "generated_at": datetime.utcnow().isoformat()}
