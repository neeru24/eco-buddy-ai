"""Consequential (marginal) emissions accounting.

Every emission factor in this app is an *average*: total emissions divided by
total activity. That is the right number for reporting a footprint and the
wrong number for deciding what to do next.

The distinction is the attributional/consequential split in LCA:

    attributional  - of the emissions that happened, how many are mine?
    consequential  - if I do this differently, what changes?

Users almost never ask the first question. They ask the second, and the app
has so far answered it with the first question's number.

For electricity the gap is large and it points in *both* directions. The plant
that responds to one extra kilowatt-hour at 2pm is not the average of
everything running at 2pm; it is whichever unit sits on the margin. On a
sunny grid at midday that unit may be renewable output which would otherwise
have been curtailed, so the marginal factor collapses towards zero while the
average factor still reads 120 gCO2/kWh. At 3am on a nuclear-heavy grid the
average looks clean but the marginal unit is usually still thermal. One error
flatters the middle of the day and the other flatters the middle of the night,
so they do not cancel - they reorder the hours, and the hour ranking is the
entire output of ``grid_scheduler``.

Rather than shipping a second set of magic constants, this module derives both
curves from one small dispatch model:

    * a stack of generating units, each with a capacity, an emission rate and
      a place in the merit order
    * an availability shape for the weather-driven units
    * a demand shape across the day

At each hour the must-run units generate what the weather allows. If that
already covers demand, the surplus is curtailed and an extra kilowatt-hour is
served by generation that would have been thrown away. Otherwise the shortfall
is filled from the dispatchable stack in merit order, and the last unit called
is the marginal one. The *average* is the emissions-weighted mean of everything
dispatched; the *marginal* is the rate of the last unit. Same model, two
questions, and the divergence is a consequence rather than an assumption.

The same average/marginal gap applies outside electricity. Recycling one more
aluminium can does not save the average aluminium factor, which blends primary
and secondary metal; it avoids *primary* production, which is roughly an order
of magnitude larger. Those factors are tabulated here directly, since there is
no dispatch model to derive them from.

Nothing in this module recomputes anyone's footprint. It takes figures the
rest of the app already produces and reports what a change to them would
actually cause. The SQLite table is created lazily and no shared files are
modified.
"""

import os
import json
import sqlite3
import logging
from typing import Any

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

HOURS_IN_DAY = 24

HOUR_LABELS = [f"{hour:02d}:00" for hour in range(HOURS_IN_DAY)]

# Normalised availability shapes for the weather-driven units, 0 to 1 against
# each unit's nameplate capacity. Solar is the familiar bell; wind carries a
# mild diurnal signal but is mostly flat, which is exactly why it ends up
# setting the margin overnight far more often than solar ever does.
SOLAR_SHAPE = [
    0.00, 0.00, 0.00, 0.00, 0.00, 0.02, 0.10, 0.24, 0.44, 0.64, 0.82, 0.94,
    1.00, 0.98, 0.88, 0.72, 0.52, 0.32, 0.14, 0.03, 0.00, 0.00, 0.00, 0.00,
]

WIND_SHAPE = [
    0.62, 0.64, 0.66, 0.67, 0.66, 0.63, 0.58, 0.52, 0.47, 0.44, 0.42, 0.41,
    0.42, 0.44, 0.47, 0.51, 0.55, 0.58, 0.61, 0.63, 0.64, 0.64, 0.63, 0.62,
]

HYDRO_SHAPE = [1.0] * HOURS_IN_DAY

AVAILABILITY_SHAPES = {
    "solar": SOLAR_SHAPE,
    "wind": WIND_SHAPE,
    "hydro": HYDRO_SHAPE,
}

# Electricity demand across the day as a fraction of the system peak. The
# evening ramp is what forces the dirtiest units on, and it is the reason the
# marginal and average curves diverge most sharply between 17:00 and 20:00.
DEMAND_SHAPE = [
    0.62, 0.58, 0.56, 0.55, 0.56, 0.60, 0.68, 0.78, 0.84, 0.85, 0.84, 0.83,
    0.82, 0.81, 0.81, 0.83, 0.88, 0.95, 1.00, 0.98, 0.92, 0.84, 0.75, 0.68,
]

