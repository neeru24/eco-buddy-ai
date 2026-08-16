WASTE_CATEGORIES = {
    "Food Scraps": {"biodegradable": True, "avg_weekly_kg": 2.0, "co2_per_kg": 2.5},
    "Plastic Packaging": {"biodegradable": False, "avg_weekly_kg": 0.5, "co2_per_kg": 6.0},
    "Paper & Cardboard": {"biodegradable": True, "avg_weekly_kg": 1.0, "co2_per_kg": 3.0},
    "Glass": {"biodegradable": False, "avg_weekly_kg": 0.8, "co2_per_kg": 1.5},
    "Metal (Cans)": {"biodegradable": False, "avg_weekly_kg": 0.3, "co2_per_kg": 8.0},
    "Electronics (E-Waste)": {"biodegradable": False, "avg_weekly_kg": 0.1, "co2_per_kg": 20.0},
    "Textiles": {"biodegradable": True, "avg_weekly_kg": 0.2, "co2_per_kg": 10.0},
    "Other (Mixed Waste)": {"biodegradable": False, "avg_weekly_kg": 1.0, "co2_per_kg": 4.0},
}

LANDFILL_METHANE_FACTOR = 0.5


def calculate_waste_footprint(waste_by_category: dict) -> dict:
    total_weekly_kg = 0.0
    total_co2_weekly = 0.0
    biodegradable_kg = 0.0
    breakdown = {}

    for cat, weekly_kg in waste_by_category.items():
        info = WASTE_CATEGORIES.get(cat)
        if not info:
            continue
        weekly_kg = max(0.0, float(weekly_kg))
        co2 = weekly_kg * info["co2_per_kg"]
        total_weekly_kg += weekly_kg
        total_co2_weekly += co2
        if info["biodegradable"]:
            biodegradable_kg += weekly_kg
        breakdown[cat] = {"weekly_kg": weekly_kg, "co2_weekly": co2}

    landfill_methane = biodegradable_kg * LANDFILL_METHANE_FACTOR
    annual_co2 = total_co2_weekly * 52
    recyclable_pct = _calc_recyclable_pct(waste_by_category)

    return {
        "total_weekly_kg": round(total_weekly_kg, 2),
        "total_co2_weekly": round(total_co2_weekly, 2),
        "annual_co2": round(annual_co2, 2),
        "landfill_methane_kg": round(landfill_methane, 2),
        "recyclable_pct": round(recyclable_pct, 1),
        "breakdown": breakdown,
    }


def _calc_recyclable_pct(waste_by_category: dict) -> float:
    recyclable = {"Plastic Packaging", "Paper & Cardboard", "Glass", "Metal (Cans)"}
    total = sum(max(0.0, float(v)) for v in waste_by_category.values())
    if total == 0:
        return 0.0
    recyclable_total = sum(max(0.0, float(waste_by_category.get(c, 0.0))) for c in recyclable)
    return (recyclable_total / total) * 100.0


WASTE_REDUCTION_TIPS = {
    "Food Scraps": [
        "Start composting food scraps instead of sending them to landfill.",
        "Plan meals ahead to reduce food waste.",
        "Store produce correctly to extend freshness.",
    ],
    "Plastic Packaging": [
        "Switch to reusable shopping bags and containers.",
        "Buy in bulk to reduce packaging waste.",
        "Choose products with minimal or recyclable packaging.",
    ],
    "Paper & Cardboard": [
        "Recycle all clean paper and cardboard.",
        "Opt for digital bills and statements.",
        "Use both sides of paper before recycling.",
    ],
    "Glass": [
        "Glass is 100% recyclable — rinse and recycle all jars and bottles.",
        "Reuse glass containers for storage.",
        "Choose glass over plastic when possible.",
    ],
    "Metal (Cans)": [
        "Rinse and recycle all aluminum and steel cans.",
        "Aluminum can be recycled infinitely — never throw cans in trash.",
        "Choose products with recycled-content packaging.",
    ],
    "Electronics (E-Waste)": [
        "Donate or sell working electronics instead of discarding.",
        "Use certified e-waste recyclers for broken devices.",
        "Extend device life by repairing instead of replacing.",
    ],
    "Textiles": [
        "Donate unwanted clothing to charity or textile recycling.",
        "Repair torn clothes instead of throwing them away.",
        "Buy second-hand or sustainably produced clothing.",
    ],
    "Other (Mixed Waste)": [
        "Audit your trash to identify what can be reduced, reused, or recycled.",
        "Avoid single-use items wherever possible.",
        "Choose products with longer lifespans to reduce overall waste.",
    ],
}
