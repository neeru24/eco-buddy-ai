"""Carbon financed by a household's savings, pension and investments.

This app measures what a user burns, drives, eats and throws away. It does not
measure what their money does while they sleep, and for anyone with a few
years of pension contributions that is frequently the largest line in their
real footprint. The app currently reports it as zero.

The mechanics are not exotic. Owning a millionth of a company makes you
responsible, under the standard attribution, for a millionth of what that
company emits. A default workplace pension is usually a global equity tracker,
which holds oil majors, cement, steel, aviation and utilities in proportion to
their market weight. The user picked none of that and in most cases has never
been shown it.

What makes this worth a page rather than a footnote is the asymmetry of the
action attached to it. Every other lever in this app is a grind - cutting
driving by a third takes a year of effort. Switching a pension to a lower
carbon fund is a form, once, and it routinely moves more tonnes.

The model
---------
Working per unit invested keeps this tractable without per-company holdings
data::

    financed emissions = holding value x carbon intensity of the holding

Intensity is expressed as tonnes CO2e per million of currency invested, which
is the unit financed-emissions reporting conventionally uses. A user who knows
their fund's sector breakdown can build a custom intensity from sector
weights instead of picking the nearest archetype.

What this is not
----------------
Financed emissions are an *attribution*, not a physical flow the user
controls. Selling a share transfers ownership; it does not shut a refinery.
The module carries that caveat in the data it returns rather than leaving the
page to imply more than the method supports, and `get_caveats()` exists
precisely so the honest limitations cannot be quietly dropped from the UI.

The figures here are documented archetypes, not claims about any named
product. They are the right order of magnitude for the decision a user is
actually making - default fund or not - and they are not investment advice.

Accounting boundary
-------------------
Financed emissions are deliberately **not** added to the operational
footprint. They sit on a different accounting boundary, and summing them would
produce a number that double-counts against the companies' own reporting and
means nothing. They are reported alongside, and `compare_to_operational()`
exists to make the size comparison without merging the two.

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

# Intensities are quoted per million invested. Every downstream calculation
# divides by this, so it lives in one place.
INTENSITY_BASIS = 1_000_000.0

# Representative carbon intensities in tonnes CO2e per million invested,
# covering scope 1 and 2 of the underlying holdings. These are archetypes
# illustrating the *spread* between fund types - which is the decision a user
# faces - not figures for any specific product. Real funds publish their own,
# and `custom_portfolio()` exists for anyone who has them.
FUND_ARCHETYPES = {
    "Global equity tracker": {
        "asset_class": "Equity",
        "intensity": 55.0,
        "description": "Whole-market index. The typical workplace pension default.",
        "basis": "Market-cap weighted global index, scope 1+2 of holdings.",
    },
    "Developed markets tracker": {
        "asset_class": "Equity",
        "intensity": 46.0,
        "description": "Developed economies only. Slightly lighter than global.",
        "basis": "Developed-market index, scope 1+2 of holdings.",
    },
    "Emerging markets equity": {
        "asset_class": "Equity",
        "intensity": 95.0,
        "description": "Heavier in materials, utilities and coal-fired grids.",
        "basis": "Emerging-market index, scope 1+2 of holdings.",
    },
    "ESG screened equity": {
        "asset_class": "Equity",
        "intensity": 32.0,
        "description": "Worst offenders excluded. A partial screen, not a solution.",
        "basis": "Broad ESG exclusion index, scope 1+2 of holdings.",
    },
    "Fossil fuel free equity": {
        "asset_class": "Equity",
        "intensity": 20.0,
        "description": "No fossil fuel reserves. Still holds heavy industry.",
        "basis": "Fossil-free screened index, scope 1+2 of holdings.",
    },
    "Paris aligned benchmark": {
        "asset_class": "Equity",
        "intensity": 15.0,
        "description": "Constructed to a declining carbon budget year on year.",
        "basis": "EU Paris-Aligned Benchmark construction rules.",
    },
    "Climate solutions / clean energy": {
        "asset_class": "Equity",
        "intensity": 28.0,
        "description": "Renewables and efficiency. Not zero - manufacturing emits.",
        "basis": "Clean energy thematic index, scope 1+2 of holdings.",
    },
    "Energy sector fund": {
        "asset_class": "Equity",
        "intensity": 380.0,
        "description": "Concentrated in oil, gas and coal. The high end, deliberately shown.",
        "basis": "Energy sector index, scope 1+2 of holdings.",
    },
    "Commodities / natural resources": {
        "asset_class": "Commodity",
        "intensity": 260.0,
        "description": "Mining, materials and extraction.",
        "basis": "Broad natural resources index, scope 1+2 of holdings.",
    },
    "Property / REIT": {
        "asset_class": "Property",
        "intensity": 45.0,
        "description": "Building operational emissions dominate.",
        "basis": "Listed real estate index, scope 1+2 of holdings.",
    },
    "Corporate bonds": {
        "asset_class": "Fixed income",
        "intensity": 38.0,
        "description": "Lending to the same companies equities own.",
        "basis": "Investment-grade corporate index, scope 1+2 of issuers.",
    },
    "Government bonds": {
        "asset_class": "Fixed income",
        "intensity": 12.0,
        "description": "Sovereign debt. Attribution here is genuinely contested.",
        "basis": "Sovereign index, production-based national emissions.",
    },
    "Green bonds": {
        "asset_class": "Fixed income",
        "intensity": 5.0,
        "description": "Proceeds ring-fenced for climate projects.",
        "basis": "Green bond index, use-of-proceeds basis.",
    },
    "Cash / money market": {
        "asset_class": "Cash",
        "intensity": 8.0,
        "description": "Lent on by the bank, so not actually zero.",
        "basis": "Short-term lending, attributed at bank book average.",
    },
    "Balanced default (60/40)": {
        "asset_class": "Mixed",
        "intensity": 42.0,
        "description": "The classic 60% equity, 40% bond default fund.",
        "basis": "Weighted blend of the equity and bond archetypes above.",
    },
}

DEFAULT_CURRENT_FUND = "Global equity tracker"
DEFAULT_PROPOSED_FUND = "Paris aligned benchmark"

# Sector intensities in tonnes CO2e per million invested, for users who know
# their fund's actual breakdown. The spread across sectors is the entire
# reason a screened fund can be so much lighter than a tracker: a handful of
# sectors carry almost all of the carbon.
SECTOR_INTENSITIES = {
    "Energy (oil, gas, coal)": 480.0,
    "Utilities": 350.0,
    "Materials (cement, steel, chemicals)": 300.0,
    "Industrials": 90.0,
    "Consumer staples": 45.0,
    "Real estate": 40.0,
    "Consumer discretionary": 30.0,
    "Healthcare": 15.0,
    "Financials": 12.0,
    "Information technology": 12.0,
    "Communication services": 10.0,
}

# Typical long-run assumptions for projecting a pension forward. All are
# overridable; none are predictions.
DEFAULT_GROWTH_RATE = 0.05
DEFAULT_YEARS = 25
MAX_YEARS = 60

# Listed-company carbon intensity has been falling for years as grids clean up
# and heavy industry shrinks as a share of index value. Ignoring that would
# overstate the benefit of switching, because part of the improvement arrives
# whether the user acts or not. Applied to both sides of the comparison.
DEFAULT_DECARBONISATION_RATE = 0.04
MAX_DECARBONISATION_RATE = 0.20

# Rough operational comparisons, in tonnes CO2e per year, used only to make a
# financed total legible. Deliberately conservative.
COMPARISON_ACTIONS = {
    "going car free": 2.4,
    "a year of a vegan diet": 0.8,
    "a return long-haul flight": 1.6,
    "switching to a heat pump": 1.8,
    "a year of home electricity": 1.0,
}


class PortfolioError(ValueError):
    """Raised when a portfolio cannot be modelled."""


# --- Catalogue --------------------------------------------------------------


def list_fund_archetypes(asset_class: str | None = None) -> list[dict[str, Any]]:
    """Return the fund catalogue, cleanest first."""
    funds = [
        {"name": name, **details}
        for name, details in FUND_ARCHETYPES.items()
        if not asset_class or details["asset_class"] == asset_class
    ]
    return sorted(funds, key=lambda item: item["intensity"])


def list_asset_classes() -> list[str]:
    """Return the distinct asset classes in the catalogue."""
    return sorted({details["asset_class"] for details in FUND_ARCHETYPES.values()})


def list_sectors() -> list[dict[str, Any]]:
    """Return sector intensities, dirtiest first - the useful reading order."""
    return sorted(
        [{"name": name, "intensity": value} for name, value in SECTOR_INTENSITIES.items()],
        key=lambda item: item["intensity"],
        reverse=True,
    )


def get_fund(name: str) -> dict[str, Any]:
    """Return one archetype, falling back to the default rather than raising."""
    details = FUND_ARCHETYPES.get(name)
    if not details:
        details = FUND_ARCHETYPES[DEFAULT_CURRENT_FUND]
        name = DEFAULT_CURRENT_FUND
    return {"name": name, **details}


def fund_intensity(name: str) -> float:
    """Carbon intensity of a fund archetype, tonnes per million invested."""
    return get_fund(name)["intensity"]


# --- Custom portfolios ------------------------------------------------------


def _clean_amount(value: float, field: str = "amount") -> float:
    """Coerce a monetary or numeric input into a usable non-negative float."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise PortfolioError(f"{field} must be a number")
    if math.isnan(number) or math.isinf(number):
        raise PortfolioError(f"{field} must be a real number")
    if number < 0:
        raise PortfolioError(f"{field} cannot be negative")
    return number


