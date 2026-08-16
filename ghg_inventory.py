"""GHG Protocol scope classification and inventory for a household boundary.

`emissions.py` and the assessment flow add everything into one number. That is
fine for a headline and wrong for almost everything else, because it conflates
three categories that behave completely differently:

*   **Scope 1** - fuel the user burns directly. Their boiler, their car's
    tank. Changing it means changing equipment or behaviour.
*   **Scope 2** - electricity they buy. Changing it can mean changing
    *supplier*: same wires, same appliances, different contract, different
    number.
*   **Scope 3** - everything embodied in what they buy, eat and throw away.
    Changing it means changing consumption.

Flattening these causes concrete problems the app has today.

The green tariff problem
------------------------
A user on a certified renewable tariff has a market-based Scope 2 near zero
and a location-based Scope 2 identical to their neighbour's. Both figures are
correct and they answer different questions:

*   **Location-based** uses the grid average. It is what the wires actually
    did while their kettle was on, and it is the number that matters for
    understanding physical grid impact.
*   **Market-based** uses the contract they hold. It is what they paid for and
    it is the number that drives demand for clean generation.

The app can currently express neither, so it either ignores green tariffs or
zeroes out electricity as though the physical grid had changed. Both are
wrong. This module reports both, as the GHG Protocol Scope 2 Guidance
requires.

It also implements the residual mix, which is the part green-tariff marketing
never mentions: if some consumers claim the clean generation, what is left for
everyone else is dirtier than the grid average. A user *not* on a green tariff
should see a market-based figure slightly above the grid average, because that
is the accounting counterpart of their neighbour's certificates.

Boundaries and completeness
---------------------------
An inventory without a stated boundary is not an inventory. Every result
carries what was included, what was excluded and why. Completeness is scored
against the categories a personal inventory ought to cover, so a user with a
suspiciously low total is told they have not reported their flights rather
than congratulated.

Base years and recalculation
----------------------------
Changing method is not the same as changing behaviour, and without the
standard recalculation rules the two are indistinguishable on a trend line.
`recalculate_base_year()` applies them.

This module classifies and reports; it does not recompute anyone's emissions.
It takes the totals the rest of the app already produces and gives them the
structure they have been missing, which keeps the change additive and leaves
the assessment path untouched.

The module is self-contained: only the standard library is used, its SQLite
tables are created lazily, and no shared files are modified.
"""

import os
import json
import math
import sqlite3
import logging
import datetime
from typing import Any

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

SCOPE_1 = 1
SCOPE_2 = 2
SCOPE_3 = 3

SCOPE_LABELS = {
    SCOPE_1: "Scope 1 - direct emissions",
    SCOPE_2: "Scope 2 - purchased energy",
    SCOPE_3: "Scope 3 - everything else",
}

SCOPE_DESCRIPTIONS = {
    SCOPE_1: (
        "Fuel you burn yourself, in equipment you control. Your boiler, your "
        "car's tank, your wood stove. You change these by changing the "
        "equipment or how you use it."
    ),
    SCOPE_2: (
        "Energy you buy that was generated somewhere else - electricity, "
        "district heating. Uniquely, you can change this number by changing "
        "supplier without changing anything you do."
    ),
    SCOPE_3: (
        "Everything embodied in what you buy, eat, travel on and throw away. "
        "Usually the largest share, and the hardest to measure."
    ),
}

# Scope 3 categories adapted to a household boundary. The corporate standard
# has fifteen; several are meaningless for an individual (there are no sold
# products, no franchises) and are dropped rather than left in to be scored
# as permanently missing.
SCOPE_3_CATEGORIES = {
    "purchased_goods": "Purchased goods and services",
    "capital_goods": "Capital goods (vehicles, appliances, renovations)",
    "fuel_and_energy": "Fuel and energy related activities (upstream of scope 1 and 2)",
    "upstream_transport": "Upstream transport and delivery",
    "waste": "Waste generated",
    "business_travel": "Travel not in your own vehicle",
    "commuting": "Commuting",
    "food": "Food and diet",
    "water": "Water supply and treatment",
    "digital": "Digital services and devices",
    "financial": "Investments and financial services",
}

