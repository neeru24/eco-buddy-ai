"""Gas-resolved climate metrics: GWP100, GWP20 and GWP*.

The app reports everything in "kg CO2e". That is a conversion, and every
conversion has a convention buried in it. The convention used here without
ever being stated is GWP100, and for methane it is badly behaved.

Why methane breaks the metric
-----------------------------
Methane has an atmospheric lifetime of about twelve years. CO2 does not have
a meaningful lifetime at all - a fraction of it is still there in a thousand
years. GWP100 papers over that difference by integrating radiative forcing
over a century and dividing, which produces one convenient number and one
specific, consequential error:

*   A **constant** methane source causes roughly **constant** warming, not
    rising warming. After a couple of decades the methane destroyed each year
    matches the methane emitted, and the atmospheric stock stops growing.
    GWP100 reports that same emission every year as though it were adding to
    a permanent stock, which is true for CO2 and false for methane.

*   The converse is what makes it matter. A **reduction** in a sustained
    methane source actively cools, faster and further than GWP100 credits.
    A user cutting dairy is doing more in the near term than the app says.

*   A one-off methane **pulse** is genuinely different from a sustained
    **flow**, and the app cannot distinguish them because it converts both
    with the same factor.

GWP* exists for exactly this. It relates the *rate of change* of a
short-lived gas to a CO2-equivalent warming effect, so stable emissions map
to roughly zero additional warming and changes map to real ones.

What this module does not do
----------------------------
It does not switch the app to GWP*. GWP* is not a drop-in replacement: it is
undefined for a single pulse with no history, and inventory reporting
conventions require GWP100. Both have to coexist, which is why every result
here carries both.

The other conflation
--------------------
Biogenic and fossil carbon are added together today. Burning wood releases
carbon a tree recently removed from the atmosphere; burning gas releases
carbon that has been underground for 300 million years. Both currently land
in the same total at the same weight with no payback period attached. That is
not a rounding difference, it is the difference between a cycle and a one-way
transfer, and the honest answer is a payback period rather than a side.

The decomposition is designed to be **conservative**: splitting a footprint
into gases leaves the GWP100 total unchanged. This is a decomposition, not a
restatement, and a user's headline number does not move because they opened
this page.

Self-contained: standard library only, SQLite tables created lazily, no
shared files modified.
"""

import os
import json
import sqlite3
import logging
from typing import Any

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

# ---------------------------------------------------------------------------
# Metric constants
# ---------------------------------------------------------------------------

# IPCC AR6 values, including climate-carbon feedbacks. Fossil methane carries
# a slightly higher GWP than biogenic methane because its oxidation adds CO2
# that was not in the active carbon cycle to begin with.
GWP100 = {
    "co2_fossil": 1.0,
    "co2_biogenic": 1.0,
    "ch4_fossil": 29.8,
    "ch4_biogenic": 27.0,
    "n2o": 273.0,
}

GWP20 = {
    "co2_fossil": 1.0,
    "co2_biogenic": 1.0,
    "ch4_fossil": 82.5,
    "ch4_biogenic": 79.7,
    "n2o": 273.0,
}

GAS_LABELS = {
    "co2_fossil": "Fossil CO2",
    "co2_biogenic": "Biogenic CO2",
    "ch4_fossil": "Methane (fossil)",
    "ch4_biogenic": "Methane (biogenic)",
    "n2o": "Nitrous oxide",
}

GAS_LIFETIMES = {
    "co2_fossil": None,
    "co2_biogenic": None,
    "ch4_fossil": 11.8,
    "ch4_biogenic": 11.8,
    "n2o": 109.0,
}

GAS_NOTES = {
    "co2_fossil": (
        "Carbon moved out of geological storage and into the atmosphere. A "
        "fraction of it is still there in a thousand years, which is why it "
        "is the reference gas and why cutting it is the only durable move."
    ),
    "co2_biogenic": (
        "Carbon a plant recently took out of the atmosphere and you have put "
        "back. Not free - the timing matters and regrowth takes decades - but "
        "not equivalent to fossil carbon either."
    ),
    "ch4_fossil": (
        "Leaked gas, coal seams, flaring. Short-lived and very potent. Its "
        "oxidation also adds CO2 that was not in the active carbon cycle, "
        "which is why its GWP is a little above biogenic methane's."
    ),
    "ch4_biogenic": (
        "Livestock, rice paddies, landfill. Short-lived and very potent. "
        "A steady source causes steady warming rather than rising warming - "
        "and a reduction cools, which GWP100 systematically under-credits."
    ),
    "n2o": (
        "Mostly fertiliser. Over a century in the atmosphere and 273 times "
        "the warming of CO2 per kilogram, so it behaves like a long-lived "
        "gas even though it is grouped with agricultural methane."
    ),
}