def custom_portfolio(sector_weights: dict[str, float]) -> dict[str, Any]:
    """Build a portfolio intensity from sector weights.

    Weights are normalised rather than required to sum to one, because a user
    reading percentages off a fund factsheet will not have them add up
    exactly, and refusing their input over a rounding error would be useless
    pedantry.
    """
    if not sector_weights:
        raise PortfolioError("At least one sector weight is required")

    cleaned = {}
    for sector, weight in sector_weights.items():
        if sector not in SECTOR_INTENSITIES:
            continue
        try:
            value = float(weight)
        except (TypeError, ValueError):
            continue
        if value <= 0 or math.isnan(value) or math.isinf(value):
            continue
        cleaned[sector] = value

    total_weight = sum(cleaned.values())
    if total_weight <= 0:
        raise PortfolioError("No usable sector weights were supplied")

    breakdown = []
    intensity = 0.0
    for sector, weight in cleaned.items():
        share = weight / total_weight
        contribution = share * SECTOR_INTENSITIES[sector]
        intensity += contribution
        breakdown.append(
            {
                "sector": sector,
                "weight": share,
                "sector_intensity": SECTOR_INTENSITIES[sector],
                "contribution": contribution,
            }
        )

    for entry in breakdown:
        entry["share_of_carbon"] = (
            entry["contribution"] / intensity if intensity > 0 else 0.0
        )

    breakdown.sort(key=lambda item: item["contribution"], reverse=True)
    return {
        "intensity": intensity,
        "breakdown": breakdown,
        "sectors": len(breakdown),
        "nearest_archetype": nearest_archetype(intensity),
    }


