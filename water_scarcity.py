"""Water scarcity footprint: blue/green/grey separation with AWARE weighting.

``water.py`` reports a water footprint in litres. A litre is not a unit of
impact. A litre drawn from an aquifer in a drought and a litre of rain that
fell on a field are the same number and completely different things, and the
current model adds them together.

Three things go wrong with a single litre total.

Adding water that is not comparable
-----------------------------------
*   **Blue water** is surface and groundwater withdrawn from a basin. This is
    the water that competes with other users and with ecosystems.
*   **Green water** is rainfall held in soil and used by plants. It does not
    compete in the same way - it was going to fall on that field regardless.
*   **Grey water** is not consumed at all. It is a *dilution volume*: the
    water needed to assimilate a pollutant load to an acceptable
    concentration. Adding it to blue water counts water that is still in the
    river.

The diet term is the worst offender, because agricultural virtual water is
overwhelmingly green. A user eating a diet with a large green footprint sees
the same litre total as a user pumping the same volume out of a depleting
aquifer.

Location is not represented at all
----------------------------------
Two thousand litres a day is unremarkable in Norway and serious in Rajasthan.
The app's shower advice is identical in both. This is the largest error in
the module and it cannot be fixed by refining the per-shower factor. AWARE
(Available WAter REmaining) handles it by weighting blue water consumption
against what is left in the basin after demand, producing a figure in cubic
metres world-equivalent - a unit that can legitimately be compared across
locations.

Withdrawal is not consumption
-----------------------------
Most household "use" is withdrawal that returns to the basin, treated, a
short time later. Consumption is the part that evaporates or leaves in
product. Applying scarcity weighting to withdrawal rather than consumption
overstates household use several-fold, and getting this right is most of the
point of the module. A shower withdraws ten litres a minute and consumes
almost none of it.

What follows from all this
--------------------------
Ranking actions by scarcity-weighted saving inverts the app's current advice
for most users: direct household use is a small share of a personal water
footprint and food is nearly all of it. That inversion is the output worth
having, and the module states plainly when it happens.

Self-contained: standard library only, SQLite tables created lazily, no
shared files modified. ``water.py`` is untouched, so no stored litre figure
changes meaning underneath a user.
"""

import os
import json
import sqlite3
import logging
from typing import Any

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

LITRES_PER_CUBIC_METRE = 1000.0

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# AWARE characterisation factors, m3 world-equivalent per m3 consumed. The
# global average is 1.0 by construction; the scale runs to 100 for the most
# stressed basins and to 0.1 for the least. These are regional archetypes
# rather than any particular basin - a real assessment uses a basin factor,
# and get_region() returns enough structure to swap one in.
REGIONS = {
    "Global average": {
        "factor": 1.0,
        "note": "The reference point. Useful for a comparison, meaningless "
                "as a description of anywhere in particular.",
    },
    "Northern Europe": {
        "factor": 0.4,
        "note": "Rain-fed and cool. Household water use here is close to "
                "harmless, which is worth knowing before optimising it.",
    },
    "Western Europe": {
        "factor": 1.1,
        "note": "Moderate stress with real summer pressure in the south.",
    },
    "Mediterranean": {
        "factor": 8.5,
        "note": "Seasonal scarcity with irrigation demand peaking exactly "
                "when availability troughs.",
    },
    "US Northeast": {
        "factor": 0.9,
        "note": "Generally water-rich.",
    },
    "US Southwest": {
        "factor": 34.0,
        "note": "Colorado basin. Structural over-allocation - the river has "
                "not reliably reached the sea since the 1960s.",
    },
    "South Asia": {
        "factor": 45.0,
        "note": "Groundwater depletion at rates that are not replaceable on "
                "any human timescale.",
    },
    "Northern China": {
        "factor": 38.0,
        "note": "Severe scarcity, heavy inter-basin transfer.",
    },
    "Southeast Asia": {
        "factor": 3.2,
        "note": "Wet overall, with sharp dry-season stress.",
    },
    "Sub-Saharan Africa": {
        "factor": 12.0,
        "note": "Highly variable. A regional average hides more here than "
                "almost anywhere else.",
    },
    "Australia": {
        "factor": 22.0,
        "note": "Murray-Darling. Drought is the normal state, not the "
                "exception.",
    },
    "South America": {
        "factor": 1.6,
        "note": "Water-rich in aggregate, with badly stressed exceptions.",
    },
}

DEFAULT_REGION = "Global average"

