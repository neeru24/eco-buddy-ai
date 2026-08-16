"""Carbon opportunity cost of land: what the land would hold if it were not farmed.

Every food footprint in this app counts the emissions released to *produce* the
food. None of them count the carbon the land would be holding if it were not
being farmed. That missing term is the carbon opportunity cost of land, and for
ruminant meat it is of the same order as the production emissions already
reported.

What it is
----------
A kilogram of beef carries roughly 100 kg CO2e of production emissions and
occupies a few hundred square metres of land for a year. Released, that land
regrows towards its potential natural vegetation and accumulates carbon for
decades. Ignoring that is a choice, and it is a choice that always favours the
land-hungry option.

Two things this module refuses to hide
--------------------------------------
**Amortisation.** Regrowth is not instant, and the annual figure depends
entirely on the period the recovered stock is amortised over. Over 20 years it
is large; over 100 years it is a fraction of that. There is no single correct
number, so the period is a visible parameter and the result is reported across a
range rather than at a point.

**Land is not interchangeable.** Rough upland grazing that would regrow to
grassland holds a small fraction of the carbon that cleared tropical forest
would. Treating "a hectare" as one thing would produce a headline number with no
decision content, so the recoverable stock varies by biome and by whether the
land is cropland or pasture.

What the correction actually does to the comparison
---------------------------------------------------
Not what one might expect. Adding a term proportional to land area *narrows* the
ratio between beef and peas, because the difference in land use between them,
while large, is smaller than the difference in production emissions. What it
widens - roughly doubling it for ruminants - is the **absolute** gap in kg. That
matters because the app compares actions in kg: dietary change is competing with
insulation and flights on an absolute scale, and it has been competing with a
third of its weight missing.

The stock and the flow
----------------------
Releasing land produces a one-off stock change that saturates as the vegetation
matures. It is not an annual flow that continues forever. Conflating the two is
the standard error in this area, and this module reports the accumulation
schedule alongside the annualised figure so the saturation is visible rather
than asserted.

Where this connects to code already merged
------------------------------------------
*   ``meal_planner.py`` and ``food_scanner.py`` score meals on production-only
    factors.
*   ``emission_factors.py`` carries no land column, so no downstream module
    *can* account for this even if it wanted to.
*   ``lifestyle_optimizer.py`` ranks actions in kg, which is exactly the scale
    this correction changes.
*   ``local_biodiversity.py`` already reasons about land and habitat; this is
    the carbon side of the same coin.

Self-contained: standard library only, SQLite tables created lazily, no shared
files modified.
"""

import os
import json
import math
import sqlite3
import logging
from typing import Any

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

# Carbon to carbon dioxide, by molecular weight.
CO2_PER_C = 44.0 / 12.0

# Tonnes of carbon per hectare into kilograms of CO2 per square metre:
# 1 tC/ha = 1000 kgC / 10000 m2 = 0.1 kgC/m2.
TC_HA_TO_KGCO2_M2 = 0.1 * CO2_PER_C

DEFAULT_AMORTISATION_YEARS = 30
AMORTISATION_RANGE = (20, 30, 50, 100)

