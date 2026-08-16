"""Rainwater harvesting potential, tank sizing and payback.

The existing water footprint feature is demand-side only: it tells a user how
much water they consume. This module is the supply-side counterpart - how much
rain lands on their roof, how big a tank actually makes sense, how much of
their demand it covers, and how long it takes to pay for itself.

The harvest model is the standard design formula::

    litres = roof_area_m2 * rainfall_mm * runoff_coefficient * system_efficiency

``rainfall_mm`` doubles as litres per square metre (1 mm over 1 m² = 1 litre).
The runoff coefficient accounts for the roof material; system efficiency
accounts for first-flush diversion and filter losses.

Built-in climate profiles keep the feature usable offline, and a user who
knows their local rainfall can override every month.

The module is self-contained: its SQLite table is created lazily and no shared
files are modified.
"""

import os
import json
import sqlite3
import logging
from typing import Any

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

MONTHS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

# Fraction of rainfall that actually reaches the tank from each roof type.
ROOF_MATERIALS = {
    "Metal / corrugated sheet": {"runoff": 0.90, "note": "The best harvesting surface - smooth and fast draining."},
    "Glazed tile": {"runoff": 0.85, "note": "Very good; little is lost to absorption."},
    "Concrete / RCC": {"runoff": 0.80, "note": "Good, though a porous slab absorbs some rain."},
    "Asphalt shingle": {"runoff": 0.75, "note": "Usable, but check that granules are filtered out."},
    "Unglazed tile": {"runoff": 0.70, "note": "Porous clay soaks up part of every shower."},
    "Gravel / built-up": {"runoff": 0.60, "note": "Significant absorption and evaporation losses."},
    "Green roof": {"runoff": 0.30, "note": "Most rain feeds the planting - great for runoff, poor for harvesting."},
}

# Losses from first-flush diversion, filters and tank overflow plumbing.
SYSTEM_EFFICIENCY = 0.85

# Representative monthly rainfall in mm. These let the planner work with no
# network access; users with local figures can override every month.
CLIMATE_ZONES = {
    "Tropical monsoon": [10, 12, 25, 70, 180, 420, 480, 390, 250, 120, 35, 12],
    "Temperate maritime": [85, 65, 70, 60, 60, 60, 65, 75, 70, 95, 100, 95],
    "Mediterranean": [90, 80, 65, 50, 25, 8, 3, 6, 30, 75, 100, 100],
    "Semi-arid": [12, 14, 18, 20, 25, 15, 30, 35, 25, 20, 10, 10],
    "Continental": [45, 40, 50, 60, 75, 85, 80, 75, 60, 55, 50, 48],
    "Humid subtropical": [95, 100, 115, 100, 95, 105, 120, 115, 95, 85, 90, 95],
}

DEFAULT_CLIMATE_ZONE = "Temperate maritime"

# Candidate tank sizes in litres, from a domestic barrel to a small cistern.
TANK_SIZES = [500, 1000, 2000, 3000, 5000, 7500, 10000, 15000, 20000]

# Typical installed cost per litre of storage, in the user's currency.
TANK_COST_PER_LITRE = 0.35
DEFAULT_INSTALL_COST = 400.0

# Municipal water price per kilolitre (1000 L).
DEFAULT_WATER_PRICE_PER_KL = 2.50

# kg CO2 per litre of mains water from treatment and pumping.
DEFAULT_TREATMENT_INTENSITY = 0.00034

# Baseline household demand, in litres per person per day, for the domestic
# uses rainwater can serve (toilets, laundry, cleaning, garden).
LITRES_PER_PERSON_PER_DAY = 90.0
GARDEN_LITRES_PER_M2_PER_MONTH = 40.0


def list_roof_materials() -> list[dict[str, Any]]:
    """Return roof materials, best harvesting surface first."""
    return sorted(
        ({"name": name, **info} for name, info in ROOF_MATERIALS.items()),
        key=lambda item: item["runoff"],
        reverse=True,
    )


