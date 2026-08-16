"""Weekly eco meal planning with carbon and water footprints.

Users compose meals from an ingredient catalogue, plan a full week, and get
lower-impact swap suggestions before they shop. Every meal is scored on two
axes:

* ``co2_kg``    - kg CO2e per kg of ingredient (Poore & Nemecek, 2018)
* ``water_l``   - litres of virtual water per kg (Mekonnen & Hoekstra, 2011)

Both figures are per kilogram of ingredient as purchased, so a meal is simply
the sum of ``grams / 1000 * factor`` over its ingredients.

The module is self-contained: its SQLite table is created lazily and no
shared files are modified.
"""

import os
import json
import sqlite3
import logging
from typing import Any

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

DAYS_OF_WEEK = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]

MEAL_SLOTS = ["Breakfast", "Lunch", "Dinner", "Snack"]

INGREDIENT_CATEGORIES = [
    "Protein", "Legume", "Grain", "Dairy", "Vegetable",
    "Fruit", "Oil", "Beverage",
]

# co2_kg  : kg CO2e per kg of ingredient
# water_l : litres of water per kg of ingredient
INGREDIENTS = {
    # --- Proteins -------------------------------------------------------
    "Beef": {"category": "Protein", "co2_kg": 60.0, "water_l": 15400},
    "Lamb": {"category": "Protein", "co2_kg": 24.5, "water_l": 10400},
    "Pork": {"category": "Protein", "co2_kg": 7.2, "water_l": 5990},
    "Chicken": {"category": "Protein", "co2_kg": 6.1, "water_l": 4330},
    "Farmed fish": {"category": "Protein", "co2_kg": 5.1, "water_l": 3700},
    "Eggs": {"category": "Protein", "co2_kg": 4.5, "water_l": 3270},
    "Prawns": {"category": "Protein", "co2_kg": 11.8, "water_l": 4100},
    "Tofu": {"category": "Protein", "co2_kg": 3.0, "water_l": 2500},
    "Tempeh": {"category": "Protein", "co2_kg": 2.4, "water_l": 2300},

    # --- Legumes --------------------------------------------------------
    "Lentils": {"category": "Legume", "co2_kg": 0.9, "water_l": 5870},
    "Chickpeas": {"category": "Legume", "co2_kg": 0.8, "water_l": 4180},
    "Black beans": {"category": "Legume", "co2_kg": 0.8, "water_l": 5050},
    "Peas": {"category": "Legume", "co2_kg": 0.9, "water_l": 1980},

    # --- Grains ---------------------------------------------------------
    "Rice": {"category": "Grain", "co2_kg": 4.0, "water_l": 2500},
    "Wheat bread": {"category": "Grain", "co2_kg": 1.6, "water_l": 1600},
    "Pasta": {"category": "Grain", "co2_kg": 1.4, "water_l": 1850},
    "Oats": {"category": "Grain", "co2_kg": 1.6, "water_l": 1790},
    "Maize / corn": {"category": "Grain", "co2_kg": 1.1, "water_l": 1220},
    "Potatoes": {"category": "Grain", "co2_kg": 0.5, "water_l": 290},

    # --- Dairy ----------------------------------------------------------
    "Cheese": {"category": "Dairy", "co2_kg": 21.0, "water_l": 5060},
    "Butter": {"category": "Dairy", "co2_kg": 12.1, "water_l": 5550},
    "Cow milk": {"category": "Dairy", "co2_kg": 3.2, "water_l": 1020},
    "Yoghurt": {"category": "Dairy", "co2_kg": 2.2, "water_l": 940},
    "Oat milk": {"category": "Dairy", "co2_kg": 0.9, "water_l": 480},
    "Soy milk": {"category": "Dairy", "co2_kg": 1.0, "water_l": 300},

    # --- Vegetables -----------------------------------------------------
    "Tomatoes": {"category": "Vegetable", "co2_kg": 2.1, "water_l": 210},
    "Onions": {"category": "Vegetable", "co2_kg": 0.5, "water_l": 270},
    "Broccoli": {"category": "Vegetable", "co2_kg": 0.6, "water_l": 285},
    "Spinach": {"category": "Vegetable", "co2_kg": 0.5, "water_l": 290},
    "Carrots": {"category": "Vegetable", "co2_kg": 0.4, "water_l": 195},
    "Mushrooms": {"category": "Vegetable", "co2_kg": 3.3, "water_l": 320},

    # --- Fruit ----------------------------------------------------------
    "Apples": {"category": "Fruit", "co2_kg": 0.4, "water_l": 820},
    "Bananas": {"category": "Fruit", "co2_kg": 0.9, "water_l": 790},
    "Berries": {"category": "Fruit", "co2_kg": 1.5, "water_l": 840},
    "Citrus": {"category": "Fruit", "co2_kg": 0.4, "water_l": 560},

    # --- Oils -----------------------------------------------------------
    "Olive oil": {"category": "Oil", "co2_kg": 6.0, "water_l": 14430},
    "Sunflower oil": {"category": "Oil", "co2_kg": 3.6, "water_l": 6790},
    "Palm oil": {"category": "Oil", "co2_kg": 7.6, "water_l": 5000},

    # --- Beverages ------------------------------------------------------
    "Coffee beans": {"category": "Beverage", "co2_kg": 28.5, "water_l": 18900},
    "Tea leaves": {"category": "Beverage", "co2_kg": 7.0, "water_l": 8860},
    "Chocolate": {"category": "Beverage", "co2_kg": 46.7, "water_l": 17200},
}