# Dispatch stacks. ``capacity`` is nameplate as a fraction of system peak
# demand, so a stack summing above 1.0 has reserve margin. ``intensity`` is
# lifecycle gCO2/kWh - construction included, which is why nothing is exactly
# zero. ``variable`` names the availability shape, or None for firm plant.
# ``must_run`` marks units that generate whenever available and are therefore
# never on the margin except when they are being curtailed.
#
# Dispatchable units are listed in merit order (cheapest first), which is the
# order the system actually calls them in. It correlates with emission rate
# but is not identical to it, and where the two disagree the merit order wins
# - that is the whole point of modelling dispatch rather than sorting by
# carbon.
GENERATION_STACKS = {
    "Solar-heavy": [
        {"name": "Solar PV", "capacity": 0.70, "intensity": 41.0,
         "variable": "solar", "must_run": True},
        {"name": "Wind", "capacity": 0.14, "intensity": 11.0,
         "variable": "wind", "must_run": True},
        {"name": "Hydro", "capacity": 0.08, "intensity": 24.0,
         "variable": "hydro", "must_run": True},
        {"name": "CCGT", "capacity": 0.62, "intensity": 380.0,
         "variable": None, "must_run": False},
        {"name": "OCGT peaker", "capacity": 0.34, "intensity": 560.0,
         "variable": None, "must_run": False},
    ],
    "Wind-heavy": [
        {"name": "Wind", "capacity": 0.78, "intensity": 11.0,
         "variable": "wind", "must_run": True},
        {"name": "Solar PV", "capacity": 0.16, "intensity": 41.0,
         "variable": "solar", "must_run": True},
        {"name": "Hydro", "capacity": 0.10, "intensity": 24.0,
         "variable": "hydro", "must_run": True},
        {"name": "CCGT", "capacity": 0.58, "intensity": 380.0,
         "variable": None, "must_run": False},
        {"name": "OCGT peaker", "capacity": 0.30, "intensity": 560.0,
         "variable": None, "must_run": False},
    ],
    "Coal-heavy": [
        {"name": "Wind", "capacity": 0.10, "intensity": 11.0,
         "variable": "wind", "must_run": True},
        {"name": "Solar PV", "capacity": 0.08, "intensity": 41.0,
         "variable": "solar", "must_run": True},
        {"name": "Coal", "capacity": 0.82, "intensity": 900.0,
         "variable": None, "must_run": False},
        {"name": "CCGT", "capacity": 0.30, "intensity": 380.0,
         "variable": None, "must_run": False},
        {"name": "OCGT peaker", "capacity": 0.20, "intensity": 560.0,
         "variable": None, "must_run": False},
    ],
    "Gas-balanced": [
        {"name": "Wind", "capacity": 0.24, "intensity": 11.0,
         "variable": "wind", "must_run": True},
        {"name": "Solar PV", "capacity": 0.20, "intensity": 41.0,
         "variable": "solar", "must_run": True},
        {"name": "Nuclear", "capacity": 0.15, "intensity": 12.0,
         "variable": None, "must_run": True},
        {"name": "CCGT", "capacity": 0.70, "intensity": 380.0,
         "variable": None, "must_run": False},
        {"name": "OCGT peaker", "capacity": 0.32, "intensity": 560.0,
         "variable": None, "must_run": False},
    ],
    "Nuclear baseload": [
        {"name": "Nuclear", "capacity": 0.42, "intensity": 12.0,
         "variable": None, "must_run": True},
        {"name": "Wind", "capacity": 0.16, "intensity": 11.0,
         "variable": "wind", "must_run": True},
        {"name": "Solar PV", "capacity": 0.10, "intensity": 41.0,
         "variable": "solar", "must_run": True},
        {"name": "CCGT", "capacity": 0.44, "intensity": 380.0,
         "variable": None, "must_run": False},
        {"name": "OCGT peaker", "capacity": 0.22, "intensity": 560.0,
         "variable": None, "must_run": False},
    ],
    "Hydro-dominant": [
        {"name": "Hydro", "capacity": 0.86, "intensity": 24.0,
         "variable": "hydro", "must_run": True},
        {"name": "Wind", "capacity": 0.12, "intensity": 11.0,
         "variable": "wind", "must_run": True},
        {"name": "CCGT", "capacity": 0.34, "intensity": 380.0,
         "variable": None, "must_run": False},
        {"name": "OCGT peaker", "capacity": 0.16, "intensity": 560.0,
         "variable": None, "must_run": False},
    ],
}

DEFAULT_STACK = "Gas-balanced"

