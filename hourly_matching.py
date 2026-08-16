"""Hourly carbon-free energy matching: what a supply claim actually delivers.

The app treats a household on a "100% renewable" tariff as though its
electricity were carbon free. That claim rests on **annual** certificate
matching: over a year, someone somewhere generated as many clean kilowatt-hours
as the household consumed. It says nothing about whether clean power was on the
wire during the hours the household actually drew from it.

The two answers differ, and not by a rounding error
---------------------------------------------------
A household with rooftop solar exports its surplus at midday and takes its
largest load at 7pm on a winter evening. Annually it may cover 90% of its
consumption. Hour by hour it may cover 35%. The other 65% came from whatever
was marginal on the grid that evening, which on a still winter evening is gas.

The same holds for a green tariff with no on-site generation at all. The
supplier retires certificates from wind that generated at 3am in a windy month;
the household consumed at 6pm in a calm one. The certificates net out on paper.
The emissions do not.

What this module computes
-------------------------
*   An **hourly CFE score** - the share of consumption met by clean supply in
    the hour it was consumed - reported next to the annual figure, because the
    difference between the two is the finding.
*   **Residual-mix pricing** of unmatched imports. Unmatched consumption is not
    average grid; it is what remains after everyone else's clean claims have
    been subtracted, and it is dirtier than the average by construction.
*   **Export valued at what it displaces in the hour it happens**, with
    curtailment flagged. A kilowatt-hour exported into an already-saturated
    midday is worth much less than one exported into a gas-fired evening, and
    annual netting cannot express that at all.
*   **Both accounting frames**, location-based and market-based, using the same
    vocabulary ``ghg_inventory.py`` already established rather than inventing a
    second one.
*   **A certificate gap** in kg: the difference between what the tariff claims
    and what hourly matching supports. That number is the reason this exists.

Where it connects to code already merged
----------------------------------------
*   ``ghg_inventory.py`` implements dual scope 2 reporting. The dual report is
    only informative if the market-based side can be wrong in a measurable way,
    and this module is what makes it measurable.
*   ``grid_scheduler.py`` shifts flexible load to cleaner hours. Load shifting
    raises the hourly score, so this gives that module something physically
    real to optimise against.
*   ``marginal_emissions.py`` models the intensity of an extra kilowatt-hour.
    The unmatched hours here are exactly where that number belongs.

A stated simplification
-----------------------
Load shape is held constant across seasons and the seasonal variation is
carried in the *volume* allocated to each season. Supply shapes do vary by
season, because a winter solar day is a genuinely different shape and pretending
otherwise would remove the effect this module exists to show. The load
simplification flatters nothing in particular; it is recorded here so that a
reader knows it is a choice and not an oversight.

Self-contained: standard library only, SQLite tables created lazily, no shared
files modified.
"""

import os
import json
import sqlite3
import logging
from typing import Any

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

HOURS_IN_DAY = 24

# ---------------------------------------------------------------------------
# Seasons
#
# Three seasons rather than 8760 hours. The point being made here is about the
# mismatch between when clean supply arrives and when load happens, and that
# mismatch is visible at this resolution - a winter evening and a summer midday
# are different enough to carry the argument. Day counts sum to 365; the
# weights are relative and are normalised at use, so they can be edited without
# having to keep a total balanced by hand.
# ---------------------------------------------------------------------------
SEASONS = {
    "winter": {
        "days": 120,
        "load_weight": 1.35,
        "supply_weight": 0.45,
        "label": "Winter",
        "note": "The season that decides the answer. Load is highest, solar "
                "is at its weakest, and the evening peak lands on the dirtiest "
                "hours of the year.",
    },
    "shoulder": {
        "days": 123,
        "load_weight": 1.00,
        "supply_weight": 1.00,
        "label": "Spring and autumn",
        "note": "The season an annual average most resembles, which is why an "
                "annual average reads as reassuring.",
    },
    "summer": {
        "days": 122,
        "load_weight": 0.80,
        "supply_weight": 1.55,
        "label": "Summer",
        "note": "Where the surplus is generated, and where it is worth least "
                "because everyone else's surplus arrives at the same time.",
    },
}

DEFAULT_SEASON = "shoulder"