# Impact tier thresholds in kg CO2e per kg of ingredient.
TIER_THRESHOLDS = [
    (2.0, "low"),
    (6.0, "moderate"),
    (20.0, "high"),
]
HIGHEST_TIER = "very high"

TIER_ICONS = {
    "low": "🟢",
    "moderate": "🟡",
    "high": "🟠",
    "very high": "🔴",
}

# A meal above this many kg CO2e is worth suggesting swaps for.
SWAP_TRIGGER_KG = 1.0

# Average daily food footprints in kg CO2e for each diet type in config.py,
# used to give a plan context rather than an absolute verdict.
DIET_DAILY_BASELINE_KG = {
    "Vegan": 2.9,
    "Vegetarian": 3.8,
    "Omnivore": 5.6,
    "Non-Vegetarian": 6.3,
    "Heavy Meat": 7.2,
}

# Weekly kg CO2e used to anchor the 0-100 plan score. A week at or below the
# vegan baseline scores 100; a week at or above the heavy-meat baseline
# scores 0.
SCORE_BEST_WEEKLY_KG = DIET_DAILY_BASELINE_KG["Vegan"] * 7
SCORE_WORST_WEEKLY_KG = DIET_DAILY_BASELINE_KG["Heavy Meat"] * 7

GRADE_BANDS = [
    (90, "A"),
    (75, "B"),
    (60, "C"),
    (40, "D"),
]
LOWEST_GRADE = "E"


def list_ingredients(category: str | None = None) -> list[dict[str, Any]]:
    """Return the ingredient catalogue, optionally filtered by category."""
    items = [
        dict(info, name=name)
        for name, info in INGREDIENTS.items()
        if category is None or info["category"] == category
    ]
    return sorted(items, key=lambda item: item["co2_kg"])


def get_ingredient(name: str) -> dict[str, Any] | None:
    """Return one ingredient's factors, or None if it is not in the catalogue."""
    info = INGREDIENTS.get(name)
    return dict(info, name=name) if info else None


def impact_tier(co2_per_kg: float) -> str:
    """Classify an ingredient's per-kg carbon intensity into a tier."""
    try:
        value = float(co2_per_kg)
    except (TypeError, ValueError):
        return "low"
    for threshold, tier in TIER_THRESHOLDS:
        if value < threshold:
            return tier
    return HIGHEST_TIER