# How the categories the app already collects map onto scopes. Every entry
# carries a rationale, because the interesting cases are genuinely not
# obvious - an electric car is scope 2 for its charging and scope 3 for its
# battery, and a user should be able to see why rather than being told.
ACTIVITY_CLASSIFICATION = {
    "gas_heating": {
        "scope": SCOPE_1,
        "category": None,
        "label": "Gas heating",
        "rationale": "You burn the gas yourself, in a boiler you control.",
    },
    "oil_heating": {
        "scope": SCOPE_1,
        "category": None,
        "label": "Oil heating",
        "rationale": "Combustion happens on your property, in your equipment.",
    },
    "wood_burning": {
        "scope": SCOPE_1,
        "category": None,
        "label": "Wood burning",
        "rationale": (
            "Direct combustion. Biogenic CO2 is reported separately by "
            "convention, but the stove is still scope 1."
        ),
    },
    "petrol_vehicle": {
        "scope": SCOPE_1,
        "category": None,
        "label": "Petrol vehicle fuel",
        "rationale": "You burn the fuel in a vehicle you control.",
    },
    "diesel_vehicle": {
        "scope": SCOPE_1,
        "category": None,
        "label": "Diesel vehicle fuel",
        "rationale": "You burn the fuel in a vehicle you control.",
    },
    "refrigerant_leakage": {
        "scope": SCOPE_1,
        "category": None,
        "label": "Refrigerant leakage",
        "rationale": (
            "Fugitive emissions from your own fridge, air conditioning or "
            "heat pump. Small in mass, large in warming potential."
        ),
    },
    "electricity": {
        "scope": SCOPE_2,
        "category": None,
        "label": "Purchased electricity",
        "rationale": (
            "Generated elsewhere and bought by you. This is the only scope "
            "you can change by switching supplier."
        ),
    },
    "district_heating": {
        "scope": SCOPE_2,
        "category": None,
        "label": "District heating",
        "rationale": "Heat generated elsewhere and delivered to you.",
    },
    "electric_vehicle_charging": {
        "scope": SCOPE_2,
        "category": None,
        "label": "EV charging",
        "rationale": (
            "The electricity is scope 2. The battery that stores it is scope "
            "3 capital goods - the same vehicle sits in two scopes."
        ),
    },
    "food": {
        "scope": SCOPE_3,
        "category": "food",
        "label": "Food and diet",
        "rationale": "Emissions occurred in farming and processing, upstream of you.",
    },
    "goods": {
        "scope": SCOPE_3,
        "category": "purchased_goods",
        "label": "Goods and services",
        "rationale": "Embodied in things made before you bought them.",
    },
    "appliances": {
        "scope": SCOPE_3,
        "category": "capital_goods",
        "label": "Appliances and vehicles bought",
        "rationale": (
            "Capital goods. Reported in the year of purchase, which makes a "
            "year with a new car look unusually bad - that is correct, not a bug."
        ),
    },
    "flights": {
        "scope": SCOPE_3,
        "category": "business_travel",
        "label": "Flights",
        "rationale": "You do not operate the aircraft, so it is not your scope 1.",
    },
    "public_transport": {
        "scope": SCOPE_3,
        "category": "commuting",
        "label": "Public transport",
        "rationale": "Someone else burns the fuel in a vehicle they control.",
    },
    "taxi_rideshare": {
        "scope": SCOPE_3,
        "category": "commuting",
        "label": "Taxis and rideshare",
        "rationale": "Another operator's vehicle, so scope 3 for you.",
    },
    "waste": {
        "scope": SCOPE_3,
        "category": "waste",
        "label": "Waste and recycling",
        "rationale": "Emissions occur downstream, at the treatment facility.",
    },
    "water": {
        "scope": SCOPE_3,
        "category": "water",
        "label": "Water supply and treatment",
        "rationale": "Energy used by the water utility on your behalf.",
    },
    "deliveries": {
        "scope": SCOPE_3,
        "category": "upstream_transport",
        "label": "Deliveries and online orders",
        "rationale": "Transport arranged and operated by the retailer.",
    },
    "digital": {
        "scope": SCOPE_3,
        "category": "digital",
        "label": "Digital services and devices",
        "rationale": "Data centre and network energy, plus embodied device carbon.",
    },
    "upstream_fuel": {
        "scope": SCOPE_3,
        "category": "fuel_and_energy",
        "label": "Upstream fuel and grid losses",
        "rationale": (
            "Extracting, refining and transmitting the energy behind your "
            "scope 1 and 2. Routinely forgotten and worth 15-25% of them."
        ),
    },
    "investments": {
        "scope": SCOPE_3,
        "category": "financial",
        "label": "Investments and pensions",
        "rationale": (
            "Emissions financed by capital you own. Reported here for "
            "completeness; it is a contested inclusion at household level."
        ),
    },
}

