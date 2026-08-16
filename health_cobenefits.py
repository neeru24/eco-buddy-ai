"""Local air quality and health co-benefits of climate actions.

Every recommendation in this app is denominated in one currency: kgCO2e. That
framing has two problems, and this module exists to fix both.

**It undersells local actions.** Carbon benefits are global and arrive over
decades. Air quality benefits are local and arrive immediately - on the user's
street, in their lungs, this year. That is a materially better motivator and
the app throws it away.

**It can recommend things that make the air worse.** A wood stove has a modest
carbon story, because the wood grows back, and it is a serious particulate
source in a way a gas boiler is not. Ranked purely on CO2e the app will
cheerfully suggest something that measurably worsens the air in the user's own
home. Diesel is the same story from the other end: its carbon advantage over
petrol is real, and so is its NOx and particulate penalty, and only one of
those currently shows up anywhere.

The chain
---------
This is standard screening-level health impact assessment::

    activity -> pollutant emissions -> exposure weighting -> health outcome -> damage cost

Each step is deliberately the simplest defensible form:

*   **Emission factors** in grams per unit of activity, for the sources a
    household actually controls.
*   **Exposure weighting** by an intake-fraction style multiplier. A kilogram
    of PM2.5 from a car exhaust at street level in a dense city does far more
    harm than a kilogram from a tall stack in open country. Ignoring this
    would produce numbers that are confidently wrong in the direction that
    matters most, so it is not optional.
*   **Health outcomes** as the standard endpoints - deaths, hospital
    admissions, asthma attacks, working days lost.
*   **Damage cost** per tonne, which puts pollutants with different units on
    one scale and lets carbon and air quality be added into a single figure.

The most useful output in the module is `rank_actions()`, and specifically the
disagreements it surfaces: the actions whose carbon ranking and whose combined
ranking point in different directions.

On precision
------------
These are screening figures. Real exposure depends on meteorology, street
geometry and where people actually are, none of which are modelled here. The
module reports its outputs as order-of-magnitude estimates and
`get_method_caveats()` keeps that honest, because a page that presented three
significant figures of avoided mortality would be lying.

The module is self-contained: only the standard library is used, its SQLite
table is created lazily, and no shared files are modified.
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

POLLUTANTS = ("pm25", "nox", "so2", "voc")

POLLUTANT_LABELS = {
    "pm25": "PM2.5 (fine particulates)",
    "nox": "NOx (nitrogen oxides)",
    "so2": "SO2 (sulphur dioxide)",
    "voc": "VOCs (volatile organics)",
}

# Grams of pollutant, and grams of CO2e, per unit of activity. Vehicle figures
# are per kilometre and include non-exhaust particulates from brakes and tyres,
# which now dominate PM2.5 from modern road vehicles and are the reason an
# electric car is not a zero-particulate option. Heating and electricity
# figures are per kWh delivered.
#
# These are screening-level values chosen to be right in magnitude and in
# ranking. They are documented per entry and are not a substitute for measured
# local data.
ACTIVITIES = {
    "Petrol car": {
        "unit": "km",
        "category": "transport",
        "pm25": 0.025, "nox": 0.040, "so2": 0.001, "voc": 0.030,
        "co2e": 170.0,
        "setting": "street",
        "basis": "Euro 6 petrol car, exhaust plus brake and tyre wear.",
    },
    "Diesel car": {
        "unit": "km",
        "category": "transport",
        "pm25": 0.023, "nox": 0.350, "so2": 0.001, "voc": 0.010,
        "co2e": 150.0,
        "setting": "street",
        "basis": "Euro 6 diesel car at real-world NOx, plus non-exhaust wear.",
    },
    "Older diesel car": {
        "unit": "km",
        "category": "transport",
        "pm25": 0.070, "nox": 0.800, "so2": 0.002, "voc": 0.020,
        "co2e": 165.0,
        "setting": "street",
        "basis": "Pre-Euro 5 diesel without a particulate filter.",
    },
    "Electric car": {
        "unit": "km",
        "category": "transport",
        "pm25": 0.022, "nox": 0.000, "so2": 0.000, "voc": 0.000,
        "co2e": 55.0,
        "setting": "street",
        "basis": "No exhaust. Non-exhaust wear only, slightly higher for weight.",
    },
    "Bus": {
        "unit": "passenger-km",
        "category": "transport",
        "pm25": 0.004, "nox": 0.060, "so2": 0.001, "voc": 0.004,
        "co2e": 90.0,
        "setting": "street",
        "basis": "Diesel bus at typical occupancy, per passenger-km.",
    },
    "Electric train": {
        "unit": "passenger-km",
        "category": "transport",
        "pm25": 0.001, "nox": 0.002, "so2": 0.002, "voc": 0.000,
        "co2e": 35.0,
        "setting": "stack",
        "basis": "Grid-powered rail. Emissions occur at the power station.",
    },
    "Cycling or walking": {
        "unit": "km",
        "category": "transport",
        "pm25": 0.000, "nox": 0.000, "so2": 0.000, "voc": 0.000,
        "co2e": 0.0,
        "setting": "street",
        "basis": "No combustion and no vehicle wear.",
    },
    "Gas boiler": {
        "unit": "kWh",
        "category": "heating",
        "pm25": 0.0003, "nox": 0.150, "so2": 0.0005, "voc": 0.002,
        "co2e": 210.0,
        "setting": "flue",
        "basis": "Condensing gas boiler. Clean-burning, but a real NOx source.",
    },
    "Oil boiler": {
        "unit": "kWh",
        "category": "heating",
        "pm25": 0.010, "nox": 0.200, "so2": 0.300, "voc": 0.005,
        "co2e": 270.0,
        "setting": "flue",
        "basis": "Domestic heating oil, including its sulphur content.",
    },
    "Modern wood stove": {
        "unit": "kWh",
        "category": "heating",
        "pm25": 0.800, "nox": 0.100, "so2": 0.010, "voc": 0.400,
        "co2e": 25.0,
        "setting": "flue",
        "basis": "Ecodesign-compliant stove. Biogenic CO2 excluded; supply chain only.",
    },
    "Open fire or old stove": {
        "unit": "kWh",
        "category": "heating",
        "pm25": 3.000, "nox": 0.090, "so2": 0.010, "voc": 1.200,
        "co2e": 25.0,
        "setting": "flue",
        "basis": "Open fire or pre-Ecodesign stove. Among the worst domestic PM2.5 sources.",
    },
    "Coal fire": {
        "unit": "kWh",
        "category": "heating",
        "pm25": 1.500, "nox": 0.300, "so2": 2.000, "voc": 0.300,
        "co2e": 380.0,
        "setting": "flue",
        "basis": "House coal. Bad on every measure at once.",
    },
    "Heat pump": {
        "unit": "kWh",
        "category": "heating",
        "pm25": 0.000, "nox": 0.000, "so2": 0.000, "voc": 0.000,
        "co2e": 60.0,
        "setting": "stack",
        "basis": "No combustion at the home. Upstream emissions follow the grid.",
    },
    "Coal-fired electricity": {
        "unit": "kWh",
        "category": "electricity",
        "pm25": 0.050, "nox": 0.700, "so2": 1.200, "voc": 0.010,
        "co2e": 900.0,
        "setting": "stack",
        "basis": "Coal generation with typical abatement, emitted at a tall stack.",
    },
    "Gas-fired electricity": {
        "unit": "kWh",
        "category": "electricity",
        "pm25": 0.005, "nox": 0.200, "so2": 0.002, "voc": 0.003,
        "co2e": 400.0,
        "setting": "stack",
        "basis": "Combined cycle gas turbine at a tall stack.",
    },
    "Renewable electricity": {
        "unit": "kWh",
        "category": "electricity",
        "pm25": 0.000, "nox": 0.000, "so2": 0.000, "voc": 0.000,
        "co2e": 15.0,
        "setting": "stack",
        "basis": "Wind or solar. Manufacturing carbon only, no operating emissions.",
    },
}

# Intake-fraction style multipliers. What matters for health is not what is
# emitted but what is breathed, and that depends on how high the release is
# and how many people are nearby. A tall stack in open country disperses;
# a tailpipe in a street canyon does not.
RELEASE_SETTINGS = {
    "street": {
        "label": "Street level (tailpipes, at head height)",
        "multiplier": 1.0,
        "description": "Released where people are walking and breathing.",
    },
    "flue": {
        "label": "Domestic flue (roof height, in a neighbourhood)",
        "multiplier": 0.65,
        "description": "Above head height, but still inside the neighbourhood.",
    },
    "stack": {
        "label": "Industrial stack (tall, usually away from housing)",
        "multiplier": 0.12,
        "description": "Tall release with room to disperse before it is breathed.",
    },
}

DEFAULT_RELEASE_SETTING = "street"

# Population density multiplier. The same tailpipe does far more harm in a
# dense city than on a rural lane, simply because more people breathe it.
POPULATION_DENSITY = {
    "Dense urban": {"multiplier": 2.6, "description": "Inner city, street canyons, high footfall."},
    "Urban": {"multiplier": 1.6, "description": "Town or outer city."},
    "Suburban": {"multiplier": 1.0, "description": "Residential suburb. The reference case."},
    "Rural": {"multiplier": 0.35, "description": "Village or open country."},
}

DEFAULT_DENSITY = "Suburban"

# Damage cost per tonne emitted, in the app's currency unit, at the suburban
# reference case. Values of this kind are published for exactly this purpose
# by national environment agencies. PM2.5 dominates because it is by far the
# most damaging to health per tonne.
DAMAGE_COST_PER_TONNE = {
    "pm25": 190000.0,
    "nox": 12000.0,
    "so2": 20000.0,
    "voc": 3000.0,
}

# Carbon damage cost per tonne CO2e, so climate and health land on one scale.
CARBON_DAMAGE_COST_PER_TONNE = 250.0

# Health outcomes per tonne of exposure-weighted PM2.5, at the suburban
# reference case. Screening-level central estimates: the underlying
# concentration-response functions are population-level and linear at these
# magnitudes, which is what makes the simple per-tonne form defensible.
HEALTH_OUTCOMES_PER_TONNE_PM25 = {
    "premature_deaths": 0.075,
    "hospital_admissions": 0.90,
    "asthma_exacerbations": 45.0,
    "lost_work_days": 300.0,
}

OUTCOME_LABELS = {
    "premature_deaths": "premature deaths",
    "hospital_admissions": "hospital admissions",
    "asthma_exacerbations": "asthma attacks",
    "lost_work_days": "working days lost",
}

GRAMS_PER_TONNE = 1_000_000.0

# Below this the health and carbon rankings are effectively agreeing and
# calling it a conflict would be noise.
CONFLICT_THRESHOLD = 0.15


class CoBenefitError(ValueError):
    """Raised when an action cannot be assessed."""


# --- Catalogue --------------------------------------------------------------


def list_activities(category: str | None = None) -> list[dict[str, Any]]:
    """Return the activity catalogue, cleanest PM2.5 first."""
    activities = [
        {"name": name, **details}
        for name, details in ACTIVITIES.items()
        if not category or details["category"] == category
    ]
    return sorted(activities, key=lambda item: item["pm25"])


def list_categories() -> list[str]:
    """Return the distinct activity categories."""
    return sorted({details["category"] for details in ACTIVITIES.values()})


def list_release_settings() -> list[dict[str, Any]]:
    """Return release settings, most exposing first."""
    settings = [{"key": key, **value} for key, value in RELEASE_SETTINGS.items()]
    return sorted(settings, key=lambda item: item["multiplier"], reverse=True)


def list_density_options() -> list[dict[str, Any]]:
    """Return population density options, densest first."""
    options = [{"name": name, **value} for name, value in POPULATION_DENSITY.items()]
    return sorted(options, key=lambda item: item["multiplier"], reverse=True)


def get_activity(name: str) -> dict[str, Any]:
    """Return one activity, or raise if it is not in the catalogue.

    Unlike the fund catalogue elsewhere in the app, silently substituting a
    default here would attribute one activity's pollution to another, so this
    one raises.
    """
    details = ACTIVITIES.get(name)
    if not details:
        raise CoBenefitError(f"Unknown activity: {name}")
    return {"name": name, **details}


def density_multiplier(density: str) -> float:
    """Exposure multiplier for a population density."""
    entry = POPULATION_DENSITY.get(density) or POPULATION_DENSITY[DEFAULT_DENSITY]
    return entry["multiplier"]


def release_multiplier(setting: str) -> float:
    """Exposure multiplier for a release height."""
    entry = RELEASE_SETTINGS.get(setting) or RELEASE_SETTINGS[DEFAULT_RELEASE_SETTING]
    return entry["multiplier"]


def exposure_multiplier(setting: str, density: str) -> float:
    """Combined intake weighting for a release height and population density."""
    return release_multiplier(setting) * density_multiplier(density)


# --- Emissions --------------------------------------------------------------


def _clean_amount(value: Any, field: str = "Amount") -> float:
    """Coerce an activity amount into a usable non-negative float."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise CoBenefitError(f"{field} must be a number")
    if math.isnan(number) or math.isinf(number):
        raise CoBenefitError(f"{field} must be a real number")
    if number < 0:
        raise CoBenefitError(f"{field} cannot be negative")
    return number


