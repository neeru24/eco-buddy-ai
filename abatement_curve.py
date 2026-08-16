"""Marginal abatement cost curve for a household with a finite budget.

``lifestyle_optimizer.py`` ranks actions by how much carbon they save. That is
the right ranking for a household with unlimited money and no ranking at all for
a household without it. A heat pump and a draught-proofing kit are not
comparable on carbon alone: one saves more and costs sixty times as much.

Ranking by cost per tonne alone is wrong in three ways
-------------------------------------------------------
**Capital is lumpy and budgets are finite.** A measure at 180 per tonne costing
9,000 and one at 220 per tonne costing 400 are not ordered by cost-effectiveness
when the household has 1,000 to spend. Greedy selection down a cost curve is a
known failure on the knapsack problem, and it fails hardest exactly where the
budget is tight - that is, for the households the advice matters most to.

**Measures interact.** Insulate a house and the heat pump installed afterwards
saves less carbon, because there is less heat to supply. Evaluating each measure
against the untouched baseline overstates any package of them, and the
overstatement grows with the number selected. Measures are applied against the
*remaining* base here, the way retrofit assessment does it.

**Lifetime and timing.** A measure saving 200 kg a year for 25 years is not
comparable with one saving 200 kg for 5. Annualising capital over a measure's
life needs a discount rate, and the rate reorders the curve - a household rate
of 10% and a social rate of 3% produce visibly different advice, which is why it
is a parameter rather than a constant.

Negative-cost measures
----------------------
Draught-proofing, thermostat setback, tyre pressure. They pay for themselves and
sit to the left of the axis. They are also, notoriously, the ones that do not
get adopted despite being free, so they are flagged with that gap stated rather
than presented as unambiguously first. A curve that ignores it is presenting an
economic model as a behavioural one.

The output that matters
-----------------------
Not the curve. The answer to "I have 2,000 - what should I do?", and that answer
is not the top of the curve read downwards until the money runs out. The
selection here is exact: measures are grouped by the activity they act on, every
subset of each group is enumerated with its interactions and exclusivity
resolved, and a multiple-choice knapsack over those subsets picks the optimum.
Interactions never cross groups, so this is exhaustive rather than heuristic.

Self-contained: standard library only, SQLite tables created lazily, no shared
files modified.
"""

import os
import json
import math
import sqlite3
import logging
from itertools import combinations
from typing import Any

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

DEFAULT_DISCOUNT_RATE = 0.05
DISCOUNT_RANGE = (0.03, 0.05, 0.08, 0.12)
DEFAULT_BUDGET = 2000.0

# Capital is bucketed for the exact selection. Every capital cost in the
# catalogue is a multiple of this, so the bucketing loses nothing - a coarser
# grid would round two affordable measures into one unaffordable pair, which is
# exactly the failure the exact selection exists to avoid.
BUDGET_GRANULARITY = 10.0

# The annual emissions each activity starts from. Interactions are computed
# against these, because a saving only means something as a share of what was
# there to begin with.
ACTIVITY_BASE_KG = {
    "home.gas.space_heating": 2600.0,
    "home.electricity": 1100.0,
    "travel.car": 2400.0,
    "travel.flight": 1800.0,
    "food": 1600.0,
}