def nearest_archetype(intensity: float) -> str:
    """The catalogue entry closest to a computed intensity, for orientation."""
    try:
        target = float(intensity)
    except (TypeError, ValueError):
        return DEFAULT_CURRENT_FUND
    return min(
        FUND_ARCHETYPES.items(),
        key=lambda item: abs(item[1]["intensity"] - target),
    )[0]


def concentration(breakdown: list[dict[str, Any]], top_n: int = 3) -> dict[str, Any]:
    """Share of a portfolio's carbon coming from its worst few sectors.

    Usually startling, and it is the number that makes a screened fund make
    sense: a small slice of the portfolio carries most of the carbon.
    """
    if not breakdown:
        return {"top_sectors": [], "share_of_carbon": 0.0, "share_of_value": 0.0}

    ordered = sorted(breakdown, key=lambda item: item["contribution"], reverse=True)
    top = ordered[: max(1, int(top_n))]
    return {
        "top_sectors": [entry["sector"] for entry in top],
        "share_of_carbon": sum(entry["share_of_carbon"] for entry in top),
        "share_of_value": sum(entry["weight"] for entry in top),
    }


# --- Financed emissions -----------------------------------------------------


def financed_emissions(value: float, intensity: float) -> float:
    """Tonnes CO2e attributable to a holding of a given value and intensity."""
    holding = _clean_amount(value, "Holding value")
    carbon_intensity = _clean_amount(intensity, "Intensity")
    return holding * carbon_intensity / INTENSITY_BASIS