# Categories a reasonably complete personal inventory should cover. Anything
# missing from this list is what completeness scoring reports.
EXPECTED_ACTIVITIES = (
    "electricity",
    "food",
    "goods",
    "waste",
    "upstream_fuel",
)

# Categories that are commonly large and commonly forgotten. Missing one of
# these matters more than missing water, so they are weighted accordingly.
HIGH_IMPACT_ACTIVITIES = ("electricity", "food", "flights", "goods")

# Grid average intensity in kgCO2e per kWh, used for location-based scope 2.
DEFAULT_GRID_INTENSITY = 0.21

# Residual mix uplift. When some consumers claim the clean generation via
# certificates, what remains for everyone else is dirtier than the grid
# average. A user on a standard tariff should see this, because it is the
# accounting counterpart of their neighbour's green tariff.
DEFAULT_RESIDUAL_UPLIFT = 1.25

# Supplier contract types and their market-based intensity treatment.
TARIFF_TYPES = {
    "Standard tariff": {
        "uses_residual_mix": True,
        "intensity": None,
        "description": "No specific claim. Priced at the residual mix.",
    },
    "Certified renewable tariff": {
        "uses_residual_mix": False,
        "intensity": 0.0,
        "description": "Backed by cancelled certificates for your consumption.",
    },
    "Partially renewable tariff": {
        "uses_residual_mix": False,
        "intensity": 0.10,
        "description": "A stated share of certified renewable supply.",
    },
    "Direct renewable contract": {
        "uses_residual_mix": False,
        "intensity": 0.0,
        "description": "A power purchase agreement with a named generator.",
    },
    "Own generation (solar)": {
        "uses_residual_mix": False,
        "intensity": 0.0,
        "description": "Self-consumed generation. Outside scope 2 entirely.",
    },
}

DEFAULT_TARIFF = "Standard tariff"

# Recalculation is required when a boundary or methodology change moves the
# base year by more than this share. Below it, the change is not significant
# and restating would add churn without adding meaning.
SIGNIFICANCE_THRESHOLD = 0.05

CONSOLIDATION_APPROACHES = {
    "operational_control": (
        "Operational control - everything you decide how to operate, "
        "including a leased car and a rented home's boiler."
    ),
    "financial_control": (
        "Financial control - only what you own. Excludes a landlord's boiler "
        "even though you decide when it runs."
    ),
    "equity_share": (
        "Equity share - your percentage of shared assets, which for a "
        "household usually means per-capita allocation."
    ),
}

DEFAULT_CONSOLIDATION = "operational_control"


class InventoryError(ValueError):
    """Raised when an inventory cannot be built."""


# --- Classification ---------------------------------------------------------


def list_activities(scope: int | None = None) -> list[dict[str, Any]]:
    """Return the classification table, optionally filtered to one scope."""
    activities = [
        {"key": key, **details}
        for key, details in ACTIVITY_CLASSIFICATION.items()
        if scope is None or details["scope"] == scope
    ]
    return sorted(activities, key=lambda item: (item["scope"], item["label"]))


def list_scope_3_categories() -> list[dict[str, Any]]:
    """Return the Scope 3 categories used at household boundary."""
    return [{"key": key, "label": label} for key, label in SCOPE_3_CATEGORIES.items()]


def classify(activity_key: str) -> dict[str, Any]:
    """Return the scope classification for an activity, or raise.

    Unknown activities raise rather than defaulting to Scope 3. Quietly
    filing something in the largest bucket would hide a gap in the mapping
    behind a plausible-looking total.
    """
    details = ACTIVITY_CLASSIFICATION.get(activity_key)
    if not details:
        raise InventoryError(f"Unknown activity: {activity_key}")
    return {"key": activity_key, **details}


def scope_of(activity_key: str) -> int:
    """The scope number for an activity."""
    return classify(activity_key)["scope"]


def explain(activity_key: str) -> str:
    """Why an activity sits in the scope it does."""
    details = classify(activity_key)
    return f"{details['label']} is scope {details['scope']}: {details['rationale']}"