# ---------------------------------------------------------------------------
# Biomes
#
# ``potential`` is the ecosystem carbon (vegetation plus soil) the land would
# hold as mature natural vegetation. ``cropland`` and ``pasture`` are what it
# holds while farmed. The difference between them is what is actually
# recoverable, and it is the number that varies by an order of magnitude
# between rows - which is the reason this is a table rather than a constant.
#
# ``tau`` is the time constant of regrowth in years. Recovery is fast in the
# tropics and slow in boreal forest, and using one rate everywhere would make
# the amortisation choice look far more consequential in some places and far
# less in others than it is.
# ---------------------------------------------------------------------------
BIOMES = {
    "tropical_moist_forest": {
        "label": "Tropical moist forest",
        "potential": 250.0, "cropland": 65.0, "pasture": 80.0, "tau": 30.0,
        "note": "The largest opportunity cost of any land in this table and "
                "the fastest to recover it. Soy and pasture frontier land "
                "sits here.",
    },
    "tropical_dry_forest": {
        "label": "Tropical dry forest and woodland",
        "potential": 130.0, "cropland": 50.0, "pasture": 60.0, "tau": 35.0,
        "note": "Lower stock than moist forest and still several times the "
                "recoverable carbon of temperate pasture.",
    },
    "temperate_forest": {
        "label": "Temperate forest",
        "potential": 180.0, "cropland": 80.0, "pasture": 95.0, "tau": 60.0,
        "note": "Most cropland in Europe and the eastern United States would "
                "return to this. Recovery takes roughly twice as long as in "
                "the tropics.",
    },
    "boreal_forest": {
        "label": "Boreal forest",
        "potential": 160.0, "cropland": 75.0, "pasture": 85.0, "tau": 100.0,
        "note": "Much of the stock is in soil rather than trees, and recovery "
                "is slow enough that the amortisation period dominates the "
                "answer.",
    },
    "temperate_grassland": {
        "label": "Temperate grassland",
        "potential": 110.0, "cropland": 70.0, "pasture": 90.0, "tau": 40.0,
        "note": "Grassland that was always grassland. Converting pasture back "
                "recovers relatively little, because it was never forest.",
    },
    "upland_rough_grazing": {
        "label": "Upland rough grazing",
        "potential": 95.0, "cropland": 65.0, "pasture": 85.0, "tau": 50.0,
        "note": "The case that breaks a single global figure. Rough upland "
                "grazing recovers about a tenth of what tropical pasture "
                "does, so the same kilogram of lamb has a completely "
                "different opportunity cost depending on where it was reared.",
    },
    "mediterranean_shrubland": {
        "label": "Mediterranean shrubland",
        "potential": 100.0, "cropland": 55.0, "pasture": 65.0, "tau": 45.0,
        "note": "Moderate stock, and frequently the land under olive, vine "
                "and tree-nut cultivation.",
    },
    "savanna": {
        "label": "Savanna and tropical grassland",
        "potential": 90.0, "cropland": 45.0, "pasture": 55.0, "tau": 30.0,
        "note": "Fire-maintained and carbon-poor above ground, with most of "
                "the stock below it.",
    },
}

DEFAULT_BIOME = "temperate_forest"
LAND_TYPES = ("cropland", "pasture")