def portfolio_emissions(holdings: list[dict[str, Any]]) -> dict[str, Any]:
    """Financed emissions of several holdings, with per-holding detail.

    ``holdings`` is a list of dicts with ``name``, ``value`` and either
    ``fund`` (an archetype name) or ``intensity``.
    """
    if not holdings:
        raise PortfolioError("At least one holding is required")

    lines = []
    total_value = 0.0
    total_emissions = 0.0

    for holding in holdings:
        name = str(holding.get("name") or holding.get("fund") or "Holding")
        value = _clean_amount(holding.get("value", 0.0), f"Value of {name}")
        if "intensity" in holding and holding["intensity"] is not None:
            intensity = _clean_amount(holding["intensity"], f"Intensity of {name}")
        else:
            intensity = fund_intensity(holding.get("fund"))

        emissions = value * intensity / INTENSITY_BASIS
        total_value += value
        total_emissions += emissions
        lines.append(
            {
                "name": name,
                "value": value,
                "intensity": intensity,
                "emissions": emissions,
            }
        )

    for line in lines:
        line["share_of_value"] = (line["value"] / total_value) if total_value > 0 else 0.0
        line["share_of_carbon"] = (
            (line["emissions"] / total_emissions) if total_emissions > 0 else 0.0
        )

    lines.sort(key=lambda item: item["emissions"], reverse=True)
    blended = (total_emissions * INTENSITY_BASIS / total_value) if total_value > 0 else 0.0

    return {
        "total_value": total_value,
        "total_emissions": total_emissions,
        "blended_intensity": blended,
        "holdings": lines,
        "nearest_archetype": nearest_archetype(blended),
    }


# --- Switching --------------------------------------------------------------

def compare_funds(value: float, current_intensity: float, proposed_intensity: float) -> dict[str, Any]:
    """Annual effect of moving a holding from one intensity to another."""
    holding = _clean_amount(value, "Holding value")
    current = _clean_amount(current_intensity, "Current intensity")
    proposed = _clean_amount(proposed_intensity, "Proposed intensity")

    current_emissions = holding * current / INTENSITY_BASIS
    proposed_emissions = holding * proposed / INTENSITY_BASIS
    avoided = current_emissions - proposed_emissions
    percent = (avoided / current_emissions * 100.0) if current_emissions > 0 else 0.0

    return {
        "holding_value": holding,
        "current_intensity": current,
        "proposed_intensity": proposed,
        "current_emissions": current_emissions,
        "proposed_emissions": proposed_emissions,
        "annual_avoided": avoided,
        "percent_avoided": percent,
        "is_improvement": avoided > 0,
    }


def project_switch(
    value: float,
    annual_contribution: float,
    current_intensity: float,
    proposed_intensity: float,
    years: int = DEFAULT_YEARS,
    growth_rate: float = DEFAULT_GROWTH_RATE,
    decarbonisation_rate: float = DEFAULT_DECARBONISATION_RATE,
) -> dict[str, Any]:
    """Cumulative effect of a switch over the years left until retirement.

    Contributions compound, and so does the avoided carbon, which is why a
    single-year figure understates a pension switch badly.

    The decarbonisation rate is applied to *both* sides. Listed-company
    intensity has been falling anyway, and crediting a fund switch with
    improvement that would have happened regardless would overstate the case
    for it. The honest number is the gap between the two declining curves.
    """
    balance_start = _clean_amount(value, "Starting value")
    contribution = _clean_amount(annual_contribution, "Annual contribution")
    current = _clean_amount(current_intensity, "Current intensity")
    proposed = _clean_amount(proposed_intensity, "Proposed intensity")

    try:
        horizon = int(years)
    except (TypeError, ValueError):
        horizon = DEFAULT_YEARS
    horizon = max(1, min(MAX_YEARS, horizon))

    try:
        growth = float(growth_rate)
    except (TypeError, ValueError):
        growth = DEFAULT_GROWTH_RATE
    growth = max(-0.5, min(0.5, growth))

    try:
        decline = float(decarbonisation_rate)
    except (TypeError, ValueError):
        decline = DEFAULT_DECARBONISATION_RATE
    decline = max(0.0, min(MAX_DECARBONISATION_RATE, decline))

    balance = balance_start
    cumulative_current = 0.0
    cumulative_proposed = 0.0
    timeline = []

    for year in range(1, horizon + 1):
        balance = balance * (1.0 + growth) + contribution
        decay = (1.0 - decline) ** year
        current_year = balance * current * decay / INTENSITY_BASIS
        proposed_year = balance * proposed * decay / INTENSITY_BASIS

        cumulative_current += current_year
        cumulative_proposed += proposed_year
        timeline.append(
            {
                "year": year,
                "balance": balance,
                "current_emissions": current_year,
                "proposed_emissions": proposed_year,
                "avoided": current_year - proposed_year,
                "cumulative_avoided": cumulative_current - cumulative_proposed,
            }
        )

    return {
        "years": horizon,
        "final_balance": balance,
        "cumulative_current": cumulative_current,
        "cumulative_proposed": cumulative_proposed,
        "cumulative_avoided": cumulative_current - cumulative_proposed,
        "annual_average_avoided": (cumulative_current - cumulative_proposed) / horizon,
        "growth_rate": growth,
        "decarbonisation_rate": decline,
        "timeline": timeline,
    }