# ---------------------------------------------------------------------------
# Load profiles
#
# Shapes are given as 24 relative values from midnight and are normalised on
# use, so they can be written as readable magnitudes rather than as fractions
# that have to sum to one.
# ---------------------------------------------------------------------------
LOAD_PROFILES = {
    "evening_peak": {
        "label": "Typical household, evening peak",
        "shape": [
            2.0, 1.8, 1.7, 1.7, 1.8, 2.2, 3.2, 4.5,
            4.8, 4.2, 3.8, 3.6, 3.6, 3.5, 3.6, 4.2,
            5.5, 7.5, 8.5, 7.8, 6.2, 4.8, 3.5, 2.6,
        ],
        "note": "Out during the day, home in the evening. The default shape "
                "for a working household, and the worst possible shape to "
                "pair with solar.",
    },
    "heat_pump": {
        "label": "Heat pump household",
        "shape": [
            3.4, 3.2, 3.0, 3.0, 3.2, 4.4, 6.2, 6.8,
            5.4, 4.2, 3.6, 3.4, 3.4, 3.4, 3.8, 4.8,
            6.6, 8.4, 8.8, 7.6, 6.0, 4.8, 4.0, 3.6,
        ],
        "note": "A flatter shape than a gas household because the heat runs "
                "overnight, but with a sharper morning and evening peak and a "
                "much larger winter volume.",
    },
    "ev_overnight": {
        "label": "Household charging an EV overnight",
        "shape": [
            9.0, 9.0, 9.0, 9.0, 7.0, 3.0, 3.2, 4.2,
            4.4, 3.8, 3.4, 3.2, 3.2, 3.2, 3.2, 3.8,
            4.8, 6.4, 7.0, 6.4, 5.2, 4.2, 5.0, 7.0,
        ],
        "note": "A large controllable block overnight. Overnight is cleaner "
                "than the evening peak on most grids but is rarely solar, "
                "which is why this profile scores badly against a solar claim "
                "and well against a wind one.",
    },
    "daytime_home": {
        "label": "Someone home during the day",
        "shape": [
            2.2, 2.0, 1.9, 1.9, 2.0, 2.4, 3.4, 4.4,
            5.2, 5.6, 5.8, 5.8, 5.6, 5.4, 5.2, 5.2,
            5.6, 6.6, 7.2, 6.4, 5.2, 4.2, 3.2, 2.4,
        ],
        "note": "The shape that matches solar best, and the one least likely "
                "to be assumed when a tariff is sold.",
    },
    "flat": {
        "label": "Near-flat load",
        "shape": [4.0] * HOURS_IN_DAY,
        "note": "A reference case rather than a real household. Useful "
                "because it isolates the supply shape from the load shape.",
    },
}

DEFAULT_LOAD_PROFILE = "evening_peak"

# ---------------------------------------------------------------------------
# Supply profiles
#
# ``onsite`` distinguishes generation that physically reduces the household's
# import from a contract that only moves certificates. That distinction is the
# whole of the location-based versus market-based difference, so it is a field
# rather than a convention.
# ---------------------------------------------------------------------------
SUPPLY_PROFILES = {
    "rooftop_solar": {
        "label": "Rooftop solar",
        "onsite": True,
        "shape": [
            0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 1.2, 3.0,
            5.2, 7.4, 9.0, 9.8, 10.0, 9.4, 8.2, 6.4,
            4.2, 2.2, 0.8, 0.1, 0.0, 0.0, 0.0, 0.0,
        ],
        "season_shapes": {
            "winter": [
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4,
                1.8, 3.8, 5.6, 6.6, 6.6, 5.6, 3.8, 1.8,
                0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            ],
            "summer": [
                0.0, 0.0, 0.0, 0.0, 0.6, 1.8, 3.4, 5.0,
                6.6, 8.2, 9.4, 10.0, 10.0, 9.6, 8.6, 7.2,
                5.6, 3.8, 2.2, 0.9, 0.2, 0.0, 0.0, 0.0,
            ],
        },
        "note": "Generates into the middle of the day in every season, and "
                "into a much narrower window in the season the household uses "
                "most electricity.",
    },
    "solar_with_battery": {
        "label": "Rooftop solar with a home battery",
        "onsite": True,
        "shape": [
            1.2, 0.8, 0.6, 0.4, 0.4, 0.6, 1.4, 2.6,
            4.2, 5.8, 6.8, 7.2, 7.2, 6.8, 6.2, 5.4,
            5.0, 5.8, 6.6, 6.0, 4.6, 3.2, 2.2, 1.6,
        ],
        "season_shapes": {
            "winter": [
                0.6, 0.4, 0.2, 0.2, 0.2, 0.2, 0.4, 1.0,
                2.2, 3.6, 4.8, 5.4, 5.4, 4.8, 3.8, 2.8,
                2.6, 3.2, 3.4, 2.6, 1.6, 1.0, 0.8, 0.6,
            ],
        },
        "note": "The battery moves midday generation into the evening peak, "
                "which is the single largest improvement available to an "
                "hourly score and is invisible to an annual one.",
    },
    "contracted_wind": {
        "label": "Contracted wind",
        "onsite": False,
        "shape": [
            5.4, 5.6, 5.8, 5.8, 5.6, 5.2, 4.6, 4.0,
            3.6, 3.2, 3.0, 3.0, 3.2, 3.4, 3.6, 4.0,
            4.4, 4.6, 4.8, 5.0, 5.2, 5.4, 5.4, 5.4,
        ],
        "season_shapes": {
            "summer": [
                4.4, 4.6, 4.8, 4.8, 4.6, 4.2, 3.8, 3.4,
                3.2, 3.0, 2.8, 2.8, 3.0, 3.2, 3.4, 3.6,
                3.8, 4.0, 4.2, 4.4, 4.6, 4.6, 4.6, 4.4,
            ],
        },
        "note": "Night-biased and seasonally opposite to solar, which makes "
                "it a much better match for an overnight EV load and a much "
                "worse one for a daytime household.",
    },
    "contracted_solar_farm": {
        "label": "Contracted solar farm",
        "onsite": False,
        "shape": [
            0.0, 0.0, 0.0, 0.0, 0.0, 0.3, 1.4, 3.2,
            5.4, 7.6, 9.2, 9.8, 10.0, 9.4, 8.0, 6.0,
            3.8, 1.8, 0.6, 0.0, 0.0, 0.0, 0.0, 0.0,
        ],
        "season_shapes": {
            "winter": [
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.6,
                2.0, 4.0, 5.8, 6.8, 6.8, 5.8, 4.0, 2.0,
                0.6, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            ],
        },
        "note": "The same shape as rooftop solar without the physical import "
                "reduction, which is exactly the case an annual claim cannot "
                "tell apart from the rooftop one.",
    },
    "contracted_hydro": {
        "label": "Contracted hydro",
        "onsite": False,
        "shape": [3.8] * HOURS_IN_DAY,
        "note": "Close to flat and dispatchable in practice. The best "
                "available match for an ordinary household shape, and the "
                "scarcest.",
    },
    "unspecified_certificates": {
        "label": "Unspecified annual certificates",
        "onsite": False,
        "shape": [
            4.8, 5.0, 5.2, 5.2, 5.0, 4.6, 4.0, 3.6,
            3.4, 3.6, 3.8, 3.8, 3.8, 3.8, 3.8, 3.8,
            3.8, 3.8, 4.0, 4.2, 4.4, 4.6, 4.8, 4.8,
        ],
        "note": "What most 'green tariffs' are: certificates bought from "
                "whatever was cheapest, whenever it ran. Modelled on a "
                "wind-weighted shape because that is where the surplus "
                "certificates come from.",
    },
}