# ---------------------------------------------------------------------------
# The measure catalogue
#
# ``capital`` is up-front cost, ``running_change`` is the annual change in
# running costs (negative saves money), ``lifetime`` is in years, and
# ``activity`` decides which measures interact with which. Behavioural measures
# are included at zero capital so that the curve is not implicitly a shopping
# list - a curve made only of things you buy would rank buying above not doing.
# ---------------------------------------------------------------------------
MEASURES = {
    "thermostat_setback": {
        "label": "Turn the thermostat down one degree",
        "capital": 0.0, "saving_kg": 300.0, "running_change": -80.0,
        "lifetime": 5.0, "activity": "home.gas.space_heating",
        "behavioural": True, "exclusive_group": None,
        "note": "Free, immediate and reversible at any moment, which is both "
                "its strength and the reason it is rarely sustained.",
    },
    "draught_proofing": {
        "label": "Draught-proofing",
        "capital": 150.0, "saving_kg": 250.0, "running_change": -60.0,
        "lifetime": 10.0, "activity": "home.gas.space_heating",
        "behavioural": False, "exclusive_group": None,
        "note": "The cheapest physical measure in the table and among the "
                "least adopted.",
    },
    "loft_insulation": {
        "label": "Loft insulation",
        "capital": 600.0, "saving_kg": 450.0, "running_change": -120.0,
        "lifetime": 40.0, "activity": "home.gas.space_heating",
        "behavioural": False, "exclusive_group": None,
        "note": "Long-lived and cheap. Doing it before a heat pump lets the "
                "heat pump be smaller, which the interaction handling shows "
                "as a reduced saving rather than a reduced price.",
    },
    "cavity_wall_insulation": {
        "label": "Cavity wall insulation",
        "capital": 1200.0, "saving_kg": 500.0, "running_change": -140.0,
        "lifetime": 40.0, "activity": "home.gas.space_heating",
        "behavioural": False, "exclusive_group": None,
        "note": "Only available on some housing stock, which is a constraint "
                "this table cannot express.",
    },
    "solid_wall_insulation": {
        "label": "Solid wall insulation",
        "capital": 12000.0, "saving_kg": 900.0, "running_change": -260.0,
        "lifetime": 40.0, "activity": "home.gas.space_heating",
        "behavioural": False, "exclusive_group": None,
        "note": "Large saving, very large capital. It is the measure most "
                "often recommended on carbon alone and least often affordable.",
    },
    "smart_thermostat": {
        "label": "Smart heating controls",
        "capital": 220.0, "saving_kg": 200.0, "running_change": -55.0,
        "lifetime": 12.0, "activity": "home.gas.space_heating",
        "behavioural": False, "exclusive_group": None,
        "note": "Overlaps heavily with turning the thermostat down, which is "
                "exactly what the interaction handling is for.",
    },
    "double_glazing": {
        "label": "Double glazing",
        "capital": 6000.0, "saving_kg": 250.0, "running_change": -70.0,
        "lifetime": 30.0, "activity": "home.gas.space_heating",
        "behavioural": False, "exclusive_group": None,
        "note": "Frequently done for comfort and noise, and justified "
                "afterwards on carbon. On carbon alone it is poor value.",
    },
    "heat_pump": {
        "label": "Air source heat pump",
        "capital": 9000.0, "saving_kg": 1800.0, "running_change": -50.0,
        "lifetime": 20.0, "activity": "home.gas.space_heating",
        "behavioural": False, "exclusive_group": "heating_system",
        "note": "The largest single household measure available, and one that "
                "cannot coexist with a new gas boiler.",
    },
    "new_gas_boiler": {
        "label": "Replace the gas boiler",
        "capital": 2500.0, "saving_kg": 400.0, "running_change": -90.0,
        "lifetime": 15.0, "activity": "home.gas.space_heating",
        "behavioural": False, "exclusive_group": "heating_system",
        "note": "Cheaper per tonne today and locks in fifteen years of gas, "
                "which a single-year cost curve cannot see.",
    },
    "led_lighting": {
        "label": "LED lighting throughout",
        "capital": 120.0, "saving_kg": 90.0, "running_change": -35.0,
        "lifetime": 12.0, "activity": "home.electricity",
        "behavioural": False, "exclusive_group": None,
        "note": "Small, cheap, and largely already done in most households.",
    },
    "solar_pv": {
        "label": "Rooftop solar",
        "capital": 5500.0, "saving_kg": 800.0, "running_change": -350.0,
        "lifetime": 25.0, "activity": "home.electricity",
        "behavioural": False, "exclusive_group": None,
        "note": "Long life and a large running saving, which is what pulls it "
                "leftwards on the curve despite the capital.",
    },
    "home_battery": {
        "label": "Home battery",
        "capital": 4000.0, "saving_kg": 150.0, "running_change": -120.0,
        "lifetime": 12.0, "activity": "home.electricity",
        "behavioural": False, "exclusive_group": None,
        "note": "Poor value on carbon alone at current prices, and it is worth "
                "the curve saying so.",
    },
    "ev_switch": {
        "label": "Switch to an electric car",
        "capital": 12000.0, "saving_kg": 1200.0, "running_change": -600.0,
        "lifetime": 12.0, "activity": "travel.car",
        "behavioural": False, "exclusive_group": None,
        "note": "Capital is the premium over the petrol car that would "
                "otherwise have been bought, not the whole price.",
    },
    "ecodriving": {
        "label": "Drive more gently",
        "capital": 0.0, "saving_kg": 180.0, "running_change": -70.0,
        "lifetime": 3.0, "activity": "travel.car",
        "behavioural": True, "exclusive_group": None,
        "note": "Free and real, and it decays without reinforcement.",
    },
    "tyre_pressure": {
        "label": "Keep the tyres inflated",
        "capital": 0.0, "saving_kg": 60.0, "running_change": -25.0,
        "lifetime": 1.0, "activity": "travel.car",
        "behavioural": True, "exclusive_group": None,
        "note": "The clearest example of a free measure that goes undone.",
    },
    "one_fewer_flight": {
        "label": "One fewer long flight a year",
        "capital": 0.0, "saving_kg": 900.0, "running_change": -400.0,
        "lifetime": 1.0, "activity": "travel.flight",
        "behavioural": True, "exclusive_group": None,
        "note": "The largest zero-capital measure available, and the only one "
                "here that costs something other than money.",
    },
    "diet_shift": {
        "label": "Halve red meat and dairy",
        "capital": 0.0, "saving_kg": 500.0, "running_change": -150.0,
        "lifetime": 1.0, "activity": "food",
        "behavioural": True, "exclusive_group": None,
        "note": "Zero capital, a running saving, and it competes with "
                "measures costing thousands.",
    },
}