# Average and marginal factors for material flows, kgCO2e per kg. The average
# blends primary and secondary supply; the marginal is what one more unit of
# recycling actually displaces, which is primary production. The ratio is the
# interesting column and it is why recycling is systematically undersold by
# average-factor tools.
MATERIAL_FACTORS = {
    "Aluminium": {
        "average": 8.2, "marginal": 16.1,
        "note": "Secondary aluminium needs about 5% of the energy of primary. "
                "One more recycled can displaces smelting, not the blend.",
    },
    "Steel": {
        "average": 1.9, "marginal": 2.5,
        "note": "Scrap already dominates in electric arc routes, so the gap "
                "is real but far smaller than aluminium's.",
    },
    "Glass": {
        "average": 0.9, "marginal": 1.1,
        "note": "Cullet saves furnace energy. Modest gap, and the transport "
                "leg can eat a noticeable share of it.",
    },
    "Paper / card": {
        "average": 0.85, "marginal": 1.3,
        "note": "Displaces virgin pulp. Fibre degrades each cycle, so the "
                "marginal benefit falls with the number of prior loops.",
    },
    "PET plastic": {
        "average": 2.4, "marginal": 3.1,
        "note": "Only worth the gap where the recyclate genuinely re-enters "
                "bottle production rather than being downcycled.",
    },
    "HDPE plastic": {
        "average": 1.9, "marginal": 2.5,
        "note": "Similar story to PET with a slightly lower virgin factor.",
    },
    "Copper": {
        "average": 3.8, "marginal": 6.4,
        "note": "Primary copper grades are falling, so the marginal figure "
                "is drifting upwards over time.",
    },
    "Textiles (cotton)": {
        "average": 15.0, "marginal": 19.5,
        "note": "Reuse displaces new garment production, which is where "
                "nearly all of the footprint sits.",
    },
}

# Food is the other place the gap bites. Short-run marginal response to one
# person's demand change is smaller than the average factor because herds and
# plantings adjust slowly; the long-run response is closer to average and for
# land-intensive products can exceed it once land use change is included.
FOOD_FACTORS = {
    "Beef": {"average": 27.0, "short_run": 19.0, "long_run": 31.0},
    "Lamb": {"average": 24.5, "short_run": 17.5, "long_run": 27.0},
    "Pork": {"average": 7.2, "short_run": 5.8, "long_run": 7.6},
    "Chicken": {"average": 6.1, "short_run": 5.0, "long_run": 6.4},
    "Dairy milk": {"average": 3.2, "short_run": 2.4, "long_run": 3.4},
    "Cheese": {"average": 13.5, "short_run": 10.2, "long_run": 14.2},
    "Eggs": {"average": 4.5, "short_run": 3.8, "long_run": 4.7},
    "Rice": {"average": 4.0, "short_run": 3.5, "long_run": 4.2},
    "Legumes": {"average": 0.9, "short_run": 0.8, "long_run": 0.9},
    "Vegetables": {"average": 0.5, "short_run": 0.45, "long_run": 0.5},
}

# Annual fractional decline in grid intensity under each trajectory. Applied
# to long-lived assets, because a heat pump bought today spends most of its
# life on a grid that does not exist yet.
DECARBONISATION_RATES = {
    "Stalled": 0.005,
    "Slow": 0.020,
    "Central": 0.045,
    "Rapid": 0.075,
}

DEFAULT_DECARBONISATION = "Central"

# Two accountings are worth showing separately only when they actually differ.
# Below this relative gap the divergence is noise and flagging it would train
# users to ignore the flag.
DIVERGENCE_THRESHOLD = 0.15

DEFAULT_DAYS_PER_YEAR = 365


def _as_float(value: Any, default: float = 0.0) -> float:
    """Coerce to float, falling back rather than raising on junk input."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float(default)
    if number != number or number in (float("inf"), float("-inf")):
        return float(default)
    return number


def _non_negative(value: Any, default: float = 0.0) -> float:
    return max(0.0, _as_float(value, default))


def list_stacks() -> list[str]:
    """Names of the built-in generation stacks."""
    return sorted(GENERATION_STACKS.keys())


def get_stack(name: str | None = None) -> list[dict[str, Any]]:
    """Return a copy of a generation stack, defaulting to the balanced one."""
    key = name if name in GENERATION_STACKS else DEFAULT_STACK
    return [dict(unit) for unit in GENERATION_STACKS[key]]


def clean_stack(stack: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Validate a user-supplied stack, dropping units that make no sense.

    A unit with no capacity contributes nothing and a negative emission rate
    is not a thing, so both are rejected rather than silently coerced - a
    stack that quietly loses half its plant would produce a plausible curve
    for the wrong system.
    """
    cleaned = []
    for unit in stack or []:
        if not isinstance(unit, dict):
            continue
        name = str(unit.get("name") or "").strip()
        if not name:
            continue
        capacity = _non_negative(unit.get("capacity"), 0.0)
        intensity = _as_float(unit.get("intensity"), 0.0)
        if capacity <= 0 or intensity < 0:
            continue
        variable = unit.get("variable")
        if variable not in AVAILABILITY_SHAPES:
            variable = None
        cleaned.append({
            "name": name,
            "capacity": capacity,
            "intensity": intensity,
            "variable": variable,
            "must_run": bool(unit.get("must_run")),
        })
    return cleaned


def clean_demand_shape(shape: list[float] | None) -> list[float]:
    """Coerce a 24-value demand shape, falling back to the built-in one."""
    values = list(shape or [])
    if len(values) != HOURS_IN_DAY:
        return list(DEMAND_SHAPE)
    cleaned = [_non_negative(value, 0.0) for value in values]
    if sum(cleaned) <= 0:
        return list(DEMAND_SHAPE)
    return cleaned