DEFAULT_SUPPLY_PROFILE = "unspecified_certificates"

# ---------------------------------------------------------------------------
# Grid intensity profiles, in gCO2e per kWh
#
# ``residual_uplift`` is the factor by which the residual mix exceeds the plain
# average, because the clean attributes have been sold to someone making a
# claim. Pricing unmatched imports at the average would be the same optimism in
# a smaller place.
#
# ``curtailment_intensity`` is the level below which the grid is clean enough
# that additional export displaces very little and may be curtailed outright.
# ---------------------------------------------------------------------------
GRID_PROFILES = {
    "gas_peaking": {
        "label": "Temperate grid with gas on the margin",
        "residual_uplift": 1.18,
        "curtailment_intensity": 120.0,
        "hourly": {
            "winter": [
                290, 280, 275, 275, 285, 305, 345, 375,
                380, 370, 355, 345, 340, 340, 350, 375,
                420, 455, 460, 430, 395, 360, 330, 305,
            ],
            "shoulder": [
                250, 240, 235, 235, 245, 265, 300, 320,
                305, 275, 250, 235, 230, 230, 240, 265,
                310, 355, 370, 350, 320, 295, 275, 260,
            ],
            "summer": [
                215, 205, 200, 200, 210, 225, 250, 255,
                230, 200, 175, 160, 155, 155, 165, 190,
                235, 285, 310, 300, 275, 250, 235, 225,
            ],
        },
        "note": "The common case in north-west Europe. The evening peak is "
                "the dirtiest hour of the day in every season, and it is when "
                "an ordinary household uses most of its electricity.",
    },
    "solar_saturated": {
        "label": "Solar-saturated grid",
        "residual_uplift": 1.22,
        "curtailment_intensity": 110.0,
        "hourly": {
            "winter": [
                330, 320, 315, 315, 325, 350, 380, 360,
                290, 220, 175, 155, 150, 160, 200, 270,
                380, 460, 490, 470, 430, 395, 370, 345,
            ],
            "shoulder": [
                300, 290, 285, 285, 295, 315, 330, 280,
                190, 120, 85, 70, 65, 75, 110, 190,
                320, 440, 490, 470, 425, 385, 350, 320,
            ],
            "summer": [
                280, 270, 265, 265, 275, 290, 285, 210,
                125, 75, 50, 40, 38, 45, 75, 145,
                270, 415, 480, 465, 420, 375, 335, 300,
            ],
        },
        "note": "The duck curve. Midday is nearly free of carbon and the "
                "evening ramp is met by whatever can start quickly. Export "
                "into the middle of the day here displaces very little.",
    },
    "coal_baseload": {
        "label": "Coal-heavy grid",
        "residual_uplift": 1.09,
        "curtailment_intensity": 300.0,
        "hourly": {
            "winter": [
                680, 675, 670, 670, 675, 690, 710, 725,
                720, 710, 700, 695, 690, 690, 695, 710,
                735, 760, 765, 750, 730, 715, 700, 690,
            ],
            "shoulder": [
                650, 645, 640, 640, 645, 660, 680, 690,
                680, 665, 650, 640, 635, 635, 645, 660,
                690, 720, 730, 715, 695, 680, 665, 655,
            ],
            "summer": [
                630, 625, 620, 620, 625, 640, 660, 670,
                660, 645, 630, 620, 615, 615, 625, 645,
                680, 715, 730, 715, 695, 675, 655, 640,
            ],
        },
        "note": "Flat and high. Matching matters least here in percentage "
                "terms and most in absolute kilograms, which is the opposite "
                "of the intuition.",
    },
}

DEFAULT_GRID_PROFILE = "gas_peaking"