def _clean_grams(grams: float) -> float:
    """Coerce a portion size into a sane, non-negative number of grams."""
    try:
        value = float(grams)
    except (TypeError, ValueError):
        return 0.0
    if value != value or value in (float("inf"), float("-inf")):
        return 0.0
    return max(0.0, min(value, 5000.0))


def build_meal(name: str, items: list[tuple[str, float]] | None, slot: str = "Dinner") -> dict[str, Any]:
    """Build a meal from ``items`` - a list of ``(ingredient_name, grams)``.

    Unknown ingredients are skipped so a stale saved plan never crashes the
    calculator.
    """
    contributions = []
    total_co2 = 0.0
    total_water = 0.0
    total_grams = 0.0

    for entry in items or []:
        try:
            ingredient_name, grams = entry
        except (TypeError, ValueError):
            continue

        info = INGREDIENTS.get(ingredient_name)
        if not info:
            continue

        grams = _clean_grams(grams)
        if grams <= 0:
            continue

        kg = grams / 1000.0
        co2 = kg * info["co2_kg"]
        water = kg * info["water_l"]

        total_co2 += co2
        total_water += water
        total_grams += grams

        contributions.append(
            {
                "ingredient": ingredient_name,
                "category": info["category"],
                "grams": round(grams, 1),
                "co2_kg": round(co2, 3),
                "water_l": round(water, 1),
                "tier": impact_tier(info["co2_kg"]),
            }
        )

    for item in contributions:
        item["co2_share_pct"] = (
            round(item["co2_kg"] / total_co2 * 100, 1) if total_co2 > 0 else 0.0
        )

    contributions.sort(key=lambda item: item["co2_kg"], reverse=True)

    return {
        "name": name or "Untitled meal",
        "slot": slot if slot in MEAL_SLOTS else "Dinner",
        "items": [(item["ingredient"], item["grams"]) for item in contributions],
        "contributions": contributions,
        "co2_kg": round(total_co2, 3),
        "water_l": round(total_water, 1),
        "grams": round(total_grams, 1),
        "tier": impact_tier(total_co2 / (total_grams / 1000.0)) if total_grams else "low",
    }


def plan_week(meals_by_day: dict[str, list[dict[str, Any]]] | None) -> dict[str, Any]:
    """Aggregate a week of meals.

    ``meals_by_day`` maps day names to lists of meals built by ``build_meal``.
    """
    meals_by_day = meals_by_day or {}

    daily = {}
    ingredient_totals = {}
    total_co2 = 0.0
    total_water = 0.0
    meal_count = 0

    for day in DAYS_OF_WEEK:
        meals = meals_by_day.get(day, []) or []
        day_co2 = 0.0
        day_water = 0.0

        for meal in meals:
            day_co2 += meal.get("co2_kg", 0.0)
            day_water += meal.get("water_l", 0.0)
            meal_count += 1

            for item in meal.get("contributions", []):
                bucket = ingredient_totals.setdefault(
                    item["ingredient"],
                    {
                        "ingredient": item["ingredient"],
                        "category": item["category"],
                        "grams": 0.0,
                        "co2_kg": 0.0,
                        "water_l": 0.0,
                    },
                )
                bucket["grams"] += item["grams"]
                bucket["co2_kg"] += item["co2_kg"]
                bucket["water_l"] += item["water_l"]

        daily[day] = {
            "day": day,
            "meals": len(meals),
            "co2_kg": round(day_co2, 3),
            "water_l": round(day_water, 1),
        }
        total_co2 += day_co2
        total_water += day_water

    for bucket in ingredient_totals.values():
        bucket["grams"] = round(bucket["grams"], 1)
        bucket["co2_kg"] = round(bucket["co2_kg"], 3)
        bucket["water_l"] = round(bucket["water_l"], 1)

    top_ingredients = sorted(
        ingredient_totals.values(), key=lambda item: item["co2_kg"], reverse=True
    )

    days_with_meals = [d for d in daily.values() if d["meals"] > 0]
    worst_day = max(days_with_meals, key=lambda d: d["co2_kg"], default=None)

    by_category = {}
    for bucket in ingredient_totals.values():
        by_category.setdefault(bucket["category"], 0.0)
        by_category[bucket["category"]] += bucket["co2_kg"]

    return {
        "daily": daily,
        "total_co2_kg": round(total_co2, 2),
        "total_water_l": round(total_water, 1),
        "avg_daily_co2_kg": round(total_co2 / 7, 3),
        "meal_count": meal_count,
        "avg_meal_co2_kg": round(total_co2 / meal_count, 3) if meal_count else 0.0,
        "worst_day": worst_day["day"] if worst_day else None,
        "top_ingredients": top_ingredients,
        "by_category": {k: round(v, 3) for k, v in sorted(by_category.items())},
    }