def availability(unit: dict[str, Any], hour: int) -> float:
    """Fraction of a unit's capacity available in a given hour."""
    hour = int(hour) % HOURS_IN_DAY
    shape_name = unit.get("variable")
    if not shape_name:
        return 1.0
    shape = AVAILABILITY_SHAPES.get(shape_name)
    if not shape:
        return 1.0
    return shape[hour]


def dispatch_hour(stack: list[dict[str, Any]] | None, hour: int, demand: float | None = None) -> dict[str, Any]:
    """Dispatch one hour and report what ran and what set the margin.

    Returns a dict with the per-unit generation, the average intensity of
    everything dispatched, the marginal intensity, the unit on the margin,
    and whether must-run output is being curtailed.

    The curtailment case is the one average-factor tools cannot see. When
    weather-driven output already exceeds demand, an extra kilowatt-hour is
    served by generation that was about to be thrown away, so its marginal
    intensity is that unit's own rate rather than any thermal plant's.
    """
    stack = clean_stack(stack) or get_stack()
    hour = int(hour) % HOURS_IN_DAY
    if demand is None:
        demand = DEMAND_SHAPE[hour]
    demand = _non_negative(demand, 0.0)

    must_run = [unit for unit in stack if unit["must_run"]]
    dispatchable = [unit for unit in stack if not unit["must_run"]]

    # Seed every unit at zero so the generation dict always describes the
    # whole stack. A curtailed hour that simply omitted the thermal plant
    # would force every caller to guess whether a missing key meant "did not
    # run" or "not in this stack".
    generation = {unit["name"]: 0.0 for unit in stack}
    available_must_run = 0.0
    for unit in must_run:
        output = unit["capacity"] * availability(unit, hour)
        generation[unit["name"]] = output
        available_must_run += output

    curtailed = 0.0
    marginal_unit = None
    marginal_intensity = 0.0
    unserved = 0.0

    if demand <= 0:
        # No demand means nothing is dispatched and the margin is undefined.
        # Everything available is curtailed.
        for unit in must_run:
            generation[unit["name"]] = 0.0
        curtailed = available_must_run
        marginal_candidates = sorted(must_run, key=lambda item: item["intensity"])
        if marginal_candidates:
            marginal_unit = marginal_candidates[0]["name"]
            marginal_intensity = marginal_candidates[0]["intensity"]
        return {
            "hour": hour,
            "demand": 0.0,
            "generation": generation,
            "average_intensity": 0.0,
            "marginal_intensity": marginal_intensity,
            "marginal_unit": marginal_unit,
            "curtailed": True,
            "curtailed_energy": curtailed,
            "unserved": 0.0,
            "must_run_available": available_must_run,
        }

    if available_must_run >= demand:
        # Surplus renewables. Scale must-run output down proportionally to
        # meet demand and record the spill. The marginal unit is whichever
        # must-run plant is being curtailed - it is the one that would soak
        # up an extra kilowatt-hour at no additional cost to the system.
        scale = demand / available_must_run if available_must_run > 0 else 0.0
        for unit in must_run:
            generation[unit["name"]] *= scale
        curtailed = available_must_run - demand
        curtailable = [
            unit for unit in must_run
            if unit["capacity"] * availability(unit, hour) > 0
        ]
        # Highest-intensity must-run unit is curtailed first, so that is what
        # an extra kilowatt-hour brings back.
        curtailable.sort(key=lambda item: item["intensity"], reverse=True)
        if curtailable:
            marginal_unit = curtailable[0]["name"]
            marginal_intensity = curtailable[0]["intensity"]
        dispatched_energy = demand
    else:
        shortfall = demand - available_must_run
        for unit in dispatchable:
            take = min(unit["capacity"], shortfall)
            generation[unit["name"]] = take
            if take > 0:
                marginal_unit = unit["name"]
                marginal_intensity = unit["intensity"]
            shortfall -= take
            if shortfall <= 1e-12:
                shortfall = 0.0
                break
        for unit in dispatchable:
            generation.setdefault(unit["name"], 0.0)
        if shortfall > 1e-12:
            # Demand above total capacity. Report it rather than pretending
            # the system coped; the dirtiest available unit stays on margin.
            unserved = shortfall
            if dispatchable:
                marginal_unit = dispatchable[-1]["name"]
                marginal_intensity = dispatchable[-1]["intensity"]
        dispatched_energy = demand - unserved

    total_emissions = sum(
        generation.get(unit["name"], 0.0) * unit["intensity"] for unit in stack
    )
    average_intensity = (
        total_emissions / dispatched_energy if dispatched_energy > 0 else 0.0
    )

    return {
        "hour": hour,
        "demand": demand,
        "generation": generation,
        "average_intensity": average_intensity,
        "marginal_intensity": marginal_intensity,
        "marginal_unit": marginal_unit,
        "curtailed": curtailed > 1e-12,
        "curtailed_energy": curtailed,
        "unserved": unserved,
        "must_run_available": available_must_run,
    }


