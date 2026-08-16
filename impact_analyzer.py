from emissions import calculate_footprint
from typing import Any

# Simple qualitative effort score — lower number = easier change
EFFORT_SCORE = {"Low": 1, "Medium": 2, "High": 3}


def analyze_minimal_change(transport: str, distance: float, electricity: float, diet: str,
                           flights: int, region: str, total: float,
                           dynamic_factors: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """
    Simulates small, realistic lifestyle tweaks and ranks them by
    CO2 savings relative to how much effort they take, so the
    smallest change with the biggest impact is surfaced first.
    Reuses emission factors and calculation logic efficiently without redundant transformations.
    """
    candidates = []

    # 1. Reduce electricity usage by 10%
    if electricity > 0:
        new_total = calculate_footprint(transport, distance, electricity * 0.9, diet, flights, region)[0]
        candidates.append({
            "change": "Reduce electricity usage by 10%",
            "effort": "Low",
            "savings": round(total - new_total, 2),
            "reason": "Small cuts to daily electricity use (e.g. turning off standby devices) require almost no lifestyle disruption.",
        })

    # 2. Reduce daily commute distance by 20% (e.g. work from home once a week)
    if distance > 0:
        new_total = calculate_footprint(transport, distance * 0.8, electricity, diet, flights, region)[0]
        candidates.append({
            "change": "Reduce daily commute distance by 20% (e.g. work from home once a week)",
            "effort": "Low",
            "savings": round(total - new_total, 2),
            "reason": "Cutting commute distance slightly reduces emissions every day without changing your mode of transport.",
        })

    # 3. Switch to a Vegetarian diet
    if diet == "Non-Vegetarian":
        new_total = calculate_footprint(transport, distance, electricity, "Vegetarian", flights, region)[0]
        candidates.append({
            "change": "Switch to a Vegetarian diet",
            "effort": "Medium",
            "savings": round(total - new_total, 2),
            "reason": "Diet has one of the largest fixed annual emission factors, so switching yields a large one-time drop.",
        })

    # 4. Take one fewer flight per year
    if flights >= 1:
        new_total = calculate_footprint(transport, distance, electricity, diet, flights - 1, region)[0]
        candidates.append({
            "change": "Take one fewer flight per year",
            "effort": "Medium",
            "savings": round(total - new_total, 2),
            "reason": "Flights have a very high per-trip emission factor, so avoiding even one has an outsized effect.",
        })

    # 5. Switch from Car to Public Transport
    if transport == "Car":
        new_total = calculate_footprint("Public Transport", distance, electricity, diet, flights, region)[0]
        candidates.append({
            "change": "Switch from Car to Public Transport",
            "effort": "Medium",
            "savings": round(total - new_total, 2),
            "reason": "Public transport has a much lower per-km emission factor than driving a car.",
        })

    # Only keep changes that actually save emissions
    candidates = [c for c in candidates if c["savings"] > 0]
    if not candidates:
        return []

    # Rank by savings-per-unit-effort, so small/easy changes with big payoff rank highest
    for c in candidates:
        c["impact_ratio"] = c["savings"] / EFFORT_SCORE[c["effort"]]

    candidates.sort(key=lambda c: c["impact_ratio"], reverse=True)
    return candidates