def pollutant_emissions(activity_name: str, amount: float) -> dict[str, Any]:
    """Grams of each pollutant, and of CO2e, from an amount of an activity."""
    activity = get_activity(activity_name)
    quantity = _clean_amount(amount, "Activity amount")

    emissions = {pollutant: activity[pollutant] * quantity for pollutant in POLLUTANTS}
    emissions["co2e"] = activity["co2e"] * quantity
    return {
        "activity": activity_name,
        "amount": quantity,
        "unit": activity["unit"],
        "setting": activity["setting"],
        "grams": emissions,
    }


def exposure_weighted_emissions(
    grams: dict[str, float], setting: str, density: str = DEFAULT_DENSITY
) -> dict[str, Any]:
    """Apply the intake weighting to a set of pollutant emissions.

    Carbon is deliberately left unweighted: a tonne of CO2e does the same
    damage wherever it is released, which is precisely what distinguishes it
    from the local pollutants alongside it.
    """
    multiplier = exposure_multiplier(setting, density)
    weighted = {
        pollutant: max(0.0, float(grams.get(pollutant, 0.0))) * multiplier
        for pollutant in POLLUTANTS
    }
    weighted["co2e"] = max(0.0, float(grams.get("co2e", 0.0)))
    return {"weighted_grams": weighted, "multiplier": multiplier}