# ---------------------------------------------------------------------------
# Foods
#
# ``land_m2_year`` is land occupation per kilogram of food as purchased and
# ``production_kg`` is cradle-to-retail emissions excluding any land carbon.
# ``protein_g`` is zero where the food is not a meaningful protein source; the
# per-protein comparison skips those rows rather than dividing by something
# close to nothing and producing a spectacular number.
# ---------------------------------------------------------------------------
FOODS = {
    "beef_beef_herd": {
        "label": "Beef (beef herd)",
        "land_m2_year": 326.0, "production_kg": 99.5, "protein_g": 200.0,
        "land_type": "pasture", "typical_biome": "tropical_dry_forest",
        "note": "The largest land occupation of any common food. The land "
                "figure is a global average dominated by extensive grazing, "
                "so it is defaulted to dry forest and woodland rather than to "
                "the moist forest frontier - pairing an average area with the "
                "most carbon-dense land available would roughly triple the "
                "answer for no defensible reason.",
    },
    "beef_dairy_herd": {
        "label": "Beef (from a dairy herd)",
        "land_m2_year": 43.2, "production_kg": 33.3, "protein_g": 200.0,
        "land_type": "pasture", "typical_biome": "temperate_grassland",
        "note": "Shares its land with milk production, so the land is "
                "allocated between the two and the figure is far lower than "
                "for a dedicated beef herd.",
    },
    "lamb": {
        "label": "Lamb and mutton",
        "land_m2_year": 369.0, "production_kg": 39.7, "protein_g": 190.0,
        "land_type": "pasture", "typical_biome": "upland_rough_grazing",
        "note": "More land than beef and much less recoverable carbon under "
                "it, because upland grazing was rarely high-carbon forest. "
                "The default biome matters more here than anywhere else.",
    },
    "pork": {
        "label": "Pork",
        "land_m2_year": 17.4, "production_kg": 12.3, "protein_g": 200.0,
        "land_type": "cropland", "typical_biome": "temperate_forest",
        "note": "Grain-fed, so the land is cropland rather than pasture.",
    },
    "poultry": {
        "label": "Poultry",
        "land_m2_year": 12.2, "production_kg": 9.9, "protein_g": 210.0,
        "land_type": "cropland", "typical_biome": "temperate_forest",
        "note": "The most feed-efficient common meat, and correspondingly "
                "the least land per kilogram.",
    },
    "eggs": {
        "label": "Eggs",
        "land_m2_year": 6.3, "production_kg": 4.7, "protein_g": 125.0,
        "land_type": "cropland", "typical_biome": "temperate_forest",
        "note": "",
    },
    "milk": {
        "label": "Milk",
        "land_m2_year": 8.9, "production_kg": 3.2, "protein_g": 33.0,
        "land_type": "pasture", "typical_biome": "temperate_grassland",
        "note": "Mostly water by mass, which flatters it per kilogram and "
                "not per unit of protein.",
    },
    "cheese": {
        "label": "Cheese",
        "land_m2_year": 87.8, "production_kg": 23.9, "protein_g": 250.0,
        "land_type": "pasture", "typical_biome": "temperate_grassland",
        "note": "Roughly ten kilograms of milk per kilogram of cheese, and "
                "the land follows.",
    },
    "farmed_fish": {
        "label": "Farmed fish",
        "land_m2_year": 3.7, "production_kg": 13.6, "protein_g": 200.0,
        "land_type": "cropland", "typical_biome": "tropical_moist_forest",
        "note": "High production emissions and very little land, which is the "
                "combination that shows the two terms are independent.",
    },
    "tofu": {
        "label": "Tofu",
        "land_m2_year": 3.5, "production_kg": 3.2, "protein_g": 80.0,
        "land_type": "cropland", "typical_biome": "savanna",
        "note": "Soy for tofu is grown mostly on cerrado rather than on "
                "cleared moist forest, which is a smaller opportunity cost "
                "per square metre and worth defaulting honestly.",
    },
    "peas": {
        "label": "Peas (dry)",
        "land_m2_year": 7.5, "production_kg": 0.98, "protein_g": 220.0,
        "land_type": "cropland", "typical_biome": "temperate_forest",
        "note": "The standard comparison against beef, and the one where the "
                "ratio behaves counter-intuitively once land is counted.",
    },
    "other_pulses": {
        "label": "Other pulses",
        "land_m2_year": 15.6, "production_kg": 1.8, "protein_g": 240.0,
        "land_type": "cropland", "typical_biome": "tropical_dry_forest",
        "note": "",
    },
    "nuts": {
        "label": "Nuts",
        "land_m2_year": 13.0, "production_kg": 0.43, "protein_g": 200.0,
        "land_type": "cropland", "typical_biome": "mediterranean_shrubland",
        "note": "Very low production emissions and a land footprint that is "
                "not negligible, so this is a food whose ranking moves.",
    },
    "rice": {
        "label": "Rice",
        "land_m2_year": 2.8, "production_kg": 4.5, "protein_g": 70.0,
        "land_type": "cropland", "typical_biome": "tropical_moist_forest",
        "note": "Methane from flooded paddies dominates, and the land term "
                "barely moves it.",
    },
    "wheat_bread": {
        "label": "Bread and wheat products",
        "land_m2_year": 3.9, "production_kg": 1.6, "protein_g": 90.0,
        "land_type": "cropland", "typical_biome": "temperate_forest",
        "note": "",
    },
    "potatoes": {
        "label": "Potatoes",
        "land_m2_year": 0.9, "production_kg": 0.46, "protein_g": 20.0,
        "land_type": "cropland", "typical_biome": "temperate_forest",
        "note": "",
    },
    "root_vegetables": {
        "label": "Root vegetables",
        "land_m2_year": 0.3, "production_kg": 0.43, "protein_g": 12.0,
        "land_type": "cropland", "typical_biome": "temperate_forest",
        "note": "",
    },
    "tomatoes": {
        "label": "Tomatoes",
        "land_m2_year": 0.8, "production_kg": 2.1, "protein_g": 9.0,
        "land_type": "cropland", "typical_biome": "mediterranean_shrubland",
        "note": "Heated greenhouse production, so the emissions are energy "
                "rather than land.",
    },
    "bananas": {
        "label": "Bananas",
        "land_m2_year": 1.9, "production_kg": 0.86, "protein_g": 11.0,
        "land_type": "cropland", "typical_biome": "tropical_moist_forest",
        "note": "Tropical land, which is expensive per square metre in "
                "opportunity terms, but very little of it.",
    },
    "coffee": {
        "label": "Coffee (roasted)",
        "land_m2_year": 21.6, "production_kg": 28.5, "protein_g": 0.0,
        "land_type": "cropland", "typical_biome": "tropical_moist_forest",
        "note": "Tropical land and high processing emissions, on a food eaten "
                "in gram quantities.",
    },
    "dark_chocolate": {
        "label": "Dark chocolate",
        "land_m2_year": 68.6, "production_kg": 46.7, "protein_g": 0.0,
        "land_type": "cropland", "typical_biome": "tropical_moist_forest",
        "note": "The highest land occupation outside ruminant meat, on the "
                "most carbon-dense land in the table.",
    },
}