# Free measures are not adopted at anything like the rate their cost implies.
# The share is a stated assumption, used only to annotate the curve - it never
# changes a number.
ADOPTION_GAP_NOTE = (
    "Zero-cost measures are adopted far less than their cost-effectiveness "
    "implies. The curve shows what is economic, not what will happen."
)


class AbatementError(ValueError):
    """Raised for an unknown measure or an unusable input."""


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


def list_measures() -> list[str]:
    return list(MEASURES)


def get_measure(key: str) -> dict[str, Any]:
    if key not in MEASURES:
        raise AbatementError(
            f"Unknown measure '{key}'. Known measures: "
            f"{', '.join(sorted(MEASURES))}."
        )
    return dict(MEASURES[key])


def list_activities() -> list[str]:
    return list(ACTIVITY_BASE_KG)


# ---------------------------------------------------------------------------
# Cost per tonne
# ---------------------------------------------------------------------------

def annualise(capital: float, rate: float, years: float) -> float:
    """Spread a capital cost over a measure's life at a discount rate.

    The standard capital recovery factor. At a zero rate it degenerates to
    straight-line division, which is handled rather than divided by zero.
    """
    amount = _non_negative(capital)
    life = _non_negative(years)
    if life <= 0:
        raise AbatementError(
            "A measure with no lifetime cannot have its capital annualised; "
            "the whole comparison is between things that last different times."
        )
    discount = _as_float(rate)
    if discount <= 0:
        return amount / life
    factor = discount / (1.0 - (1.0 + discount) ** -life)
    return amount * factor