# The share of an exported kilowatt-hour that is assumed to be curtailed rather
# than used, in hours where the grid is already below its curtailment
# threshold. It is not 100%: some of it is absorbed locally.
CURTAILMENT_LOSS = 0.60


class MatchingError(ValueError):
    """Raised for an unknown profile or an unusable input."""


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


def normalise_shape(values: list[float] | None) -> list[float]:
    """Turn 24 relative values into 24 shares that sum to one.

    Profiles are written as readable magnitudes rather than fractions, so the
    normalisation happens here rather than in the tables. A shape that is all
    zeros is rejected: it would silently divide a whole day of consumption by
    nothing and report a perfect score.
    """
    if not values or len(values) != HOURS_IN_DAY:
        raise MatchingError(
            f"A profile shape needs exactly {HOURS_IN_DAY} hourly values, "
            f"got {len(values) if values else 0}."
        )

    cleaned = [_non_negative(value) for value in values]
    total = sum(cleaned)
    if total <= 0:
        raise MatchingError(
            "A profile shape cannot be all zeros - there would be no hour in "
            "which anything happened."
        )
    return [value / total for value in cleaned]


def list_load_profiles() -> list[str]:
    return list(LOAD_PROFILES)


def get_load_profile(name: str) -> dict[str, Any]:
    if name not in LOAD_PROFILES:
        raise MatchingError(
            f"Unknown load profile '{name}'. The shape of the load is half of "
            f"the answer, so there is no sensible default to fall back on. "
            f"Known profiles: {', '.join(sorted(LOAD_PROFILES))}."
        )
    return dict(LOAD_PROFILES[name])


def list_supply_profiles() -> list[str]:
    return list(SUPPLY_PROFILES)


def get_supply_profile(name: str) -> dict[str, Any]:
    if name not in SUPPLY_PROFILES:
        raise MatchingError(
            f"Unknown supply profile '{name}'. Known profiles: "
            f"{', '.join(sorted(SUPPLY_PROFILES))}."
        )
    return dict(SUPPLY_PROFILES[name])


def list_grid_profiles() -> list[str]:
    return list(GRID_PROFILES)


def get_grid_profile(name: str) -> dict[str, Any]:
    if name not in GRID_PROFILES:
        raise MatchingError(
            f"Unknown grid profile '{name}'. Known profiles: "
            f"{', '.join(sorted(GRID_PROFILES))}."
        )
    return dict(GRID_PROFILES[name])


def list_seasons() -> list[str]:
    return list(SEASONS)


def get_season(name: str) -> dict[str, Any]:
    if name not in SEASONS:
        raise MatchingError(
            f"Unknown season '{name}'. Known seasons: "
            f"{', '.join(sorted(SEASONS))}."
        )
    return dict(SEASONS[name])


def shape_for_season(profile: dict[str, Any], season: str) -> list[float]:
    """The 24-hour shape a profile takes in a given season, normalised.

    Supply profiles may override their shape per season. A winter solar day is
    a genuinely different shape from a summer one - narrower and later to
    start - and flattening that would remove the effect this module exists to
    show.
    """
    if season not in SEASONS:
        raise MatchingError(f"Unknown season '{season}'.")
    overrides = profile.get("season_shapes") or {}
    return normalise_shape(overrides.get(season, profile.get("shape")))


def season_allocation(annual_kwh: float, weight_key: str = "load_weight") -> dict[str, float]:
    """Split an annual quantity across the seasons, in kWh per season.

    The weights are relative and are normalised here against the day counts, so
    the allocation always sums back to the annual figure regardless of what the
    weights are set to.
    """
    annual = _non_negative(annual_kwh)
    raw = {
        name: season["days"] * _non_negative(season.get(weight_key), 1.0)
        for name, season in SEASONS.items()
    }
    total = sum(raw.values())
    if total <= 0:
        raise MatchingError("Season weights sum to zero; nothing can be allocated.")
    return {name: annual * value / total for name, value in raw.items()}


# ---------------------------------------------------------------------------
# The matching itself
# ---------------------------------------------------------------------------