def health_outcomes(pm25_grams: float) -> dict[str, float]:
    """Health outcomes from a quantity of exposure-weighted PM2.5.

    Deaths come back as a fraction, and they should. One household's change is
    a small expected value across a population, not a person - the module
    returns the expectation and leaves the honest phrasing of it to the page.
    """
    try:
        grams = max(0.0, float(pm25_grams))
    except (TypeError, ValueError):
        grams = 0.0

    tonnes = grams / GRAMS_PER_TONNE
    return {
        outcome: rate * tonnes
        for outcome, rate in HEALTH_OUTCOMES_PER_TONNE_PM25.items()
    }


def damage_cost(weighted_grams: dict[str, float]) -> dict[str, Any]:
    """Monetised damage from a set of exposure-weighted emissions.

    Returns air quality damage and carbon damage separately as well as
    combined, because the whole point is to be able to see when one is
    carrying the result.
    """
    air_quality = 0.0
    per_pollutant = {}
    for pollutant in POLLUTANTS:
        tonnes = max(0.0, float(weighted_grams.get(pollutant, 0.0))) / GRAMS_PER_TONNE
        cost = tonnes * DAMAGE_COST_PER_TONNE[pollutant]
        per_pollutant[pollutant] = cost
        air_quality += cost

    carbon_tonnes = max(0.0, float(weighted_grams.get("co2e", 0.0))) / GRAMS_PER_TONNE
    carbon = carbon_tonnes * CARBON_DAMAGE_COST_PER_TONNE

    total = air_quality + carbon
    return {
        "air_quality": air_quality,
        "carbon": carbon,
        "total": total,
        "per_pollutant": per_pollutant,
        "air_quality_share": (air_quality / total) if total > 0 else 0.0,
    }