def dispatch_day(stack_name: str | None = None, stack: list[dict[str, Any]] | None = None, demand_shape: list[float] | None = None) -> list[dict[str, Any]]:
    """Dispatch all 24 hours and return the per-hour results."""
    units = clean_stack(stack) if stack else get_stack(stack_name)
    if not units:
        units = get_stack(stack_name)
    shape = clean_demand_shape(demand_shape)
    return [
        dispatch_hour(units, hour, shape[hour]) for hour in range(HOURS_IN_DAY)
    ]


def average_curve(stack_name: str | None = None, stack: list[dict[str, Any]] | None = None, demand_shape: list[float] | None = None) -> list[float]:
    """24-hour average (attributional) intensity curve in gCO2/kWh."""
    return [
        result["average_intensity"]
        for result in dispatch_day(stack_name, stack, demand_shape)
    ]


def marginal_curve(stack_name: str | None = None, stack: list[dict[str, Any]] | None = None, demand_shape: list[float] | None = None) -> list[float]:
    """24-hour marginal (consequential) intensity curve in gCO2/kWh."""
    return [
        result["marginal_intensity"]
        for result in dispatch_day(stack_name, stack, demand_shape)
    ]


def curve_divergence(stack_name: str | None = None, stack: list[dict[str, Any]] | None = None, demand_shape: list[float] | None = None) -> list[dict[str, Any]]:
    """Per-hour gap between the marginal and average curves.

    Positive means the marginal factor is higher - the hour looks cleaner
    than it behaves. Negative means the opposite, which is the curtailment
    case and the one worth acting on.
    """
    day = dispatch_day(stack_name, stack, demand_shape)
    rows = []
    for result in day:
        average = result["average_intensity"]
        marginal = result["marginal_intensity"]
        gap = marginal - average
        relative = gap / average if average > 0 else 0.0
        rows.append({
            "hour": result["hour"],
            "label": HOUR_LABELS[result["hour"]],
            "average": average,
            "marginal": marginal,
            "gap": gap,
            "relative_gap": relative,
            "marginal_unit": result["marginal_unit"],
            "curtailed": result["curtailed"],
            "material": abs(relative) >= DIVERGENCE_THRESHOLD,
        })
    return rows


def curtailment_hours(stack_name: str | None = None, stack: list[dict[str, Any]] | None = None, demand_shape: list[float] | None = None) -> list[int]:
    """Hours where must-run output exceeds demand.

    These are the hours where extra consumption is close to free, and the
    hours the average-factor scheduler is least able to identify.
    """
    return [
        result["hour"]
        for result in dispatch_day(stack_name, stack, demand_shape)
        if result["curtailed"]
    ]


def rank_hours(curve: list[float] | None, cleanest_first: bool = True) -> list[tuple[int, float]]:
    """Rank hours by a curve, returning (hour, value) pairs."""
    values = list(curve or [])
    if len(values) != HOURS_IN_DAY:
        raise ValueError("A curve must have exactly 24 values.")
    pairs = [(hour, _as_float(values[hour], 0.0)) for hour in range(HOURS_IN_DAY)]
    pairs.sort(key=lambda item: (item[1], item[0]), reverse=not cleanest_first)
    return pairs


def ranking_changes(average: list[float], marginal: list[float], top_n: int = 6) -> list[dict[str, Any]]:
    """Hours whose rank differs between the two accountings.

    The useful output of this module is not the numbers, it is the hours that
    swap places - those are the ones where following the average curve sends
    a user to the wrong hour.
    """
    top_n = max(1, int(top_n))
    average_rank = {
        hour: position
        for position, (hour, _) in enumerate(rank_hours(average))
    }
    marginal_rank = {
        hour: position
        for position, (hour, _) in enumerate(rank_hours(marginal))
    }
    changes = []
    for hour in range(HOURS_IN_DAY):
        before = average_rank[hour]
        after = marginal_rank[hour]
        if before == after:
            continue
        changes.append({
            "hour": hour,
            "label": HOUR_LABELS[hour],
            "average_rank": before + 1,
            "marginal_rank": after + 1,
            "movement": before - after,
            "direction": "better" if after < before else "worse",
        })
    changes.sort(key=lambda item: abs(item["movement"]), reverse=True)
    return changes[:top_n]