def cost_per_tonne(
    measure: str,
    rate: float = DEFAULT_DISCOUNT_RATE,
    energy_price_factor: float = 1.0,
    saving_kg: float | None = None,
) -> dict[str, Any]:
    """Annualised cost per tonne abated over a measure's lifetime.

    ``saving_kg`` can be overridden with an interaction-corrected figure, which
    is how a measure's position on the curve changes once something else has
    already been done to the same activity.
    """
    entry = get_measure(measure)
    saving = _non_negative(saving_kg, entry["saving_kg"]) if saving_kg is not None else entry["saving_kg"]
    price = _non_negative(energy_price_factor, 1.0) or 1.0

    annual_capital = annualise(entry["capital"], rate, entry["lifetime"])
    running = entry["running_change"] * price
    annual_cost = annual_capital + running
    tonnes = saving / 1000.0

    return {
        "measure": measure,
        "label": entry["label"],
        "activity": entry["activity"],
        "capital": entry["capital"],
        "lifetime": entry["lifetime"],
        "behavioural": entry["behavioural"],
        "exclusive_group": entry["exclusive_group"],
        "saving_kg": saving,
        "annual_capital": annual_capital,
        "annual_running_change": running,
        "annual_cost": annual_cost,
        "cost_per_tonne": (annual_cost / tonnes) if tonnes > 0 else None,
        "negative_cost": annual_cost < 0,
        "note": entry["note"],
    }


def build_curve(
    measures: list[str] | None = None,
    rate: float = DEFAULT_DISCOUNT_RATE,
    energy_price_factor: float = 1.0,
) -> list[dict[str, Any]]:
    """The curve itself: measures ordered by cost per tonne, with widths.

    Each row carries its annual abatement as a width and the cumulative
    abatement to its right edge, which is what makes the shape readable and the
    negative-cost block on the left visible for what it is.
    """
    rows = []
    for key in measures or list_measures():
        row = cost_per_tonne(key, rate, energy_price_factor)
        if row["cost_per_tonne"] is None:
            continue
        rows.append(row)

    rows.sort(key=lambda row: row["cost_per_tonne"])

    cumulative = 0.0
    for row in rows:
        row["width_tonnes"] = row["saving_kg"] / 1000.0
        row["cumulative_start"] = cumulative
        cumulative += row["width_tonnes"]
        row["cumulative_end"] = cumulative
    return rows


# ---------------------------------------------------------------------------
# Interactions
# ---------------------------------------------------------------------------

def compose_package(
    measures: list[str] | None,
    rate: float = DEFAULT_DISCOUNT_RATE,
    energy_price_factor: float = 1.0,
) -> dict[str, Any]:
    """Apply a set of measures against the remaining base, activity by activity.

    Measures acting on the same activity are applied in order of standalone
    saving, each against what the previous one left. The order changes what each
    measure is *credited* with even though the total is the same, and anything
    that ranks measures needs to know that - so both are reported.
    """
    keys = [key for key in (measures or []) if key in MEASURES]
    by_activity: dict[str, list[str]] = {}
    for key in keys:
        by_activity.setdefault(MEASURES[key]["activity"], []).append(key)

    rows = []
    for activity, group in by_activity.items():
        base = ACTIVITY_BASE_KG.get(activity, sum(MEASURES[key]["saving_kg"] for key in group))
        group.sort(key=lambda key: MEASURES[key]["saving_kg"], reverse=True)

        remaining = base
        for key in group:
            entry = MEASURES[key]
            fraction = min(1.0, entry["saving_kg"] / base) if base > 0 else 0.0
            applied = remaining * fraction
            remaining -= applied
            row = cost_per_tonne(key, rate, energy_price_factor, applied)
            row["standalone_kg"] = entry["saving_kg"]
            row["interaction_kg"] = entry["saving_kg"] - applied
            row["activity_base_kg"] = base
            rows.append(row)

    naive = sum(MEASURES[key]["saving_kg"] for key in keys)
    composed = sum(row["saving_kg"] for row in rows)
    capital = sum(MEASURES[key]["capital"] for key in keys)
    annual_cost = sum(row["annual_cost"] for row in rows)

    rows.sort(key=lambda row: row["saving_kg"], reverse=True)
    return {
        "measures": rows,
        "capital": capital,
        "naive_saving_kg": naive,
        "saving_kg": composed,
        "interaction_loss_kg": naive - composed,
        "annual_cost": annual_cost,
        "cost_per_tonne": (annual_cost / (composed / 1000.0)) if composed > 0 else None,
    }