# Monthly multipliers on the annual scarcity factor for a northern-hemisphere
# temperate pattern. Scarcity is not an annual property: irrigation demand
# peaks when availability troughs, and averaging across the year hides the
# entire effect. August at 1.9 and February at 0.5 is nearly a fourfold
# difference in the impact of the same litre.
SEASONAL_PROFILE = [
    0.55, 0.50, 0.60, 0.80, 1.10, 1.50,
    1.80, 1.90, 1.45, 0.95, 0.70, 0.60,
]

# Household activities. `withdrawal` is litres taken from supply per unit;
# `consumptive_fraction` is the share that does not return to the basin.
# The rest goes back through the sewer, is treated, and is available again -
# which is why a shower is a much smaller scarcity event than its litre
# count suggests. `grey_factor` is the dilution volume per litre withdrawn.
HOUSEHOLD_ACTIVITIES = {
    "shower": {
        "withdrawal": 10.0,
        "unit": "minute",
        "consumptive_fraction": 0.05,
        "grey_factor": 0.6,
        "note": "Nearly all of it returns to the sewer. The scarcity impact "
                "is a twentieth of the litre count, and the energy to heat "
                "it usually matters more than the water.",
    },
    "bath": {
        "withdrawal": 80.0,
        "unit": "bath",
        "consumptive_fraction": 0.05,
        "grey_factor": 0.6,
        "note": "Same story as a shower, larger volume.",
    },
    "laundry": {
        "withdrawal": 50.0,
        "unit": "load",
        "consumptive_fraction": 0.05,
        "grey_factor": 1.4,
        "note": "The grey water term dominates: detergent needs dilution "
                "well beyond the wash volume.",
    },
    "dishwasher": {
        "withdrawal": 15.0,
        "unit": "run",
        "consumptive_fraction": 0.08,
        "grey_factor": 1.2,
        "note": "More water-efficient than washing by hand, which surprises "
                "people often enough to be worth stating.",
    },
    "toilet": {
        "withdrawal": 6.0,
        "unit": "flush",
        "consumptive_fraction": 0.02,
        "grey_factor": 1.8,
        "note": "Almost no consumption. The load on treatment is the "
                "impact, not the volume.",
    },
    "garden": {
        "withdrawal": 20.0,
        "unit": "minute",
        "consumptive_fraction": 0.90,
        "grey_factor": 0.0,
        "note": "The one household use that is genuinely consumptive - it "
                "evaporates or transpires and does not come back. It is also "
                "seasonal, which compounds it.",
    },
    "pool_topup": {
        "withdrawal": 100.0,
        "unit": "week",
        "consumptive_fraction": 0.95,
        "grey_factor": 0.2,
        "note": "Evaporation, in the season when the basin can least "
                "afford it.",
    },
    "drinking_cooking": {
        "withdrawal": 4.0,
        "unit": "day",
        "consumptive_fraction": 0.60,
        "grey_factor": 0.1,
        "note": "Small volume, mostly consumed. Not worth optimising.",
    },
}

# Virtual water in food, litres per kg, split blue/green/grey. The blue
# share is what scarcity weighting applies to, and it is the column that
# decides whether a dietary change helps a stressed basin or merely moves
# rainfall around.
FOOD_WATER = {
    "Beef": {"blue": 550, "green": 14400, "grey": 450,
             "note": "Enormous total, overwhelmingly green - it is mostly "
                     "rain falling on grazing land."},
    "Lamb": {"blue": 460, "green": 9500, "grey": 380,
             "note": "As beef. Grazing systems are green-water systems."},
    "Pork": {"blue": 460, "green": 4900, "grey": 620,
             "note": "Feed-driven, so more blue water than grazed meat."},
    "Chicken": {"blue": 310, "green": 3550, "grey": 470,
                "note": "Lower across the board than red meat."},
    "Cheese": {"blue": 400, "green": 4600, "grey": 250,
               "note": "Concentrated milk, so concentrated water."},
    "Milk": {"blue": 90, "green": 860, "grey": 70,
             "note": "Modest per litre; the volumes are what add up."},
    "Eggs": {"blue": 240, "green": 2600, "grey": 430,
             "note": "Feed again."},
    "Rice": {"blue": 1670, "green": 1150, "grey": 190,
             "note": "The blue-water crop. Irrigated paddies draw directly "
                     "from the basin, which is why rice dominates a "
                     "scarcity footprint in a way it never dominates a "
                     "litre total."},
    "Wheat": {"blue": 340, "green": 1280, "grey": 210,
              "note": "Partly irrigated, mostly rain-fed."},
    "Almonds": {"blue": 6100, "green": 4630, "grey": 1080,
                "note": "Grown overwhelmingly in a water-stressed basin, "
                        "and almost entirely irrigated. The worst "
                        "blue-water ratio in the table."},
    "Sugar": {"blue": 550, "green": 1080, "grey": 160,
              "note": "Irrigation-heavy in many producing regions."},
    "Vegetables": {"blue": 40, "green": 190, "grey": 60,
                   "note": "Small by any measure."},
    "Fruit": {"blue": 190, "green": 730, "grey": 90,
              "note": "Varies enormously by crop and origin."},
    "Coffee": {"blue": 120, "green": 15400, "grey": 380,
               "note": "Huge total, almost entirely green - shade-grown "
                       "coffee is rain-fed. A striking example of a big "
                       "number that is not a big impact."},
    "Chocolate": {"blue": 230, "green": 16500, "grey": 250,
                  "note": "As coffee: enormous and overwhelmingly green."},
    "Cotton (per kg fibre)": {"blue": 3100, "green": 5160, "grey": 2280,
                              "note": "Historically the cause of the Aral "
                                      "Sea's disappearance. Blue-water "
                                      "intensive and often grown where "
                                      "water is scarcest."},
}