SHORT_LIVED = ("ch4_fossil", "ch4_biogenic")

# GWP* parameters, following the standard formulation:
#
#     E* = GWP_H x ( r x (dE/dt) x H  +  s x E )
#
# where dE/dt is the change in the annual emission *rate* measured over a
# twenty-year window, H is the GWP horizon, and the two weights split the
# result between the change and the level. Almost all of the answer comes
# from the rate term, which is the entire difference from pulse accounting:
# what matters for a short-lived gas is whether the flow is changing, not
# how big it is.
GWP_STAR_WINDOW_YEARS = 20
GWP_STAR_HORIZON_YEARS = 100
GWP_STAR_RATE_WEIGHT = 0.75
GWP_STAR_LEVEL_WEIGHT = 0.25

# Approximate transient response: warming in millikelvin per gigatonne of
# CO2-warming-equivalent. Only ever used for a relative sense of scale, which
# is the honest use for a per-person figure.
WARMING_MK_PER_GT_CO2 = 0.45

# ---------------------------------------------------------------------------
# Activity gas splits
# ---------------------------------------------------------------------------

# How each activity's CO2e divides between gases. Fractions are of the
# activity's GWP100 total, not of its mass - they are what the app can
# actually decompose, given it stores CO2e and nothing else.
#
# Every entry sums to 1.0, which is checked by the tests. A split that did
# not sum to 1 would quietly change a user's headline total, and this module
# exists to avoid exactly that class of silent restatement.
ACTIVITY_GAS_SPLITS = {
    "beef": {
        "ch4_biogenic": 0.55, "n2o": 0.20, "co2_fossil": 0.25,
        "note": "Enteric fermentation dominates. This is the most "
                "metric-sensitive item in a typical footprint.",
    },
    "lamb": {
        "ch4_biogenic": 0.53, "n2o": 0.20, "co2_fossil": 0.27,
        "note": "Ruminant, so the same story as beef.",
    },
    "dairy": {
        "ch4_biogenic": 0.48, "n2o": 0.20, "co2_fossil": 0.32,
        "note": "Enteric methane plus manure management.",
    },
    "rice": {
        "ch4_biogenic": 0.62, "n2o": 0.10, "co2_fossil": 0.28,
        "note": "Flooded paddies are anaerobic, which is a methane factory.",
    },
    "pork": {
        "ch4_biogenic": 0.24, "n2o": 0.18, "co2_fossil": 0.58,
        "note": "Manure methane, but no enteric fermentation.",
    },
    "poultry": {
        "ch4_biogenic": 0.10, "n2o": 0.20, "co2_fossil": 0.70,
        "note": "Mostly feed production and energy.",
    },
    "vegetables": {
        "ch4_biogenic": 0.04, "n2o": 0.26, "co2_fossil": 0.70,
        "note": "Fertiliser N2O is the non-CO2 share that matters here.",
    },
    "cereals": {
        "ch4_biogenic": 0.05, "n2o": 0.30, "co2_fossil": 0.65,
        "note": "Fertiliser-driven. N2O behaves like a long-lived gas.",
    },
    "food_waste": {
        "ch4_biogenic": 0.70, "n2o": 0.08, "co2_fossil": 0.22,
        "note": "Landfilled organics decompose anaerobically. Almost all of "
                "the impact is methane, and almost all of it is avoidable.",
    },
    "landfill_waste": {
        "ch4_biogenic": 0.75, "n2o": 0.05, "co2_fossil": 0.20,
        "note": "The single most methane-heavy category in the app.",
    },
    "natural_gas_heating": {
        "ch4_fossil": 0.08, "co2_fossil": 0.92,
        "note": "Combustion CO2 plus upstream leakage. The leakage share is "
                "small by mass and large by warming.",
    },
    "electricity": {
        "ch4_fossil": 0.05, "n2o": 0.01, "co2_fossil": 0.94,
        "note": "Depends entirely on the grid mix; gas-heavy grids carry "
                "more upstream methane.",
    },
    "petrol_car": {
        "ch4_fossil": 0.02, "n2o": 0.02, "co2_fossil": 0.96,
        "note": "Nearly pure fossil CO2. Metric choice barely moves it, "
                "which is exactly why it is the fair comparison point.",
    },
    "diesel_car": {
        "ch4_fossil": 0.01, "n2o": 0.03, "co2_fossil": 0.96,
        "note": "As petrol, with slightly more N2O from aftertreatment.",
    },
    "flights": {
        "ch4_fossil": 0.00, "n2o": 0.02, "co2_fossil": 0.98,
        "note": "Effectively all CO2. Non-CO2 aviation forcing is real but "
                "it is contrails and NOx, which are not greenhouse gas "
                "inventory items and are out of scope here.",
    },
    "wood_heating": {
        "co2_biogenic": 0.88, "ch4_biogenic": 0.07, "n2o": 0.05,
        "note": "The carbon was in a tree recently. Biogenic does not mean "
                "free - see the payback period.",
    },
    "public_transport": {
        "ch4_fossil": 0.02, "n2o": 0.02, "co2_fossil": 0.96,
        "note": "Fossil CO2 dominated, like private vehicles.",
    },
    "goods": {
        "ch4_fossil": 0.04, "n2o": 0.04, "co2_fossil": 0.92,
        "note": "Manufacturing energy, so mostly fossil CO2.",
    },
}