def suggest_swaps(meal: dict[str, Any], max_suggestions: int = 3) -> list[dict[str, Any]]:
    """Suggest lower-impact, same-category replacements for a meal.

    A suggestion is only returned when the alternative is genuinely lower
    impact, so applying every suggestion can never increase the footprint.
    """
    suggestions = []

    for item in meal.get("contributions", []):
        original = INGREDIENTS.get(item["ingredient"])
        if not original:
            continue

        alternatives = [
            candidate
            for candidate in list_ingredients(original["category"])
            if candidate["co2_kg"] < original["co2_kg"]
        ]
        if not alternatives:
            continue

        best = min(alternatives, key=lambda candidate: candidate["co2_kg"])
        kg = item["grams"] / 1000.0
        co2_saved = (original["co2_kg"] - best["co2_kg"]) * kg
        water_saved = (original["water_l"] - best["water_l"]) * kg

        if co2_saved <= 0:
            continue

        suggestions.append(
            {
                "from": item["ingredient"],
                "to": best["name"],
                "category": original["category"],
                "grams": item["grams"],
                "co2_saved_kg": round(co2_saved, 3),
                "water_saved_l": round(water_saved, 1),
                "from_tier": impact_tier(original["co2_kg"]),
                "to_tier": impact_tier(best["co2_kg"]),
            }
        )

    suggestions.sort(key=lambda item: item["co2_saved_kg"], reverse=True)
    return suggestions[: max(0, int(max_suggestions))]


def needs_swaps(meal: dict[str, Any]) -> bool:
    """True when a meal is heavy enough to be worth showing swaps for."""
    return meal.get("co2_kg", 0.0) >= SWAP_TRIGGER_KG and bool(suggest_swaps(meal, 1))


def heaviest_meals(meals_by_day: dict[str, list[dict[str, Any]]] | None, limit: int = 3) -> list[dict[str, Any]]:
    """Return the week's heaviest meals, tagged with the day they fall on."""
    tagged = []
    for day in DAYS_OF_WEEK:
        for meal in (meals_by_day or {}).get(day, []) or []:
            tagged.append(dict(meal, day=day))
    tagged.sort(key=lambda meal: meal.get("co2_kg", 0.0), reverse=True)
    return tagged[: max(0, int(limit))]