# Below this share of the total, a component is not worth acting on and
# saying so is more useful than listing it.
MATERIALITY_THRESHOLD = 0.05

DAYS_PER_YEAR = 365


class WaterScarcityError(ValueError):
    """Raised when a request cannot be answered honestly."""


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if result != result:
        return default
    return result


def _non_negative(value: Any, default: float = 0.0) -> float:
    return max(0.0, _as_float(value, default))


# ---------------------------------------------------------------------------
# Regions and seasonality
# ---------------------------------------------------------------------------

def list_regions() -> list[str]:
    """Regions with a characterisation factor, driest first."""
    return sorted(REGIONS, key=lambda name: -REGIONS[name]["factor"])


def get_region(region: str) -> dict[str, Any]:
    """The scarcity factor and its rationale."""
    if region not in REGIONS:
        raise WaterScarcityError(
            f"Unknown region '{region}'. Pick one of: "
            + ", ".join(sorted(REGIONS))
            + ". There is deliberately no default - a scarcity footprint "
            "without a location is not a scarcity footprint, and silently "
            "assuming the global average would flatter every stressed basin."
        )
    entry = REGIONS[region]
    return {
        "region": region,
        "factor": entry["factor"],
        "note": entry["note"],
    }


def seasonal_factor(region: str, month: str | int | None = None) -> float:
    """The scarcity factor for a given month.

    Scarcity is not an annual property. Irrigation demand peaks when
    availability troughs, so the same litre in August and February are
    nearly a fourfold difference in impact.
    """
    base = get_region(region)["factor"]
    if month is None:
        return base
    if isinstance(month, str):
        if month not in MONTHS:
            raise WaterScarcityError(f"Unknown month '{month}'.")
        index = MONTHS.index(month)
    else:
        index = int(month) - 1
        if not 0 <= index < 12:
            raise WaterScarcityError("month must be 1-12 or a month name.")
    return base * SEASONAL_PROFILE[index]


# ---------------------------------------------------------------------------
# Household use
# ---------------------------------------------------------------------------

def list_household_activities() -> list[str]:
    """Household activities with a water model."""
    return sorted(HOUSEHOLD_ACTIVITIES)


def household_activity(activity: str) -> dict[str, Any]:
    """The parameters for one household activity."""
    if activity not in HOUSEHOLD_ACTIVITIES:
        raise WaterScarcityError(
            f"No water model for '{activity}'. Add one to "
            "HOUSEHOLD_ACTIVITIES rather than assuming a consumptive "
            "fraction - guessing that would produce exactly the "
            "withdrawal-as-consumption error this module corrects."
        )
    return dict(HOUSEHOLD_ACTIVITIES[activity])