class LandCostError(ValueError):
    """Raised for an unknown food, biome or land type, or an unusable input."""


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if result != result or result in (float("inf"), float("-inf")):
        return default
    return result


def _non_negative(value: Any, default: float = 0.0) -> float:
    result = _as_float(value, default)
    return result if result > 0 else 0.0


def list_foods() -> list[str]:
    return list(FOODS)


def get_food(key: str) -> dict[str, Any]:
    if key not in FOODS:
        raise LandCostError(
            f"Unknown food '{key}'. Known foods: {', '.join(sorted(FOODS))}."
        )
    return dict(FOODS[key])


def list_biomes() -> list[str]:
    return list(BIOMES)


def get_biome(key: str) -> dict[str, Any]:
    if key not in BIOMES:
        raise LandCostError(
            f"Unknown biome '{key}'. There is no global average worth using "
            f"here - recoverable carbon varies by an order of magnitude "
            f"between these rows. Known biomes: {', '.join(sorted(BIOMES))}."
        )
    return dict(BIOMES[key])


def list_land_types() -> list[str]:
    return list(LAND_TYPES)


# ---------------------------------------------------------------------------
# The land carbon model
# ---------------------------------------------------------------------------

def recoverable_stock(biome: str, land_type: str = "cropland") -> float:
    """Recoverable carbon in tonnes of carbon per hectare.

    The difference between what the land would hold as mature natural
    vegetation and what it holds while farmed. Floored at zero: farmland that
    already holds more carbon than its potential vegetation would is not a
    carbon debt, and reporting it as a negative opportunity cost would turn the
    module into an argument for keeping the land in production.
    """
    entry = get_biome(biome)
    if land_type not in LAND_TYPES:
        raise LandCostError(
            f"Unknown land type '{land_type}'. Expected one of "
            f"{', '.join(LAND_TYPES)}."
        )
    return max(0.0, entry["potential"] - entry[land_type])


def recoverable_per_m2(biome: str, land_type: str = "cropland") -> float:
    """Recoverable carbon as kg CO2e per square metre."""
    return recoverable_stock(biome, land_type) * TC_HA_TO_KGCO2_M2


