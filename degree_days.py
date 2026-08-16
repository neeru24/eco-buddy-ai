"""Weather normalisation of household energy use via degree-day regression.

Home energy is mostly weather. The app has never acknowledged that, and every
comparison built on raw kWh inherits the confounder:

*   A user insulates their loft in October and compares November to last
    November. This November was 3 degrees colder. The bill went up, and the
    app effectively tells them insulation made things worse.
*   Another user changes nothing at all through a mild winter and gets
    congratulated for a 15% cut.
*   Monthly trend charts look like noise because they are mostly a
    temperature signal with a small behaviour signal buried inside.

This module removes the temperature signal so the behaviour signal can be
seen.

The model
---------
Degree days measure how cold a period was relative to the temperature below
which a building needs heating::

    HDD = sum over days of max(0, base - mean temperature)
    CDD = sum over days of max(0, mean temperature - base)

Consumption is then fitted against them::

    kWh = baseload + sensitivity x HDD

Those two fitted numbers are the useful output, because they map onto
completely different actions:

*   **Baseload** is the always-on load - fridge, standby, hot water, lighting.
    It is what a household burns in a mild month, and it is attacked with
    appliances and habits.
*   **Sensitivity** (kWh per degree day) is the building envelope -
    insulation, draughts, glazing. It is attacked with fabric measures.

Two households with identical annual bills and different splits need opposite
advice, and until now the app could not tell them apart.

Monthly means and Hitchin's formula
-----------------------------------
Degree days want daily temperatures, and users have monthly bills. Computing
degree days straight from a monthly mean under-counts badly, because a month
averaging 16 degrees still contains cold nights that need heating.

`monthly_degree_days()` therefore uses Hitchin's formula, the standard
correction that recovers degree days from a monthly mean by assuming a
plausible spread of daily temperatures around it. It matters most in the
shoulder months, which is exactly where the naive calculation would say zero
and the boiler says otherwise.

Honesty about fit
-----------------
Twelve points and two parameters is a small fit, and it does not always
describe a household. An electric vehicle, a new heat pump or a change of
occupancy drowns the temperature signal. Every fit reports its R squared and
is flagged unreliable when the model does not fit, because telling a user the
model does not describe them is far better than handing them a confident
wrong number.

The module is self-contained: only the standard library is used, its SQLite
tables are created lazily, and no shared files are modified.
"""

import os
import math
import sqlite3
import logging
import datetime
from typing import Any

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

# The temperature below which a building starts needing heat. It is not room
# temperature: internal gains from people, cooking and appliances make up the
# difference, which is why the conventional figure sits several degrees below
# comfort. 15.5C is the long-standing UK and EU convention; the US uses 65F
# (18.3C). It genuinely varies by building, so it is configurable everywhere.
DEFAULT_BASE_TEMPERATURE = 15.5
US_BASE_TEMPERATURE = 18.3
DEFAULT_COOLING_BASE = 22.0

MIN_BASE_TEMPERATURE = 5.0
MAX_BASE_TEMPERATURE = 30.0

# Hitchin's constant. Controls how much of a month's daily variation is
# assumed to sit either side of the monthly mean when recovering degree days
# from that mean alone.
HITCHIN_K = 0.71