def household_use(activity: str, quantity: float, days: int = 1) -> dict[str, Any]:
    """Withdrawal, consumption and grey water for a household activity.

    The distinction between withdrawal and consumption is the whole point.
    A shower withdraws ten litres a minute and consumes almost none of it,
    which is why household use is a far smaller scarcity event than a litre
    count implies.
    """
    entry = household_activity(activity)
    amount = _non_negative(quantity)
    repetitions = max(0, int(days))

    withdrawal = entry["withdrawal"] * amount * repetitions
    consumption = withdrawal * entry["consumptive_fraction"]
    grey = withdrawal * entry["grey_factor"]

    return {
        "activity": activity,
        "quantity": amount,
        "days": repetitions,
        "withdrawal_litres": withdrawal,
        "consumption_litres": consumption,
        "returned_litres": withdrawal - consumption,
        "grey_litres": grey,
        "consumptive_fraction": entry["consumptive_fraction"],
        "note": entry["note"],
    }


def household_profile(usage: dict[str, Any], days: int = DAYS_PER_YEAR) -> dict[str, Any]:
    """Aggregate a {activity: quantity_per_day} mapping over a period."""
    if not isinstance(usage, dict):
        raise WaterScarcityError("usage must be a mapping.")

    lines = [
        household_use(activity, quantity, days=days)
        for activity, quantity in usage.items()
    ]

    return {
        "lines": lines,
        "withdrawal_litres": sum(line["withdrawal_litres"] for line in lines),
        "consumption_litres": sum(line["consumption_litres"] for line in lines),
        "grey_litres": sum(line["grey_litres"] for line in lines),
        "days": max(0, int(days)),
    }


# ---------------------------------------------------------------------------
# Food and products
# ---------------------------------------------------------------------------

def list_foods() -> list[str]:
    """Foods with a blue/green/grey split."""
    return sorted(FOOD_WATER)


def food_water(food: str, kg: float) -> dict[str, Any]:
    """Blue, green and grey water for a mass of food.

    Only the blue component is scarcity-weighted later. Green water is
    rainfall that was going to land there anyway, and grey water is a
    dilution requirement rather than a withdrawal - reporting either inside
    a consumptive total is the error this separation exists to prevent.
    """
    if food not in FOOD_WATER:
        raise WaterScarcityError(
            f"No water profile for '{food}'. Add one to FOOD_WATER - "
            "an average would erase the blue/green split, which is the only "
            "part that determines whether a change helps a stressed basin."
        )
    mass = _non_negative(kg)
    entry = FOOD_WATER[food]

    blue = entry["blue"] * mass
    green = entry["green"] * mass
    grey = entry["grey"] * mass
    total = blue + green + grey

    return {
        "food": food,
        "kg": mass,
        "blue_litres": blue,
        "green_litres": green,
        "grey_litres": grey,
        "total_litres": total,
        "blue_share": blue / total if total > 0 else 0.0,
        "note": entry["note"],
    }


def diet_water(diet: dict[str, Any], days: int = DAYS_PER_YEAR) -> dict[str, Any]:
    """Aggregate a {food: kg_per_period} mapping."""
    if not isinstance(diet, dict):
        raise WaterScarcityError("diet must be a mapping.")

    lines = [food_water(food, kg) for food, kg in diet.items()]

    blue = sum(line["blue_litres"] for line in lines)
    green = sum(line["green_litres"] for line in lines)
    grey = sum(line["grey_litres"] for line in lines)

    return {
        "lines": lines,
        "blue_litres": blue,
        "green_litres": green,
        "grey_litres": grey,
        "total_litres": blue + green + grey,
        "days": max(0, int(days)),
    }


# ---------------------------------------------------------------------------
# Scarcity weighting
# ---------------------------------------------------------------------------

def scarcity_footprint(blue_litres: float, region: str, month: str | int | None = None) -> dict[str, Any]:
    """Weight blue water consumption by local scarcity.

    Returns cubic metres world-equivalent, which is the unit that can
    legitimately be compared across users and locations. Litres cannot.
    """
    blue = _non_negative(blue_litres)
    factor = seasonal_factor(region, month)
    cubic_metres = blue / LITRES_PER_CUBIC_METRE

    return {
        "region": region,
        "month": month,
        "factor": factor,
        "blue_litres": blue,
        "blue_m3": cubic_metres,
        "scarcity_m3_world_eq": cubic_metres * factor,
    }