def _valid_subset(keys: tuple[str, ...]) -> bool:
    """Measures that cannot coexist are not a package."""
    groups = [MEASURES[key]["exclusive_group"] for key in keys if MEASURES[key]["exclusive_group"]]
    return len(groups) == len(set(groups))


def _subset_options(
    group: list[str],
    rate: float,
    energy_price_factor: float,
) -> list[dict[str, Any]]:
    """Every valid combination within one activity, priced with interactions.

    Enumerated rather than searched, because a group is at most a handful of
    measures and the interactions inside it are the part a greedy pass gets
    wrong.
    """
    options = []
    for size in range(len(group) + 1):
        for subset in combinations(group, size):
            if not _valid_subset(subset):
                continue
            package = compose_package(list(subset), rate, energy_price_factor)
            options.append({
                "measures": list(subset),
                "capital": package["capital"],
                "saving_kg": package["saving_kg"],
                "annual_cost": package["annual_cost"],
            })
    return _pareto(options)


def _pareto(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop subsets that cost at least as much and save less than another.

    A dominated subset can never appear in an optimal answer, so removing them
    keeps the search exact while cutting it by an order of magnitude. This is
    the only reason enumerating every subset stays affordable.
    """
    options.sort(key=lambda option: (option["capital"], -option["saving_kg"]))
    frontier = []
    best = -1.0
    for option in options:
        if option["saving_kg"] > best:
            frontier.append(option)
            best = option["saving_kg"]
    return frontier


def select_under_budget(
    budget: float = DEFAULT_BUDGET,
    rate: float = DEFAULT_DISCOUNT_RATE,
    energy_price_factor: float = 1.0,
    measures: list[str] | None = None,
    granularity: float = BUDGET_GRANULARITY,
) -> dict[str, Any]:
    """The most abatement a budget can buy, solved exactly.

    Measures are grouped by the activity they act on. Every valid subset of each
    group is enumerated with its interactions applied and its exclusivity
    resolved, and a multiple-choice knapsack over those subsets picks the
    optimum by dynamic programming over a bucketed budget. Interactions never
    cross activities, so this is exhaustive rather than a heuristic.
    """
    available = _non_negative(budget)
    step = _non_negative(granularity, BUDGET_GRANULARITY) or BUDGET_GRANULARITY
    units = int(available // step)

    keys = [key for key in (measures or list_measures()) if key in MEASURES]
    by_activity: dict[str, list[str]] = {}
    for key in keys:
        by_activity.setdefault(MEASURES[key]["activity"], []).append(key)

    # dp[u] is the best abatement achievable using u budget units.
    dp = [0.0] * (units + 1)
    dp_choice: list[list[str]] = [[] for _ in range(units + 1)]

    for group in by_activity.values():
        options = _subset_options(group, rate, energy_price_factor)
        next_dp = [-1.0] * (units + 1)
        next_choice: list[list[str]] = [[] for _ in range(units + 1)]

        for used in range(units + 1):
            if dp[used] < 0:
                continue
            for option in options:
                cost_units = math.ceil(option["capital"] / step - 1e-9)
                total = used + cost_units
                if total > units:
                    continue
                value = dp[used] + option["saving_kg"]
                if value > next_dp[total]:
                    next_dp[total] = value
                    next_choice[total] = dp_choice[used] + option["measures"]

        dp = [value if value >= 0 else -1.0 for value in next_dp]
        dp_choice = next_choice

    best_units = max(range(units + 1), key=lambda u: (dp[u] if dp[u] >= 0 else -1.0))
    selected = dp_choice[best_units] if dp[best_units] >= 0 else []
    package = compose_package(selected, rate, energy_price_factor)

    greedy = greedy_selection(available, rate, energy_price_factor, measures)
    return {
        "budget": available,
        "selected": selected,
        "capital": package["capital"],
        "saving_kg": package["saving_kg"],
        "naive_saving_kg": package["naive_saving_kg"],
        "interaction_loss_kg": package["interaction_loss_kg"],
        "annual_cost": package["annual_cost"],
        "cost_per_tonne": package["cost_per_tonne"],
        "package": package,
        "greedy_saving_kg": greedy["saving_kg"],
        "greedy_selected": greedy["selected"],
        "beats_greedy_kg": package["saving_kg"] - greedy["saving_kg"],
        "unspent": available - package["capital"],
    }


def greedy_selection(
    budget: float = DEFAULT_BUDGET,
    rate: float = DEFAULT_DISCOUNT_RATE,
    energy_price_factor: float = 1.0,
    measures: list[str] | None = None,
) -> dict[str, Any]:
    """Read down the curve and buy until the money runs out.

    What most consumer tools do, kept here as the comparison rather than as the
    recommendation. It is not stupid - it is optimal when capital is smooth -
    and it fails on lumpy capital, which is the case households are in.
    """
    available = _non_negative(budget)
    curve = build_curve(measures, rate, energy_price_factor)

    chosen: list[str] = []
    used_groups: set[str] = set()
    spent = 0.0
    for row in curve:
        group = row["exclusive_group"]
        if group and group in used_groups:
            continue
        if spent + row["capital"] > available:
            continue
        chosen.append(row["measure"])
        spent += row["capital"]
        if group:
            used_groups.add(group)

    package = compose_package(chosen, rate, energy_price_factor)
    return {
        "budget": available,
        "selected": chosen,
        "capital": package["capital"],
        "saving_kg": package["saving_kg"],
        "package": package,
    }


def sensitivity(
    budget: float = DEFAULT_BUDGET,
    rates: tuple[float, ...] = DISCOUNT_RANGE,
    energy_price_factors: tuple[float, ...] = (0.7, 1.0, 1.4),
) -> list[dict[str, Any]]:
    """How the advice moves across discount rate and energy price.

    The ordering in the middle of the curve is genuinely unstable across
    plausible values, and presenting one ordering as definitive would be false
    precision of the kind this module exists to remove.
    """
    rows = []
    for rate in rates:
        for factor in energy_price_factors:
            curve = build_curve(None, rate, factor)
            selection = select_under_budget(budget, rate, factor)
            rows.append({
                "rate": rate,
                "energy_price_factor": factor,
                "cheapest": curve[0]["measure"] if curve else None,
                "negative_cost_count": sum(1 for row in curve if row["negative_cost"]),
                "selected": selection["selected"],
                "saving_kg": selection["saving_kg"],
            })
    return rows


def budget_ladder(
    budgets: tuple[float, ...] = (0.0, 500.0, 1000.0, 2000.0, 5000.0, 10000.0, 20000.0),
    rate: float = DEFAULT_DISCOUNT_RATE,
    energy_price_factor: float = 1.0,
) -> list[dict[str, Any]]:
    """What each budget buys, which is the question households actually ask."""
    rows = []
    for budget in budgets:
        selection = select_under_budget(budget, rate, energy_price_factor)
        rows.append({
            "budget": budget,
            "selected": selection["selected"],
            "capital": selection["capital"],
            "saving_kg": selection["saving_kg"],
            "greedy_saving_kg": selection["greedy_saving_kg"],
            "beats_greedy_kg": selection["beats_greedy_kg"],
            "cost_per_tonne": selection["cost_per_tonne"],
        })
    return rows


def get_abatement_insights(selection: dict[str, Any] | None) -> list[str]:
    """Plain statements about what the selection means, in priority order."""
    if not selection:
        return ["Set a budget to see what it can buy."]

    insights: list[str] = []
    saving = _as_float(selection.get("saving_kg"))
    budget = _as_float(selection.get("budget"))
    beats = _as_float(selection.get("beats_greedy_kg"))

    insights.append(
        f"{budget:,.0f} buys {saving:,.0f} kg a year across "
        f"{len(selection.get('selected') or [])} measure(s)."
    )

    if beats > 1.0:
        insights.append(
            f"Reading down the cost curve until the money ran out would have "
            f"saved {beats:,.0f} kg less. Greedy selection is optimal when "
            f"capital is smooth and wrong when it is lumpy, which is the "
            f"situation every household is actually in."
        )
    elif beats < -1.0:
        insights.append(
            "The greedy selection matches or beats the exact one here, which "
            "means the budget is loose enough that the ordering is all that "
            "matters."
        )
    else:
        insights.append(
            "Greedy selection happens to be optimal at this budget. That is "
            "worth knowing rather than assuming - it stops being true as soon "
            "as the budget falls between two lumps."
        )

    interaction = _as_float(selection.get("interaction_loss_kg"))
    if interaction > 1.0:
        naive = _as_float(selection.get("naive_saving_kg"))
        insights.append(
            f"Adding these measures' individual savings would give "
            f"{naive:,.0f} kg. They act on the same heat and the same miles, "
            f"so each applies to what the previous one left: {saving:,.0f} kg. "
            f"The {interaction:,.0f} kg difference is interaction, not error."
        )

    selected = selection.get("selected") or []
    behavioural = [key for key in selected if MEASURES[key]["behavioural"]]
    if behavioural:
        labels = ", ".join(MEASURES[key]["label"].lower() for key in behavioural)
        insights.append(
            f"{len(behavioural)} of these cost nothing ({labels}). "
            + ADOPTION_GAP_NOTE
        )

    unspent = _as_float(selection.get("unspent"))
    if unspent > 100.0:
        insights.append(
            f"{unspent:,.0f} is left unspent because the next measure costs "
            f"more than it. That is the lumpiness the exact selection exists "
            f"to handle, not slack in the answer."
        )

    insights.append(
        "Cost per tonne here is over each measure's whole life at the stated "
        "discount rate. Raise the rate and short-lived measures move up the "
        "curve; the ordering in the middle is not stable across plausible "
        "rates, which is why the sensitivity is shown rather than hidden."
    )
    return insights


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_abatement_db() -> bool:
    """Create the table if it does not exist yet."""
    conn = None
    try:
        conn = _connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS abatement_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                budget REAL NOT NULL,
                discount_rate REAL NOT NULL,
                capital REAL NOT NULL,
                saving_kg REAL NOT NULL,
                measure_count INTEGER NOT NULL DEFAULT 0,
                detail_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Unable to initialise abatement table: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def save_plan(
    user_id: int,
    name: str,
    selection: dict[str, Any],
    rate: float = DEFAULT_DISCOUNT_RATE,
) -> int | None:
    """Persist a plan. Returns the row id or None."""
    init_abatement_db()
    conn = None
    try:
        conn = _connect()
        cursor = conn.execute(
            """
            INSERT INTO abatement_plans (
                user_id, name, budget, discount_rate, capital, saving_kg,
                measure_count, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                (name or "Plan").strip() or "Plan",
                _as_float(selection.get("budget")),
                _as_float(rate, DEFAULT_DISCOUNT_RATE),
                _as_float(selection.get("capital")),
                _as_float(selection.get("saving_kg")),
                len(selection.get("selected") or []),
                json.dumps(selection, default=str),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as exc:
        logger.error("Unable to save abatement plan: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def get_plans(user_id: int, limit: int = 25) -> list[dict[str, Any]]:
    """A user's saved plans, newest first."""
    init_abatement_db()
    conn = None
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, name, budget, discount_rate, capital, saving_kg,
                   measure_count, detail_json, created_at
            FROM abatement_plans
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
                record["detail"] = json.loads(record.pop("detail_json") or "{}")
            except (TypeError, ValueError):
                record["detail"] = {}
            plans.append(record)
        return plans
    except sqlite3.Error as exc:
        logger.error("Unable to load abatement plans: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def delete_plan(plan_id: int) -> bool:
    """Delete a saved plan."""
    init_abatement_db()
    conn = None
    try:
        conn = _connect()
        cursor = conn.execute("DELETE FROM abatement_plans WHERE id = ?", (plan_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as exc:
        logger.error("Unable to delete abatement plan: %s", exc)
        return False
    finally:
        if conn:
            conn.close()