def assess_activity(
    activity_name: str,
    amount: float,
    density: str = DEFAULT_DENSITY,
    setting: str | None = None,
) -> dict[str, Any]:
    """Full chain for one activity: emissions, exposure, outcomes, cost."""
    emissions = pollutant_emissions(activity_name, amount)
    release = setting or emissions["setting"]
    exposure = exposure_weighted_emissions(emissions["grams"], release, density)
    costs = damage_cost(exposure["weighted_grams"])

    return {
        "activity": activity_name,
        "amount": emissions["amount"],
        "unit": emissions["unit"],
        "setting": release,
        "density": density,
        "exposure_multiplier": exposure["multiplier"],
        "grams": emissions["grams"],
        "weighted_grams": exposure["weighted_grams"],
        "outcomes": health_outcomes(exposure["weighted_grams"]["pm25"]),
        "cost": costs,
        "co2e_kg": emissions["grams"]["co2e"] / 1000.0,
    }


# --- Comparing actions ------------------------------------------------------


def assess_switch(
    from_activity: str,
    to_activity: str,
    amount: float,
    density: str = DEFAULT_DENSITY,
) -> dict[str, Any]:
    """What switching from one activity to another avoids.

    The central operation of the module. Both sides are assessed on the same
    amount of activity, which is the only comparison that means anything -
    the same distance travelled, or the same heat delivered.
    """
    before = assess_activity(from_activity, amount, density)
    after = assess_activity(to_activity, amount, density)

    avoided_pollutants = {
        pollutant: before["weighted_grams"][pollutant] - after["weighted_grams"][pollutant]
        for pollutant in POLLUTANTS
    }
    avoided_outcomes = {
        outcome: before["outcomes"][outcome] - after["outcomes"][outcome]
        for outcome in HEALTH_OUTCOMES_PER_TONNE_PM25
    }

    carbon_saving_kg = before["co2e_kg"] - after["co2e_kg"]
    air_quality_saving = before["cost"]["air_quality"] - after["cost"]["air_quality"]
    carbon_saving_cost = before["cost"]["carbon"] - after["cost"]["carbon"]
    total_saving = air_quality_saving + carbon_saving_cost

    return {
        "from": from_activity,
        "to": to_activity,
        "amount": before["amount"],
        "unit": before["unit"],
        "density": density,
        "avoided_pollutants": avoided_pollutants,
        "avoided_outcomes": avoided_outcomes,
        "carbon_saving_kg": carbon_saving_kg,
        "air_quality_value": air_quality_saving,
        "carbon_value": carbon_saving_cost,
        "total_value": total_saving,
        "health_share": (air_quality_saving / total_saving) if total_saving > 0 else 0.0,
        "carbon_improves": carbon_saving_kg > 0,
        "air_quality_improves": air_quality_saving > 0,
        "is_conflict": (carbon_saving_kg > 0) != (air_quality_saving > 0),
        "verdict": _switch_verdict(carbon_saving_kg, air_quality_saving),
        "explanation": _switch_explanation(
            from_activity, to_activity, carbon_saving_kg, air_quality_saving
        ),
    }