def regrowth_fraction(biome: str, years: float) -> float:
    """Share of the recoverable stock accumulated after a number of years.

    Saturating exponential rather than linear, because regrowth is fast while
    the vegetation is young and slows as it matures. A linear model would
    overstate the first decade and understate the last, and the first decade is
    where most amortisation periods do their work.
    """
    entry = get_biome(biome)
    horizon = _non_negative(years)
    if horizon <= 0:
        return 0.0
    return 1.0 - math.exp(-horizon / entry["tau"])


def annualised_land_carbon(
    biome: str,
    land_type: str = "cropland",
    years: float = DEFAULT_AMORTISATION_YEARS,
) -> float:
    """kg CO2e per square metre per year, at a stated amortisation period.

    This is the number the amortisation debate is about. It falls as the period
    lengthens - the stock accumulated grows more slowly than the period does -
    which is why quoting it without the period attached is meaningless.
    """
    horizon = _non_negative(years)
    if horizon <= 0:
        raise LandCostError(
            "An amortisation period of zero years has no meaning: the whole "
            "question is over what period the recovered stock is spread."
        )
    return recoverable_per_m2(biome, land_type) * regrowth_fraction(biome, horizon) / horizon


def opportunity_cost(
    food: str,
    kg: float = 1.0,
    biome: str | None = None,
    land_type: str | None = None,
    years: float = DEFAULT_AMORTISATION_YEARS,
) -> dict[str, Any]:
    """The carbon opportunity cost of the land used to grow a quantity of food."""
    entry = get_food(food)
    quantity = _non_negative(kg)
    biome_key = biome or entry["typical_biome"]
    land = land_type or entry["land_type"]

    per_m2 = annualised_land_carbon(biome_key, land, years)
    area = entry["land_m2_year"] * quantity

    return {
        "food": food,
        "label": entry["label"],
        "kg": quantity,
        "biome": biome_key,
        "biome_label": get_biome(biome_key)["label"],
        "land_type": land,
        "amortisation_years": _non_negative(years),
        "land_m2_year": area,
        "recoverable_tc_ha": recoverable_stock(biome_key, land),
        "recoverable_kg_per_m2": recoverable_per_m2(biome_key, land),
        "regrowth_fraction": regrowth_fraction(biome_key, years),
        "annualised_kg_per_m2": per_m2,
        "land_carbon_kg": area * per_m2,
    }


def food_footprint(
    food: str,
    kg: float = 1.0,
    biome: str | None = None,
    land_type: str | None = None,
    years: float = DEFAULT_AMORTISATION_YEARS,
) -> dict[str, Any]:
    """Production emissions and land opportunity cost, as two lines that sum.

    Never merged into a single number. They carry different levels of certainty,
    and a user who wants only the production figure - to compare against a label,
    or against another tool - must still be able to read it.
    """
    entry = get_food(food)
    quantity = _non_negative(kg)
    land = opportunity_cost(food, quantity, biome, land_type, years)

    production = entry["production_kg"] * quantity
    total = production + land["land_carbon_kg"]

    return {
        "food": food,
        "label": entry["label"],
        "kg": quantity,
        "production_kg": production,
        "land_carbon_kg": land["land_carbon_kg"],
        "total_kg": total,
        "land_share": (land["land_carbon_kg"] / total) if total > 0 else 0.0,
        "uplift_ratio": (total / production) if production > 0 else 0.0,
        "protein_g": entry["protein_g"] * quantity,
        "land": land,
        "note": entry["note"],
    }


def diet_footprint(
    items: list[dict[str, Any]] | None,
    biome: str | None = None,
    years: float = DEFAULT_AMORTISATION_YEARS,
) -> dict[str, Any]:
    """Aggregate a basket of food, which is the scale anyone actually changes.

    ``items`` entries are ``{"food": key, "kg": float}`` and may override
    ``biome`` and ``land_type`` individually - a household eating imported beef
    and domestic lamb is using two very different kinds of land.
    """
    rows = []
    for item in items or []:
        quantity = _non_negative(item.get("kg"))
        if quantity <= 0:
            continue
        rows.append(food_footprint(
            item.get("food"),
            quantity,
            item.get("biome") or biome,
            item.get("land_type"),
            years,
        ))

    production = sum(row["production_kg"] for row in rows)
    land = sum(row["land_carbon_kg"] for row in rows)
    total = production + land

    rows.sort(key=lambda row: row["total_kg"], reverse=True)
    return {
        "items": rows,
        "production_kg": production,
        "land_carbon_kg": land,
        "total_kg": total,
        "land_share": (land / total) if total > 0 else 0.0,
        "land_m2_year": sum(row["land"]["land_m2_year"] for row in rows),
        "amortisation_years": _non_negative(years),
        "largest_by_total": rows[0]["food"] if rows else None,
        "largest_by_production": (
            max(rows, key=lambda row: row["production_kg"])["food"] if rows else None
        ),
    }