def assess(
    household: dict[str, Any],
    diet: dict[str, Any],
    region: str,
    month: str | int | None = None,
) -> dict[str, Any]:
    """A complete scarcity assessment from household use and diet.

    Household **consumption** is weighted, not household withdrawal. Using
    withdrawal here would overstate domestic use by roughly an order of
    magnitude and would reproduce the error that makes shower advice look
    comparable to dietary advice.
    """
    region_detail = get_region(region)

    household_consumption = _non_negative(household.get("consumption_litres"))
    diet_blue = _non_negative(diet.get("blue_litres"))

    household_scarcity = scarcity_footprint(household_consumption, region, month)
    diet_scarcity = scarcity_footprint(diet_blue, region, month)

    total_scarcity = (
        household_scarcity["scarcity_m3_world_eq"]
        + diet_scarcity["scarcity_m3_world_eq"]
    )

    total_litres = (
        _non_negative(household.get("withdrawal_litres"))
        + _non_negative(diet.get("total_litres"))
    )

    return {
        "region": region_detail["region"],
        "region_note": region_detail["note"],
        "factor": household_scarcity["factor"],
        "month": month,
        "household": {
            "withdrawal_litres": _non_negative(household.get("withdrawal_litres")),
            "consumption_litres": household_consumption,
            "grey_litres": _non_negative(household.get("grey_litres")),
            "scarcity_m3": household_scarcity["scarcity_m3_world_eq"],
        },
        "diet": {
            "blue_litres": diet_blue,
            "green_litres": _non_negative(diet.get("green_litres")),
            "grey_litres": _non_negative(diet.get("grey_litres")),
            "scarcity_m3": diet_scarcity["scarcity_m3_world_eq"],
        },
        "total_litres": total_litres,
        "total_scarcity_m3": total_scarcity,
        "household_share": (
            household_scarcity["scarcity_m3_world_eq"] / total_scarcity
            if total_scarcity > 0 else 0.0
        ),
        "diet_share": (
            diet_scarcity["scarcity_m3_world_eq"] / total_scarcity
            if total_scarcity > 0 else 0.0
        ),
    }


# ---------------------------------------------------------------------------
# Interventions
# ---------------------------------------------------------------------------

def rank_interventions(
    actions: list[dict[str, Any]] | None,
    region: str,
    month: str | int | None = None,
) -> dict[str, Any]:
    """Rank saving options by scarcity, and report where litres disagree.

    ``actions`` is a list of dicts with ``label``, ``litres_saved`` and
    ``blue_fraction``. The ranking by litres is what the app shows today;
    the ranking by scarcity is what actually helps a basin. For most users
    they are in opposite orders, and that is the useful output.
    """
    scored = []
    for action in actions or []:
        if not isinstance(action, dict):
            continue
        litres = _non_negative(action.get("litres_saved"))
        blue_fraction = min(1.0, _non_negative(action.get("blue_fraction")))
        blue = litres * blue_fraction
        scarcity = scarcity_footprint(blue, region, month)
        scored.append({
            "label": action.get("label", ""),
            "litres_saved": litres,
            "blue_litres_saved": blue,
            "blue_fraction": blue_fraction,
            "scarcity_m3_saved": scarcity["scarcity_m3_world_eq"],
        })

    by_litres = sorted(scored, key=lambda item: item["litres_saved"], reverse=True)
    by_scarcity = sorted(
        scored, key=lambda item: item["scarcity_m3_saved"], reverse=True
    )

    litre_rank = {item["label"]: index for index, item in enumerate(by_litres)}
    scarcity_rank = {item["label"]: index for index, item in enumerate(by_scarcity)}

    changes = []
    for label, before in litre_rank.items():
        after = scarcity_rank[label]
        if before == after:
            continue
        changes.append({
            "label": label,
            "litre_rank": before + 1,
            "scarcity_rank": after + 1,
            "movement": before - after,
            "direction": "up" if after < before else "down",
        })
    changes.sort(key=lambda item: abs(item["movement"]), reverse=True)

    return {
        "by_litres": by_litres,
        "by_scarcity": by_scarcity,
        "ranking_changes": changes,
        "inverted": bool(changes) and by_litres[0]["label"] != by_scarcity[0]["label"],
    }