# --- Scope 2 dual reporting -------------------------------------------------


def _clean_number(value: Any, field: str, allow_zero: bool = True) -> float:
    """Coerce a numeric input, rejecting the values that would corrupt a total."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise InventoryError(f"{field} must be a number")
    if math.isnan(number) or math.isinf(number):
        raise InventoryError(f"{field} must be a real number")
    if number < 0:
        raise InventoryError(f"{field} cannot be negative")
    if not allow_zero and number == 0:
        raise InventoryError(f"{field} must be greater than zero")
    return number


def list_tariffs() -> list[dict[str, Any]]:
    """Return the supplier contract types."""
    return [{"name": name, **details} for name, details in TARIFF_TYPES.items()]


def scope_2_dual(
    kwh: float,
    grid_intensity: float = DEFAULT_GRID_INTENSITY,
    tariff: str = DEFAULT_TARIFF,
    residual_uplift: float = DEFAULT_RESIDUAL_UPLIFT,
    market_intensity: float | None = None,
) -> dict[str, Any]:
    """Location-based and market-based Scope 2, reported side by side.

    The GHG Protocol requires both, and the reason is visible in the output:
    a green tariff moves the market-based figure to zero and leaves the
    location-based figure exactly where it was. Neither number alone is the
    truth, and reporting only one is how green tariffs get either ignored or
    over-credited.
    """
    consumption = _clean_number(kwh, "Electricity consumption")
    intensity = _clean_number(grid_intensity, "Grid intensity")

    contract = TARIFF_TYPES.get(tariff) or TARIFF_TYPES[DEFAULT_TARIFF]
    tariff_name = tariff if tariff in TARIFF_TYPES else DEFAULT_TARIFF

    location_based = consumption * intensity

    if market_intensity is not None:
        applied_intensity = _clean_number(market_intensity, "Market intensity")
    elif contract["uses_residual_mix"]:
        uplift = _clean_number(residual_uplift, "Residual uplift", allow_zero=False)
        applied_intensity = intensity * uplift
    else:
        applied_intensity = contract["intensity"]

    market_based = consumption * applied_intensity
    difference = location_based - market_based

    return {
        "kwh": consumption,
        "tariff": tariff_name,
        "grid_intensity": intensity,
        "market_intensity": applied_intensity,
        "location_based": location_based,
        "market_based": market_based,
        "difference": difference,
        "uses_residual_mix": bool(contract["uses_residual_mix"]) and market_intensity is None,
        "explanation": _scope_2_explanation(tariff_name, location_based, market_based),
    }


def _scope_2_explanation(tariff: str, location_based: float, market_based: float) -> str:
    """Plain sentence explaining why the two Scope 2 numbers differ."""
    if market_based < location_based:
        return (
            f"Your {tariff.lower()} takes your reported electricity emissions "
            f"from {location_based:,.0f} kg to {market_based:,.0f} kg. The "
            f"physical grid did not change - the same electrons reached your "
            f"house - but you are paying for clean generation to be built and "
            f"the accounting recognises that."
        )
    if market_based > location_based:
        return (
            f"On a standard tariff your market-based figure "
            f"({market_based:,.0f} kg) is *higher* than the grid average "
            f"({location_based:,.0f} kg). Other consumers have claimed the "
            f"clean generation through certificates, so what is left for "
            f"everyone else is dirtier. This is the part green tariff "
            f"marketing never mentions."
        )
    return (
        f"Both methods give {location_based:,.0f} kg for your electricity."
    )


# --- Inventory --------------------------------------------------------------


def build_inventory(
    line_items: list[dict[str, Any]],
    reporting_period: str = "",
    consolidation: str = DEFAULT_CONSOLIDATION,
    scope_2_method: str = "location_based",
    exclusions: list[str] | None = None,
) -> dict[str, Any]:
    """Assemble classified line items into a structured inventory.

    ``line_items`` is a list of dicts with ``activity`` and ``emissions`` in
    kgCO2e, optionally ``location_based`` and ``market_based`` for electricity.

    The headline total uses one Scope 2 method, declared explicitly, because
    a total that silently mixed the two would be meaningless. Both are always
    reported alongside.
    """
    if not line_items:
        raise InventoryError("An inventory needs at least one line item")

    lines = []
    for item in line_items:
        activity = item.get("activity")
        details = classify(activity)
        emissions = _clean_number(item.get("emissions", 0.0), f"Emissions for {activity}")

        line = {
            "activity": activity,
            "label": details["label"],
            "scope": details["scope"],
            "category": details["category"],
            "category_label": SCOPE_3_CATEGORIES.get(details["category"], ""),
            "rationale": details["rationale"],
            "emissions": emissions,
        }

        # Electricity may carry both Scope 2 figures. When it does, the
        # headline emissions follow the declared method.
        if details["scope"] == SCOPE_2 and "location_based" in item and "market_based" in item:
            line["location_based"] = _clean_number(item["location_based"], "Location-based")
            line["market_based"] = _clean_number(item["market_based"], "Market-based")
            line["emissions"] = (
                line["market_based"]
                if scope_2_method == "market_based"
                else line["location_based"]
            )

        lines.append(line)

    totals = {SCOPE_1: 0.0, SCOPE_2: 0.0, SCOPE_3: 0.0}
    location_total = 0.0
    market_total = 0.0

    for line in lines:
        totals[line["scope"]] += line["emissions"]
        if line["scope"] == SCOPE_2:
            location_total += line.get("location_based", line["emissions"])
            market_total += line.get("market_based", line["emissions"])

    total = sum(totals.values())
    by_category = {}
    for line in lines:
        if line["scope"] != SCOPE_3 or not line["category"]:
            continue
        by_category.setdefault(line["category"], 0.0)
        by_category[line["category"]] += line["emissions"]

    lines.sort(key=lambda item: (item["scope"], -item["emissions"]))

    return {
        "reporting_period": str(reporting_period or ""),
        "consolidation": consolidation
        if consolidation in CONSOLIDATION_APPROACHES
        else DEFAULT_CONSOLIDATION,
        "scope_2_method": (
            "market_based" if scope_2_method == "market_based" else "location_based"
        ),
        "lines": lines,
        "scope_1": totals[SCOPE_1],
        "scope_2": totals[SCOPE_2],
        "scope_3": totals[SCOPE_3],
        "scope_2_location_based": location_total,
        "scope_2_market_based": market_total,
        "total": total,
        "shares": {
            scope: (value / total) if total > 0 else 0.0
            for scope, value in totals.items()
        },
        "scope_3_by_category": dict(
            sorted(by_category.items(), key=lambda entry: entry[1], reverse=True)
        ),
        "boundary": boundary_statement(reporting_period, consolidation, lines, exclusions),
        "completeness": assess_completeness(lines),
    }


def total_under_method(inventory: dict[str, Any], scope_2_method: str) -> float:
    """Restate a total under the other Scope 2 method.

    Cheap, and it stops anyone having to rebuild an inventory just to see the
    number the other way round.
    """
    scope_2 = (
        inventory["scope_2_market_based"]
        if scope_2_method == "market_based"
        else inventory["scope_2_location_based"]
    )
    return inventory["scope_1"] + scope_2 + inventory["scope_3"]


def boundary_statement(
    reporting_period: str,
    consolidation: str,
    lines: list[dict[str, Any]],
    exclusions: list[str] | None = None,
) -> dict[str, Any]:
    """The boundary declaration. An inventory without one is not an inventory."""
    approach = (
        consolidation if consolidation in CONSOLIDATION_APPROACHES else DEFAULT_CONSOLIDATION
    )
    included = sorted({line["label"] for line in lines})
    reported_keys = {line["activity"] for line in lines}
    omitted = [
        ACTIVITY_CLASSIFICATION[key]["label"]
        for key in EXPECTED_ACTIVITIES
        if key not in reported_keys
    ]

    return {
        "reporting_period": str(reporting_period or "not stated"),
        "consolidation_approach": approach,
        "consolidation_description": CONSOLIDATION_APPROACHES[approach],
        "included": included,
        "omitted": omitted,
        "stated_exclusions": list(exclusions or []),
        "statement": (
            f"Inventory prepared on an {approach.replace('_', ' ')} basis for "
            f"{reporting_period or 'an unstated period'}, covering "
            f"{len(included)} activity categories."
        ),
    }


def assess_completeness(lines: list[dict[str, Any]]) -> dict[str, Any]:
    """Score how much of a personal inventory has actually been reported.

    A user who has reported only their electricity has a low total and a
    terrible inventory, and the app should say which of those it is looking at
    rather than congratulating them.
    """
    reported = {line["activity"] for line in lines}
    missing = [key for key in EXPECTED_ACTIVITIES if key not in reported]
    missing_high_impact = [key for key in HIGH_IMPACT_ACTIVITIES if key not in reported]

    covered = len(EXPECTED_ACTIVITIES) - len(missing)
    score = covered / len(EXPECTED_ACTIVITIES) if EXPECTED_ACTIVITIES else 0.0

    # A missing high-impact category costs more than a missing minor one,
    # because the size of the gap matters more than the count of gaps.
    penalty = 0.1 * len(missing_high_impact)
    score = max(0.0, min(1.0, score - penalty))

    scopes_present = {line["scope"] for line in lines}

    if score >= 0.9 and len(scopes_present) == 3:
        rating = "comprehensive"
    elif score >= 0.7:
        rating = "good"
    elif score >= 0.4:
        rating = "partial"
    else:
        rating = "fragmentary"

    return {
        "score": score,
        "rating": rating,
        "missing": [ACTIVITY_CLASSIFICATION[key]["label"] for key in missing],
        "missing_high_impact": [
            ACTIVITY_CLASSIFICATION[key]["label"] for key in missing_high_impact
        ],
        "scopes_covered": sorted(scopes_present),
        "warning": _completeness_warning(rating, missing_high_impact, scopes_present),
    }


def _completeness_warning(
    rating: str, missing_high_impact: list[str], scopes_present: set[int]
) -> str:
    """Say plainly when a low total is under-reporting rather than achievement.

    Ordered by severity, most severe first. An entirely absent scope is a
    structural problem with the inventory and outranks any number of
    individually missing categories, so it is checked before them.
    """
    if SCOPE_3 not in scopes_present:
        return (
            "No scope 3 reported at all. For most households that is the "
            "largest share of the footprint, so this total is badly understated."
        )
    if missing_high_impact:
        labels = ", ".join(
            ACTIVITY_CLASSIFICATION[key]["label"].lower() for key in missing_high_impact
        )
        return (
            f"You have not reported {labels}. A low total here means an "
            f"incomplete inventory, not a small footprint."
        )
    if rating == "comprehensive":
        return ""
    return (
        "Some categories are missing. The total is a floor rather than a "
        "complete figure."
    )


# --- Base year and recalculation --------------------------------------------


def recalculate_base_year(
    base_year_total: float, adjustment: float, reason: str = ""
) -> dict[str, Any]:
    """Apply the GHG Protocol recalculation rules to a base year.

    Without this, a change of methodology is indistinguishable from a change
    of behaviour on a trend line - which is precisely the trap this module
    exists to avoid. The significance threshold prevents restating the base
    year over every trivial refinement, which would produce churn without
    meaning.
    """
    base = _clean_number(base_year_total, "Base year total")

    try:
        change = float(adjustment)
    except (TypeError, ValueError):
        raise InventoryError("Adjustment must be a number")
    if math.isnan(change) or math.isinf(change):
        raise InventoryError("Adjustment must be a real number")

    share = abs(change) / base if base > 0 else 0.0
    significant = share >= SIGNIFICANCE_THRESHOLD
    restated = base + change if significant else base

    return {
        "original_base_year": base,
        "adjustment": change,
        "adjustment_share": share,
        "is_significant": significant,
        "restated_base_year": restated,
        "reason": str(reason or ""),
        "explanation": (
            f"The change is {share * 100:.1f}% of the base year, at or above "
            f"the {SIGNIFICANCE_THRESHOLD * 100:.0f}% significance threshold, "
            f"so the base year is restated to {restated:,.0f} kg. Comparisons "
            f"against it remain like for like."
            if significant
            else f"The change is {share * 100:.1f}% of the base year, below the "
            f"{SIGNIFICANCE_THRESHOLD * 100:.0f}% significance threshold, so "
            f"the base year is left alone. Restating for every small "
            f"refinement would add churn without adding meaning."
        ),
    }


def compare_to_base_year(
    inventory: dict[str, Any], base_year_total: float, base_year_label: str = ""
) -> dict[str, Any]:
    """Track an inventory against its base year, per scope where possible."""
    base = _clean_number(base_year_total, "Base year total")
    current = inventory["total"]
    change = current - base
    percent = (change / base * 100.0) if base > 0 else 0.0

    return {
        "base_year_label": str(base_year_label or ""),
        "base_year_total": base,
        "current_total": current,
        "change": change,
        "percent_change": percent,
        "reduced": change < 0,
        "scope_2_method": inventory["scope_2_method"],
        "caveat": (
            "Both totals must use the same scope 2 method and the same "
            "boundary, or this comparison is meaningless."
        ),
    }


# --- Export -----------------------------------------------------------------


def export_inventory(inventory: dict[str, Any]) -> dict[str, Any]:
    """Emit an inventory as structured data suitable for reporting.

    Method notes and the boundary statement travel with the numbers, because
    a scope breakdown detached from its boundary is exactly the kind of
    figure that gets misread.
    """
    return {
        "reporting_period": inventory["reporting_period"],
        "boundary": inventory["boundary"],
        "consolidation_approach": inventory["consolidation"],
        "scope_2_method": inventory["scope_2_method"],
        "totals": {
            "scope_1": round(inventory["scope_1"], 2),
            "scope_2_location_based": round(inventory["scope_2_location_based"], 2),
            "scope_2_market_based": round(inventory["scope_2_market_based"], 2),
            "scope_3": round(inventory["scope_3"], 2),
            "total": round(inventory["total"], 2),
        },
        "scope_3_by_category": {
            SCOPE_3_CATEGORIES.get(key, key): round(value, 2)
            for key, value in inventory["scope_3_by_category"].items()
        },
        "lines": [
            {
                "activity": line["label"],
                "scope": line["scope"],
                "category": line["category_label"],
                "emissions_kgco2e": round(line["emissions"], 2),
            }
            for line in inventory["lines"]
        ],
        "completeness": inventory["completeness"],
        "method_notes": [
            "Prepared following the GHG Protocol Corporate Standard, adapted "
            "to a household boundary.",
            "Scope 2 is reported under both the location-based and "
            "market-based methods, per the Scope 2 Guidance.",
            "Scope 3 categories are a household-relevant subset of the "
            "fifteen corporate categories.",
            "Biogenic CO2 from wood burning is reported separately by "
            "convention and is not included in the scope 1 total.",
        ],
    }


def get_scope_insights(inventory: dict[str, Any]) -> list[str]:
    """Observations that follow from the scope split, not generic advice."""
    insights = []
    shares = inventory["shares"]

    if shares.get(SCOPE_2, 0) > 0.25:
        difference = (
            inventory["scope_2_location_based"] - inventory["scope_2_market_based"]
        )
        if abs(difference) > 1:
            insights.append(
                f"Scope 2 is {shares[SCOPE_2] * 100:.0f}% of your footprint, and "
                f"your two scope 2 figures differ by {abs(difference):,.0f} kg. "
                f"Switching supplier moves one of them without you changing "
                f"anything you do."
            )
        else:
            insights.append(
                f"Scope 2 is {shares[SCOPE_2] * 100:.0f}% of your footprint. A "
                f"certified renewable tariff would move your market-based "
                f"total substantially, and your location-based total not at all."
            )

    if shares.get(SCOPE_3, 0) > 0.6:
        insights.append(
            f"Scope 3 is {shares[SCOPE_3] * 100:.0f}% of your footprint. That is "
            f"normal for a household and it means most of your impact is in "
            f"what you buy rather than what you burn."
        )
    elif shares.get(SCOPE_3, 0) < 0.3 and inventory["scope_3"] > 0:
        insights.append(
            f"Scope 3 is only {shares[SCOPE_3] * 100:.0f}% of your footprint, "
            f"which is unusually low. It is far more likely that categories "
            f"are missing than that your consumption is genuinely tiny."
        )

    if shares.get(SCOPE_1, 0) > 0.4:
        insights.append(
            f"Scope 1 is {shares[SCOPE_1] * 100:.0f}% of your footprint, so most "
            f"of your emissions come out of equipment you own. Those need "
            f"replacing rather than re-contracting."
        )

    if inventory["completeness"]["warning"]:
        insights.append(inventory["completeness"]["warning"])

    return insights


# --- Persistence ------------------------------------------------------------


def _connect() -> sqlite3.Connection:
    """Open a connection with the inventory tables guaranteed to exist."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ghg_inventories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            reporting_period TEXT,
            consolidation TEXT NOT NULL,
            scope_2_method TEXT NOT NULL,
            scope_1 REAL NOT NULL,
            scope_2_location REAL NOT NULL,
            scope_2_market REAL NOT NULL,
            scope_3 REAL NOT NULL,
            total REAL NOT NULL,
            completeness REAL NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ghg_inventory_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inventory_id INTEGER NOT NULL,
            activity TEXT NOT NULL,
            scope INTEGER NOT NULL,
            category TEXT,
            emissions REAL NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def save_inventory(user_id: int, name: str, inventory: dict[str, Any]) -> int | None:
    """Persist an inventory and its line items."""
    if not user_id:
        return None

    conn = _connect()
    try:
        cursor = conn.execute(
            """
            INSERT INTO ghg_inventories (
                user_id, name, reporting_period, consolidation, scope_2_method,
                scope_1, scope_2_location, scope_2_market, scope_3, total,
                completeness, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                str(name or "Inventory"),
                str(inventory.get("reporting_period", "")),
                str(inventory.get("consolidation", DEFAULT_CONSOLIDATION)),
                str(inventory.get("scope_2_method", "location_based")),
                float(inventory.get("scope_1", 0.0)),
                float(inventory.get("scope_2_location_based", 0.0)),
                float(inventory.get("scope_2_market_based", 0.0)),
                float(inventory.get("scope_3", 0.0)),
                float(inventory.get("total", 0.0)),
                float(inventory.get("completeness", {}).get("score", 0.0)),
                datetime.datetime.now().isoformat(timespec="seconds"),
            ),
        )
        inventory_id = cursor.lastrowid

        for line in inventory.get("lines", []):
            conn.execute(
                """
                INSERT INTO ghg_inventory_lines (
                    inventory_id, activity, scope, category, emissions
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    inventory_id,
                    str(line.get("activity", "")),
                    int(line.get("scope", SCOPE_3)),
                    str(line.get("category") or ""),
                    float(line.get("emissions", 0.0)),
                ),
            )

        conn.commit()
        return inventory_id
    except (sqlite3.Error, TypeError, ValueError):
        logger.exception("Failed to save inventory")
        return None
    finally:
        conn.close()