def compare_to_operational(financed_tonnes: float, operational_tonnes: float) -> dict[str, Any]:
    """Size a financed total against the footprint the app already measures.

    Explicitly a comparison and not a sum. The two sit on different
    accounting boundaries and adding them would double-count against the
    reporting of the companies involved.
    """
    financed = _clean_amount(financed_tonnes, "Financed emissions")
    operational = _clean_amount(operational_tonnes, "Operational emissions")

    ratio = (financed / operational) if operational > 0 else 0.0
    if ratio >= 2.0:
        verdict = "dominates"
    elif ratio >= 1.0:
        verdict = "larger"
    elif ratio >= 0.5:
        verdict = "comparable"
    elif ratio > 0:
        verdict = "smaller"
    else:
        verdict = "negligible"

    return {
        "financed": financed,
        "operational": operational,
        "ratio": ratio,
        "combined_view": financed + operational,
        "verdict": verdict,
        "explanation": _comparison_explanation(verdict, ratio),
        "boundary_note": (
            "These are not added together anywhere in the app. Financed "
            "emissions sit on a different accounting boundary and summing "
            "them would double-count against the companies' own reporting."
        ),
    }


def _comparison_explanation(verdict: str, ratio: float) -> str:
    """A plain sentence sizing financed emissions against operational ones."""
    if verdict == "dominates":
        return (
            f"Your investments finance about {ratio:.1f} times the emissions of "
            f"everything else you do. Nothing else on your list is close."
        )
    if verdict == "larger":
        return (
            f"Your investments finance more carbon than your entire day-to-day "
            f"footprint - about {ratio:.1f} times as much."
        )
    if verdict == "comparable":
        return (
            f"Your investments finance roughly {ratio * 100:.0f}% as much carbon "
            f"as your day-to-day footprint. It belongs in the same conversation."
        )
    if verdict == "smaller":
        return (
            f"Your investments finance about {ratio * 100:.0f}% as much carbon as "
            f"your day-to-day footprint - real, but not the biggest lever you have."
        )
    return "There is not enough invested here for financed emissions to matter yet."


def equivalent_actions(tonnes: float) -> list[dict[str, Any]]:
    """Express a carbon figure as the operational actions it is worth.

    A pension switch measured in tonnes means nothing to most people. The same
    number expressed as years of going car-free lands.
    """
    try:
        amount = max(0.0, float(tonnes))
    except (TypeError, ValueError):
        amount = 0.0

    return sorted(
        [
            {
                "action": action,
                "annual_tonnes": annual,
                "equivalent_years": amount / annual if annual > 0 else 0.0,
            }
            for action, annual in COMPARISON_ACTIONS.items()
        ],
        key=lambda item: item["equivalent_years"],
        reverse=True,
    )