def _switch_verdict(carbon_saving: float, air_quality_saving: float) -> str:
    """Classify a switch on both axes at once."""
    if carbon_saving > 0 and air_quality_saving > 0:
        return "win_win"
    if carbon_saving > 0 >= air_quality_saving:
        return "carbon_only"
    if air_quality_saving > 0 >= carbon_saving:
        return "health_only"
    return "worse_on_both"


def _switch_explanation(
    from_activity: str,
    to_activity: str,
    carbon_saving: float,
    air_quality_saving: float,
) -> str:
    """Plain sentence for a switch, naming the trade-off where there is one."""
    verdict = _switch_verdict(carbon_saving, air_quality_saving)

    if verdict == "win_win":
        return (
            f"Moving from {from_activity.lower()} to {to_activity.lower()} cuts "
            f"both carbon and local air pollution. No trade-off to weigh."
        )
    if verdict == "carbon_only":
        return (
            f"{to_activity} saves {abs(carbon_saving):,.0f} kg of CO2e, but it "
            f"is worse for the air people breathe nearby. Good for the climate, "
            f"bad for your street - the app would have recommended this on "
            f"carbon alone."
        )
    if verdict == "health_only":
        return (
            f"{to_activity} cleans up the local air but does not help the "
            f"climate. Worth doing for the health benefit, not as a carbon "
            f"measure."
        )
    return (
        f"{to_activity} is worse than {from_activity.lower()} on both carbon "
        f"and air quality. There is no case for it."
    )