def match_day(
    consumption_kwh: float,
    load_shape: list[float],
    supplies: list[dict[str, Any]] | None,
    grid_hourly: list[float],
    residual_uplift: float = 1.0,
    curtailment_intensity: float = 0.0,
) -> dict[str, Any]:
    """Match one representative day, hour by hour.

    ``supplies`` is a list of ``{"kwh": float, "shape": [24], "onsite": bool}``.
    The ``onsite`` flag is load-bearing: on-site generation physically reduces
    the import and therefore changes the location-based number, while a
    contract only moves certificates and changes the market-based number. An
    annual claim cannot tell those two apart, which is the entire problem.
    """
    consumption = _non_negative(consumption_kwh)
    load = normalise_shape(load_shape)
    if len(grid_hourly) != HOURS_IN_DAY:
        raise MatchingError("Grid intensity needs 24 hourly values.")

    uplift = _as_float(residual_uplift, 1.0)
    if uplift < 1.0:
        # A residual mix cleaner than the average would mean the certificates
        # had been bought rather than sold, which is not the case being modelled.
        uplift = 1.0

    hours = []
    for hour in range(HOURS_IN_DAY):
        hours.append({
            "hour": hour,
            "consumption_kwh": consumption * load[hour],
            "onsite_kwh": 0.0,
            "contracted_kwh": 0.0,
            "intensity": _non_negative(grid_hourly[hour]),
        })

    for supply in supplies or []:
        amount = _non_negative(supply.get("kwh"))
        if amount <= 0:
            continue
        shape = normalise_shape(supply.get("shape"))
        key = "onsite_kwh" if supply.get("onsite") else "contracted_kwh"
        for hour in range(HOURS_IN_DAY):
            hours[hour][key] += amount * shape[hour]

    for row in hours:
        cons = row["consumption_kwh"]
        onsite = row["onsite_kwh"]
        contracted = row["contracted_kwh"]

        # Physical flows first: on-site generation is consumed before anything
        # is imported, and only the remainder is exported.
        self_consumed = min(cons, onsite)
        row["self_consumed_kwh"] = self_consumed
        row["export_kwh"] = onsite - self_consumed
        row["import_kwh"] = cons - self_consumed

        # Certificate flows second: a contract can only cover what was actually
        # imported in that hour. Anything beyond that is a certificate with no
        # consumption to attach to, which is the surplus an annual claim
        # quietly reuses somewhere else in the year.
        covered = min(row["import_kwh"], contracted)
        row["contract_matched_kwh"] = covered
        row["contract_unused_kwh"] = contracted - covered
        row["residual_kwh"] = row["import_kwh"] - covered

        row["matched_kwh"] = self_consumed + covered
        row["unmatched_kwh"] = cons - row["matched_kwh"]

        row["residual_intensity"] = row["intensity"] * uplift
        row["location_kg"] = row["import_kwh"] * row["intensity"] / 1000.0
        row["market_kg"] = row["residual_kwh"] * row["residual_intensity"] / 1000.0

        # Export is worth what it displaces in the hour it happens. In an hour
        # already below the curtailment threshold most of it displaces nothing.
        curtailed = row["intensity"] <= _non_negative(curtailment_intensity)
        usable = row["export_kwh"] * ((1.0 - CURTAILMENT_LOSS) if curtailed else 1.0)
        row["export_curtailed"] = curtailed
        row["export_curtailed_kwh"] = row["export_kwh"] - usable
        row["export_credit_kg"] = usable * row["intensity"] / 1000.0

    totals = {
        "consumption_kwh": sum(row["consumption_kwh"] for row in hours),
        "onsite_kwh": sum(row["onsite_kwh"] for row in hours),
        "contracted_kwh": sum(row["contracted_kwh"] for row in hours),
        "self_consumed_kwh": sum(row["self_consumed_kwh"] for row in hours),
        "import_kwh": sum(row["import_kwh"] for row in hours),
        "export_kwh": sum(row["export_kwh"] for row in hours),
        "export_curtailed_kwh": sum(row["export_curtailed_kwh"] for row in hours),
        "export_credit_kg": sum(row["export_credit_kg"] for row in hours),
        "matched_kwh": sum(row["matched_kwh"] for row in hours),
        "unmatched_kwh": sum(row["unmatched_kwh"] for row in hours),
        "residual_kwh": sum(row["residual_kwh"] for row in hours),
        "contract_unused_kwh": sum(row["contract_unused_kwh"] for row in hours),
        "location_kg": sum(row["location_kg"] for row in hours),
        "market_hourly_kg": sum(row["market_kg"] for row in hours),
    }

    # The market-based number as it is reported today: certificates are netted
    # against imports over the whole period, with no requirement that they
    # arrived in the same hour.
    annual_covered = min(totals["import_kwh"], totals["contracted_kwh"])
    uncovered = totals["import_kwh"] - annual_covered
    average_residual = (
        sum(row["residual_intensity"] * row["import_kwh"] for row in hours) / totals["import_kwh"]
        if totals["import_kwh"] > 0 else 0.0
    )
    totals["annual_covered_kwh"] = annual_covered
    totals["market_annual_kg"] = uncovered * average_residual / 1000.0
    totals["certificate_gap_kg"] = totals["market_hourly_kg"] - totals["market_annual_kg"]

    totals["hourly_cfe_pct"] = (
        100.0 * totals["matched_kwh"] / totals["consumption_kwh"]
        if totals["consumption_kwh"] > 0 else 0.0
    )
    supplied = totals["onsite_kwh"] + totals["contracted_kwh"]
    totals["annual_match_pct"] = (
        min(100.0, 100.0 * supplied / totals["consumption_kwh"])
        if totals["consumption_kwh"] > 0 else 0.0
    )
    totals["matching_gap_pct"] = totals["annual_match_pct"] - totals["hourly_cfe_pct"]

    return {"hours": hours, "totals": totals}