def apply_swaps(meal: dict[str, Any], swaps: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Return a new meal with the given swaps applied."""
    replacements = {swap["from"]: swap["to"] for swap in swaps or []}
    items = [
        (replacements.get(ingredient, ingredient), grams)
        for ingredient, grams in meal.get("items", [])
    ]
    return build_meal(meal.get("name"), items, meal.get("slot"))


def score_plan(weekly: dict[str, Any]) -> dict[str, Any]:
    """Score a weekly plan from 0 to 100 and assign a letter grade."""
    total = max(0.0, float(weekly.get("total_co2_kg", 0.0)))

    if weekly.get("meal_count", 0) == 0:
        return {"score": 0, "grade": LOWEST_GRADE, "label": "No meals planned yet"}

    span = SCORE_WORST_WEEKLY_KG - SCORE_BEST_WEEKLY_KG
    raw = (SCORE_WORST_WEEKLY_KG - total) / span if span else 0.0
    score = int(round(max(0.0, min(1.0, raw)) * 100))

    grade = LOWEST_GRADE
    for threshold, band in GRADE_BANDS:
        if score >= threshold:
            grade = band
            break

    labels = {
        "A": "Outstanding - a genuinely low-carbon week",
        "B": "Strong - a few swaps from excellent",
        "C": "Middle of the road - real room to improve",
        "D": "Heavy - a couple of meals dominate this week",
        "E": "Very heavy - start with your worst day",
    }

    return {"score": score, "grade": grade, "label": labels[grade]}


def compare_to_baseline(weekly: dict[str, Any], diet_type: str = "Omnivore") -> dict[str, Any]:
    """Compare a weekly plan against the average week for a diet type."""
    baseline_daily = DIET_DAILY_BASELINE_KG.get(
        diet_type, DIET_DAILY_BASELINE_KG["Omnivore"]
    )
    baseline_weekly = baseline_daily * 7
    total = max(0.0, float(weekly.get("total_co2_kg", 0.0)))
    difference = total - baseline_weekly

    return {
        "diet_type": diet_type if diet_type in DIET_DAILY_BASELINE_KG else "Omnivore",
        "baseline_weekly_kg": round(baseline_weekly, 2),
        "plan_weekly_kg": round(total, 2),
        "difference_kg": round(difference, 2),
        "difference_pct": (
            round(difference / baseline_weekly * 100, 1) if baseline_weekly else 0.0
        ),
        "better_than_baseline": difference < 0,
    }


def generate_shopping_list(weekly: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Aggregate the week's ingredients into a shopping list by category."""
    grouped = {}
    for bucket in weekly.get("top_ingredients", []):
        grouped.setdefault(bucket["category"], []).append(
            {
                "ingredient": bucket["ingredient"],
                "grams": bucket["grams"],
                "co2_kg": bucket["co2_kg"],
                "tier": impact_tier(INGREDIENTS[bucket["ingredient"]]["co2_kg"])
                if bucket["ingredient"] in INGREDIENTS
                else "low",
            }
        )

    for items in grouped.values():
        items.sort(key=lambda item: item["ingredient"])

    return {category: grouped[category] for category in sorted(grouped)}


def plan_insights(weekly: dict[str, Any], limit: int = 4) -> list[str]:
    """Generate plain-language observations about a weekly plan."""
    insights = []

    if weekly.get("meal_count", 0) == 0:
        return ["Add a few meals to see how your week stacks up."]

    top = weekly.get("top_ingredients", [])
    if top and weekly["total_co2_kg"] > 0:
        leader = top[0]
        share = leader["co2_kg"] / weekly["total_co2_kg"] * 100
        insights.append(
            f"{leader['ingredient']} alone is {share:.0f}% of your week's food carbon."
        )

    worst = weekly.get("worst_day")
    if worst:
        day = weekly["daily"][worst]
        insights.append(
            f"{worst} is your heaviest day at {day['co2_kg']:.1f} kg CO₂ "
            f"- a good place to try one swap."
        )

    by_category = weekly.get("by_category", {})
    if by_category:
        heaviest = max(by_category, key=by_category.get)
        insights.append(
            f"{heaviest} ingredients drive {by_category[heaviest]:.1f} kg CO₂ this week."
        )

    water_bathtubs = weekly.get("total_water_l", 0) / 150
    if water_bathtubs >= 1:
        insights.append(
            f"Your week's meals carry about {water_bathtubs:.0f} bathtubs of virtual water."
        )

    return insights[: max(0, int(limit))]


def _get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_meal_planner_db() -> None:
    """Create the meal plan table if it does not exist yet."""
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meal_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_name TEXT NOT NULL,
                total_co2_kg REAL NOT NULL,
                total_water_l REAL NOT NULL,
                score INTEGER NOT NULL,
                grade TEXT NOT NULL,
                plan_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Meal planner init error: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def serialize_plan(meals_by_day: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    """Reduce a week of meals to the minimum needed to rebuild it."""
    return {
        day: [
            {
                "name": meal.get("name"),
                "slot": meal.get("slot"),
                "items": [list(item) for item in meal.get("items", [])],
            }
            for meal in meals_by_day.get(day, []) or []
        ]
        for day in DAYS_OF_WEEK
    }


def deserialize_plan(raw: dict[str, list[dict[str, Any]]] | None) -> dict[str, list[dict[str, Any]]]:
    """Rebuild a week of meals from its serialized form."""
    raw = raw or {}
    return {
        day: [
            build_meal(
                meal.get("name"),
                [tuple(item) for item in meal.get("items", [])],
                meal.get("slot"),
            )
            for meal in raw.get(day, []) or []
        ]
        for day in DAYS_OF_WEEK
    }


def save_meal_plan(user_id: int, plan_name: str, meals_by_day: dict[str, list[dict[str, Any]]]) -> int | None:
    """Persist a weekly plan. Returns the new row id or None on failure."""
    init_meal_planner_db()
    conn = None
    try:
        weekly = plan_week(meals_by_day)
        scored = score_plan(weekly)
        conn = _get_conn()
        cursor = conn.execute(
            """
            INSERT INTO meal_plans (
                user_id, plan_name, total_co2_kg, total_water_l,
                score, grade, plan_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                plan_name or "My week",
                weekly["total_co2_kg"],
                weekly["total_water_l"],
                scored["score"],
                scored["grade"],
                json.dumps(serialize_plan(meals_by_day)),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as exc:
        logger.error("Unable to save meal plan: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def get_meal_plans(user_id: int, limit: int = 25) -> list[dict[str, Any]]:
    """Return a user's saved plans, newest first."""
    init_meal_planner_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, plan_name, total_co2_kg, total_water_l, score, grade,
                   plan_json, created_at
            FROM meal_plans
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
                record["plan"] = json.loads(record.pop("plan_json"))
            except (TypeError, ValueError):
                record["plan"] = {}
            plans.append(record)
        return plans
    except sqlite3.Error as exc:
        logger.error("Unable to load meal plans: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def get_plan_history(user_id: int, limit: int = 12) -> dict[str, Any]:
    """Return a chronological carbon series across a user's saved plans."""
    plans = get_meal_plans(user_id, limit=limit)
    series = [
        {
            "date": plan.get("created_at"),
            "name": plan.get("plan_name"),
            "total_co2_kg": plan.get("total_co2_kg", 0.0),
            "score": plan.get("score", 0),
        }
        for plan in reversed(plans)
    ]

    change_kg = 0.0
    if len(series) >= 2:
        change_kg = round(series[-1]["total_co2_kg"] - series[0]["total_co2_kg"], 2)

    return {
        "series": series,
        "entries": len(series),
        "change_kg": change_kg,
        "improving": change_kg < 0,
        "best_score": max((item["score"] for item in series), default=0),
    }


def delete_meal_plan(plan_id: int) -> bool:
    """Delete a saved plan. Returns True when a row was removed."""
    init_meal_planner_db()
    conn = None
    try:
        conn = _get_conn()
        cursor = conn.execute("DELETE FROM meal_plans WHERE id = ?", (plan_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as exc:
        logger.error("Unable to delete meal plan: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def empty_week() -> dict[str, list[dict[str, Any]]]:
    """Return an empty week structure."""
    return {day: [] for day in DAYS_OF_WEEK}