def attributional_delta(kwh_by_hour: list[float] | None, curve: list[float] | None) -> float:
    """Emissions change under average factors, in kgCO2e.

    ``kwh_by_hour`` is a 24-length list of signed energy changes: positive
    for load added in that hour, negative for load removed.
    """
    energy = list(kwh_by_hour or [])
    values = list(curve or [])
    if len(energy) != HOURS_IN_DAY or len(values) != HOURS_IN_DAY:
        raise ValueError("Both energy and curve must have exactly 24 values.")
    grams = sum(
        _as_float(energy[hour], 0.0) * _as_float(values[hour], 0.0)
        for hour in range(HOURS_IN_DAY)
    )
    return grams / 1000.0


def consequential_delta(kwh_by_hour: list[float] | None, curve: list[float] | None) -> float:
    """Emissions change under marginal factors, in kgCO2e.

    Identical arithmetic to the attributional version - the difference is
    entirely in which curve is passed. Kept as a separate name because the
    two answers mean different things and calling sites should have to say
    which one they want.
    """
    return attributional_delta(kwh_by_hour, curve)


def shift_load(kwh: float, from_hour: int, to_hour: int, duration_hours: int = 1) -> list[float]:
    """Build a signed 24-hour energy vector for moving a load.

    Energy is spread evenly across the run duration, which is what a delay
    timer actually does.
    """
    kwh = _non_negative(kwh, 0.0)
    duration = max(1, int(duration_hours))
    vector = [0.0] * HOURS_IN_DAY
    per_hour = kwh / duration if duration else 0.0
    for step in range(duration):
        vector[(int(from_hour) + step) % HOURS_IN_DAY] -= per_hour
        vector[(int(to_hour) + step) % HOURS_IN_DAY] += per_hour
    return vector


def compare_shift(kwh: float, from_hour: int, to_hour: int, duration_hours: int = 1,
                  stack_name: str | None = None, stack: list[dict[str, Any]] | None = None,
                  demand_shape: list[float] | None = None) -> dict[str, Any]:
    """Score a load shift under both accountings and report the divergence."""
    vector = shift_load(kwh, from_hour, to_hour, duration_hours)
    average = average_curve(stack_name, stack, demand_shape)
    marginal = marginal_curve(stack_name, stack, demand_shape)

    attributional = attributional_delta(vector, average)
    consequential = consequential_delta(vector, marginal)

    return describe_divergence(
        attributional,
        consequential,
        label=f"Shift {kwh:g} kWh from {HOUR_LABELS[int(from_hour) % HOURS_IN_DAY]} "
              f"to {HOUR_LABELS[int(to_hour) % HOURS_IN_DAY]}",
    )


def describe_divergence(attributional: float, consequential: float, label: str = "") -> dict[str, Any]:
    """Package the two answers with a plain reading of their disagreement."""
    attributional = _as_float(attributional, 0.0)
    consequential = _as_float(consequential, 0.0)
    gap = consequential - attributional
    denominator = abs(attributional)
    relative = gap / denominator if denominator > 1e-12 else 0.0
    material = abs(relative) >= DIVERGENCE_THRESHOLD or (
        denominator <= 1e-12 and abs(gap) > 1e-9
    )

    if attributional < 0 and consequential > 0:
        reading = (
            "Your reported footprint falls but actual emissions rise. The "
            "action looks good on paper and is not."
        )
    elif attributional > 0 and consequential < 0:
        reading = (
            "Your reported footprint rises but actual emissions fall. The "
            "action is worth doing and the report will not thank you for it."
        )
    elif not material:
        reading = (
            "Both accountings agree within the noise. The reported saving is "
            "a fair estimate of the real one."
        )
    elif abs(consequential) > abs(attributional):
        reading = (
            "The real effect is larger than the reported one. Average factors "
            "understate this action."
        )
    else:
        reading = (
            "The real effect is smaller than the reported one. Average factors "
            "flatter this action."
        )

    return {
        "label": label,
        "attributional_kg": attributional,
        "consequential_kg": consequential,
        "gap_kg": gap,
        "relative_gap": relative,
        "material": material,
        "sign_flip": (attributional < 0) != (consequential < 0),
        "reading": reading,
    }


def long_run_factor(base_intensity: float, years: int, trajectory: str = DEFAULT_DECARBONISATION,
                    rate: float | None = None) -> float:
    """Mean intensity over an asset's life under a decarbonisation path.

    A heat pump bought today is routinely scored against today's grid, which
    is the grid it will spend the least of its life on. This returns the
    average intensity across the whole period, which is the number that
    belongs in a lifetime calculation.
    """
    base = _non_negative(base_intensity, 0.0)
    years = max(1, int(years))
    if rate is None:
        rate = DECARBONISATION_RATES.get(trajectory, DECARBONISATION_RATES[DEFAULT_DECARBONISATION])
    rate = min(0.99, max(0.0, _as_float(rate, 0.0)))

    total = 0.0
    for year in range(years):
        total += base * ((1.0 - rate) ** year)
    return total / years