def rank_actions(
    actions: list[dict[str, Any]], density: str = DEFAULT_DENSITY
) -> dict[str, Any]:
    """Rank candidate switches by combined benefit, and flag the disagreements.

    ``actions`` is a list of dicts with ``from``, ``to`` and ``amount``.

    The ranking by carbon alone is computed alongside the combined one, and
    any action whose position moves materially between them is flagged. Those
    disagreements are the most useful thing this module produces: they are
    exactly the cases where a single-metric recommender gets it wrong.
    """
    if not actions:
        raise CoBenefitError("At least one action is required")

    assessed = [
        assess_switch(action["from"], action["to"], action.get("amount", 0), density)
        for action in actions
    ]

    by_carbon = sorted(assessed, key=lambda item: item["carbon_saving_kg"], reverse=True)
    by_combined = sorted(assessed, key=lambda item: item["total_value"], reverse=True)

    carbon_positions = {id(item): index for index, item in enumerate(by_carbon)}
    count = len(assessed)

    ranked = []
    for index, item in enumerate(by_combined):
        carbon_rank = carbon_positions[id(item)]
        # Normalised so a one-place move in a long list is not treated the
        # same as a one-place move in a list of two.
        movement = abs(carbon_rank - index) / count if count > 1 else 0.0
        entry = dict(item)
        entry["combined_rank"] = index + 1
        entry["carbon_rank"] = carbon_rank + 1
        entry["rank_movement"] = movement
        entry["ranking_disagrees"] = movement >= CONFLICT_THRESHOLD or item["is_conflict"]
        ranked.append(entry)

    return {
        "ranked": ranked,
        "conflicts": [item for item in ranked if item["ranking_disagrees"]],
        "top_by_carbon": by_carbon[0]["to"] if by_carbon else None,
        "top_by_combined": by_combined[0]["to"] if by_combined else None,
        "rankings_agree": by_carbon[0] is by_combined[0] if assessed else True,
    }


def scale_to_population(
    assessment: dict[str, Any], households: int
) -> dict[str, Any]:
    """Scale one household's result up to a neighbourhood, town or city.

    One household's avoided PM2.5 is genuinely tiny, and quoting a fractional
    death to a single user is both meaningless and slightly grotesque. The
    same action across a city is a real public health number, and showing both
    is the honest way to present it.
    """
    try:
        count = max(1, int(households))
    except (TypeError, ValueError):
        count = 1

    outcomes = assessment.get("avoided_outcomes") or assessment.get("outcomes") or {}
    return {
        "households": count,
        "outcomes": {key: value * count for key, value in outcomes.items()},
        "carbon_saving_tonnes": assessment.get("carbon_saving_kg", 0.0) * count / 1000.0,
        "total_value": assessment.get("total_value", 0.0) * count,
    }


def describe_outcomes(outcomes: dict[str, Any], households: int = 1) -> list[str]:
    """Turn outcome numbers into sentences that do not overclaim.

    A fractional death is a statistical expectation across a population, not
    a person, and phrasing it as "you saved 0.003 lives" is both wrong and
    absurd. Below one, the module reframes rather than rounds.
    """
    lines = []
    deaths = outcomes.get("premature_deaths", 0.0)

    if deaths >= 1.0:
        lines.append(
            f"Around {deaths:.1f} premature deaths avoided across the "
            f"{households:,} households modelled."
        )
    elif deaths > 0:
        # Expressing a small expectation as odds is the honest reading and it
        # is far more intuitive than a decimal fraction of a death.
        one_in = int(round(1.0 / deaths)) if deaths > 0 else 0
        lines.append(
            f"Too small to express as a life saved: roughly a 1 in {one_in:,} "
            f"chance of preventing one premature death. That is what one "
            f"household's share of a population effect looks like."
        )

    for outcome in ("hospital_admissions", "asthma_exacerbations", "lost_work_days"):
        value = outcomes.get(outcome, 0.0)
        if value >= 1.0:
            lines.append(f"About {value:,.0f} {OUTCOME_LABELS[outcome]} avoided.")

    if not lines:
        lines.append(
            "The health effect of this change on its own is too small to "
            "express in outcomes. Scale it to a neighbourhood to see it."
        )
    return lines