# Regrowth period for biogenic carbon, in years, by source. Biogenic carbon
# is not neutral on the timescale anyone cares about; it is neutral once the
# replacement has grown, and saying which is the whole point.
BIOGENIC_PAYBACK_YEARS = {
    "wood_heating": 45,
    "food_waste": 1,
    "landfill_waste": 1,
    "beef": 1,
    "lamb": 1,
    "dairy": 1,
    "rice": 1,
    "pork": 1,
    "poultry": 1,
    "vegetables": 1,
    "cereals": 1,
}

DEFAULT_PAYBACK_YEARS = 1


class ClimateMetricsError(ValueError):
    """Raised when a request cannot be answered honestly."""


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if result != result:  # NaN
        return default
    return result


def _non_negative(value: Any, default: float = 0.0) -> float:
    return max(0.0, _as_float(value, default))


# ---------------------------------------------------------------------------
# Decomposition
# ---------------------------------------------------------------------------

def list_activities() -> list[str]:
    """Activities with a known gas split."""
    return sorted(ACTIVITY_GAS_SPLITS.keys())


def gas_split(activity: str) -> dict[str, float]:
    """The gas fractions for an activity, without the prose note."""
    if activity not in ACTIVITY_GAS_SPLITS:
        raise ClimateMetricsError(
            f"No gas split for '{activity}'. Add one to ACTIVITY_GAS_SPLITS "
            "rather than defaulting to pure CO2 - assuming an unknown "
            "activity is all CO2 would hide precisely the methane this "
            "module exists to surface."
        )
    return {
        gas: value
        for gas, value in ACTIVITY_GAS_SPLITS[activity].items()
        if gas != "note"
    }


def split_note(activity: str) -> str:
    """Why an activity's split looks the way it does."""
    if activity not in ACTIVITY_GAS_SPLITS:
        raise ClimateMetricsError(f"No gas split for '{activity}'.")
    return ACTIVITY_GAS_SPLITS[activity].get("note", "")


def decompose(activity: str, co2e_kg: float) -> dict[str, Any]:
    """Split an activity's GWP100 CO2e into per-gas CO2e contributions.

    The app stores CO2e and not gas masses, so this divides the CO2e figure
    it already has. Per-gas *masses* are recovered by dividing back out by
    the GWP100 factor, which is what the GWP* calculation needs.

    The sum of the parts equals the input. Always. That is what makes this a
    decomposition rather than a restatement.
    """
    total = _non_negative(co2e_kg)
    fractions = gas_split(activity)

    contributions = {}
    masses = {}
    for gas, fraction in fractions.items():
        share = total * _as_float(fraction)
        contributions[gas] = share
        factor = GWP100.get(gas, 1.0)
        masses[gas] = share / factor if factor else 0.0

    return {
        "activity": activity,
        "co2e_kg": total,
        "by_gas_co2e": contributions,
        "by_gas_mass": masses,
        "note": split_note(activity),
    }