# Representative monthly mean temperatures in Celsius, January to December,
# for the northern hemisphere. These are climate normals - the shape of a
# typical year - not a forecast. Anyone holding real local data can override
# every month, which is the intended path for serious use.
CLIMATE_ZONES = {
    "Cold continental": {
        "description": "Long hard winters, warm summers. Inland North America, Northern Europe.",
        "temperatures": [-9.0, -7.0, -1.0, 7.0, 14.0, 19.0, 22.0, 21.0, 16.0, 8.0, 0.0, -6.0],
    },
    "Temperate maritime": {
        "description": "Mild damp winters, cool summers. UK, Ireland, coastal Northwest Europe.",
        "temperatures": [5.0, 5.0, 7.0, 9.0, 13.0, 16.0, 18.0, 17.5, 15.0, 11.5, 8.0, 6.0],
    },
    "Temperate continental": {
        "description": "Cold winters, warm summers. Central and Eastern Europe.",
        "temperatures": [0.0, 1.0, 5.0, 10.0, 15.0, 18.0, 20.0, 19.5, 15.0, 10.0, 5.0, 1.0],
    },
    "Mediterranean": {
        "description": "Mild winters, hot dry summers. Southern Europe, coastal California.",
        "temperatures": [10.0, 11.0, 13.0, 15.0, 19.0, 23.0, 26.0, 26.0, 23.0, 19.0, 14.0, 11.0],
    },
    "Subtropical humid": {
        "description": "Short mild winters, long humid summers. Southeast US, East Asia.",
        "temperatures": [8.0, 10.0, 14.0, 19.0, 24.0, 28.0, 29.0, 29.0, 26.0, 20.0, 14.0, 9.0],
    },
    "Hot arid": {
        "description": "Warm winters, extreme summers. Gulf states, desert Southwest.",
        "temperatures": [14.0, 16.0, 20.0, 26.0, 31.0, 34.0, 36.0, 36.0, 33.0, 28.0, 21.0, 16.0],
    },
    "Tropical": {
        "description": "Warm all year, no heating season. Cooling dominates.",
        "temperatures": [26.0, 26.0, 27.0, 27.5, 27.5, 26.5, 26.0, 26.0, 26.0, 26.0, 26.0, 26.0],
    },
}

DEFAULT_CLIMATE_ZONE = "Temperate maritime"

# Below this R squared the two-parameter model is not describing the
# household and its outputs should not be quoted as fact.
RELIABLE_FIT_R_SQUARED = 0.70
WEAK_FIT_R_SQUARED = 0.40

# Fewer readings than this cannot support a fit worth reporting.
MIN_READINGS = 4
RECOMMENDED_READINGS = 12

# Below this annual total there is no heating season worth speaking of, and
# relative tests against the total stop meaning anything.
MIN_MEANINGFUL_ANNUAL_HDD = 100.0

# The fit classifications whose numbers are safe to quote as measurements.
TRUSTWORTHY_QUALITIES = ("good", "good_but_short")

# A household whose weather-sensitive share is above this is an envelope
# problem; below it, an appliance problem.
ENVELOPE_DOMINANT_SHARE = 0.55
BASELOAD_DOMINANT_SHARE = 0.55


class DegreeDayError(ValueError):
    """Raised when readings cannot support a weather-normalised model."""


# --- Climate data -----------------------------------------------------------


def list_climate_zones() -> list[dict[str, Any]]:
    """Return the built-in climate zones, coldest first."""
    zones = []
    for name, details in CLIMATE_ZONES.items():
        temperatures = details["temperatures"]
        zones.append(
            {
                "name": name,
                "description": details["description"],
                "temperatures": list(temperatures),
                "mean_temperature": round(sum(temperatures) / len(temperatures), 1),
                "annual_hdd": round(annual_degree_days(name)["hdd"], 0),
                "annual_cdd": round(annual_degree_days(name)["cdd"], 0),
            }
        )
    return sorted(zones, key=lambda item: item["mean_temperature"])


def get_climate_profile(zone: str) -> list[float]:
    """Return the 12 monthly mean temperatures for a climate zone."""
    details = CLIMATE_ZONES.get(zone) or CLIMATE_ZONES[DEFAULT_CLIMATE_ZONE]
    return list(details["temperatures"])


def clean_base_temperature(base: float) -> float:
    """Coerce a base temperature into a physically sensible range."""
    try:
        value = float(base)
    except (TypeError, ValueError):
        return DEFAULT_BASE_TEMPERATURE
    if math.isnan(value) or math.isinf(value):
        return DEFAULT_BASE_TEMPERATURE
    return max(MIN_BASE_TEMPERATURE, min(MAX_BASE_TEMPERATURE, value))


def clean_temperatures(temperatures: list[float] | None, fallback_zone: str = DEFAULT_CLIMATE_ZONE) -> list[float]:
    """Normalise a user-supplied 12-month temperature series."""
    fallback = get_climate_profile(fallback_zone)
    values = list(temperatures or [])[:12]
    cleaned = []
    for index in range(12):
        default = fallback[index]
        if index >= len(values):
            cleaned.append(default)
            continue
        try:
            number = float(values[index])
        except (TypeError, ValueError):
            cleaned.append(default)
            continue
        if math.isnan(number) or math.isinf(number):
            cleaned.append(default)
            continue
        # Wider than any inhabited place, but a sanity bound all the same.
        cleaned.append(max(-60.0, min(60.0, number)))
    return cleaned