def lifetime_comparison(annual_kwh: float, lifetime_years: int, base_intensity: float,
                        trajectory: str = DEFAULT_DECARBONISATION, embodied_kg: float = 0.0) -> dict[str, Any]:
    """Score a long-lived electrical asset today's way and the honest way."""
    annual_kwh = _non_negative(annual_kwh, 0.0)
    lifetime_years = max(1, int(lifetime_years))
    base = _non_negative(base_intensity, 0.0)
    embodied = _non_negative(embodied_kg, 0.0)

    static_intensity = base
    declining_intensity = long_run_factor(base, lifetime_years, trajectory)

    static_kg = annual_kwh * lifetime_years * static_intensity / 1000.0
    declining_kg = annual_kwh * lifetime_years * declining_intensity / 1000.0

    return {
        "annual_kwh": annual_kwh,
        "lifetime_years": lifetime_years,
        "trajectory": trajectory,
        "static_intensity": static_intensity,
        "lifetime_mean_intensity": declining_intensity,
        "static_lifetime_kg": static_kg + embodied,
        "declining_lifetime_kg": declining_kg + embodied,
        "embodied_kg": embodied,
        "overstatement_kg": static_kg - declining_kg,
        "overstatement_pct": (
            (static_kg - declining_kg) / static_kg * 100.0 if static_kg > 0 else 0.0
        ),
    }


def list_materials() -> list[str]:
    """Materials with tabulated average and marginal factors."""
    return sorted(MATERIAL_FACTORS.keys())


def material_comparison(material: str, kg: float) -> dict[str, Any]:
    """Score recycling or reusing a mass of material under both accountings."""
    if material not in MATERIAL_FACTORS:
        raise KeyError(
            f"No marginal factor for '{material}'. Add it to MATERIAL_FACTORS "
            "rather than falling back to an average - a silent fallback here "
            "would report the exact error this module exists to correct."
        )
    mass = _non_negative(kg, 0.0)
    entry = MATERIAL_FACTORS[material]
    attributional = -mass * entry["average"]
    consequential = -mass * entry["marginal"]
    result = describe_divergence(
        attributional, consequential, label=f"Recycle {mass:g} kg of {material}"
    )
    result.update({
        "material": material,
        "kg": mass,
        "average_factor": entry["average"],
        "marginal_factor": entry["marginal"],
        "ratio": entry["marginal"] / entry["average"] if entry["average"] else 0.0,
        "note": entry["note"],
    })
    return result


def list_foods() -> list[str]:
    """Foods with tabulated short-run and long-run marginal factors."""
    return sorted(FOOD_FACTORS.keys())


def food_comparison(food: str, kg: float, horizon: str = "long_run") -> dict[str, Any]:
    """Score a dietary change under average and marginal factors."""
    if food not in FOOD_FACTORS:
        raise KeyError(f"No marginal factor for '{food}'.")
    if horizon not in ("short_run", "long_run"):
        raise ValueError("horizon must be 'short_run' or 'long_run'.")
    mass = _non_negative(kg, 0.0)
    entry = FOOD_FACTORS[food]
    attributional = -mass * entry["average"]
    consequential = -mass * entry[horizon]
    result = describe_divergence(
        attributional, consequential,
        label=f"Avoid {mass:g} kg of {food} ({horizon.replace('_', ' ')})",
    )
    result.update({
        "food": food,
        "kg": mass,
        "horizon": horizon,
        "average_factor": entry["average"],
        "marginal_factor": entry[horizon],
    })
    return result


def rank_actions(actions: list[dict[str, Any]] | None, key: str = "consequential_kg") -> list[dict[str, Any]]:
    """Rank scored actions by saving, largest first."""
    if key not in ("attributional_kg", "consequential_kg"):
        raise ValueError("key must be 'attributional_kg' or 'consequential_kg'.")
    scored = [action for action in actions or [] if isinstance(action, dict)]
    return sorted(scored, key=lambda item: _as_float(item.get(key), 0.0))