def decompose_footprint(activities: dict[str, float]) -> dict[str, Any]:
    """Decompose a whole footprint given {activity: co2e_kg}.

    Unknown activities raise rather than being silently filed as CO2.
    """
    if not isinstance(activities, dict):
        raise ClimateMetricsError("activities must be a mapping.")

    by_gas_co2e = {}
    by_gas_mass = {}
    lines = []
    total = 0.0

    for activity, co2e in activities.items():
        line = decompose(activity, co2e)
        lines.append(line)
        total += line["co2e_kg"]
        for gas, value in line["by_gas_co2e"].items():
            by_gas_co2e[gas] = by_gas_co2e.get(gas, 0.0) + value
        for gas, value in line["by_gas_mass"].items():
            by_gas_mass[gas] = by_gas_mass.get(gas, 0.0) + value

    return {
        "lines": lines,
        "by_gas_co2e": by_gas_co2e,
        "by_gas_mass": by_gas_mass,
        "total_gwp100_kg": total,
        "methane_share": methane_share(by_gas_co2e),
    }


def methane_share(by_gas_co2e: dict[str, float] | None) -> float:
    """Fraction of a GWP100 total that is methane."""
    total = sum(_as_float(value) for value in (by_gas_co2e or {}).values())
    if total <= 0:
        return 0.0
    methane = sum(
        _as_float(by_gas_co2e.get(gas, 0.0)) for gas in SHORT_LIVED
    )
    return methane / total


# ---------------------------------------------------------------------------
# Metric conversion
# ---------------------------------------------------------------------------

def convert(by_gas_mass: dict[str, float] | None, metric: str = "gwp100") -> dict[str, float]:
    """Convert per-gas masses (kg) into CO2e (kg) under a chosen metric.

    Only pulse metrics are available here. GWP* needs an emissions history
    and lives in gwp_star() - offering it as a metric option would invite it
    to be applied to a single year, which is the one thing it cannot do.
    """
    if metric not in ("gwp100", "gwp20"):
        raise ClimateMetricsError(
            "metric must be 'gwp100' or 'gwp20'. GWP* is not a pulse metric "
            "and needs an emissions history - use gwp_star()."
        )

    factors = GWP100 if metric == "gwp100" else GWP20
    return {
        gas: _non_negative(mass) * factors.get(gas, 1.0)
        for gas, mass in (by_gas_mass or {}).items()
    }


def compare_metrics(by_gas_mass: dict[str, float] | None) -> dict[str, Any]:
    """The same emissions under GWP100 and GWP20, with the gap explained."""
    masses = by_gas_mass or {}
    hundred = convert(masses, "gwp100")
    twenty = convert(masses, "gwp20")

    total_100 = sum(hundred.values())
    total_20 = sum(twenty.values())
    ratio = total_20 / total_100 if total_100 > 0 else 1.0

    if ratio >= 1.6:
        reading = (
            "Your footprint is much larger over 20 years than over 100. That "
            "is methane, and it means near-term cuts here buy near-term "
            "cooling - which is the timescale most climate targets are set on."
        )
    elif ratio >= 1.2:
        reading = (
            "A meaningful share of your footprint is short-lived. The "
            "hundred-year figure understates what cutting it does this decade."
        )
    else:
        reading = (
            "Your footprint is dominated by long-lived gases, so the horizon "
            "barely changes the answer. Only cutting CO2 helps durably here."
        )

    return {
        "gwp100_kg": total_100,
        "gwp20_kg": total_20,
        "ratio": ratio,
        "by_gas_gwp100": hundred,
        "by_gas_gwp20": twenty,
        "reading": reading,
    }


# ---------------------------------------------------------------------------
# GWP*
# ---------------------------------------------------------------------------