# --- Degree days ------------------------------------------------------------


def degree_days_from_daily(temperatures: list[float] | None, base: float = DEFAULT_BASE_TEMPERATURE, cooling_base: float | None = None) -> dict[str, Any]:
    """Heating and cooling degree days from a series of daily mean temperatures.

    The textbook definition, used whenever real daily data is available. No
    correction is needed here because nothing has been averaged away.
    """
    heating_base = clean_base_temperature(base)
    cool_base = clean_base_temperature(
        cooling_base if cooling_base is not None else DEFAULT_COOLING_BASE
    )

    hdd = 0.0
    cdd = 0.0
    days = 0
    for temperature in temperatures or []:
        try:
            value = float(temperature)
        except (TypeError, ValueError):
            continue
        if math.isnan(value) or math.isinf(value):
            continue
        days += 1
        hdd += max(0.0, heating_base - value)
        cdd += max(0.0, value - cool_base)

    return {"hdd": hdd, "cdd": cdd, "days": days}


def _hitchin(difference: float, days: int) -> float:
    """Hitchin's formula: degree days from a monthly mean temperature.

    ``difference`` is (base - mean) for heating or (mean - base) for cooling.
    A month whose mean sits exactly on the base still accumulates degree days,
    because half its days were colder than the mean - that limiting case is
    ``days / k`` and has to be handled separately or the formula divides by
    zero.
    """
    if abs(difference) < 1e-9:
        return days / HITCHIN_K

    denominator = 1.0 - math.exp(-HITCHIN_K * difference)
    if abs(denominator) < 1e-12:
        return 0.0
    return max(0.0, days * difference / denominator)


def monthly_degree_days(
    month_index: int,
    mean_temperature: float,
    base: float = DEFAULT_BASE_TEMPERATURE,
    cooling_base: float | None = None,
    days: int | None = None,
) -> dict[str, Any]:
    """Degree days for one month, recovered from its mean temperature.

    Using ``max(0, base - mean) * days`` instead would report zero heating for
    any month averaging above the base, which is wrong for every shoulder
    month in a temperate climate - and shoulder months are where the
    interesting variation lives.
    """
    index = int(month_index) % 12
    day_count = int(days) if days else DAYS_IN_MONTH[index]
    heating_base = clean_base_temperature(base)
    cool_base = clean_base_temperature(
        cooling_base if cooling_base is not None else DEFAULT_COOLING_BASE
    )

    try:
        mean = float(mean_temperature)
    except (TypeError, ValueError):
        mean = heating_base

    return {
        "month": MONTHS[index],
        "month_index": index,
        "days": day_count,
        "mean_temperature": mean,
        "hdd": _hitchin(heating_base - mean, day_count),
        "cdd": _hitchin(mean - cool_base, day_count),
    }


def monthly_degree_day_series(
    zone: str = DEFAULT_CLIMATE_ZONE,
    base: float = DEFAULT_BASE_TEMPERATURE,
    cooling_base: float | None = None,
    temperatures: list[float] | None = None,
) -> list[dict[str, Any]]:
    """Degree days for all twelve months of a climate zone or custom series."""
    profile = clean_temperatures(temperatures, zone) if temperatures else get_climate_profile(zone)
    return [
        monthly_degree_days(index, profile[index], base, cooling_base)
        for index in range(12)
    ]


def annual_degree_days(zone: str = DEFAULT_CLIMATE_ZONE, base: float = DEFAULT_BASE_TEMPERATURE, cooling_base: float | None = None, temperatures: list[float] | None = None) -> dict[str, Any]:
    """Annual heating and cooling degree day totals."""
    series = monthly_degree_day_series(zone, base, cooling_base, temperatures)
    return {
        "hdd": sum(month["hdd"] for month in series),
        "cdd": sum(month["cdd"] for month in series),
        "months": series,
    }


def heating_season_months(zone: str = DEFAULT_CLIMATE_ZONE, base: float = DEFAULT_BASE_TEMPERATURE, threshold: float = 0.05) -> list[str]:
    """Months carrying a meaningful share of the year's heating demand.

    The absolute floor matters as much as the relative threshold. In a
    tropical climate the annual total is a handful of degree days spread
    evenly, so every month clears 5% of nothing and a share test alone would
    report a twelve-month heating season for somewhere that never heats.
    """
    series = monthly_degree_day_series(zone, base)
    total = sum(month["hdd"] for month in series)
    if total < MIN_MEANINGFUL_ANNUAL_HDD:
        return []
    return [month["month"] for month in series if month["hdd"] / total >= threshold]