def compare_foods(
    foods: list[str] | None = None,
    basis: str = "mass",
    biome: str | None = None,
    years: float = DEFAULT_AMORTISATION_YEARS,
) -> list[dict[str, Any]]:
    """Rank foods with and without the land term.

    ``basis`` is ``mass`` (per kg) or ``protein`` (per 100 g of protein). Foods
    with no meaningful protein are dropped from the protein comparison rather
    than divided by something close to zero.
    """
    if basis not in ("mass", "protein"):
        raise LandCostError(
            f"Unknown comparison basis '{basis}'. Expected 'mass' or 'protein'."
        )

    rows = []
    for key in foods or list_foods():
        entry = get_food(key)
        if basis == "protein" and entry["protein_g"] <= 0:
            continue

        footprint = food_footprint(key, 1.0, biome, None, years)
        divisor = 1.0
        if basis == "protein":
            # Per 100 g of protein.
            divisor = entry["protein_g"] / 100.0

        rows.append({
            "food": key,
            "label": entry["label"],
            "basis": basis,
            "production_kg": footprint["production_kg"] / divisor,
            "land_carbon_kg": footprint["land_carbon_kg"] / divisor,
            "total_kg": footprint["total_kg"] / divisor,
            "land_m2_year": entry["land_m2_year"] / divisor,
            "uplift_ratio": footprint["uplift_ratio"],
            "biome": footprint["land"]["biome"],
        })

    rows.sort(key=lambda row: row["total_kg"], reverse=True)
    return rows


def ratio_and_gap(
    high_land_food: str,
    low_land_food: str,
    biome: str | None = None,
    years: float = DEFAULT_AMORTISATION_YEARS,
) -> dict[str, Any]:
    """What the land term does to a comparison, in both directions.

    Reported explicitly because the two directions disagree and it would be easy
    to quote whichever supports the point being made. Adding a term proportional
    to land area narrows the *ratio* between a land-hungry food and a frugal one,
    because the land difference between them is smaller than the emissions
    difference. It widens the *absolute gap*, which is the scale on which the app
    compares dietary change against everything else.
    """
    high = food_footprint(high_land_food, 1.0, biome, None, years)
    low = food_footprint(low_land_food, 1.0, biome, None, years)

    production_ratio = (
        high["production_kg"] / low["production_kg"] if low["production_kg"] > 0 else 0.0
    )
    total_ratio = high["total_kg"] / low["total_kg"] if low["total_kg"] > 0 else 0.0

    return {
        "high": high_land_food,
        "low": low_land_food,
        "high_label": high["label"],
        "low_label": low["label"],
        "production_ratio": production_ratio,
        "total_ratio": total_ratio,
        "ratio_narrows": total_ratio < production_ratio,
        "production_gap_kg": high["production_kg"] - low["production_kg"],
        "total_gap_kg": high["total_kg"] - low["total_kg"],
        "gap_widens": (high["total_kg"] - low["total_kg"])
                      > (high["production_kg"] - low["production_kg"]),
    }