def get_switch_advice(
    comparison: dict[str, Any],
    projection: dict[str, Any] | None = None,
) -> list[str]:
    """Advice that follows from the numbers, with the limitations attached."""
    advice = []

    if not comparison.get("is_improvement"):
        advice.append(
            "The fund you are considering is not lighter than what you hold. "
            "Check the intensity figures before moving anything."
        )
        return advice

    advice.append(
        f"Switching cuts the carbon financed by this holding by "
        f"{comparison['percent_avoided']:.0f}%, or "
        f"{comparison['annual_avoided']:.2f} tonnes a year."
    )

    if projection:
        advice.append(
            f"Over {projection['years']} years of contributions that compounds "
            f"to about {projection['cumulative_avoided']:.0f} tonnes - and that "
            f"is after allowing for the market getting cleaner on its own."
        )

    advice.append(
        "Check the fund is actually available in your scheme, and look at "
        "charges and diversification before switching. This is a carbon "
        "comparison, not investment advice."
    )
    return advice


def get_caveats() -> list[str]:
    """Limitations of the method, kept in the module so they cannot be dropped.

    A page that showed the tonnage without these would be overclaiming, and
    the criticisms are well founded enough that leaving them out would be a
    fair reason to distrust the whole feature.
    """
    return [
        (
            "This is an attribution, not a switch you can flip. Selling shares "
            "moves ownership to another investor; it does not by itself reduce "
            "what the company emits."
        ),
        (
            "Divestment and engagement work on different timescales. Staying "
            "invested and voting is a defensible strategy, and some funds do it "
            "well."
        ),
        (
            "The figures cover scope 1 and 2 of the underlying holdings. Scope 3 "
            "would be far larger for most sectors and is not consistently "
            "reported, so it is excluded rather than guessed."
        ),
        (
            "Fund intensities here are archetypes illustrating the spread "
            "between fund types. Your actual fund publishes its own figure and "
            "you should use that where you have it."
        ),
        (
            "A lower carbon fund is not automatically a better investment. "
            "Charges, diversification and your scheme's options all matter, and "
            "none of them are modelled here."
        ),
    ]


# --- Persistence ------------------------------------------------------------


def _connect() -> sqlite3.Connection:
    """Open a connection with the portfolio table guaranteed to exist."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS investment_portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            holdings TEXT NOT NULL,
            total_value REAL NOT NULL,
            total_emissions REAL NOT NULL,
            blended_intensity REAL NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def save_portfolio(user_id: int, name: str, result: dict[str, Any]) -> int | None:
    """Persist a portfolio and the emissions it financed."""
    if not user_id:
        return None

    conn = _connect()
    try:
        cursor = conn.execute(
            """
            INSERT INTO investment_portfolios (
                user_id, name, holdings, total_value, total_emissions,
                blended_intensity, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                str(name or "Portfolio"),
                json.dumps(result.get("holdings", [])),
                float(result.get("total_value", 0.0)),
                float(result.get("total_emissions", 0.0)),
                float(result.get("blended_intensity", 0.0)),
                datetime.datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except (sqlite3.Error, TypeError, ValueError):
        logger.exception("Failed to save portfolio")
        return None
    finally:
        conn.close()


def get_portfolios(user_id: int, limit: int = 25) -> list[dict[str, Any]]:
    """Return saved portfolios for a user, newest first."""
    if not user_id:
        return []

    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT id, name, holdings, total_value, total_emissions,
                   blended_intensity, created_at
            FROM investment_portfolios
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(user_id), int(limit)),
        ).fetchall()
    except sqlite3.Error:
        logger.exception("Failed to read portfolios")
        return []
    finally:
        conn.close()

    portfolios = []
    for row in rows:
        try:
            holdings = json.loads(row[2])
        except (TypeError, ValueError):
            holdings = []
        portfolios.append(
            {
                "id": row[0],
                "name": row[1],
                "holdings": holdings,
                "total_value": row[3],
                "total_emissions": row[4],
                "blended_intensity": row[5],
                "created_at": row[6],
            }
        )
    return portfolios


def delete_portfolio(user_id: int, portfolio_id: int) -> bool:
    """Delete one saved portfolio. Scoped by user so ids cannot be guessed."""
    if not user_id or not portfolio_id:
        return False

    conn = _connect()
    try:
        cursor = conn.execute(
            "DELETE FROM investment_portfolios WHERE id = ? AND user_id = ?",
            (int(portfolio_id), int(user_id)),
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error:
        logger.exception("Failed to delete portfolio")
        return False
    finally:
        conn.close()