def gwp_star(methane_history_kg: list[float] | None, window_years: int = GWP_STAR_WINDOW_YEARS) -> dict[str, Any]:
    """CO2-warming-equivalent of a methane emissions history.

    ``methane_history_kg`` is annual methane emissions in kg, oldest first.
    The final year is the one being reported; the earlier years establish
    whether the source is rising, flat or falling.

    A flat history returns a small positive number, not zero: a constant
    source sustains the warming it has already caused. A falling history can
    return a **negative** figure, which is the point - reducing a sustained
    short-lived source actively cools, and no pulse metric can express that.

    With fewer than two years of history there is no rate of change to
    measure. Rather than inventing a trend, this falls back to GWP100 pulse
    accounting and says so in ``basis``.
    """
    history = [_non_negative(value) for value in (methane_history_kg or [])]
    if not history:
        raise ClimateMetricsError("A methane history needs at least one year.")

    window_limit = max(1, int(window_years))
    current = history[-1]

    if len(history) < 2:
        return {
            "co2we_kg": current * GWP100["ch4_biogenic"],
            "basis": "pulse",
            "rate_change_kg_per_year": 0.0,
            "trend": "unknown",
            "years_of_history": len(history),
            "reading": (
                "One year of data cannot show a trend, so this is ordinary "
                "GWP100 pulse accounting. GWP* needs history; come back once "
                "there is more than one year of it."
            ),
        }

    window = min(window_limit, len(history) - 1)
    earlier = history[-(window + 1)]
    rate_change = (current - earlier) / window

    rate_term = (
        GWP_STAR_RATE_WEIGHT
        * GWP_STAR_HORIZON_YEARS
        * rate_change
        * GWP100["ch4_biogenic"]
    )
    level_term = GWP_STAR_LEVEL_WEIGHT * current * GWP100["ch4_biogenic"]
    co2we = rate_term + level_term

    if rate_change > 1e-9:
        trend = "rising"
        reading = (
            "Your methane emissions are rising, so they are adding warming "
            "on top of what the existing flow already causes. GWP* weights "
            "that increase heavily."
        )
    elif rate_change < -1e-9:
        trend = "falling"
        reading = (
            "Your methane emissions are falling. A sustained short-lived "
            "source that shrinks actively cools, which is why this figure "
            "can go below zero and why GWP100 under-credits the change."
        )
    else:
        trend = "flat"
        reading = (
            "Your methane emissions are steady, so they sustain the warming "
            "they already cause rather than adding to it. GWP100 reports "
            "this as though it were piling up a permanent stock, which for "
            "methane it is not."
        )

    return {
        "co2we_kg": co2we,
        "basis": "gwp_star",
        "rate_change_kg_per_year": rate_change,
        "trend": trend,
        "years_of_history": len(history),
        "window_years": window,
        "pulse_gwp100_kg": current * GWP100["ch4_biogenic"],
        "reading": reading,
    }


def gwp_star_vs_gwp100(methane_history_kg: list[float] | None, window_years: int = GWP_STAR_WINDOW_YEARS) -> dict[str, Any]:
    """Both accountings of a methane history, with the disagreement stated."""
    star = gwp_star(methane_history_kg, window_years)
    pulse = star.get("pulse_gwp100_kg", star["co2we_kg"])
    gap = star["co2we_kg"] - pulse

    return {
        "gwp100_kg": pulse,
        "gwp_star_kg": star["co2we_kg"],
        "gap_kg": gap,
        "trend": star["trend"],
        "basis": star["basis"],
        "sign_flip": (pulse > 0) and (star["co2we_kg"] < 0),
        "reading": star["reading"],
    }


# ---------------------------------------------------------------------------
# Biogenic carbon
# ---------------------------------------------------------------------------

def biogenic_payback(activity: str, biogenic_co2_kg: float, years: int | None = None) -> dict[str, Any]:
    """Report biogenic carbon with the regrowth period attached.

    Neither "carbon neutral" nor "same as fossil" is true. Both are answers
    to the question of whether the replacement has grown yet, and that
    question has a number.
    """
    amount = _non_negative(biogenic_co2_kg)
    if years is None:
        years = BIOGENIC_PAYBACK_YEARS.get(activity, DEFAULT_PAYBACK_YEARS)
    years = max(0, int(years))

    if years <= 1:
        verdict = (
            "Within the annual cycle. Treating this as neutral is reasonable "
            "- the carbon was taken up in the same year it was released."
        )
    elif years <= 10:
        verdict = (
            f"Payback in about {years} years. Short enough that the debt is "
            "repaid inside a decade, long enough that it is not nothing."
        )
    else:
        verdict = (
            f"Payback in about {years} years. On the timescale that matters "
            "for a 2050 target, this behaves much closer to fossil carbon "
            "than the label 'renewable' suggests. The carbon is in the air "
            "now; the tree that repays it has not grown yet."
        )

    return {
        "activity": activity,
        "biogenic_co2_kg": amount,
        "payback_years": years,
        "counted_as_neutral": years <= 1,
        "verdict": verdict,
    }