def land_release_scenario(
    before: list[dict[str, Any]] | None,
    after: list[dict[str, Any]] | None,
    biome: str | None = None,
    years: float = DEFAULT_AMORTISATION_YEARS,
) -> dict[str, Any]:
    """What a dietary change frees, and what that land would accumulate.

    The accumulation is a **one-off stock change that saturates**, not an annual
    flow that continues forever. The schedule is returned alongside the totals so
    that the saturation is visible: the annual increment in the fifth decade is a
    small fraction of the increment in the first.
    """
    start = diet_footprint(before, biome, years)
    end = diet_footprint(after, biome, years)

    area_freed = start["land_m2_year"] - end["land_m2_year"]
    biome_key = biome or DEFAULT_BIOME

    # The freed area is scored against a single biome, since a mixed release
    # would need each item's own land tracked separately through the change.
    per_m2_full = recoverable_per_m2(biome_key, "cropland")

    schedule = []
    previous = 0.0
    for year in (5, 10, 20, 30, 50, 100):
        fraction = regrowth_fraction(biome_key, year)
        stock = max(0.0, area_freed) * per_m2_full * fraction
        schedule.append({
            "year": year,
            "fraction": fraction,
            "stock_kg": stock,
            "added_since_previous_kg": stock - previous,
        })
        previous = stock

    total_stock = max(0.0, area_freed) * per_m2_full
    return {
        "before_total_kg": start["total_kg"],
        "after_total_kg": end["total_kg"],
        "annual_saving_kg": start["total_kg"] - end["total_kg"],
        "production_saving_kg": start["production_kg"] - end["production_kg"],
        "land_saving_kg": start["land_carbon_kg"] - end["land_carbon_kg"],
        "area_freed_m2": area_freed,
        "biome": biome_key,
        "eventual_stock_kg": total_stock,
        "stock_at_horizon_kg": total_stock * regrowth_fraction(biome_key, years),
        "schedule": schedule,
        "saturates": True,
        "caveat": (
            "The stock figure is a one-off gain that saturates as the "
            "vegetation matures. It is not an annual saving and it cannot be "
            "claimed twice."
        ),
    }


def sensitivity(
    food: str,
    kg: float = 1.0,
    biome: str | None = None,
    periods: tuple[int, ...] = AMORTISATION_RANGE,
) -> list[dict[str, Any]]:
    """The same food across amortisation periods, because the period decides."""
    rows = []
    for period in periods:
        footprint = food_footprint(food, kg, biome, None, period)
        rows.append({
            "amortisation_years": period,
            "production_kg": footprint["production_kg"],
            "land_carbon_kg": footprint["land_carbon_kg"],
            "total_kg": footprint["total_kg"],
            "land_share": footprint["land_share"],
        })
    return rows


def biome_sensitivity(
    food: str,
    kg: float = 1.0,
    years: float = DEFAULT_AMORTISATION_YEARS,
) -> list[dict[str, Any]]:
    """The same food on every kind of land, because land is not interchangeable."""
    entry = get_food(food)
    rows = []
    for key in list_biomes():
        footprint = food_footprint(food, kg, key, entry["land_type"], years)
        rows.append({
            "biome": key,
            "label": get_biome(key)["label"],
            "recoverable_tc_ha": recoverable_stock(key, entry["land_type"]),
            "land_carbon_kg": footprint["land_carbon_kg"],
            "total_kg": footprint["total_kg"],
        })
    rows.sort(key=lambda row: row["land_carbon_kg"], reverse=True)
    return rows