def get_method_caveats() -> list[str]:
    """Limitations of the method, kept in the module so they cannot be dropped."""
    return [
        (
            "These are screening-level estimates. Real exposure depends on "
            "weather, street layout and where people actually spend their "
            "time, none of which are modelled here."
        ),
        (
            "Health outcomes are population-level expectations, not "
            "predictions about any individual. A fraction of a death means a "
            "small share of a population effect."
        ),
        (
            "Exposure weighting uses intake-fraction style multipliers for "
            "release height and population density. It is a screening "
            "approximation, not dispersion modelling."
        ),
        (
            "Damage costs per tonne vary considerably between published "
            "sources and countries. Treat the ranking of actions as more "
            "reliable than the absolute money figures."
        ),
        (
            "Wood burning is counted as near-zero carbon because the wood "
            "regrows. That accounting is standard and contested, and it is "
            "the reason wood stoves look good on carbon and terrible on air "
            "quality."
        ),
    ]


# --- Persistence ------------------------------------------------------------


def _connect() -> sqlite3.Connection:
    """Open a connection with the co-benefit table guaranteed to exist."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cobenefit_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            from_activity TEXT NOT NULL,
            to_activity TEXT NOT NULL,
            amount REAL NOT NULL,
            density TEXT NOT NULL,
            carbon_saving_kg REAL NOT NULL,
            air_quality_value REAL NOT NULL,
            total_value REAL NOT NULL,
            outcomes TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def save_assessment(
    user_id: int, name: str, assessment: dict[str, Any]
) -> int | None:
    """Persist a switch assessment."""
    if not user_id:
        return None

    conn = _connect()
    try:
        cursor = conn.execute(
            """
            INSERT INTO cobenefit_assessments (
                user_id, name, from_activity, to_activity, amount, density,
                carbon_saving_kg, air_quality_value, total_value, outcomes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                str(name or "Assessment"),
                str(assessment.get("from", "")),
                str(assessment.get("to", "")),
                float(assessment.get("amount", 0.0)),
                str(assessment.get("density", DEFAULT_DENSITY)),
                float(assessment.get("carbon_saving_kg", 0.0)),
                float(assessment.get("air_quality_value", 0.0)),
                float(assessment.get("total_value", 0.0)),
                json.dumps(assessment.get("avoided_outcomes", {})),
                datetime.datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except (sqlite3.Error, TypeError, ValueError):
        logger.exception("Failed to save co-benefit assessment")
        return None
    finally:
        conn.close()


def get_assessments(user_id: int, limit: int = 25) -> list[dict[str, Any]]:
    """Return saved assessments for a user, newest first."""
    if not user_id:
        return []

    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT id, name, from_activity, to_activity, amount, density,
                   carbon_saving_kg, air_quality_value, total_value, outcomes, created_at
            FROM cobenefit_assessments
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(user_id), int(limit)),
        ).fetchall()
    except sqlite3.Error:
        logger.exception("Failed to read co-benefit assessments")
        return []
    finally:
        conn.close()

    assessments = []
    for row in rows:
        try:
            outcomes = json.loads(row[9])
        except (TypeError, ValueError):
            outcomes = {}
        assessments.append(
            {
                "id": row[0],
                "name": row[1],
                "from": row[2],
                "to": row[3],
                "amount": row[4],
                "density": row[5],
                "carbon_saving_kg": row[6],
                "air_quality_value": row[7],
                "total_value": row[8],
                "avoided_outcomes": outcomes,
                "created_at": row[10],
            }
        )
    return assessments


def delete_assessment(user_id: int, assessment_id: int) -> bool:
    """Delete one saved assessment. Scoped by user so ids cannot be guessed."""
    if not user_id or not assessment_id:
        return False

    conn = _connect()
    try:
        cursor = conn.execute(
            "DELETE FROM cobenefit_assessments WHERE id = ? AND user_id = ?",
            (int(assessment_id), int(user_id)),
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error:
        logger.exception("Failed to delete co-benefit assessment")
        return False
    finally:
        conn.close()
