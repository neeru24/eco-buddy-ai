from datetime import date, datetime
from typing import Any

GLOBAL_BIOCAPACITY_PER_PERSON = 1.6
GLOBAL_CO2_PER_PERSON_YEAR = 4.8

OVERSHOOT_HISTORY = {
    2026: date(2026, 7, 28),
    2025: date(2025, 7, 29),
    2024: date(2024, 8, 1),
    2023: date(2023, 8, 2),
    2022: date(2022, 7, 28),
    2021: date(2021, 7, 29),
    2020: date(2020, 8, 22),
    2019: date(2019, 7, 29),
    2018: date(2018, 8, 1),
    2017: date(2017, 8, 2),
    2016: date(2016, 8, 8),
    2015: date(2015, 8, 13),
    2014: date(2014, 8, 19),
    2013: date(2013, 8, 20),
    2012: date(2012, 8, 22),
    2011: date(2011, 8, 27),
    2010: date(2010, 8, 21),
}

DAYS_IN_YEAR = 365.0


def get_current_overshoot_day() -> date:
    today = date.today()
    year = today.year
    if year in OVERSHOOT_HISTORY:
        return OVERSHOOT_HISTORY[year]
    return date(year, 7, 28)


def get_next_overshoot_day() -> date:
    today = date.today()
    overshoot_date = get_current_overshoot_day()
    if today > overshoot_date:
        year = today.year + 1
        if year in OVERSHOOT_HISTORY:
            return OVERSHOOT_HISTORY[year]
        return date(year, 7, 28)
    return overshoot_date


def calculate_personal_overshoot_day(total_annual_footprint_kg: float) -> dict[str, Any] | None:
    if total_annual_footprint_kg <= 0:
        return None
    footprint_tonnes = total_annual_footprint_kg / 1000.0
    earths_needed = footprint_tonnes / GLOBAL_CO2_PER_PERSON_YEAR
    daily_budget_kg = (GLOBAL_CO2_PER_PERSON_YEAR * 1000) / DAYS_IN_YEAR
    user_daily_kg = total_annual_footprint_kg / DAYS_IN_YEAR
    if user_daily_kg <= 0:
        return None
    days_until_overshoot = int(daily_budget_kg / user_daily_kg * DAYS_IN_YEAR)
    days_until_overshoot = max(1, min(days_until_overshoot, DAYS_IN_YEAR * 10))
    jan1 = date(date.today().year, 1, 1)
    personal_date = datetime.fromordinal(jan1.toordinal() + days_until_overshoot - 1).date()
    if personal_date.year > date.today().year:
        personal_date = date(date.today().year, 12, 31)
    today = date.today()
    return {
        "date": personal_date,
        "earths_needed": round(earths_needed, 2),
        "days_until": (personal_date - today).days if personal_date > today else 0,
    }


def calculate_countdown(target_date: date) -> dict[str, Any]:
    today = date.today()
    if target_date <= today:
        return {"days_until": 0, "passed": True}
    return {"days_until": (target_date - today).days, "passed": False}