# --- Fitting ----------------------------------------------------------------


def _clean_readings(readings: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Validate and normalise meter readings into (hdd, kwh) pairs."""
    cleaned = []
    for reading in readings or []:
        try:
            hdd = float(reading.get("hdd", 0.0))
            kwh = float(reading.get("kwh", 0.0))
        except (TypeError, ValueError, AttributeError):
            continue
        if math.isnan(hdd) or math.isnan(kwh) or math.isinf(hdd) or math.isinf(kwh):
            continue
        if hdd < 0 or kwh < 0:
            continue
        cleaned.append(
            {
                "label": str(reading.get("label", "")),
                "hdd": hdd,
                "kwh": kwh,
            }
        )
    return cleaned


def fit_energy_model(readings: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Fit ``kWh = baseload + sensitivity x HDD`` by ordinary least squares.

    The baseload is clamped at zero. A negative intercept is arithmetically
    possible and physically meaningless - no household consumes less than
    nothing in a warm month - and when it happens it is a sign the fit is bad,
    which the R squared will already be saying.
    """
    cleaned = _clean_readings(readings)
    if len(cleaned) < MIN_READINGS:
        raise DegreeDayError(
            f"At least {MIN_READINGS} readings are needed to fit a model; got {len(cleaned)}"
        )

    count = len(cleaned)
    mean_hdd = sum(item["hdd"] for item in cleaned) / count
    mean_kwh = sum(item["kwh"] for item in cleaned) / count

    covariance = sum(
        (item["hdd"] - mean_hdd) * (item["kwh"] - mean_kwh) for item in cleaned
    )
    variance = sum((item["hdd"] - mean_hdd) ** 2 for item in cleaned)

    if variance <= 1e-9:
        # Every reading came from a period with the same weather, so there is
        # no temperature signal to separate. Report the average as pure
        # baseload and flag it rather than dividing by zero.
        return {
            "baseload": mean_kwh,
            "sensitivity": 0.0,
            "r_squared": 0.0,
            "readings": count,
            "mean_hdd": mean_hdd,
            "mean_kwh": mean_kwh,
            "is_reliable": False,
            "quality": "no_variation",
            "warning": (
                "Every reading covers similar weather, so heating cannot be "
                "separated from baseload. Add readings from colder months."
            ),
        }

    sensitivity = covariance / variance
    baseload = mean_kwh - sensitivity * mean_hdd

    clamped = False
    if baseload < 0:
        baseload = 0.0
        clamped = True

    total_variation = sum((item["kwh"] - mean_kwh) ** 2 for item in cleaned)
    if total_variation <= 1e-9:
        r_squared = 1.0 if abs(sensitivity) < 1e-9 else 0.0
    else:
        residuals = sum(
            (item["kwh"] - (baseload + sensitivity * item["hdd"])) ** 2
            for item in cleaned
        )
        r_squared = max(0.0, min(1.0, 1.0 - residuals / total_variation))

    quality, warning = _fit_quality(r_squared, count, sensitivity, clamped)

    # Reliability has to follow the classification, not the R squared alone.
    # Perfectly flat consumption fits a zero slope perfectly, and a household
    # whose usage *falls* as it gets colder fits a negative slope perfectly.
    # Both score well and neither supports a heating/baseload split.
    return {
        "baseload": baseload,
        "sensitivity": sensitivity,
        "r_squared": r_squared,
        "readings": count,
        "mean_hdd": mean_hdd,
        "mean_kwh": mean_kwh,
        "baseload_clamped": clamped,
        "is_reliable": (
            quality in TRUSTWORTHY_QUALITIES
            and r_squared >= RELIABLE_FIT_R_SQUARED
            and count >= MIN_READINGS
        ),
        "quality": quality,
        "warning": warning,
    }


def _fit_quality(r_squared: float, count: int, sensitivity: float, clamped: bool) -> tuple[str, str]:
    """Classify a fit and explain what a poor one usually means."""
    if sensitivity <= 0:
        return (
            "no_heating_signal",
            "Consumption does not rise in colder months. Either the home is "
            "not heated by this meter, or something else dominates the bill.",
        )
    if clamped:
        return (
            "implausible",
            "The fit implies negative baseload consumption, which cannot be "
            "right. Check the readings cover full, non-overlapping periods.",
        )
    if r_squared < WEAK_FIT_R_SQUARED:
        return (
            "poor",
            "Temperature explains very little of this consumption. An "
            "electric vehicle, a heat pump or a change of occupancy will do "
            "this. Treat the split below as indicative only.",
        )
    if r_squared < RELIABLE_FIT_R_SQUARED:
        return (
            "weak",
            "Temperature explains some but not most of this consumption. The "
            "split below is a rough guide rather than a measurement.",
        )
    if count < RECOMMENDED_READINGS:
        return (
            "good_but_short",
            f"A good fit, but on only {count} readings. A full "
            f"{RECOMMENDED_READINGS} months would make it dependable.",
        )
    return ("good", "")


def predict_consumption(fit: dict[str, Any], hdd: float) -> float:
    """Consumption the fitted model expects for a given number of degree days."""
    try:
        degree_days = max(0.0, float(hdd))
    except (TypeError, ValueError):
        degree_days = 0.0
    return max(0.0, fit.get("baseload", 0.0) + fit.get("sensitivity", 0.0) * degree_days)


def split_consumption(fit: dict[str, Any], annual_hdd: float, periods: int = 12) -> dict[str, Any]:
    """Split annual consumption into the baseload and weather-driven parts.

    This is the output that changes what a household should do next.
    """
    try:
        degree_days = max(0.0, float(annual_hdd))
    except (TypeError, ValueError):
        degree_days = 0.0

    baseload_total = max(0.0, fit.get("baseload", 0.0)) * max(1, int(periods))
    weather_total = max(0.0, fit.get("sensitivity", 0.0)) * degree_days
    total = baseload_total + weather_total

    baseload_share = (baseload_total / total) if total > 0 else 0.0
    weather_share = (weather_total / total) if total > 0 else 0.0

    if weather_share >= ENVELOPE_DOMINANT_SHARE:
        dominant = "envelope"
    elif baseload_share >= BASELOAD_DOMINANT_SHARE:
        dominant = "baseload"
    else:
        dominant = "balanced"

    return {
        "baseload_total": baseload_total,
        "weather_total": weather_total,
        "total": total,
        "baseload_share": baseload_share,
        "weather_share": weather_share,
        "dominant": dominant,
        "annual_hdd": degree_days,
    }


# --- Normalisation and attribution ------------------------------------------


def normalise_consumption(kwh: float, actual_hdd: float, reference_hdd: float, fit: dict[str, Any]) -> dict[str, Any]:
    """Restate consumption at reference weather.

    Only the weather-sensitive part is scaled. Scaling the whole bill by the
    ratio of degree days is the obvious shortcut and it is wrong - it would
    inflate a household's fridge and lighting along with its heating.
    """
    try:
        actual = max(0.0, float(actual_hdd))
        reference = max(0.0, float(reference_hdd))
        consumption = max(0.0, float(kwh))
    except (TypeError, ValueError):
        raise DegreeDayError("Consumption and degree days must be numeric")

    sensitivity = max(0.0, fit.get("sensitivity", 0.0))
    weather_part = sensitivity * actual
    baseload_part = max(0.0, consumption - weather_part)
    normalised = baseload_part + sensitivity * reference

    return {
        "actual_kwh": consumption,
        "normalised_kwh": normalised,
        "actual_hdd": actual,
        "reference_hdd": reference,
        "weather_adjustment": normalised - consumption,
        "baseload_part": baseload_part,
        "weather_part": weather_part,
    }


def attribute_change(before_kwh: float, before_hdd: float, after_kwh: float, after_hdd: float, fit: dict[str, Any], emission_factor: float = 0.0) -> dict[str, Any]:
    """Split a year-on-year change into a weather part and a behaviour part.

    The weather part is what the fitted sensitivity says the temperature
    difference alone should have caused. Whatever is left is behaviour - which
    is the number the user has been trying to see all along.
    """
    try:
        before_consumption = max(0.0, float(before_kwh))
        after_consumption = max(0.0, float(after_kwh))
        before_degree_days = max(0.0, float(before_hdd))
        after_degree_days = max(0.0, float(after_hdd))
    except (TypeError, ValueError):
        raise DegreeDayError("Consumption and degree days must be numeric")

    sensitivity = max(0.0, fit.get("sensitivity", 0.0))
    total_change = after_consumption - before_consumption
    weather_change = sensitivity * (after_degree_days - before_degree_days)
    behaviour_change = total_change - weather_change

    try:
        factor = max(0.0, float(emission_factor))
    except (TypeError, ValueError):
        factor = 0.0

    percent = (total_change / before_consumption * 100.0) if before_consumption > 0 else 0.0
    behaviour_percent = (
        (behaviour_change / before_consumption * 100.0) if before_consumption > 0 else 0.0
    )

    return {
        "total_change": total_change,
        "weather_change": weather_change,
        "behaviour_change": behaviour_change,
        "total_change_percent": percent,
        "behaviour_change_percent": behaviour_percent,
        "total_change_co2": total_change * factor,
        "weather_change_co2": weather_change * factor,
        "behaviour_change_co2": behaviour_change * factor,
        "colder": after_degree_days > before_degree_days,
        "verdict": _attribution_verdict(total_change, behaviour_change),
        "explanation": _attribution_explanation(
            total_change, weather_change, behaviour_change
        ),
    }


def _attribution_verdict(total_change: float, behaviour_change: float) -> str:
    """Classify the four interesting combinations of bill and behaviour."""
    bill_fell = total_change < 0
    behaviour_improved = behaviour_change < 0

    if bill_fell and behaviour_improved:
        return "genuine_improvement"
    if bill_fell and not behaviour_improved:
        return "mild_weather_flattered"
    if not bill_fell and behaviour_improved:
        return "hidden_improvement"
    return "genuine_increase"


def _attribution_explanation(total_change: float, weather_change: float, behaviour_change: float) -> str:
    """Plain sentence for the attribution, because the signs get misread."""
    verdict = _attribution_verdict(total_change, behaviour_change)
    total = abs(total_change)
    weather = abs(weather_change)
    behaviour = abs(behaviour_change)

    if verdict == "genuine_improvement":
        return (
            f"Your usage fell by {total:,.0f} kWh, and {behaviour:,.0f} kWh of "
            f"that was you rather than the weather. That is a real improvement."
        )
    if verdict == "mild_weather_flattered":
        return (
            f"Your usage fell by {total:,.0f} kWh, but a milder year accounts "
            f"for {weather:,.0f} kWh of it. Adjusted for weather you actually "
            f"used {behaviour:,.0f} kWh more."
        )
    if verdict == "hidden_improvement":
        return (
            f"Your bill went up by {total:,.0f} kWh, but it was a colder year. "
            f"Adjusted for weather you used {behaviour:,.0f} kWh less - the "
            f"improvement is real, the weather just hid it."
        )
    return (
        f"Your usage rose by {total:,.0f} kWh, and {behaviour:,.0f} kWh of that "
        f"was not the weather."
    )


def estimate_retrofit(before_fit: dict[str, Any], after_fit: dict[str, Any], annual_hdd: float, emission_factor: float = 0.0) -> dict[str, Any]:
    """What a retrofit actually delivered, measured rather than promised.

    Fabric measures show up as a drop in kWh per degree day. A change in
    baseload is a different thing entirely - new appliances, or someone
    working from home - so the two are reported separately rather than
    summed into one flattering headline.
    """
    try:
        degree_days = max(0.0, float(annual_hdd))
        factor = max(0.0, float(emission_factor))
    except (TypeError, ValueError):
        raise DegreeDayError("Degree days and emission factor must be numeric")

    before_sensitivity = max(0.0, before_fit.get("sensitivity", 0.0))
    after_sensitivity = max(0.0, after_fit.get("sensitivity", 0.0))
    before_baseload = max(0.0, before_fit.get("baseload", 0.0))
    after_baseload = max(0.0, after_fit.get("baseload", 0.0))

    sensitivity_change = after_sensitivity - before_sensitivity
    sensitivity_percent = (
        (sensitivity_change / before_sensitivity * 100.0) if before_sensitivity > 0 else 0.0
    )
    annual_saving = -sensitivity_change * degree_days
    baseload_change = (after_baseload - before_baseload) * 12

    both_reliable = bool(before_fit.get("is_reliable")) and bool(after_fit.get("is_reliable"))

    return {
        "before_sensitivity": before_sensitivity,
        "after_sensitivity": after_sensitivity,
        "sensitivity_change": sensitivity_change,
        "sensitivity_change_percent": sensitivity_percent,
        "annual_kwh_saving": annual_saving,
        "annual_co2_saving": annual_saving * factor,
        "baseload_change_kwh": baseload_change,
        "improved": sensitivity_change < 0,
        "both_fits_reliable": both_reliable,
        "confidence": "measured" if both_reliable else "indicative",
        "note": (
            ""
            if both_reliable
            else "One or both fits are weak, so treat this as indicative "
                 "rather than a measurement."
        ),
    }


# --- Narrative --------------------------------------------------------------


def get_energy_tips(fit: dict[str, Any], split: dict[str, Any]) -> list[str]:
    """Advice that follows from the split, not generic energy-saving filler."""
    tips = []

    if not fit.get("is_reliable"):
        tips.append(
            "The model does not fit your readings well enough to give confident "
            "advice. Check the readings cover complete, non-overlapping periods "
            "before acting on the split below."
        )

    dominant = split.get("dominant")
    if dominant == "envelope":
        tips.append(
            f"{split['weather_share'] * 100:.0f}% of your energy goes on "
            f"heating. Your building fabric is the problem, not your "
            f"appliances - insulation and draught-proofing are where the money "
            f"is."
        )
        tips.append(
            "At this sensitivity, a one degree cut in thermostat setting is "
            "worth more than any appliance you could replace."
        )
    elif dominant == "baseload":
        tips.append(
            f"{split['baseload_share'] * 100:.0f}% of your energy is baseload - "
            f"consumption that does not care about the weather. Insulation "
            f"would barely touch it. Look at always-on appliances, hot water "
            f"and standby loads."
        )
        tips.append(
            "Find your baseload directly: read the meter last thing at night "
            "and first thing in the morning, when nothing should be running."
        )
    else:
        tips.append(
            "Your consumption is split fairly evenly between heating and "
            "baseload, so both fabric measures and appliance changes are worth "
            "doing."
        )

    if fit.get("sensitivity", 0.0) > 0:
        tips.append(
            f"Every heating degree day costs you "
            f"{fit['sensitivity']:.2f} kWh. That single number is what a "
            f"retrofit has to move, and it is how you will know whether one "
            f"worked."
        )

    return tips


def compare_to_typical(fit: dict[str, Any], annual_hdd: float, floor_area_m2: float | None = None) -> dict[str, Any]:
    """Put a household's sensitivity in context.

    Sensitivity per square metre is roughly comparable between homes, which
    makes it far more useful than a raw bill for answering "is this normal?".
    """
    split = split_consumption(fit, annual_hdd)
    result = {
        "annual_total": split["total"],
        "weather_share": split["weather_share"],
        "sensitivity": fit.get("sensitivity", 0.0),
    }

    try:
        area = float(floor_area_m2) if floor_area_m2 else 0.0
    except (TypeError, ValueError):
        area = 0.0

    if area > 0:
        result["sensitivity_per_m2"] = fit.get("sensitivity", 0.0) / area
        result["annual_kwh_per_m2"] = split["total"] / area
        # Rough bands for annual heating energy per square metre. A modern
        # well-insulated home lands near the bottom, an uninsulated solid-wall
        # house near the top.
        per_m2 = result["annual_kwh_per_m2"]
        if per_m2 < 60:
            result["band"] = "excellent"
        elif per_m2 < 120:
            result["band"] = "good"
        elif per_m2 < 200:
            result["band"] = "typical"
        else:
            result["band"] = "poor"
    return result


# --- Persistence ------------------------------------------------------------


def _connect() -> sqlite3.Connection:
    """Open a connection with the degree-day tables guaranteed to exist."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS meter_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            label TEXT NOT NULL,
            kwh REAL NOT NULL,
            hdd REAL NOT NULL,
            period TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS energy_baselines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            baseload REAL NOT NULL,
            sensitivity REAL NOT NULL,
            r_squared REAL NOT NULL,
            readings INTEGER NOT NULL,
            climate_zone TEXT,
            base_temperature REAL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def save_reading(user_id: int, label: str, kwh: float, hdd: float, period: str = "") -> int | None:
    """Store one meter reading with the degree days it covered."""
    if not user_id:
        return None

    conn = _connect()
    try:
        cursor = conn.execute(
            """
            INSERT INTO meter_readings (user_id, label, kwh, hdd, period, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                str(label or ""),
                max(0.0, float(kwh)),
                max(0.0, float(hdd)),
                str(period or ""),
                datetime.datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except (sqlite3.Error, TypeError, ValueError):
        logger.exception("Failed to save meter reading")
        return None
    finally:
        conn.close()


def get_readings(user_id: int, limit: int = 60) -> list[dict[str, Any]]:
    """Return a user's readings, oldest first so they plot in order."""
    if not user_id:
        return []

    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT id, label, kwh, hdd, period, created_at
            FROM meter_readings
            WHERE user_id = ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (int(user_id), int(limit)),
        ).fetchall()
    except sqlite3.Error:
        logger.exception("Failed to read meter readings")
        return []
    finally:
        conn.close()

    return [
        {
            "id": row[0],
            "label": row[1],
            "kwh": row[2],
            "hdd": row[3],
            "period": row[4],
            "created_at": row[5],
        }
        for row in rows
    ]


def delete_reading(user_id: int, reading_id: int) -> bool:
    """Delete one reading. Scoped by user so ids cannot be guessed."""
    if not user_id or not reading_id:
        return False

    conn = _connect()
    try:
        cursor = conn.execute(
            "DELETE FROM meter_readings WHERE id = ? AND user_id = ?",
            (int(reading_id), int(user_id)),
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error:
        logger.exception("Failed to delete meter reading")
        return False
    finally:
        conn.close()


def save_baseline(user_id: int, name: str, fit: dict[str, Any], climate_zone: str = "", base_temperature: float = DEFAULT_BASE_TEMPERATURE) -> int | None:
    """Persist a fitted model so a later retrofit can be measured against it."""
    if not user_id:
        return None

    conn = _connect()
    try:
        cursor = conn.execute(
            """
            INSERT INTO energy_baselines (
                user_id, name, baseload, sensitivity, r_squared, readings,
                climate_zone, base_temperature, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                str(name or "Baseline"),
                float(fit.get("baseload", 0.0)),
                float(fit.get("sensitivity", 0.0)),
                float(fit.get("r_squared", 0.0)),
                int(fit.get("readings", 0)),
                str(climate_zone or ""),
                float(base_temperature),
                datetime.datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except (sqlite3.Error, TypeError, ValueError):
        logger.exception("Failed to save energy baseline")
        return None
    finally:
        conn.close()


def get_baselines(user_id: int, limit: int = 25) -> list[dict[str, Any]]:
    """Return saved baselines for a user, newest first."""
    if not user_id:
        return []

    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT id, name, baseload, sensitivity, r_squared, readings,
                   climate_zone, base_temperature, created_at
            FROM energy_baselines
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(user_id), int(limit)),
        ).fetchall()
    except sqlite3.Error:
        logger.exception("Failed to read energy baselines")
        return []
    finally:
        conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "baseload": row[2],
            "sensitivity": row[3],
            "r_squared": row[4],
            "readings": row[5],
            "climate_zone": row[6],
            "base_temperature": row[7],
            "created_at": row[8],
            # Re-derived rather than stored, so the thresholds stay in one
            # place. A non-positive sensitivity disqualifies a baseline for
            # the same reason it does at fit time: there is no heating signal
            # in it to compare a later retrofit against.
            "is_reliable": (
                row[3] > 0
                and row[4] >= RELIABLE_FIT_R_SQUARED
                and row[5] >= MIN_READINGS
            ),
        }
        for row in rows
    ]


def delete_baseline(user_id: int, baseline_id: int) -> bool:
    """Delete one saved baseline. Scoped by user."""
    if not user_id or not baseline_id:
        return False

    conn = _connect()
    try:
        cursor = conn.execute(
            "DELETE FROM energy_baselines WHERE id = ? AND user_id = ?",
            (int(baseline_id), int(user_id)),
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error:
        logger.exception("Failed to delete energy baseline")
        return False
    finally:
        conn.close()