def separate_carbon(by_gas_co2e: dict[str, float] | None) -> dict[str, Any]:
    """Split a decomposed footprint into fossil and biogenic carbon."""
    gases = by_gas_co2e or {}
    fossil = (
        _as_float(gases.get("co2_fossil", 0.0))
        + _as_float(gases.get("ch4_fossil", 0.0))
    )
    biogenic = (
        _as_float(gases.get("co2_biogenic", 0.0))
        + _as_float(gases.get("ch4_biogenic", 0.0))
    )
    other = _as_float(gases.get("n2o", 0.0))
    total = fossil + biogenic + other

    return {
        "fossil_kg": fossil,
        "biogenic_kg": biogenic,
        "other_kg": other,
        "total_kg": total,
        "fossil_share": fossil / total if total > 0 else 0.0,
        "biogenic_share": biogenic / total if total > 0 else 0.0,
    }


# ---------------------------------------------------------------------------
# Temperature framing
# ---------------------------------------------------------------------------

def warming_contribution(co2we_kg: float, population: int = 1) -> dict[str, Any]:
    """Approximate warming from a flow of emissions, in microkelvin.

    A per-person warming figure is not a precise quantity and should not be
    presented as one. It is here because it is the thing all of the metrics
    above are proxies for, and because seeing methane and CO2 on a
    temperature axis settles the argument faster than any table of factors.
    """
    amount = _as_float(co2we_kg)
    people = max(1, int(population))
    gigatonnes = amount * people / 1e12
    millikelvin = gigatonnes * WARMING_MK_PER_GT_CO2
    return {
        "co2we_kg": amount,
        "population": people,
        "microkelvin": millikelvin * 1000.0,
        "millikelvin": millikelvin,
        "caveat": (
            "Order of magnitude only. One person's emissions do not produce "
            "a measurable temperature; this scales them to a population to "
            "show what the metric choice is actually a proxy for."
        ),
    }


# ---------------------------------------------------------------------------
# Metric disagreement
# ---------------------------------------------------------------------------

def rank_under_metric(activities: dict[str, float], metric: str = "gwp100") -> list[dict[str, Any]]:
    """Rank {activity: co2e_kg} by size under a chosen metric."""
    decomposed = decompose_footprint(activities)
    ranked = []
    for line in decomposed["lines"]:
        converted = convert(line["by_gas_mass"], metric)
        ranked.append({
            "activity": line["activity"],
            "value_kg": sum(converted.values()),
        })
    ranked.sort(key=lambda item: item["value_kg"], reverse=True)
    return ranked


def metric_disagreement(activities: dict[str, float]) -> list[dict[str, Any]]:
    """Activities whose ranking changes between GWP100 and GWP20.

    The most useful single output here. Two totals differing is expected;
    two activities **swapping places** means the advice the app gives about
    which to tackle first depends on a convention it never states.
    """
    by_100 = rank_under_metric(activities, "gwp100")
    by_20 = rank_under_metric(activities, "gwp20")

    position_100 = {row["activity"]: index for index, row in enumerate(by_100)}
    position_20 = {row["activity"]: index for index, row in enumerate(by_20)}

    changes = []
    for activity, before in position_100.items():
        after = position_20[activity]
        if before == after:
            continue
        changes.append({
            "activity": activity,
            "gwp100_rank": before + 1,
            "gwp20_rank": after + 1,
            "movement": before - after,
            "direction": "up" if after < before else "down",
        })

    changes.sort(key=lambda item: abs(item["movement"]), reverse=True)
    return changes