def rank_movement(actions: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Actions whose position changes between the two accountings.

    This is the headline output for a set of options. Two numbers moving is
    unremarkable; two options swapping order means the average-factor advice
    was pointing at the wrong one.
    """
    by_attributional = rank_actions(actions, "attributional_kg")
    by_consequential = rank_actions(actions, "consequential_kg")

    positions_a = {
        id(action): index for index, action in enumerate(by_attributional)
    }
    positions_c = {
        id(action): index for index, action in enumerate(by_consequential)
    }

    movements = []
    for action in by_attributional:
        before = positions_a[id(action)]
        after = positions_c[id(action)]
        if before == after:
            continue
        movements.append({
            "label": action.get("label", ""),
            "attributional_rank": before + 1,
            "consequential_rank": after + 1,
            "movement": before - after,
            "direction": "up" if after < before else "down",
        })
    movements.sort(key=lambda item: abs(item["movement"]), reverse=True)
    return movements


def annualise(daily_kg: float, days: int = DEFAULT_DAYS_PER_YEAR) -> float:
    """Scale a daily figure to a year."""
    return _as_float(daily_kg, 0.0) * max(0, int(days))


def get_marginal_tips(divergences: list[dict[str, Any]] | None, limit: int = 6) -> list[str]:
    """Plain-language guidance drawn from a set of scored comparisons."""
    tips = []
    rows = [row for row in divergences or [] if isinstance(row, dict)]

    flips = [row for row in rows if row.get("sign_flip")]
    if flips:
        tips.append(
            "At least one action changes sign between the two accountings - "
            "it reduces your reported footprint while increasing real "
            "emissions, or the reverse. Those are worth looking at first."
        )

    understated = [
        row for row in rows
        if row.get("material")
        and abs(_as_float(row.get("consequential_kg"), 0.0))
        > abs(_as_float(row.get("attributional_kg"), 0.0))
    ]
    if understated:
        tips.append(
            "Some actions do more than your footprint report will show. "
            "Recycling is the usual example: the report credits you with an "
            "average factor while you are actually displacing primary "
            "production."
        )

    flattered = [
        row for row in rows
        if row.get("material")
        and abs(_as_float(row.get("consequential_kg"), 0.0))
        < abs(_as_float(row.get("attributional_kg"), 0.0))
    ]
    if flattered:
        tips.append(
            "Some actions do less than reported. That is not a reason to "
            "skip them, but it is a reason not to count on the headline "
            "number when choosing between options."
        )

    if not rows:
        tips.append(
            "Add an action to see how the two accountings compare. The "
            "interesting cases are the ones where they disagree."
        )

    tips.append(
        "Use average factors to report what you emitted and marginal factors "
        "to decide what to do next. They are both correct and they answer "
        "different questions."
    )
    tips.append(
        "Marginal factors move faster than average ones. A grid that adds "
        "storage changes its margin long before it changes its mix."
    )

    return tips[: max(0, int(limit))]


def _get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_marginal_emissions_db() -> bool:
    """Create the comparison table if it does not exist yet."""
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS marginal_comparisons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                comparison_name TEXT NOT NULL,
                stack_name TEXT NOT NULL,
                attributional_kg REAL NOT NULL,
                consequential_kg REAL NOT NULL,
                relative_gap REAL,
                sign_flip INTEGER DEFAULT 0,
                detail_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Marginal emissions init error: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def save_comparison(user_id: int, comparison_name: str | None, comparison: dict[str, Any], stack_name: str | None = None) -> int | None:
    """Persist a scored comparison. Returns the new row id or None."""
    init_marginal_emissions_db()
    conn = None
    try:
        conn = _get_conn()
        cursor = conn.execute(
            """
            INSERT INTO marginal_comparisons (
                user_id, comparison_name, stack_name, attributional_kg,
                consequential_kg, relative_gap, sign_flip, detail_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                (comparison_name or "Comparison").strip() or "Comparison",
                stack_name or DEFAULT_STACK,
                _as_float(comparison.get("attributional_kg"), 0.0),
                _as_float(comparison.get("consequential_kg"), 0.0),
                _as_float(comparison.get("relative_gap"), 0.0),
                1 if comparison.get("sign_flip") else 0,
                json.dumps(comparison, default=str),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as exc:
        logger.error("Unable to save marginal comparison: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def get_comparisons(user_id: int, limit: int = 25) -> list[dict[str, Any]]:
    """Return a user's saved comparisons, newest first."""
    init_marginal_emissions_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, comparison_name, stack_name, attributional_kg,
                   consequential_kg, relative_gap, sign_flip, detail_json,
                   created_at
            FROM marginal_comparisons
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT ?
            """,
            (user_id, int(limit)),
        ).fetchall()

        comparisons = []
        for row in rows:
            record = dict(row)
            try:
                record["detail"] = json.loads(record.pop("detail_json") or "{}")
            except (TypeError, ValueError):
                record["detail"] = {}
            record["sign_flip"] = bool(record.get("sign_flip"))
            comparisons.append(record)
        return comparisons
    except sqlite3.Error as exc:
        logger.error("Unable to load marginal comparisons: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def delete_comparison(comparison_id: int) -> bool:
    """Delete a saved comparison."""
    init_marginal_emissions_db()
    conn = None
    try:
        conn = _get_conn()
        cursor = conn.execute(
            "DELETE FROM marginal_comparisons WHERE id = ?", (comparison_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as exc:
        logger.error("Unable to delete marginal comparison: %s", exc)
        return False
    finally:
        if conn:
            conn.close()