def match_year(
    annual_consumption_kwh: float,
    load_profile: str = DEFAULT_LOAD_PROFILE,
    supplies: list[dict[str, Any]] | None = None,
    grid_profile: str = DEFAULT_GRID_PROFILE,
) -> dict[str, Any]:
    """Match a full year, season by season, and report both accounting frames.

    ``supplies`` entries are ``{"profile": name, "annual_kwh": float}``. Each is
    allocated across the seasons on its own seasonal weighting - solar in
    January is not a twelfth of the year's solar - which is what makes the
    winter result look as bad as it should.
    """
    consumption = _non_negative(annual_consumption_kwh)
    if consumption <= 0:
        raise MatchingError(
            "Annual consumption must be greater than zero; a household that "
            "uses no electricity has nothing to match."
        )

    load = get_load_profile(load_profile)
    grid = get_grid_profile(grid_profile)

    prepared = []
    for supply in supplies or []:
        name = supply.get("profile")
        profile = get_supply_profile(name)
        annual_kwh = _non_negative(supply.get("annual_kwh"))
        if annual_kwh <= 0:
            continue
        weight_key = "supply_weight" if profile.get("onsite") or "solar" in name else "load_weight"
        prepared.append({
            "name": name,
            "label": profile["label"],
            "onsite": bool(profile.get("onsite")),
            "annual_kwh": annual_kwh,
            "profile": profile,
            # Solar-shaped supply is seasonal; a wind or hydro contract is
            # bought as an even annual volume, so it is allocated by days.
            "allocation": season_allocation(annual_kwh, weight_key),
        })

    consumption_by_season = season_allocation(consumption, "load_weight")

    seasons = []
    aggregate_hours = [
        {"hour": hour, "consumption_kwh": 0.0, "matched_kwh": 0.0,
         "import_kwh": 0.0, "export_kwh": 0.0, "intensity_weighted": 0.0}
        for hour in range(HOURS_IN_DAY)
    ]
    year_totals: dict[str, float] = {}

    for season_name, season in SEASONS.items():
        days = season["days"]
        daily_consumption = consumption_by_season[season_name] / days
        day_supplies = []
        for item in prepared:
            day_supplies.append({
                "kwh": item["allocation"][season_name] / days,
                "shape": shape_for_season(item["profile"], season_name),
                "onsite": item["onsite"],
            })

        day = match_day(
            daily_consumption,
            shape_for_season(load, season_name),
            day_supplies,
            grid["hourly"][season_name],
            grid["residual_uplift"],
            grid["curtailment_intensity"],
        )

        scaled = {key: value * days for key, value in day["totals"].items()
                  if key.endswith("_kwh") or key.endswith("_kg")}
        scaled["hourly_cfe_pct"] = day["totals"]["hourly_cfe_pct"]
        scaled["annual_match_pct"] = day["totals"]["annual_match_pct"]
        scaled["matching_gap_pct"] = day["totals"]["matching_gap_pct"]
        scaled["season"] = season_name
        scaled["label"] = season["label"]
        scaled["note"] = season["note"]
        scaled["days"] = days
        seasons.append(scaled)

        for hour in range(HOURS_IN_DAY):
            row = day["hours"][hour]
            target = aggregate_hours[hour]
            target["consumption_kwh"] += row["consumption_kwh"] * days
            target["matched_kwh"] += row["matched_kwh"] * days
            target["import_kwh"] += row["import_kwh"] * days
            target["export_kwh"] += row["export_kwh"] * days
            target["intensity_weighted"] += row["intensity"] * row["import_kwh"] * days

        for key, value in scaled.items():
            if isinstance(value, (int, float)) and (key.endswith("_kwh") or key.endswith("_kg")):
                year_totals[key] = year_totals.get(key, 0.0) + value

    for row in aggregate_hours:
        row["cfe_pct"] = (
            100.0 * row["matched_kwh"] / row["consumption_kwh"]
            if row["consumption_kwh"] > 0 else 0.0
        )
        row["mean_import_intensity"] = (
            row["intensity_weighted"] / row["import_kwh"] if row["import_kwh"] > 0 else 0.0
        )
        row.pop("intensity_weighted")

    hourly_cfe = (
        100.0 * year_totals.get("matched_kwh", 0.0) / consumption if consumption > 0 else 0.0
    )
    supplied = sum(item["annual_kwh"] for item in prepared)
    annual_match = min(100.0, 100.0 * supplied / consumption) if consumption > 0 else 0.0

    # The location-based number as it is usually stated: total imports at the
    # grid's annual average intensity. It differs from the hourly location-based
    # figure purely because imports are concentrated in the dirtier hours, which
    # is worth showing on its own.
    average_intensity = _annual_average_intensity(grid)
    location_flat = year_totals.get("import_kwh", 0.0) * average_intensity / 1000.0

    result = {
        "consumption_kwh": consumption,
        "supplied_kwh": supplied,
        "onsite_kwh": sum(i["annual_kwh"] for i in prepared if i["onsite"]),
        "contracted_kwh": sum(i["annual_kwh"] for i in prepared if not i["onsite"]),
        "import_kwh": year_totals.get("import_kwh", 0.0),
        "export_kwh": year_totals.get("export_kwh", 0.0),
        "export_curtailed_kwh": year_totals.get("export_curtailed_kwh", 0.0),
        "export_credit_kg": year_totals.get("export_credit_kg", 0.0),
        "matched_kwh": year_totals.get("matched_kwh", 0.0),
        "unmatched_kwh": year_totals.get("unmatched_kwh", 0.0),
        "contract_unused_kwh": year_totals.get("contract_unused_kwh", 0.0),
        "hourly_cfe_pct": hourly_cfe,
        "annual_match_pct": annual_match,
        "matching_gap_pct": annual_match - hourly_cfe,
        "location_based_kg": year_totals.get("location_kg", 0.0),
        "location_based_flat_kg": location_flat,
        "timing_premium_kg": year_totals.get("location_kg", 0.0) - location_flat,
        "market_based_hourly_kg": year_totals.get("market_hourly_kg", 0.0),
        "market_based_annual_kg": year_totals.get("market_annual_kg", 0.0),
        "certificate_gap_kg": year_totals.get("certificate_gap_kg", 0.0),
        "average_grid_intensity": average_intensity,
        "load_profile": load_profile,
        "grid_profile": grid_profile,
        "supplies": [
            {"profile": i["name"], "label": i["label"], "onsite": i["onsite"],
             "annual_kwh": i["annual_kwh"]}
            for i in prepared
        ],
        "seasons": seasons,
        "hours": aggregate_hours,
    }
    result["worst_season"] = min(seasons, key=lambda s: s["hourly_cfe_pct"])["season"] if seasons else None
    return result