def get_runoff_coefficient(roof_material: str) -> float:
    """Return the runoff coefficient for a roof material."""
    info = ROOF_MATERIALS.get(roof_material)
    if not info:
        return ROOF_MATERIALS["Concrete / RCC"]["runoff"]
    return info["runoff"]


def get_climate_profile(zone: str) -> list[float]:
    """Return the 12-month rainfall profile for a climate zone, in mm."""
    return list(CLIMATE_ZONES.get(zone, CLIMATE_ZONES[DEFAULT_CLIMATE_ZONE]))


def _clean_positive(value: float, maximum: float, default: float = 0.0) -> float:
    """Coerce a user-supplied number into a sane, non-negative range."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number != number or number in (float("inf"), float("-inf")):
        return default
    return max(0.0, min(number, maximum))


def _clean_rainfall_series(monthly_rainfall_mm: list[float] | None) -> list[float]:
    """Normalise a rainfall series to exactly 12 non-negative months."""
    series = list(monthly_rainfall_mm or [])[:12]
    series = [_clean_positive(value, 3000.0) for value in series]
    series += [0.0] * (12 - len(series))
    return series


def annual_harvest_potential(roof_area_m2: float, annual_rainfall_mm: float, roof_material: str) -> float:
    """Litres of rainwater that can be captured in a year."""
    area = _clean_positive(roof_area_m2, 10000.0)
    rainfall = _clean_positive(annual_rainfall_mm, 20000.0)
    runoff = get_runoff_coefficient(roof_material)
    return round(area * rainfall * runoff * SYSTEM_EFFICIENCY, 1)


def monthly_harvest(roof_area_m2: float, monthly_rainfall_mm: list[float] | None, roof_material: str) -> list[float]:
    """Return the 12-month harvest series in litres."""
    area = _clean_positive(roof_area_m2, 10000.0)
    runoff = get_runoff_coefficient(roof_material)
    rainfall = _clean_rainfall_series(monthly_rainfall_mm)
    return [round(area * mm * runoff * SYSTEM_EFFICIENCY, 1) for mm in rainfall]


def estimate_household_demand(people: int, garden_m2: float = 0.0, monthly_profile: list[float] | None = None) -> list[float]:
    """Estimate the monthly household demand rainwater could serve, in litres.

    ``monthly_profile`` optionally scales garden watering by month (a list of
    12 multipliers) so summer irrigation is not spread evenly across the year.
    """
    people = max(0.0, _clean_positive(people, 50.0))
    garden = _clean_positive(garden_m2, 5000.0)

    if monthly_profile and len(monthly_profile) == 12:
        garden_profile = [_clean_positive(value, 5.0, 1.0) for value in monthly_profile]
    else:
        garden_profile = [1.0] * 12

    demand = []
    for index, days in enumerate(DAYS_IN_MONTH):
        indoor = people * LITRES_PER_PERSON_PER_DAY * days
        outdoor = garden * GARDEN_LITRES_PER_M2_PER_MONTH * garden_profile[index]
        demand.append(round(indoor + outdoor, 1))
    return demand


def demand_from_water_assessment(assessment: dict[str, Any] | None, people: int = 1, garden_m2: float = 0.0) -> list[float]:
    """Build a monthly demand series from a saved Water Footprint assessment.

    The water feature stores a daily litre total, so it is expanded across the
    month; when no assessment is available the generic estimate is used.
    """
    daily = None
    if assessment:
        for key in ("total_liters", "total_litres", "daily_liters"):
            if assessment.get(key):
                daily = _clean_positive(assessment[key], 100000.0)
                break

    if not daily:
        return estimate_household_demand(people, garden_m2)

    return [round(daily * days, 1) for days in DAYS_IN_MONTH]


def simulate_storage(tank_litres: float, monthly_harvest_l: list[float] | None, monthly_demand_l: list[float] | None) -> dict[str, Any]:
    """Simulate a month-by-month tank water balance.

    Returns the per-month stored, supplied, overflow and shortfall figures.
    The simulation guarantees that storage never goes negative and never
    exceeds the tank capacity, and that every litre harvested is either
    supplied, stored or overflowed.
    """
    capacity = _clean_positive(tank_litres, 1000000.0)
    harvest = list(monthly_harvest_l or [0.0] * 12)[:12]
    harvest += [0.0] * (12 - len(harvest))
    demand = list(monthly_demand_l or [0.0] * 12)[:12]
    demand += [0.0] * (12 - len(demand))

    stored = 0.0
    months = []
    total_supplied = 0.0
    total_overflow = 0.0
    total_shortfall = 0.0

    for index in range(12):
        available = stored + max(0.0, harvest[index])
        needed = max(0.0, demand[index])

        supplied = min(available, needed)
        shortfall = needed - supplied
        remaining = available - supplied

        overflow = max(0.0, remaining - capacity)
        stored = min(remaining, capacity)

        total_supplied += supplied
        total_overflow += overflow
        total_shortfall += shortfall

        months.append(
            {
                "month": MONTHS[index],
                "harvest_l": round(harvest[index], 1),
                "demand_l": round(needed, 1),
                "supplied_l": round(supplied, 1),
                "shortfall_l": round(shortfall, 1),
                "overflow_l": round(overflow, 1),
                "stored_l": round(stored, 1),
            }
        )

    total_demand = sum(max(0.0, value) for value in demand)

    return {
        "tank_litres": round(capacity, 1),
        "months": months,
        "total_harvest_l": round(sum(max(0.0, v) for v in harvest), 1),
        "total_demand_l": round(total_demand, 1),
        "total_supplied_l": round(total_supplied, 1),
        "total_overflow_l": round(total_overflow, 1),
        "total_shortfall_l": round(total_shortfall, 1),
        "coverage_pct": (
            round(total_supplied / total_demand * 100, 1) if total_demand > 0 else 0.0
        ),
        "overflow_months": [m["month"] for m in months if m["overflow_l"] > 0],
        "shortfall_months": [m["month"] for m in months if m["shortfall_l"] > 0],
    }


def recommend_tank_size(monthly_harvest_l: list[float], monthly_demand_l: list[float], candidates: list[float] | None = None) -> dict[str, Any]:
    """Pick the tank size with the best coverage per litre of storage.

    Bigger is always at least as good hydraulically, so the recommendation
    stops once extra storage stops meaningfully improving coverage.
    """
    candidates = TANK_SIZES if candidates is None else list(candidates)
    options = []

    for size in candidates:
        simulation = simulate_storage(size, monthly_harvest_l, monthly_demand_l)
        options.append(
            {
                "tank_litres": size,
                "coverage_pct": simulation["coverage_pct"],
                "supplied_l": simulation["total_supplied_l"],
                "overflow_l": simulation["total_overflow_l"],
                "coverage_per_1000l": round(
                    simulation["coverage_pct"] / (size / 1000.0), 3
                ),
            }
        )

    if not options:
        return {"recommended": None, "options": []}

    best_coverage = max(option["coverage_pct"] for option in options)

    # The smallest tank that reaches within 2 percentage points of the best
    # achievable coverage - beyond that, extra storage is wasted money.
    recommended = next(
        option
        for option in options
        if option["coverage_pct"] >= best_coverage - 2.0
    )

    return {
        "recommended": recommended,
        "best_coverage_pct": best_coverage,
        "options": options,
    }


def demand_coverage(supplied_l: float, demand_l: float) -> float:
    """Percentage of demand met by harvested water, bounded to 0-100."""
    demand_l = max(0.0, float(demand_l or 0.0))
    if demand_l <= 0:
        return 0.0
    supplied_l = max(0.0, float(supplied_l or 0.0))
    return round(min(100.0, supplied_l / demand_l * 100), 1)


def savings_estimate(
    litres_supplied: float,
    water_price_per_kl: float = DEFAULT_WATER_PRICE_PER_KL,
    tank_litres: float = 0,
    install_cost: float = DEFAULT_INSTALL_COST,
) -> dict[str, Any]:
    """Annual money saved and simple payback period in years."""
    litres = max(0.0, float(litres_supplied or 0.0))
    price = max(0.0, float(water_price_per_kl or 0.0))
    tank_cost = max(0.0, float(tank_litres or 0.0)) * TANK_COST_PER_LITRE
    setup_cost = tank_cost + max(0.0, float(install_cost or 0.0))

    annual_saving = litres / 1000.0 * price
    payback = setup_cost / annual_saving if annual_saving > 0 else None

    return {
        "litres_supplied": round(litres, 1),
        "annual_saving": round(annual_saving, 2),
        "tank_cost": round(tank_cost, 2),
        "install_cost": round(max(0.0, float(install_cost or 0.0)), 2),
        "setup_cost": round(setup_cost, 2),
        "payback_years": round(payback, 1) if payback is not None else None,
        "ten_year_net": round(annual_saving * 10 - setup_cost, 2),
    }


def co2_savings(litres_supplied: float, treatment_intensity: float = DEFAULT_TREATMENT_INTENSITY) -> dict[str, Any]:
    """CO2 avoided by not treating and pumping the equivalent mains water."""
    litres = max(0.0, float(litres_supplied or 0.0))
    intensity = max(0.0, float(treatment_intensity or 0.0))
    annual_kg = litres * intensity

    return {
        "annual_kg": round(annual_kg, 2),
        "ten_year_kg": round(annual_kg * 10, 2),
        # A mature tree absorbs roughly 21 kg CO2 a year.
        "tree_equivalent": round(annual_kg / 21.0, 2),
    }


def build_plan(
    roof_area_m2: float,
    roof_material: str,
    climate_zone: str = DEFAULT_CLIMATE_ZONE,
    monthly_rainfall_mm: list[float] | None = None,
    people: int = 2,
    garden_m2: float = 0.0,
    tank_litres: float | None = None,
    water_price_per_kl: float = DEFAULT_WATER_PRICE_PER_KL,
    install_cost: float = DEFAULT_INSTALL_COST,
) -> dict[str, Any]:
    """Build a complete harvesting plan in one call."""
    rainfall = (
        _clean_rainfall_series(monthly_rainfall_mm)
        if monthly_rainfall_mm
        else get_climate_profile(climate_zone)
    )
    harvest = monthly_harvest(roof_area_m2, rainfall, roof_material)
    demand = estimate_household_demand(people, garden_m2)

    recommendation = recommend_tank_size(harvest, demand)
    chosen_tank = tank_litres or (
        recommendation["recommended"]["tank_litres"]
        if recommendation["recommended"]
        else 0
    )

    simulation = simulate_storage(chosen_tank, harvest, demand)
    savings = savings_estimate(
        simulation["total_supplied_l"], water_price_per_kl, chosen_tank, install_cost
    )
    carbon = co2_savings(simulation["total_supplied_l"])

    return {
        "roof_area_m2": _clean_positive(roof_area_m2, 10000.0),
        "roof_material": roof_material if roof_material in ROOF_MATERIALS else "Concrete / RCC",
        "runoff_coefficient": get_runoff_coefficient(roof_material),
        "climate_zone": climate_zone if climate_zone in CLIMATE_ZONES else DEFAULT_CLIMATE_ZONE,
        "monthly_rainfall_mm": rainfall,
        "annual_rainfall_mm": round(sum(rainfall), 1),
        "monthly_harvest_l": harvest,
        "annual_harvest_l": round(sum(harvest), 1),
        "monthly_demand_l": demand,
        "annual_demand_l": round(sum(demand), 1),
        "tank_litres": chosen_tank,
        "recommendation": recommendation,
        "simulation": simulation,
        "savings": savings,
        "carbon": carbon,
    }


def get_harvesting_tips(plan: dict[str, Any], limit: int = 5) -> list[str]:
    """Return guidance ranked by what this particular plan looks like."""
    simulation = plan.get("simulation", {})
    if not simulation.get("total_demand_l"):
        return ["Enter your roof size and household to see a harvesting estimate."]

    tips = []

    overflow = simulation.get("total_overflow_l", 0.0)
    harvest = simulation.get("total_harvest_l", 0.0)
    if harvest > 0 and overflow / harvest > 0.4:
        tips.append(
            f"You are overflowing {overflow / harvest * 100:.0f}% of what you collect - "
            f"a larger tank, or a second use for the water, would capture more of it."
        )

    if simulation.get("shortfall_months"):
        tips.append(
            f"You run dry in {', '.join(simulation['shortfall_months'][:3])}. "
            f"Storing more before the dry season helps more than a bigger roof."
        )

    if simulation.get("coverage_pct", 0) >= 50:
        tips.append(
            f"Harvested rain can cover {simulation['coverage_pct']}% of the demand "
            f"rainwater is suited to - toilets, laundry, cleaning and the garden."
        )

    payback = plan.get("savings", {}).get("payback_years")
    if payback and payback <= 10:
        tips.append(f"At current water prices the system pays for itself in {payback} years.")
    elif payback:
        tips.append(
            f"Payback is {payback} years at current water prices - worth revisiting "
            f"if water gets more expensive or you add uses for the water."
        )

    tips.append(
        "Fit a first-flush diverter: the first few litres off a roof carry most of "
        "the dust, leaves and droppings."
    )
    tips.append(
        "Keep the tank covered and screened - standing open water breeds mosquitoes."
    )

    return tips[: max(0, int(limit))]


def _get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_rainwater_db() -> None:
    """Create the rainwater plan table if it does not exist yet."""
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rainwater_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_name TEXT NOT NULL,
                roof_area_m2 REAL NOT NULL,
                roof_material TEXT NOT NULL,
                climate_zone TEXT NOT NULL,
                tank_litres REAL NOT NULL,
                annual_harvest_l REAL NOT NULL,
                coverage_pct REAL NOT NULL,
                payback_years REAL,
                plan_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Rainwater init error: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def save_harvest_plan(user_id: int, plan_name: str, plan: dict[str, Any]) -> int | None:
    """Persist a harvesting plan. Returns the new row id or None."""
    init_rainwater_db()
    conn = None
    try:
        conn = _get_conn()
        cursor = conn.execute(
            """
            INSERT INTO rainwater_plans (
                user_id, plan_name, roof_area_m2, roof_material, climate_zone,
                tank_litres, annual_harvest_l, coverage_pct, payback_years, plan_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                (plan_name or "My roof").strip() or "My roof",
                plan.get("roof_area_m2", 0.0),
                plan.get("roof_material", "Concrete / RCC"),
                plan.get("climate_zone", DEFAULT_CLIMATE_ZONE),
                plan.get("tank_litres", 0),
                plan.get("annual_harvest_l", 0.0),
                plan.get("simulation", {}).get("coverage_pct", 0.0),
                plan.get("savings", {}).get("payback_years"),
                json.dumps(
                    {
                        "monthly_rainfall_mm": plan.get("monthly_rainfall_mm", []),
                        "monthly_harvest_l": plan.get("monthly_harvest_l", []),
                        "monthly_demand_l": plan.get("monthly_demand_l", []),
                    }
                ),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as exc:
        logger.error("Unable to save rainwater plan: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def get_harvest_plans(user_id: int, limit: int = 25) -> list[dict[str, Any]]:
    """Return a user's saved harvesting plans, newest first."""
    init_rainwater_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, plan_name, roof_area_m2, roof_material, climate_zone,
                   tank_litres, annual_harvest_l, coverage_pct, payback_years,
                   plan_json, created_at
            FROM rainwater_plans
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT ?
            """,
            (user_id, int(limit)),
        ).fetchall()

        plans = []
        for row in rows:
            record = dict(row)
            try:
                record["series"] = json.loads(record.pop("plan_json"))
            except (TypeError, ValueError):
                record["series"] = {}
            plans.append(record)
        return plans
    except sqlite3.Error as exc:
        logger.error("Unable to load rainwater plans: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def delete_harvest_plan(plan_id: int) -> bool:
    """Delete a saved harvesting plan."""
    init_rainwater_db()
    conn = None
    try:
        conn = _get_conn()
        cursor = conn.execute("DELETE FROM rainwater_plans WHERE id = ?", (plan_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as exc:
        logger.error("Unable to delete rainwater plan: %s", exc)
        return False
    finally:
        if conn:
            conn.close()