def get_metric_insights(decomposed: dict[str, Any] | None, comparison: dict[str, Any] | None = None) -> list[str]:
    """Plain-language guidance from a decomposed footprint."""
    insights = []
    gases = (decomposed or {}).get("by_gas_co2e", {})
    share = methane_share(gases)

    if share >= 0.30:
        insights.append(
            f"Methane is {share * 100:.0f}% of your GWP100 total. That share "
            "is short-lived, which means cutting it changes the temperature "
            "this decade rather than in the next century."
        )
    elif share >= 0.10:
        insights.append(
            f"Methane is {share * 100:.0f}% of your total - enough that the "
            "reporting horizon changes how large your footprint looks."
        )
    else:
        insights.append(
            "Your footprint is almost entirely long-lived gases. The metric "
            "convention barely matters for you, which is itself worth "
            "knowing before comparing yourself to someone else."
        )

    carbon = separate_carbon(gases)
    if carbon["biogenic_share"] >= 0.10:
        insights.append(
            f"{carbon['biogenic_share'] * 100:.0f}% of your carbon is "
            "biogenic. It is not free and it is not the same as fossil "
            "carbon - the difference is the regrowth period, which is "
            "attached to each source rather than assumed."
        )

    if _as_float(gases.get("n2o", 0.0)) > 0.15 * sum(
        _as_float(value) for value in gases.values()
    ):
        insights.append(
            "Nitrous oxide is a significant share of your footprint. It sits "
            "in the atmosphere for over a century, so despite arriving with "
            "your food it behaves like CO2, not like methane."
        )

    if comparison and comparison.get("ratio", 1.0) >= 1.3:
        insights.append(
            f"Over 20 years your footprint is {comparison['ratio']:.1f}× its "
            "hundred-year figure. Both numbers are correct; they answer "
            "different questions about when the warming happens."
        )

    insights.append(
        "Use GWP100 for reporting, because inventories require it, and GWP* "
        "for judging whether a sustained change in a short-lived source is "
        "actually working. Neither replaces the other."
    )

    return insights


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_climate_metrics_db() -> bool:
    """Create the tables if they do not exist yet."""
    conn = None
    try:
        conn = _connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS climate_metric_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                gwp100_kg REAL NOT NULL,
                gwp20_kg REAL NOT NULL,
                methane_share REAL NOT NULL,
                biogenic_share REAL NOT NULL,
                detail_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS climate_methane_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                year INTEGER NOT NULL,
                methane_kg REAL NOT NULL,
                UNIQUE(user_id, year)
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Unable to initialise climate metrics tables: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def save_assessment(user_id: int, name: str | None, decomposed: dict[str, Any], comparison: dict[str, Any]) -> int | None:
    """Persist a decomposed footprint. Returns the row id or None."""
    init_climate_metrics_db()
    conn = None
    try:
        carbon = separate_carbon(decomposed.get("by_gas_co2e", {}))
        conn = _connect()
        cursor = conn.execute(
            """
            INSERT INTO climate_metric_assessments (
                user_id, name, gwp100_kg, gwp20_kg, methane_share,
                biogenic_share, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                (name or "Assessment").strip() or "Assessment",
                _as_float(comparison.get("gwp100_kg")),
                _as_float(comparison.get("gwp20_kg")),
                _as_float(decomposed.get("methane_share")),
                carbon["biogenic_share"],
                json.dumps(
                    {"decomposed": decomposed, "comparison": comparison},
                    default=str,
                ),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as exc:
        logger.error("Unable to save climate metric assessment: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def get_assessments(user_id: int, limit: int = 25) -> list[dict[str, Any]]:
    """A user's saved assessments, newest first."""
    init_climate_metrics_db()
    conn = None
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, name, gwp100_kg, gwp20_kg, methane_share,
                   biogenic_share, detail_json, created_at
            FROM climate_metric_assessments
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
        logger.error("Unable to load climate metric assessments: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def delete_assessment(assessment_id: int) -> bool:
    """Delete a saved assessment."""
    init_climate_metrics_db()
    conn = None
    try:
        conn = _connect()
        cursor = conn.execute(
            "DELETE FROM climate_metric_assessments WHERE id = ?",
            (assessment_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as exc:
        logger.error("Unable to delete climate metric assessment: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def record_methane_year(user_id: int, year: int, methane_kg: float) -> bool:
    """Record one year of methane emissions, replacing any existing entry."""
    init_climate_metrics_db()
    conn = None
    try:
        conn = _connect()
        conn.execute(
            """
            INSERT INTO climate_methane_history (user_id, year, methane_kg)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, year) DO UPDATE SET
                methane_kg = excluded.methane_kg
            """,
            (user_id, int(year), _non_negative(methane_kg)),
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Unable to record methane year: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def get_methane_history(user_id: int) -> list[tuple[int, float]]:
    """A user's methane history as [(year, kg)], oldest first."""
    init_climate_metrics_db()
    conn = None
    try:
        conn = _connect()
        rows = conn.execute(
            """
            SELECT year, methane_kg
            FROM climate_methane_history
            WHERE user_id = ?
            ORDER BY year ASC
            """,
            (user_id,),
        ).fetchall()
        return [(int(row[0]), float(row[1])) for row in rows]
    except sqlite3.Error as exc:
        logger.error("Unable to load methane history: %s", exc)
        return []
    finally:
        if conn:
            conn.close()
