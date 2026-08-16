"""Permanence: what a removal is worth against a fossil emission.

The app treats a tonne of carbon bought as an offset as equal to a tonne of
carbon not emitted. They are not equal. A tonne released from fossil fuel is a
permanent addition to the active carbon cycle. A tonne stored in a young forest
is stored for as long as the forest stands, which may be forty years, or may be
until the next fire.

Ton-years, not tonnes
---------------------
The right unit is not the tonne but the **ton-year**: a tonne held out of the
atmosphere for a year. A fossil tonne imposes a burden over the whole horizon
being considered; a temporary store avoids the tail end of it. The equivalence
ratio between them is therefore calculable rather than assumed to be one, and
this module calculates it two ways because the two accepted methods disagree by
a factor of two and a half.

*   **Lashof.** The stored tonne is released after D years, so its atmospheric
    burden is the fossil curve shifted by D. What the credit avoided is the
    slice of the curve pushed beyond the horizon. Integrated against the Bern
    decay curve for CO2.
*   **Moura Costa.** Storage duration divided by an equivalence time - the
    period over which regrowth would absorb an equivalent tonne. Simpler and
    considerably more generous.

Both are reported. Reporting only one would present a contested methodology as
settled, and the disagreement between them is larger than most of the other
uncertainties in this app.

Reversal, and whether the buffer covers it
-------------------------------------------
Registries hold buffer pools against reversal. Whether a buffer is *adequate* is
an empirical question, and where reversal risk is rising with climate - which is
the case for forestry in fire-prone regions - a buffer sized on historical rates
is by construction too small. The buffer assumption is exposed rather than
inherited.

Delivery
--------
A credit for carbon that will be removed over the next thirty years is not the
same asset as carbon already removed. Ex-ante and ex-post credits are separate
rows here, and the future ones are discounted for both timing and the chance
that delivery never happens.

The horizon is doing the work
------------------------------
Over 100 years a 40-year forestry credit is worth about a third of a fossil
tonne. Over 500 years it is worth a fraction of that. There is no single correct
horizon, which is exactly why it is a parameter with the sensitivity reported.

One thing this is not for
--------------------------
A discounted equivalence ratio can be read as a price list for how many
temporary credits substitute for a real reduction. It is not that. It is a
measure of how much less a credit delivers, and the result says so in words
rather than leaving it to a footnote.

Where this connects to code already merged
------------------------------------------
*   ``carbon_marketplace.py`` nets credits at face value against a footprint.
*   ``goals.py`` counts offsets towards reduction targets.
*   ``climate_metrics.py`` implements GWP*, which exists precisely because the
    timing and persistence of a forcing matter. Netting a temporary removal
    against a permanent emission at 1:1 contradicts the reasoning that module
    is built on.

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

# ---------------------------------------------------------------------------
# The Bern decay curve for a pulse of CO2 (IPCC AR5 parameterisation).
#
# ``a0`` is the fraction that stays effectively forever on any horizon a person
# cares about, which is the reason a fossil tonne and a forty-year store are not
# the same asset.
# ---------------------------------------------------------------------------
BERN_A0 = 0.2173
BERN_TERMS = (
    (0.2240, 394.4),
    (0.2824, 36.54),
    (0.2763, 4.304),
)

DEFAULT_HORIZON_YEARS = 100
HORIZON_RANGE = (20, 100, 500, 1000)

# The equivalence time used by the Moura Costa method: the period over which
# growing biomass absorbs a tonne equivalent to the one being stored. Reported
# as a parameter because the choice is contested and it scales the whole answer.
DEFAULT_EQUIVALENCE_TIME = 48.0

# ---------------------------------------------------------------------------
# Durability classes
#
# ``expected_years`` is the nominal storage duration and ``reversal_rate`` the
# annual hazard of losing the store. ``mechanism`` matters as much as the
# number: it tells a holder whether the risk is correlated with the things they
# are already worried about, which a percentage cannot.
# ---------------------------------------------------------------------------
DURABILITY_CLASSES = {
    "soil_carbon": {
        "label": "Soil organic carbon",
        "expected_years": 20.0, "low": 5.0, "high": 50.0,
        "reversal_rate": 0.030, "typical_buffer": 0.10, "family": "biological",
        "mechanism": "One season of conventional tillage can release years of "
                     "accumulation. The store depends on a management practice "
                     "continuing, and practices change with owners and prices.",
    },
    "forestry_tropical": {
        "label": "Tropical afforestation",
        "expected_years": 40.0, "low": 15.0, "high": 100.0,
        "reversal_rate": 0.020, "typical_buffer": 0.15, "family": "biological",
        "mechanism": "Fire, clearance and drought. Fast to accumulate and "
                     "exposed to the same pressures that cleared the land "
                     "originally.",
    },
    "forestry_temperate": {
        "label": "Temperate afforestation",
        "expected_years": 60.0, "low": 25.0, "high": 150.0,
        "reversal_rate": 0.012, "typical_buffer": 0.15, "family": "biological",
        "mechanism": "Fire, disease and harvest. Slower to accumulate than "
                     "tropical planting and less exposed, though fire risk is "
                     "rising in regions that historically had little.",
    },
    "avoided_deforestation": {
        "label": "Avoided deforestation",
        "expected_years": 30.0, "low": 10.0, "high": 80.0,
        "reversal_rate": 0.025, "typical_buffer": 0.20, "family": "biological",
        "mechanism": "Protection lasts as long as the protection does. Carries "
                     "a baseline problem on top of the permanence one, since "
                     "the counterfactual clearance is itself a projection.",
    },
    "blue_carbon": {
        "label": "Mangrove and coastal wetland",
        "expected_years": 60.0, "low": 20.0, "high": 200.0,
        "reversal_rate": 0.015, "typical_buffer": 0.15, "family": "biological",
        "mechanism": "Storm damage, sea level change and coastal development. "
                     "Dense storage per hectare and a concentrated risk.",
    },
    "biochar": {
        "label": "Biochar",
        "expected_years": 500.0, "low": 100.0, "high": 1000.0,
        "reversal_rate": 0.001, "typical_buffer": 0.05, "family": "hybrid",
        "mechanism": "Slow mineralisation in soil. The fraction that is stable "
                     "depends on production temperature, so the class hides "
                     "real variation between suppliers.",
    },
    "mineralisation": {
        "label": "Mineralisation in concrete",
        "expected_years": 1000.0, "low": 500.0, "high": 10000.0,
        "reversal_rate": 0.0002, "typical_buffer": 0.02, "family": "geochemical",
        "mechanism": "Chemically bound. Reversal requires the material to be "
                     "heated, which is not a normal fate for concrete.",
    },
    "enhanced_weathering": {
        "label": "Enhanced rock weathering",
        "expected_years": 10000.0, "low": 1000.0, "high": 100000.0,
        "reversal_rate": 0.00005, "typical_buffer": 0.05, "family": "geochemical",
        "mechanism": "Carbon ends up as dissolved bicarbonate in the ocean. "
                     "Durable; the harder question is measuring how much was "
                     "removed, not whether it stays.",
    },
    "geological_storage": {
        "label": "Geological storage (BECCS or DACCS)",
        "expected_years": 10000.0, "low": 1000.0, "high": 100000.0,
        "reversal_rate": 0.00002, "typical_buffer": 0.02, "family": "geological",
        "mechanism": "Injection into deep saline formations. Leakage rates "
                     "observed so far are very low, and this is the only "
                     "family that is genuinely like-for-like with a fossil "
                     "emission.",
    },
}

DEFAULT_CLASS = "forestry_temperate"

# How the two ton-year methods are labelled in output.
METHODS = ("lashof", "moura_costa")


class PermanenceError(ValueError):
    """Raised for an unknown durability class or an unusable input."""


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


def list_classes() -> list[str]:
    return list(DURABILITY_CLASSES)


def get_class(name: str) -> dict[str, Any]:
    if name not in DURABILITY_CLASSES:
        raise PermanenceError(
            f"Unknown durability class '{name}'. There is no average worth "
            f"taking across these - they span four orders of magnitude in "
            f"storage duration. Known classes: "
            f"{', '.join(sorted(DURABILITY_CLASSES))}."
        )
    return dict(DURABILITY_CLASSES[name])


# ---------------------------------------------------------------------------
# Ton-year accounting
# ---------------------------------------------------------------------------

def atmospheric_fraction(years: float) -> float:
    """Share of a CO2 pulse still airborne after a number of years."""
    time = _non_negative(years)
    total = BERN_A0
    for share, tau in BERN_TERMS:
        total += share * math.exp(-time / tau)
    return total


def cumulative_burden(years: float) -> float:
    """Ton-years imposed by one tonne of CO2 over a horizon.

    The integral of the Bern curve, in closed form rather than numerically -
    it is analytic, and a quadrature here would be a needless source of
    disagreement between runs.
    """
    horizon = _non_negative(years)
    total = BERN_A0 * horizon
    for share, tau in BERN_TERMS:
        total += share * tau * (1.0 - math.exp(-horizon / tau))
    return total


def lashof_equivalence(storage_years: float, horizon_years: float = DEFAULT_HORIZON_YEARS) -> float:
    """Share of a fossil tonne that a temporary store actually offsets.

    Storing a tonne for D years and then releasing it shifts its atmospheric
    burden D years into the future. What the credit avoided is the slice of the
    decay curve pushed beyond the horizon, which is the difference between the
    burden over the full horizon and the burden over what is left of it.
    """
    horizon = _non_negative(horizon_years)
    if horizon <= 0:
        raise PermanenceError(
            "A horizon of zero years cannot distinguish a permanent store from "
            "a temporary one, which is the only thing this calculation does."
        )
    duration = _non_negative(storage_years)
    if duration >= horizon:
        return 1.0

    full = cumulative_burden(horizon)
    if full <= 0:
        return 0.0
    remaining = cumulative_burden(horizon - duration)
    return (full - remaining) / full


def moura_costa_equivalence(
    storage_years: float,
    equivalence_time: float = DEFAULT_EQUIVALENCE_TIME,
) -> float:
    """Storage duration over an equivalence time, capped at one.

    Considerably more generous than Lashof for short stores, and the gap between
    the two is not a rounding difference - it is the reason two credible
    registries can value the same credit very differently.
    """
    period = _non_negative(equivalence_time)
    if period <= 0:
        raise PermanenceError("The equivalence time must be greater than zero.")
    return min(1.0, _non_negative(storage_years) / period)


def expected_storage_years(
    durability_class: str,
    nominal_years: float | None = None,
    reversal_rate: float | None = None,
) -> float:
    """Storage duration after reversal risk, as an expected value.

    A store with an annual hazard of loss does not last its nominal duration on
    average; it lasts the integral of its survival curve. For a low-hazard class
    the two are almost identical, and for soil carbon they are not.
    """
    entry = get_class(durability_class)
    nominal = _non_negative(nominal_years, entry["expected_years"]) or entry["expected_years"]
    rate = reversal_rate if reversal_rate is not None else entry["reversal_rate"]
    rate = _non_negative(rate)

    if rate <= 0:
        return nominal
    return (1.0 - math.exp(-rate * nominal)) / rate


def buffer_adequacy(
    durability_class: str,
    buffer_share: float | None = None,
    horizon_years: float = DEFAULT_HORIZON_YEARS,
) -> dict[str, Any]:
    """Whether the buffer held against a credit covers its reversal risk.

    Reported both ways round. A buffer that covers the risk is a real quality
    signal and saying so matters as much as flagging one that does not.
    """
    entry = get_class(durability_class)
    offered = entry["typical_buffer"] if buffer_share is None else _non_negative(buffer_share)
    exposure = min(_non_negative(horizon_years), entry["expected_years"])
    required = 1.0 - math.exp(-entry["reversal_rate"] * exposure)

    return {
        "class": durability_class,
        "offered": offered,
        "required": required,
        "shortfall": max(0.0, required - offered),
        "adequate": offered >= required,
        "exposure_years": exposure,
        "mechanism": entry["mechanism"],
    }


def delivery_discount(
    delivery_years: float = 0.0,
    delivery_probability: float = 1.0,
    horizon_years: float = DEFAULT_HORIZON_YEARS,
) -> dict[str, Any]:
    """What a promise of future removal is worth against a delivered one.

    Two separate reductions, kept separate: the removal happens later, so it
    holds carbon out of the atmosphere for less of the horizon; and it may not
    happen at all.
    """
    horizon = _non_negative(horizon_years, DEFAULT_HORIZON_YEARS)
    delay = min(_non_negative(delivery_years), horizon)
    probability = min(1.0, max(0.0, _as_float(delivery_probability, 1.0)))

    timing = (horizon - delay) / horizon if horizon > 0 else 0.0
    return {
        "delivery_years": delay,
        "delivery_probability": probability,
        "timing_factor": timing,
        "combined_factor": timing * probability,
        "ex_ante": delay > 0 or probability < 1.0,
    }


def credit_value(
    durability_class: str,
    tonnes: float = 1.0,
    horizon_years: float = DEFAULT_HORIZON_YEARS,
    buffer_share: float | None = None,
    nominal_years: float | None = None,
    delivery_years: float = 0.0,
    delivery_probability: float = 1.0,
    equivalence_time: float = DEFAULT_EQUIVALENCE_TIME,
    label: str | None = None,
) -> dict[str, Any]:
    """What a credit is worth against a fossil tonne, by both methods."""
    entry = get_class(durability_class)
    quantity = _non_negative(tonnes)
    nominal = _non_negative(nominal_years, entry["expected_years"]) or entry["expected_years"]

    effective = expected_storage_years(durability_class, nominal)
    lashof = lashof_equivalence(effective, horizon_years)
    moura = moura_costa_equivalence(effective, equivalence_time)
    delivery = delivery_discount(delivery_years, delivery_probability, horizon_years)
    buffer = buffer_adequacy(durability_class, buffer_share, horizon_years)

    return {
        "class": durability_class,
        "label": label or entry["label"],
        "family": entry["family"],
        "tonnes": quantity,
        "horizon_years": _non_negative(horizon_years, DEFAULT_HORIZON_YEARS),
        "nominal_years": nominal,
        "effective_years": effective,
        "reversal_loss_years": nominal - effective,
        "lashof_ratio": lashof,
        "moura_costa_ratio": moura,
        "method_disagreement": abs(moura - lashof),
        "lashof_tonnes": quantity * lashof * delivery["combined_factor"],
        "moura_costa_tonnes": quantity * moura * delivery["combined_factor"],
        "delivery": delivery,
        "buffer": buffer,
        "mechanism": entry["mechanism"],
        "caveat": (
            "This ratio measures how much less this credit delivers than a "
            "reduction of the same size. It is not a conversion rate for "
            "buying the difference."
        ),
    }


def portfolio_value(
    credits: list[dict[str, Any]] | None,
    horizon_years: float = DEFAULT_HORIZON_YEARS,
    equivalence_time: float = DEFAULT_EQUIVALENCE_TIME,
) -> dict[str, Any]:
    """Score a mixed holding, and say which part of it is the weak one.

    A portfolio's durability is not its average. One large short-lived holding
    determines what the portfolio is worth far more than several small durable
    ones, so the concentration is reported rather than averaged away.
    """
    rows = []
    for entry in credits or []:
        quantity = _non_negative(entry.get("tonnes"))
        if quantity <= 0:
            continue
        rows.append(credit_value(
            entry.get("class"),
            quantity,
            horizon_years,
            entry.get("buffer_share"),
            entry.get("nominal_years"),
            _non_negative(entry.get("delivery_years")),
            entry.get("delivery_probability", 1.0),
            equivalence_time,
            entry.get("label"),
        ))

    face = sum(row["tonnes"] for row in rows)
    lashof = sum(row["lashof_tonnes"] for row in rows)
    moura = sum(row["moura_costa_tonnes"] for row in rows)

    rows.sort(key=lambda row: row["tonnes"] - row["lashof_tonnes"], reverse=True)
    inadequate = [row for row in rows if not row["buffer"]["adequate"]]
    ex_ante = [row for row in rows if row["delivery"]["ex_ante"]]

    return {
        "credits": rows,
        "face_value_tonnes": face,
        "lashof_tonnes": lashof,
        "moura_costa_tonnes": moura,
        "lashof_ratio": (lashof / face) if face > 0 else 0.0,
        "moura_costa_ratio": (moura / face) if face > 0 else 0.0,
        "discount_tonnes": face - lashof,
        "horizon_years": _non_negative(horizon_years, DEFAULT_HORIZON_YEARS),
        "weakest": rows[0]["class"] if rows else None,
        "weakest_share": (
            (rows[0]["tonnes"] - rows[0]["lashof_tonnes"]) / (face - lashof)
            if rows and face > lashof else 0.0
        ),
        "inadequate_buffers": [row["class"] for row in inadequate],
        "ex_ante_tonnes": sum(row["tonnes"] for row in ex_ante),
        "caveat": (
            "Face value is what was bought. The discounted figures are what it "
            "delivers over the stated horizon, and neither is a licence to "
            "emit the difference."
        ),
    }


def like_for_like(
    fossil_tonnes: float,
    durability_class: str,
    horizon_years: float = DEFAULT_HORIZON_YEARS,
) -> dict[str, Any]:
    """How much of a class it takes to genuinely neutralise a fossil tonne.

    The caveat travels with the result rather than sitting in a docstring,
    because this is the number most likely to be quoted on its own.
    """
    quantity = _non_negative(fossil_tonnes)
    value = credit_value(durability_class, 1.0, horizon_years)

    ratio = value["lashof_ratio"]
    required = quantity / ratio if ratio > 0 else None

    return {
        "fossil_tonnes": quantity,
        "class": durability_class,
        "label": value["label"],
        "horizon_years": value["horizon_years"],
        "lashof_ratio": ratio,
        "moura_costa_ratio": value["moura_costa_ratio"],
        "credits_required": required,
        "credits_required_moura": (
            quantity / value["moura_costa_ratio"] if value["moura_costa_ratio"] > 0 else None
        ),
        "caveat": (
            "Buying this many temporary credits is not equivalent to not "
            "emitting the tonne. It is what it would take for the ton-year "
            "arithmetic to balance over this horizon, and the arithmetic "
            "balancing is not the same as the emission not happening."
        ),
    }


def sensitivity(
    durability_class: str,
    horizons: tuple[int, ...] = HORIZON_RANGE,
) -> list[dict[str, Any]]:
    """The same credit across horizons, because the horizon decides."""
    rows = []
    for horizon in horizons:
        value = credit_value(durability_class, 1.0, horizon)
        rows.append({
            "horizon_years": horizon,
            "lashof_ratio": value["lashof_ratio"],
            "moura_costa_ratio": value["moura_costa_ratio"],
            "disagreement": value["method_disagreement"],
        })
    return rows


def compare_classes(
    horizon_years: float = DEFAULT_HORIZON_YEARS,
    equivalence_time: float = DEFAULT_EQUIVALENCE_TIME,
) -> list[dict[str, Any]]:
    """Every class at one horizon, ranked by what it actually delivers."""
    rows = []
    for name in list_classes():
        value = credit_value(name, 1.0, horizon_years, equivalence_time=equivalence_time)
        rows.append({
            "class": name,
            "label": value["label"],
            "family": value["family"],
            "nominal_years": value["nominal_years"],
            "effective_years": value["effective_years"],
            "lashof_ratio": value["lashof_ratio"],
            "moura_costa_ratio": value["moura_costa_ratio"],
            "buffer_adequate": value["buffer"]["adequate"],
            "mechanism": value["mechanism"],
        })
    rows.sort(key=lambda row: row["lashof_ratio"], reverse=True)
    return rows


def get_permanence_insights(result: dict[str, Any] | None) -> list[str]:
    """Plain statements about what the numbers mean, in priority order."""
    if not result:
        return ["Add some credits to see what they deliver against an emission."]

    insights: list[str] = []
    face = _as_float(result.get("face_value_tonnes"))
    lashof = _as_float(result.get("lashof_tonnes"))
    ratio = _as_float(result.get("lashof_ratio"))
    horizon = _as_float(result.get("horizon_years"), DEFAULT_HORIZON_YEARS)

    if face > 0 and ratio < 0.5:
        insights.append(
            f"{face:,.1f} tonnes of credits deliver {lashof:,.1f} tonnes of "
            f"permanent-equivalent removal over {horizon:.0f} years - about "
            f"{ratio * 100:.0f}% of face value. The gap is not fraud; it is "
            f"what temporary storage is worth against a permanent emission."
        )
    elif face > 0:
        insights.append(
            f"{face:,.1f} tonnes of credits deliver {lashof:,.1f} tonnes over "
            f"{horizon:.0f} years, {ratio * 100:.0f}% of face value. That is a "
            f"durable portfolio by the standards of this market."
        )

    moura = _as_float(result.get("moura_costa_ratio"))
    if abs(moura - ratio) > 0.1:
        insights.append(
            f"The two accepted ton-year methods disagree here: "
            f"{ratio * 100:.0f}% by Lashof against {moura * 100:.0f}% by Moura "
            f"Costa. Both are defensible and the difference is larger than most "
            f"other uncertainties in this app, so both are reported rather than "
            f"one being presented as settled."
        )

    weakest = result.get("weakest")
    share = _as_float(result.get("weakest_share"))
    if weakest and share > 0.4:
        insights.append(
            f"{get_class(weakest)['label']} accounts for {share * 100:.0f}% of "
            f"the total discount. A portfolio's durability is not its average - "
            f"one large short-lived holding decides most of the answer."
        )

    inadequate = result.get("inadequate_buffers") or []
    if inadequate:
        labels = ", ".join(get_class(name)["label"].lower() for name in inadequate)
        insights.append(
            f"The buffer held against {labels} is thinner than the reversal "
            f"risk of the class implies. Buffers sized on historical rates are "
            f"by construction too small where the risk is rising."
        )

    ex_ante = _as_float(result.get("ex_ante_tonnes"))
    if ex_ante > 0:
        insights.append(
            f"{ex_ante:,.1f} tonnes of this is a promise of future removal "
            f"rather than carbon already removed. A footprint reduced today by "
            f"a removal scheduled for 2040 has not been reduced today."
        )

    insights.append(
        "None of this is a conversion rate for buying the difference. It "
        "measures how much less a credit delivers than a reduction of the same "
        "size, which is an argument for the reduction."
    )
    return insights


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_permanence_db() -> bool:
    """Create the table if it does not exist yet."""
    conn = None
    try:
        conn = _connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS permanence_portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                horizon_years REAL NOT NULL,
                face_value_tonnes REAL NOT NULL,
                lashof_tonnes REAL NOT NULL,
                moura_costa_tonnes REAL NOT NULL,
                detail_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Unable to initialise permanence table: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def save_portfolio(user_id: int, name: str, result: dict[str, Any]) -> int | None:
    """Persist a scored portfolio. Returns the row id or None."""
    init_permanence_db()
    conn = None
    try:
        conn = _connect()
        cursor = conn.execute(
            """
            INSERT INTO permanence_portfolios (
                user_id, name, horizon_years, face_value_tonnes,
                lashof_tonnes, moura_costa_tonnes, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                (name or "Portfolio").strip() or "Portfolio",
                _as_float(result.get("horizon_years"), DEFAULT_HORIZON_YEARS),
                _as_float(result.get("face_value_tonnes")),
                _as_float(result.get("lashof_tonnes")),
                _as_float(result.get("moura_costa_tonnes")),
                json.dumps(result, default=str),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as exc:
        logger.error("Unable to save permanence portfolio: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def get_portfolios(user_id: int, limit: int = 25) -> list[dict[str, Any]]:
    """A user's saved portfolios, newest first."""
    init_permanence_db()
    conn = None
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, name, horizon_years, face_value_tonnes, lashof_tonnes,
                   moura_costa_tonnes, detail_json, created_at
            FROM permanence_portfolios
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT ?
            """,
            (user_id, int(limit)),
        ).fetchall()

        portfolios = []
        for row in rows:
            record = dict(row)
            try:
                record["detail"] = json.loads(record.pop("detail_json") or "{}")
            except (TypeError, ValueError):
                record["detail"] = {}
            portfolios.append(record)
        return portfolios
    except sqlite3.Error as exc:
        logger.error("Unable to load permanence portfolios: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def delete_portfolio(portfolio_id: int) -> bool:
    """Delete a saved portfolio."""
    init_permanence_db()
    conn = None
    try:
        conn = _connect()
        cursor = conn.execute(
            "DELETE FROM permanence_portfolios WHERE id = ?", (portfolio_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as exc:
        logger.error("Unable to delete permanence portfolio: %s", exc)
        return False
    finally:
        if conn:
            conn.close()