def get_inventories(user_id: int, limit: int = 25) -> list[dict[str, Any]]:
    """Return saved inventories for a user, newest first, with their lines."""
    if not user_id:
        return []

    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT id, name, reporting_period, consolidation, scope_2_method,
                   scope_1, scope_2_location, scope_2_market, scope_3, total,
                   completeness, created_at
            FROM ghg_inventories
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(user_id), int(limit)),
        ).fetchall()

        inventories = []
        for row in rows:
            lines = conn.execute(
                """
                SELECT activity, scope, category, emissions
                FROM ghg_inventory_lines
                WHERE inventory_id = ?
                ORDER BY scope ASC, emissions DESC
                """,
                (row[0],),
            ).fetchall()

            inventories.append(
                {
                    "id": row[0],
                    "name": row[1],
                    "reporting_period": row[2],
                    "consolidation": row[3],
                    "scope_2_method": row[4],
                    "scope_1": row[5],
                    "scope_2_location_based": row[6],
                    "scope_2_market_based": row[7],
                    "scope_3": row[8],
                    "total": row[9],
                    "completeness": row[10],
                    "created_at": row[11],
                    "lines": [
                        {
                            "activity": line[0],
                            "scope": line[1],
                            "category": line[2],
                            "emissions": line[3],
                        }
                        for line in lines
                    ],
                }
            )
        return inventories
    except sqlite3.Error:
        logger.exception("Failed to read inventories")
        return []
    finally:
        conn.close()


def delete_inventory(user_id: int, inventory_id: int) -> bool:
    """Delete an inventory and its lines. Scoped by user."""
    if not user_id or not inventory_id:
        return False

    conn = _connect()
    try:
        cursor = conn.execute(
            "DELETE FROM ghg_inventories WHERE id = ? AND user_id = ?",
            (int(inventory_id), int(user_id)),
        )
        # Only clear the lines if the parent actually belonged to this user,
        # so a guessed id cannot orphan someone else's data.
        if cursor.rowcount > 0:
            conn.execute(
                "DELETE FROM ghg_inventory_lines WHERE inventory_id = ?",
                (int(inventory_id),),
            )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error:
        logger.exception("Failed to delete inventory")
        return False
    finally:
        conn.close()
