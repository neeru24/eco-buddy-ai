"""Time-of-use scheduling for flexible electrical loads.

Every other electricity feature in this app treats grid carbon intensity as a
single flat number: one gCO2/kWh figure multiplied by consumption. Real grids
do not work that way. Intensity swings by a factor of two or three across a
single day as solar comes up, wind changes, and peaking gas plants switch on
to cover the evening ramp.

That means the same kilowatt-hour emits very different amounts depending on
*when* it is drawn. This module answers the question the rest of the app
cannot: not how much you use, but when to use it.

The model is deliberately simple and inspectable:

    load emissions = kWh * mean(intensity over the run window) / 1000

A load is described by its energy draw and how long it runs. Scheduling is a
search over the contiguous windows a user is willing to allow, picking the one
with the lowest average intensity. Cost is computed the same way against a
time-of-use tariff, because the cheapest and greenest hours do not always
coincide and users deserve to see both.

Built-in 24-hour curves keep the feature usable with no network access, and
anyone with real figures from their grid operator can override every hour.

The module is self-contained: its SQLite table is created lazily and no shared
files are modified.
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

# Representative 24-hour grid carbon intensity curves in gCO2/kWh, indexed by
# hour 0-23 in local time. These are shapes rather than forecasts - what
# matters for scheduling is the relative difference between hours, not the
# absolute level. Users with real operator data can override every hour.
GRID_PROFILES = {
    "Solar-heavy": [
        295, 290, 288, 288, 292, 300, 310, 300, 255, 195, 150, 122,
        110, 108, 118, 150, 215, 300, 375, 400, 385, 355, 325, 305,
    ],
    "Wind-heavy": [
        180, 172, 168, 165, 168, 178, 205, 235, 245, 240, 232, 228,
        225, 222, 224, 232, 258, 290, 305, 298, 272, 240, 210, 192,
    ],
    "Coal-heavy": [
        780, 772, 768, 768, 775, 795, 830, 862, 858, 845, 838, 832,
        828, 826, 832, 848, 878, 905, 918, 908, 880, 848, 815, 795,
    ],
    "Gas-balanced": [
        320, 308, 300, 298, 305, 330, 375, 410, 398, 380, 368, 360,
        355, 352, 360, 382, 425, 468, 485, 472, 440, 402, 368, 340,
    ],
    "Nuclear baseload": [
        82, 80, 79, 78, 79, 82, 86, 90, 89, 87, 86, 85,
        85, 84, 85, 87, 90, 92, 92, 91, 89, 87, 85, 83,
    ],
    "Hydro-dominant": [
        44, 42, 41, 40, 41, 44, 50, 56, 55, 53, 51, 50,
        49, 49, 50, 53, 58, 63, 65, 63, 59, 54, 50, 46,
    ],
}

DEFAULT_GRID_PROFILE = "Gas-balanced"

# Normalised rooftop solar generation shape, 0 at night and 1 at solar noon.
# Used to reshape a grid curve for users who self-consume their own output:
# the hours they generate are effectively far cleaner for them personally than
# the grid average suggests.
SOLAR_SHAPE = [
    0.00, 0.00, 0.00, 0.00, 0.00, 0.02, 0.10, 0.24, 0.44, 0.64, 0.82, 0.94,
    1.00, 0.98, 0.88, 0.72, 0.52, 0.32, 0.14, 0.03, 0.00, 0.00, 0.00, 0.00,
]

# Flexible household loads. ``kwh`` is the energy for one complete run and
# ``duration_hours`` how long that run takes. ``shiftable`` marks the loads
# whose timing a household can genuinely choose - a fridge cannot be moved,
# a dishwasher can.
SHIFTABLE_LOADS = {
    "Dishwasher": {
        "kwh": 1.4, "duration_hours": 2, "shiftable": True,
        "note": "Nearly every machine has a delay-start button already.",
    },
    "Washing machine": {
        "kwh": 0.9, "duration_hours": 2, "shiftable": True,
        "note": "Easy to batch - two loads back to back in the cleanest window.",
    },
    "Tumble dryer": {
        "kwh": 2.5, "duration_hours": 2, "shiftable": True,
        "note": "The heaviest routine load in most homes, and fully shiftable.",
    },
    "EV charge": {
        "kwh": 30.0, "duration_hours": 6, "shiftable": True,
        "note": "The single biggest shiftable load - worth getting right.",
    },
    "Hot water cylinder": {
        "kwh": 6.0, "duration_hours": 3, "shiftable": True,
        "note": "A timer on the immersion heater costs almost nothing to fit.",
    },
    "Pool pump": {
        "kwh": 4.5, "duration_hours": 4, "shiftable": True,
        "note": "Filtration only has to happen daily, not at any given hour.",
    },
    "Home battery charge": {
        "kwh": 10.0, "duration_hours": 4, "shiftable": True,
        "note": "Charge in the trough, discharge through the evening ramp.",
    },
    "Oven / cooking": {
        "kwh": 1.8, "duration_hours": 1, "shiftable": False,
        "note": "Tied to mealtimes - listed so it shows in the daily picture.",
    },
    "Refrigeration": {
        "kwh": 1.2, "duration_hours": 24, "shiftable": False,
        "note": "Runs continuously; included for completeness only.",
    },
}

# Time-of-use tariffs as a price per kWh for each hour of the day. The prices
# are illustrative; the point is the shape, and users can override it.
TARIFFS = {
    "Flat rate": [0.28] * HOURS_IN_DAY,
    "Day / night": [
        0.14, 0.14, 0.14, 0.14, 0.14, 0.14, 0.14, 0.32, 0.32, 0.32, 0.32, 0.32,
        0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.14,
    ],
    "Three-band peak": [
        0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.22, 0.22, 0.22, 0.22, 0.22, 0.22,
        0.22, 0.22, 0.22, 0.22, 0.45, 0.45, 0.45, 0.45, 0.22, 0.22, 0.22, 0.12,
    ],
}

DEFAULT_TARIFF = "Flat rate"

DEFAULT_DAYS_PER_YEAR = 313  # Roughly six runs a week rather than every day.

# Below this score a grid is flat enough that shifting is not worth the effort,
# and the feature says so instead of inventing advice.
SHIFT_WORTH_IT_SCORE = 25.0


def list_grid_profiles() -> list[dict[str, Any]]:
    """Return the built-in grid profiles, cleanest average first."""
    profiles = []
    for name, curve in GRID_PROFILES.items():
        average = sum(curve) / len(curve)
        profiles.append(
            {
                "name": name,
                "average_intensity": round(average, 1),
                "min_intensity": min(curve),
                "max_intensity": max(curve),
                "shift_potential": shift_potential(curve),
            }
        )
    return sorted(profiles, key=lambda item: item["average_intensity"])


def list_shiftable_loads(shiftable_only: bool = False) -> list[dict[str, Any]]:
    """Return the load catalogue, heaviest energy draw first."""
    loads = [
        {"name": name, **details}
        for name, details in SHIFTABLE_LOADS.items()
        if not shiftable_only or details["shiftable"]
    ]
    return sorted(loads, key=lambda item: item["kwh"], reverse=True)


def get_intensity_curve(grid_profile: str) -> list[float]:
    """Return the 24-hour gCO2/kWh curve for a grid mix."""
    return list(GRID_PROFILES.get(grid_profile, GRID_PROFILES[DEFAULT_GRID_PROFILE]))


def get_tariff(tariff_name: str) -> list[float]:
    """Return the 24-hour price-per-kWh series for a tariff."""
    return list(TARIFFS.get(tariff_name, TARIFFS[DEFAULT_TARIFF]))


def _clean_series(series: list[float] | None, fallback: list[float], maximum: float) -> list[float]:
    """Normalise a user-supplied 24-value series into a usable curve.

    Short series are padded from the fallback, long ones truncated, and every
    entry is coerced into a sane non-negative range so a stray text box or a
    pasted spreadsheet cell cannot produce nonsense downstream.
    """
    values = list(series or [])[:HOURS_IN_DAY]
    cleaned = []
    for index in range(HOURS_IN_DAY):
        default = fallback[index] if index < len(fallback) else 0.0
        if index >= len(values):
            cleaned.append(float(default))
            continue
        try:
            number = float(values[index])
        except (TypeError, ValueError):
            cleaned.append(float(default))
            continue
        if number != number or number in (float("inf"), float("-inf")):
            cleaned.append(float(default))
            continue
        cleaned.append(max(0.0, min(number, maximum)))
    return cleaned


def clean_intensity_curve(curve: list[float] | None) -> list[float]:
    """Coerce a user-entered intensity curve into 24 sane hourly values."""
    return _clean_series(curve, GRID_PROFILES[DEFAULT_GRID_PROFILE], 2000.0)


def clean_tariff(prices: list[float] | None) -> list[float]:
    """Coerce a user-entered tariff into 24 sane hourly prices."""
    return _clean_series(prices, TARIFFS[DEFAULT_TARIFF], 100.0)


def blend_curve(curve: list[float], solar_share: float) -> list[float]:
    """Reshape a grid curve for a household with its own rooftop solar.

    ``solar_share`` is the fraction of a midday load the panels can cover. The
    hours the array generates become effectively cleaner for that household
    than the grid average, which is why an overnight EV charge can be exactly
    the wrong answer for a solar home even on a grid where nights look green.

    The result is never above the original curve and never below zero.
    """
    try:
        share = float(solar_share)
    except (TypeError, ValueError):
        share = 0.0
    share = max(0.0, min(1.0, share))

    base = clean_intensity_curve(curve)
    return [
        round(max(0.0, base[hour] * (1.0 - share * SOLAR_SHAPE[hour])), 2)
        for hour in range(HOURS_IN_DAY)
    ]


def _normalise_hour(hour: int) -> int:
    """Wrap any integer into a valid hour of the day."""
    try:
        return int(hour) % HOURS_IN_DAY
    except (TypeError, ValueError):
        return 0


def _clean_duration(duration_hours: float | int) -> int:
    """Clamp a run length to between one hour and a full day."""
    try:
        duration = int(round(float(duration_hours)))
    except (TypeError, ValueError):
        duration = 1
    return max(1, min(HOURS_IN_DAY, duration))


def window_hours(start_hour: int, duration_hours: float | int) -> list[int]:
    """Return the hours a run occupies, wrapping across midnight."""
    start = _normalise_hour(start_hour)
    duration = _clean_duration(duration_hours)
    return [(start + offset) % HOURS_IN_DAY for offset in range(duration)]


def window_average(curve: list[float], start_hour: int, duration_hours: float | int) -> float:
    """Mean intensity (or price) across a run window."""
    values = clean_intensity_curve(curve)
    hours = window_hours(start_hour, duration_hours)
    return sum(values[hour] for hour in hours) / len(hours)


def allowed_start_hours(earliest_hour: int, latest_hour: int, duration_hours: float | int) -> list[int]:
    """Return the start hours where a run fits inside the user's window.

    ``earliest_hour`` and ``latest_hour`` bound when the appliance may run;
    the run has to *finish* by ``latest_hour``. Setting both to the same value
    means no constraint at all. Overnight windows such as 22:00 to 06:00 wrap
    correctly.

    If the allowed span is shorter than the run itself the constraint cannot
    be honoured, and rather than returning nothing we fall back to the single
    earliest hour so the caller always gets a workable answer.
    """
    duration = _clean_duration(duration_hours)
    earliest = _normalise_hour(earliest_hour)
    latest = _normalise_hour(latest_hour)

    if earliest == latest:
        return list(range(HOURS_IN_DAY))

    span = (latest - earliest) % HOURS_IN_DAY
    if span < duration:
        return [earliest]

    return [(earliest + offset) % HOURS_IN_DAY for offset in range(span - duration + 1)]


def find_best_window(curve: list[float], duration_hours: float | int, candidate_hours: list[int] | None = None) -> dict[str, Any]:
    """Lowest-average-intensity contiguous window of a given length."""
    return _search_window(curve, duration_hours, candidate_hours, best=True)


def find_worst_window(curve: list[float], duration_hours: float | int, candidate_hours: list[int] | None = None) -> dict[str, Any]:
    """Highest-average-intensity window - used to size avoidable emissions."""
    return _search_window(curve, duration_hours, candidate_hours, best=False)


def _search_window(curve: list[float], duration_hours: float | int, candidate_hours: list[int] | None, best: bool) -> dict[str, Any]:
    """Shared window search. Ties resolve to the earliest start hour."""
    values = clean_intensity_curve(curve)
    duration = _clean_duration(duration_hours)
    candidates = list(candidate_hours) if candidate_hours else list(range(HOURS_IN_DAY))
    if not candidates:
        candidates = list(range(HOURS_IN_DAY))

    chosen_start = None
    chosen_average = None
    for start in candidates:
        average = window_average(values, start, duration)
        if chosen_average is None:
            chosen_start, chosen_average = _normalise_hour(start), average
            continue
        if (best and average < chosen_average) or (not best and average > chosen_average):
            chosen_start, chosen_average = _normalise_hour(start), average

    hours = window_hours(chosen_start, duration)
    return {
        "start_hour": chosen_start,
        "end_hour": (chosen_start + duration) % HOURS_IN_DAY,
        "duration_hours": duration,
        "hours": hours,
        "average_intensity": round(chosen_average, 2),
        "label": f"{HOUR_LABELS[chosen_start]}-{HOUR_LABELS[(chosen_start + duration) % HOURS_IN_DAY]}",
    }


def peak_and_trough(curve: list[float]) -> dict[str, Any]:
    """The greenest and dirtiest single hours, for a plain-language summary."""
    values = clean_intensity_curve(curve)
    lowest = min(values)
    highest = max(values)
    average = sum(values) / len(values)
    return {
        "greenest_hour": values.index(lowest),
        "greenest_intensity": round(lowest, 2),
        "dirtiest_hour": values.index(highest),
        "dirtiest_intensity": round(highest, 2),
        "average_intensity": round(average, 2),
        "spread_pct": round(((highest - lowest) / highest * 100) if highest else 0.0, 1),
    }


def shift_potential(curve: list[float]) -> float:
    """Score 0-100 for how much a grid rewards moving load around.

    A flat grid - nuclear or hydro baseload - scores near zero, and the honest
    answer for those users is that timing barely matters. A solar grid with a
    deep midday trough and a steep evening ramp scores near the top, because
    the same appliance run can differ by a factor of three.

    The score is the intensity range as a share of the daily peak, rescaled so
    a realistic solar duck curve reaches the ceiling.
    """
    values = clean_intensity_curve(curve)
    highest = max(values)
    if highest <= 0:
        return 0.0
    normalised_range = (highest - min(values)) / highest
    return round(min(100.0, normalised_range * 125.0), 1)


def schedule_load(
    load_name: str,
    curve: list[float],
    tariff: list[float] | None = None,
    earliest_hour: int = 0,
    latest_hour: int = 0,
    kwh: float | None = None,
    duration_hours: float | int | None = None,
) -> dict[str, Any]:
    """Place one appliance at its best hour inside the user's allowed window.

    Returns the recommended start, what the run emits and costs there, and the
    same figures at the worst and average timing so the saving is visible as a
    comparison rather than an unanchored number.
    """
    details = SHIFTABLE_LOADS.get(load_name, {})
    energy = details.get("kwh", 1.0) if kwh is None else kwh
    try:
        energy = max(0.0, float(energy))
    except (TypeError, ValueError):
        energy = 0.0

    duration = _clean_duration(
        details.get("duration_hours", 1) if duration_hours is None else duration_hours
    )

    intensity = clean_intensity_curve(curve)
    prices = clean_tariff(tariff if tariff is not None else TARIFFS[DEFAULT_TARIFF])
    candidates = allowed_start_hours(earliest_hour, latest_hour, duration)

    best = find_best_window(intensity, duration, candidates)
    worst = find_worst_window(intensity, duration, candidates)
    average_intensity = sum(intensity) / len(intensity)

    def _emissions(mean_intensity: float) -> float:
        return round(energy * mean_intensity / 1000.0, 4)

    def _cost(start: int) -> float:
        per_hour = energy / duration
        return round(
            sum(prices[hour] * per_hour for hour in window_hours(start, duration)), 4
        )

    best_co2 = _emissions(best["average_intensity"])
    worst_co2 = _emissions(worst["average_intensity"])
    average_co2 = _emissions(average_intensity)

    cheapest = _search_window(prices, duration, candidates, best=True)

    return {
        "load": load_name,
        "kwh": round(energy, 3),
        "duration_hours": duration,
        "shiftable": bool(details.get("shiftable", True)),
        "start_hour": best["start_hour"],
        "window_label": best["label"],
        "hours": best["hours"],
        "best_intensity": best["average_intensity"],
        "worst_intensity": worst["average_intensity"],
        "average_intensity": round(average_intensity, 2),
        "co2_kg": best_co2,
        "worst_co2_kg": worst_co2,
        "average_co2_kg": average_co2,
        "saving_vs_worst_kg": round(max(0.0, worst_co2 - best_co2), 4),
        "saving_vs_average_kg": round(max(0.0, average_co2 - best_co2), 4),
        "cost": _cost(best["start_hour"]),
        "cheapest_start_hour": cheapest["start_hour"],
        "cheapest_cost": _cost(cheapest["start_hour"]),
        "cost_conflict": cheapest["start_hour"] != best["start_hour"],
        "constrained": len(candidates) < HOURS_IN_DAY,
    }


def build_schedule(load_names: list[str] | None, curve: list[float], tariff: list[float] | None = None, constraints: dict[str, Any] | None = None, days_per_year: int | None = None) -> dict[str, Any]:
    """Plan every selected appliance across one day and total up the savings."""
    intensity = clean_intensity_curve(curve)
    prices = clean_tariff(tariff if tariff is not None else TARIFFS[DEFAULT_TARIFF])
    constraints = constraints or {}

    scheduled = []
    for name in load_names or []:
        window = constraints.get(name, {})
        scheduled.append(
            schedule_load(
                name,
                intensity,
                prices,
                earliest_hour=window.get("earliest_hour", 0),
                latest_hour=window.get("latest_hour", 0),
                kwh=window.get("kwh"),
                duration_hours=window.get("duration_hours"),
            )
        )

    scheduled.sort(key=lambda item: item["saving_vs_average_kg"], reverse=True)

    total_kwh = round(sum(item["kwh"] for item in scheduled), 3)
    total_co2 = round(sum(item["co2_kg"] for item in scheduled), 4)
    total_worst = round(sum(item["worst_co2_kg"] for item in scheduled), 4)
    total_average = round(sum(item["average_co2_kg"] for item in scheduled), 4)

    return {
        "loads": scheduled,
        "total_kwh": total_kwh,
        "total_co2_kg": total_co2,
        "worst_co2_kg": total_worst,
        "average_co2_kg": total_average,
        "daily_saving_vs_average_kg": round(max(0.0, total_average - total_co2), 4),
        "daily_saving_vs_worst_kg": round(max(0.0, total_worst - total_co2), 4),
        "total_cost": round(sum(item["cost"] for item in scheduled), 4),
        "shift_potential": shift_potential(intensity),
        "peak_and_trough": peak_and_trough(intensity),
        "days_per_year": int(days_per_year or DEFAULT_DAYS_PER_YEAR),
    }


def annual_savings(schedule: dict[str, Any], days_per_year: int | None = None) -> dict[str, Any]:
    """Scale a daily plan up to a year of CO2 and money saved by timing alone."""
    # Checked against None rather than truthiness so an explicit zero days -
    # "I never run these" - is honoured instead of silently falling back.
    days = days_per_year
    if days is None:
        days = schedule.get("days_per_year", DEFAULT_DAYS_PER_YEAR)
    try:
        days = max(0, int(days))
    except (TypeError, ValueError):
        days = DEFAULT_DAYS_PER_YEAR

    daily_co2 = schedule.get("daily_saving_vs_average_kg", 0.0)
    daily_worst = schedule.get("daily_saving_vs_worst_kg", 0.0)

    # Where the greenest hour is not also the cheapest one, choosing carbon
    # costs the user money. That gap is reported honestly rather than hidden.
    daily_penalty = 0.0
    for item in schedule.get("loads", []):
        daily_penalty += max(0.0, item.get("cost", 0.0) - item.get("cheapest_cost", 0.0))

    return {
        "days_per_year": days,
        "co2_saved_kg": round(daily_co2 * days, 2),
        "co2_saved_vs_worst_kg": round(daily_worst * days, 2),
        "annual_co2_kg": round(schedule.get("total_co2_kg", 0.0) * days, 2),
        "annual_cost": round(schedule.get("total_cost", 0.0) * days, 2),
        "cost_penalty": round(daily_penalty * days, 2),
    }


def get_scheduling_tips(schedule: dict[str, Any], curve: list[float] | None = None, limit: int = 6) -> list[str]:
    """Advice ranked by the user's own plan rather than a generic checklist."""
    tips = []
    intensity = clean_intensity_curve(curve if curve is not None else GRID_PROFILES[DEFAULT_GRID_PROFILE])
    marks = schedule.get("peak_and_trough") or peak_and_trough(intensity)
    potential = schedule.get("shift_potential", shift_potential(intensity))

    if potential < SHIFT_WORTH_IT_SCORE:
        tips.append(
            "Your grid is close to flat across the day, so shifting loads saves "
            "very little. Spend the effort on using less rather than moving it."
        )
        return tips[: max(0, int(limit))]

    tips.append(
        f"Your greenest hour is {HOUR_LABELS[marks['greenest_hour']]} at "
        f"{marks['greenest_intensity']:.0f} gCO2/kWh and your dirtiest is "
        f"{HOUR_LABELS[marks['dirtiest_hour']]} at {marks['dirtiest_intensity']:.0f}. "
        f"That is a {marks['spread_pct']:.0f}% spread for the same kilowatt-hour."
    )

    loads = schedule.get("loads", [])
    biggest = next((item for item in loads if item.get("shiftable")), None)
    if biggest and biggest["saving_vs_average_kg"] > 0:
        tips.append(
            f"Start with the {biggest['load'].lower()}: moving it to "
            f"{biggest['window_label']} saves {biggest['saving_vs_average_kg']:.2f} kg "
            "CO2 every run, and it is the largest single win in your plan."
        )

    evening = [item for item in loads if 17 <= item["start_hour"] <= 20]
    if evening:
        tips.append(
            "Some runs still land in the evening ramp, the dirtiest stretch of "
            "the day on most grids. A delay-start timer moves them for free."
        )

    conflicted = [item for item in loads if item.get("cost_conflict")]
    if conflicted:
        tips.append(
            "On this tariff the greenest hour is not the cheapest one for "
            f"{len(conflicted)} of your loads. The plan optimises carbon - check "
            "the cost column before committing if the bill matters more."
        )

    constrained = [item for item in loads if item.get("constrained")]
    if constrained:
        tips.append(
            "A few loads are boxed into narrow allowed windows. Widening them "
            "even by two hours usually finds a noticeably cleaner slot."
        )

    tips.append(
        "Batch the same appliance rather than spreading runs across the day - "
        "two laundry loads in the trough beat one in the trough and one at peak."
    )

    return tips[: max(0, int(limit))]