def _annual_average_intensity(grid: dict[str, Any]) -> float:
    """Consumption-blind annual average, weighted only by hours in the year."""
    total = 0.0
    hours = 0.0
    for season_name, season in SEASONS.items():
        values = grid["hourly"][season_name]
        total += sum(values) * season["days"]
        hours += HOURS_IN_DAY * season["days"]
    return total / hours if hours > 0 else 0.0


def certificate_gap(result: dict[str, Any] | None) -> dict[str, Any]:
    """The difference between the claim and what hourly matching supports.

    Reported as its own object because it is the number this module exists to
    produce, and burying it in a totals dictionary would invite it being
    dropped from a summary.
    """
    if not result:
        return {"gap_kg": 0.0, "claimed_kg": 0.0, "supported_kg": 0.0, "overstatement_pct": 0.0}

    claimed = _non_negative(result.get("market_based_annual_kg"))
    supported = _non_negative(result.get("market_based_hourly_kg"))
    gap = supported - claimed
    return {
        "claimed_kg": claimed,
        "supported_kg": supported,
        "gap_kg": gap,
        "overstatement_pct": (100.0 * gap / supported) if supported > 0 else 0.0,
        "annual_match_pct": _as_float(result.get("annual_match_pct")),
        "hourly_cfe_pct": _as_float(result.get("hourly_cfe_pct")),
    }


def sensitivity(
    annual_consumption_kwh: float,
    load_profile: str = DEFAULT_LOAD_PROFILE,
    supplies: list[dict[str, Any]] | None = None,
    grid_profiles: list[str] | None = None,
) -> list[dict[str, Any]]:
    """The same household on each grid, because the grid is not a detail.

    A matching score is a statement about a household *and* the system it sits
    in. The same solar array scores very differently against a solar-saturated
    grid than against a coal one, and reporting a single number without saying
    which grid it assumed would be false precision of exactly the kind this
    module was written to remove.
    """
    names = grid_profiles or list_grid_profiles()
    rows = []
    for name in names:
        result = match_year(annual_consumption_kwh, load_profile, supplies, name)
        rows.append({
            "grid_profile": name,
            "label": get_grid_profile(name)["label"],
            "hourly_cfe_pct": result["hourly_cfe_pct"],
            "annual_match_pct": result["annual_match_pct"],
            "market_based_hourly_kg": result["market_based_hourly_kg"],
            "market_based_annual_kg": result["market_based_annual_kg"],
            "certificate_gap_kg": result["certificate_gap_kg"],
            "export_curtailed_kwh": result["export_curtailed_kwh"],
        })
    return rows


def compare_supply_options(
    annual_consumption_kwh: float,
    options: list[dict[str, Any]] | None,
    load_profile: str = DEFAULT_LOAD_PROFILE,
    grid_profile: str = DEFAULT_GRID_PROFILE,
) -> list[dict[str, Any]]:
    """Score several supply arrangements against the same load.

    This is the output a user can act on: not "your tariff is worse than it
    says", but "this arrangement scores 41% and this one scores 68% against
    your actual consumption".
    """
    rows = []
    for option in options or []:
        result = match_year(
            annual_consumption_kwh,
            load_profile,
            option.get("supplies"),
            grid_profile,
        )
        rows.append({
            "label": option.get("label") or "Option",
            "hourly_cfe_pct": result["hourly_cfe_pct"],
            "annual_match_pct": result["annual_match_pct"],
            "matching_gap_pct": result["matching_gap_pct"],
            "market_based_hourly_kg": result["market_based_hourly_kg"],
            "certificate_gap_kg": result["certificate_gap_kg"],
            "worst_season": result["worst_season"],
            "result": result,
        })
    rows.sort(key=lambda row: row["hourly_cfe_pct"], reverse=True)
    return rows