def get_land_insights(result: dict[str, Any] | None) -> list[str]:
    """Plain statements about what the numbers mean, in priority order."""
    if not result:
        return ["Add some food to see what the land under it would hold."]

    insights: list[str] = []
    share = _as_float(result.get("land_share"))
    total = _as_float(result.get("total_kg"))
    land = _as_float(result.get("land_carbon_kg"))
    production = _as_float(result.get("production_kg"))

    if share >= 0.4:
        insights.append(
            f"Land opportunity cost is {share * 100:.0f}% of this footprint - "
            f"{land:,.0f} kg against {production:,.0f} kg of production "
            f"emissions. The larger term is the one no food label reports."
        )
    elif share >= 0.15:
        insights.append(
            f"Land opportunity cost adds {land:,.0f} kg to {production:,.0f} kg "
            f"of production emissions, a {share * 100:.0f}% share. Enough to "
            f"change how this compares with non-food actions."
        )
    else:
        insights.append(
            f"Land opportunity cost is a small part of this footprint "
            f"({share * 100:.0f}%). That is a real result: this diet is not "
            f"land-hungry, and the emissions are somewhere else."
        )

    years = _as_float(result.get("amortisation_years"), DEFAULT_AMORTISATION_YEARS)
    insights.append(
        f"That land figure is amortised over {years:.0f} years. Over 100 years "
        f"it would be roughly half the size, and over 20 years noticeably "
        f"larger. There is no correct period, which is exactly why it is shown "
        f"rather than chosen quietly."
    )

    largest_total = result.get("largest_by_total")
    largest_production = result.get("largest_by_production")
    if largest_total and largest_production and largest_total != largest_production:
        insights.append(
            f"The largest item changes once land is counted: "
            f"{get_food(largest_production)['label'].lower()} by production "
            f"emissions, {get_food(largest_total)['label'].lower()} once the "
            f"land under it is included."
        )

    area = _as_float(result.get("land_m2_year"))
    if area > 0:
        insights.append(
            f"This basket occupies {area:,.0f} m² for a year. Released, it "
            f"would accumulate carbon for decades and then stop - a one-off "
            f"stock gain, not an annual saving, and it cannot be counted twice."
        )

    insights.append(
        "The two lines are kept separate on purpose. Production emissions are "
        "measured; land opportunity cost is modelled against a counterfactual, "
        "and merging them would hide which is which."
    )
    return insights


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_land_db() -> bool:
    """Create the table if it does not exist yet."""
    conn = None
    try:
        conn = _connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS land_opportunity_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                amortisation_years REAL NOT NULL,
                production_kg REAL NOT NULL,
                land_carbon_kg REAL NOT NULL,
                total_kg REAL NOT NULL,
                land_m2_year REAL NOT NULL,
                detail_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Unable to initialise land opportunity table: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def save_analysis(user_id: int, name: str, result: dict[str, Any]) -> int | None:
    """Persist a diet analysis. Returns the row id or None."""
    init_land_db()
    conn = None
    try:
        conn = _connect()
        cursor = conn.execute(
            """
            INSERT INTO land_opportunity_analyses (
                user_id, name, amortisation_years, production_kg,
                land_carbon_kg, total_kg, land_m2_year, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                (name or "Diet").strip() or "Diet",
                _as_float(result.get("amortisation_years"), DEFAULT_AMORTISATION_YEARS),
                _as_float(result.get("production_kg")),
                _as_float(result.get("land_carbon_kg")),
                _as_float(result.get("total_kg")),
                _as_float(result.get("land_m2_year")),
                json.dumps(result, default=str),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as exc:
        logger.error("Unable to save land analysis: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def get_analyses(user_id: int, limit: int = 25) -> list[dict[str, Any]]:
    """A user's saved analyses, newest first."""
    init_land_db()
    conn = None
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, name, amortisation_years, production_kg, land_carbon_kg,
                   total_kg, land_m2_year, detail_json, created_at
            FROM land_opportunity_analyses
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT ?
            """,
            (user_id, int(limit)),
        ).fetchall()

        analyses = []
        for row in rows:
            record = dict(row)
            try:
                record["detail"] = json.loads(record.pop("detail_json") or "{}")
            except (TypeError, ValueError):
                record["detail"] = {}
            analyses.append(record)
        return analyses
    except sqlite3.Error as exc:
        logger.error("Unable to load land analyses: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def delete_analysis(analysis_id: int) -> bool:
    """Delete a saved analysis."""
    init_land_db()
    conn = None
    try:
        conn = _connect()
        cursor = conn.execute(
            "DELETE FROM land_opportunity_analyses WHERE id = ?", (analysis_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as exc:
        logger.error("Unable to delete land analysis: %s", exc)
        return False
    finally:
        if conn:
            conn.close()