def _get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_grid_scheduler_db() -> bool:
    """Create the schedule table if it does not exist yet."""
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS grid_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                schedule_name TEXT NOT NULL,
                grid_profile TEXT NOT NULL,
                tariff_name TEXT NOT NULL,
                total_kwh REAL NOT NULL,
                total_co2_kg REAL NOT NULL,
                daily_saving_kg REAL NOT NULL,
                annual_saving_kg REAL,
                shift_potential REAL,
                schedule_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Grid scheduler init error: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def save_schedule(user_id: int, schedule_name: str, schedule: dict[str, Any], grid_profile: str | None = None, tariff_name: str | None = None) -> int | None:
    """Persist a daily schedule. Returns the new row id or None."""
    init_grid_scheduler_db()
    conn = None
    try:
        conn = _get_conn()
        annual = annual_savings(schedule)
        cursor = conn.execute(
            """
            INSERT INTO grid_schedules (
                user_id, schedule_name, grid_profile, tariff_name, total_kwh,
                total_co2_kg, daily_saving_kg, annual_saving_kg, shift_potential,
                schedule_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                (schedule_name or "My day").strip() or "My day",
                grid_profile or DEFAULT_GRID_PROFILE,
                tariff_name or DEFAULT_TARIFF,
                schedule.get("total_kwh", 0.0),
                schedule.get("total_co2_kg", 0.0),
                schedule.get("daily_saving_vs_average_kg", 0.0),
                annual.get("co2_saved_kg", 0.0),
                schedule.get("shift_potential", 0.0),
                json.dumps(
                    {
                        "loads": schedule.get("loads", []),
                        "peak_and_trough": schedule.get("peak_and_trough", {}),
                    }
                ),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as exc:
        logger.error("Unable to save grid schedule: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def get_schedules(user_id: int, limit: int = 25) -> list[dict[str, Any]]:
    """Return a user's saved schedules, newest first."""
    init_grid_scheduler_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, schedule_name, grid_profile, tariff_name, total_kwh,
                   total_co2_kg, daily_saving_kg, annual_saving_kg,
                   shift_potential, schedule_json, created_at
            FROM grid_schedules
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT ?
            """,
            (user_id, int(limit)),
        ).fetchall()

        schedules = []
        for row in rows:
            record = dict(row)
            try:
                record["detail"] = json.loads(record.pop("schedule_json"))
            except (TypeError, ValueError):
                record["detail"] = {}
            schedules.append(record)
        return schedules
    except sqlite3.Error as exc:
        logger.error("Unable to load grid schedules: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def delete_schedule(schedule_id: int) -> bool:
    """Delete a saved schedule."""
    init_grid_scheduler_db()
    conn = None
    try:
        conn = _get_conn()
        cursor = conn.execute("DELETE FROM grid_schedules WHERE id = ?", (schedule_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as exc:
        logger.error("Unable to delete grid schedule: %s", exc)
        return False
    finally:
        if conn:
            conn.close()