def get_matching_insights(result: dict[str, Any] | None) -> list[str]:
    """Plain statements about what the numbers mean, in priority order."""
    if not result:
        return ["Run an analysis to see what a supply claim is delivering."]

    insights: list[str] = []
    gap = _as_float(result.get("matching_gap_pct"))
    hourly = _as_float(result.get("hourly_cfe_pct"))
    annual = _as_float(result.get("annual_match_pct"))

    if gap >= 25.0:
        insights.append(
            f"The annual claim is {annual:.0f}% and hourly matching supports "
            f"{hourly:.0f}%. That {gap:.0f} point gap is not an accounting "
            f"subtlety - it is the share of consumption that was met by the "
            f"grid at the time it happened, and the grid was not clean then."
        )
    elif gap >= 8.0:
        insights.append(
            f"Annual matching reads {annual:.0f}% against an hourly score of "
            f"{hourly:.0f}%. A gap this size is normal and still worth stating "
            f"rather than rounding away."
        )
    else:
        insights.append(
            f"Annual and hourly matching agree closely ({annual:.0f}% against "
            f"{hourly:.0f}%). That is a real result and an uncommon one - it "
            f"means the supply arrives when the consumption happens."
        )

    certificate = _as_float(result.get("certificate_gap_kg"))
    if certificate > 1.0:
        insights.append(
            f"Pricing the unmatched hours at the residual mix instead of "
            f"netting certificates annually adds {certificate:,.0f} kg to the "
            f"market-based footprint. The tariff did not become worse; the "
            f"reporting became honest about the hours it never covered."
        )

    curtailed = _as_float(result.get("export_curtailed_kwh"))
    if curtailed > 1.0:
        insights.append(
            f"{curtailed:,.0f} kWh of export lands in hours where the grid is "
            f"already clean enough that it displaces little or nothing. Annual "
            f"netting counts those kilowatt-hours at full value against evening "
            f"consumption, which is where most of the flattery comes from."
        )

    timing = _as_float(result.get("timing_premium_kg"))
    if timing > 1.0:
        insights.append(
            f"Imports are concentrated in the dirtier hours, so using the "
            f"grid's annual average understates the location-based footprint "
            f"by {timing:,.0f} kg. This is true regardless of what tariff the "
            f"household is on."
        )

    worst = result.get("worst_season")
    if worst:
        season = SEASONS.get(worst, {})
        insights.append(
            f"{season.get('label', worst)} is the weakest season for matching. "
            f"An annual figure averages it away, and it is the season the "
            f"household uses most electricity."
        )

    unused = _as_float(result.get("contract_unused_kwh"))
    if unused > 1.0:
        insights.append(
            f"{unused:,.0f} kWh of contracted clean supply arrived in hours "
            f"with no import left to cover. Under annual matching those "
            f"certificates are reused elsewhere in the year; under hourly "
            f"matching they simply have nothing to attach to."
        )

    insights.append(
        "Shifting flexible load towards the matched hours raises this score "
        "and lowers real emissions at the same time. Buying more certificates "
        "raises only the annual figure."
    )
    return insights


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_matching_db() -> bool:
    """Create the table if it does not exist yet."""
    conn = None
    try:
        conn = _connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS hourly_matching_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                load_profile TEXT NOT NULL,
                grid_profile TEXT NOT NULL,
                consumption_kwh REAL NOT NULL,
                hourly_cfe_pct REAL NOT NULL,
                annual_match_pct REAL NOT NULL,
                certificate_gap_kg REAL NOT NULL,
                detail_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Unable to initialise hourly matching table: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def save_analysis(user_id: int, name: str, result: dict[str, Any]) -> int | None:
    """Persist an analysis. Returns the row id or None."""
    init_matching_db()
    conn = None
    try:
        conn = _connect()
        # The hourly and seasonal detail is large and only ever read back as a
        # whole, so it is stored as JSON rather than as its own table.
        summary = {key: value for key, value in (result or {}).items() if key != "hours"}
        cursor = conn.execute(
            """
            INSERT INTO hourly_matching_analyses (
                user_id, name, load_profile, grid_profile, consumption_kwh,
                hourly_cfe_pct, annual_match_pct, certificate_gap_kg, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                (name or "Analysis").strip() or "Analysis",
                str(result.get("load_profile", "")),
                str(result.get("grid_profile", "")),
                _as_float(result.get("consumption_kwh")),
                _as_float(result.get("hourly_cfe_pct")),
                _as_float(result.get("annual_match_pct")),
                _as_float(result.get("certificate_gap_kg")),
                json.dumps(summary, default=str),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as exc:
        logger.error("Unable to save matching analysis: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def get_analyses(user_id: int, limit: int = 25) -> list[dict[str, Any]]:
    """A user's saved analyses, newest first."""
    init_matching_db()
    conn = None
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, name, load_profile, grid_profile, consumption_kwh,
                   hourly_cfe_pct, annual_match_pct, certificate_gap_kg,
                   detail_json, created_at
            FROM hourly_matching_analyses
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
        logger.error("Unable to load matching analyses: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def delete_analysis(analysis_id: int) -> bool:
    """Delete a saved analysis."""
    init_matching_db()
    conn = None
    try:
        conn = _connect()
        cursor = conn.execute(
            "DELETE FROM hourly_matching_analyses WHERE id = ?", (analysis_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as exc:
        logger.error("Unable to delete matching analysis: %s", exc)
        return False
    finally:
        if conn:
            conn.close()