def get_water_insights(assessment: dict[str, Any], diet_detail: dict[str, Any] | None = None) -> list[str]:
    """Plain-language guidance from a completed assessment."""
    insights = []

    if assessment.get("diet_share", 0.0) >= 0.6:
        insights.append(
            f"{assessment['diet_share'] * 100:.0f}% of your scarcity "
            "footprint is food. Shortening a shower is not the lever here, "
            "and the app's litre total makes it look as though it were."
        )
    elif assessment.get("household_share", 0.0) >= 0.6:
        insights.append(
            "Household use dominates your scarcity footprint, which is "
            "unusual and normally means either a garden or a pool - the two "
            "domestic uses that are genuinely consumptive."
        )

    household = assessment.get("household", {})
    withdrawal = household.get("withdrawal_litres", 0.0)
    consumption = household.get("consumption_litres", 0.0)
    if withdrawal > 0 and consumption / withdrawal < 0.2:
        insights.append(
            f"You withdraw {withdrawal:,.0f} litres at home and consume "
            f"{consumption:,.0f} of them. The rest returns to the basin "
            "treated. Counting the withdrawal as though it were consumed is "
            "why domestic water advice is usually aimed at the wrong place."
        )

    factor = assessment.get("factor", 1.0)
    if factor >= 10:
        insights.append(
            f"Your region carries a scarcity factor of {factor:.0f}× the "
            "world average. Blue water here is genuinely expensive in "
            "impact terms, and the same litre elsewhere would barely "
            "register."
        )
    elif factor <= 0.6:
        insights.append(
            f"Your region carries a scarcity factor of {factor:.1f}× the "
            "world average. Domestic water saving here is close to "
            "symbolic - which is worth knowing before spending effort on it."
        )

    if diet_detail:
        blue_heavy = sorted(
            diet_detail.get("lines", []),
            key=lambda line: line["blue_litres"],
            reverse=True,
        )
        if blue_heavy and blue_heavy[0]["blue_litres"] > 0:
            worst = blue_heavy[0]
            insights.append(
                f"**{worst['food']}** is your largest blue-water item at "
                f"{worst['blue_litres']:,.0f} litres. Blue water is the part "
                "that competes with other users, so this is where a dietary "
                "change actually reaches a stressed basin."
            )

        green_heavy = [
            line for line in diet_detail.get("lines", [])
            if line["total_litres"] > 0 and line["blue_share"] < 0.1
        ]
        if green_heavy:
            names = ", ".join(line["food"] for line in green_heavy[:3])
            insights.append(
                f"{names}: large totals, almost entirely green water. These "
                "look alarming in litres and are close to irrelevant for "
                "scarcity - the rain was falling there regardless."
            )

    insights.append(
        "Grey water is reported alongside, never inside, the consumptive "
        "total. It is a dilution requirement, not a withdrawal, and adding "
        "it in would count water that is still in the river."
    )

    return insights


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_water_scarcity_db() -> bool:
    """Create the table if it does not exist yet."""
    conn = None
    try:
        conn = _connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS water_scarcity_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                region TEXT NOT NULL,
                month TEXT,
                total_litres REAL NOT NULL,
                scarcity_m3 REAL NOT NULL,
                diet_share REAL NOT NULL,
                detail_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Unable to initialise water scarcity table: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def save_assessment(user_id: int, name: str, assessment: dict[str, Any]) -> int | None:
    """Persist an assessment. Returns the row id or None."""
    init_water_scarcity_db()
    conn = None
    try:
        conn = _connect()
        cursor = conn.execute(
            """
            INSERT INTO water_scarcity_assessments (
                user_id, name, region, month, total_litres, scarcity_m3,
                diet_share, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                (name or "Assessment").strip() or "Assessment",
                assessment.get("region", DEFAULT_REGION),
                str(assessment.get("month") or ""),
                _as_float(assessment.get("total_litres")),
                _as_float(assessment.get("total_scarcity_m3")),
                _as_float(assessment.get("diet_share")),
                json.dumps(assessment, default=str),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as exc:
        logger.error("Unable to save water scarcity assessment: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def get_saved_assessments(user_id: int, limit: int = 25) -> list[dict[str, Any]]:
    """A user's saved assessments, newest first."""
    init_water_scarcity_db()
    conn = None
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, name, region, month, total_litres, scarcity_m3,
                   diet_share, detail_json, created_at
            FROM water_scarcity_assessments
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT ?
            """,
            (user_id, int(limit)),
        ).fetchall()

        assessments = []
        for row in rows:
            record = dict(row)
            try:
                record["detail"] = json.loads(record.pop("detail_json") or "{}")
            except (TypeError, ValueError):
                record["detail"] = {}
            assessments.append(record)
        return assessments
    except sqlite3.Error as exc:
        logger.error("Unable to load water scarcity assessments: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def delete_saved_assessment(assessment_id: int) -> bool:
    """Delete a saved assessment."""
    init_water_scarcity_db()
    conn = None
    try:
        conn = _connect()
        cursor = conn.execute(
            "DELETE FROM water_scarcity_assessments WHERE id = ?",
            (assessment_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as exc:
        logger.error("Unable to delete water scarcity assessment: %s", exc)
        return False
    finally:
        if conn:
            conn.close()
