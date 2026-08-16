"""Water footprint calculation and estimation module for EcoBuddy AI."""

from __future__ import annotations

from typing import Any
import streamlit as st
from config import GLOBAL_WATER_AVERAGE_LITERS, WATER_FACTORS, DIET_VIRTUAL_WATER, normalize_diet
from cache import cached
from cache_config import TTL_COMPUTED_ANALYTICS, CACHE_CATEGORY_COMPUTED

LITERS_PER_GALLON = 3.785411784

EXTENDED_WATER_FACTORS = {
    "bath_liter_per_bath": 120.0,
    "teeth_hands_running_liter_per_min": 8.0,
    "teeth_hands_conserved_liter_per_min": 2.0,
    "toilet_flush_standard_liter": 9.0,
    "toilet_flush_lowflow_liter": 4.5,
    "shower_lowflow_liter_per_min": 6.0,
    "laundry_lowflow_liter_per_load": 35.0,
    "cooking_drinking_liter_per_day": 10.0,
    "garden_lowflow_liter_per_min": 8.0,
    "car_wash_hose_liter": 150.0,
    "car_wash_bucket_liter": 30.0,
    "cleaning_liter_per_day": 5.0,
}


def liters_to_gallons(liters: float) -> float:
    """Convert volume in liters to US gallons."""
    return float(liters) / LITERS_PER_GALLON


def gallons_to_liters(gallons: float) -> float:
    """Convert volume in US gallons to liters."""
    return float(gallons) * LITERS_PER_GALLON


def validate_water_inputs(
    shower_mins: float = 10.0,
    laundry_loads: int = 2,
    dishwasher_runs: int = 3,
    garden_mins: float = 0.0,
    baths_per_week: int = 0,
    teeth_mins: float = 2.0,
    toilet_flushes: int = 5,
    car_washes_month: int = 0,
) -> list[str]:
    """Validate daily and weekly water activity inputs, returning warning messages for extremes."""
    warnings: list[str] = []
    if shower_mins > 120:
        warnings.append("Shower duration exceeds 2 hours — please verify your input.")
    if laundry_loads > 30:
        warnings.append("Laundry loads exceed 30 per week — please verify your input.")
    if dishwasher_runs > 30:
        warnings.append("Dishwasher runs exceed 30 per week — please verify your input.")
    if garden_mins > 300:
        warnings.append("Garden watering exceeds 5 hours per week — please verify your input.")
    if baths_per_week > 21:
        warnings.append("Baths exceed 3 per day (21/week) — please verify your input.")
    if teeth_mins > 30:
        warnings.append("Sink/brushing duration exceeds 30 minutes/day — please verify your input.")
    if toilet_flushes > 30:
        warnings.append("Toilet flushes exceed 30 per day — please verify your input.")
    if car_washes_month > 30:
        warnings.append("Car washes exceed 30 per month — please verify your input.")
    return warnings


@cached(category=CACHE_CATEGORY_COMPUTED, ttl=TTL_COMPUTED_ANALYTICS)
def calculate_water_footprint(
    shower_mins_per_day: float = 10.0,
    laundry_loads_per_week: int = 2,
    dishwasher_runs_per_week: int = 3,
    garden_mins_per_week: float = 0.0,
    diet: str = "Omnivore",
    *,
    baths_per_week: int = 0,
    teeth_handwash_mins_per_day: float = 0.0,
    tap_running_while_brushing: bool = False,
    toilet_flushes_per_day: int = 0,
    low_flow_fixtures: bool = False,
    cooking_drinking_liters_per_day: float = 0.0,
    car_washes_per_month: int = 0,
    cleaning_liters_per_day: float = 0.0,
) -> tuple[float, dict[str, float]]:
    """Calculates the estimated daily water footprint in liters.

    Provides backwards compatibility for standard 5 parameters while supporting
    granular common daily activity inputs.
    """
    shower_mins_per_day = max(0.0, float(shower_mins_per_day))
    laundry_loads_per_week = max(0, int(laundry_loads_per_week))
    dishwasher_runs_per_week = max(0, int(dishwasher_runs_per_week))
    garden_mins_per_week = max(0.0, float(garden_mins_per_week))
    baths_per_week = max(0, int(baths_per_week))
    teeth_handwash_mins_per_day = max(0.0, float(teeth_handwash_mins_per_day))
    toilet_flushes_per_day = max(0, int(toilet_flushes_per_day))
    cooking_drinking_liters_per_day = max(0.0, float(cooking_drinking_liters_per_day))
    car_washes_per_month = max(0, int(car_washes_per_month))
    cleaning_liters_per_day = max(0.0, float(cleaning_liters_per_day))

    shower_rate = (
        EXTENDED_WATER_FACTORS["shower_lowflow_liter_per_min"]
        if low_flow_fixtures
        else WATER_FACTORS["shower_liter_per_min"]
    )
    daily_shower = shower_mins_per_day * shower_rate

    laundry_rate = (
        EXTENDED_WATER_FACTORS["laundry_lowflow_liter_per_load"]
        if low_flow_fixtures
        else WATER_FACTORS["laundry_liter_per_load"]
    )
    daily_laundry = (laundry_loads_per_week * laundry_rate) / 7.0

    daily_dishwasher = (
        dishwasher_runs_per_week * WATER_FACTORS["dishwasher_liter_per_run"]
    ) / 7.0

    garden_rate = (
        EXTENDED_WATER_FACTORS["garden_lowflow_liter_per_min"]
        if low_flow_fixtures
        else WATER_FACTORS["garden_liter_per_min"]
    )
    daily_garden = (garden_mins_per_week * garden_rate) / 7.0

    diet_norm = normalize_diet(diet)
    daily_diet = DIET_VIRTUAL_WATER.get(diet_norm, DIET_VIRTUAL_WATER.get("Omnivore", 4000.0))

    daily_baths = (baths_per_week * EXTENDED_WATER_FACTORS["bath_liter_per_bath"]) / 7.0

    sink_rate = (
        EXTENDED_WATER_FACTORS["teeth_hands_running_liter_per_min"]
        if tap_running_while_brushing
        else EXTENDED_WATER_FACTORS["teeth_hands_conserved_liter_per_min"]
    )
    daily_sink = teeth_handwash_mins_per_day * sink_rate

    toilet_rate = (
        EXTENDED_WATER_FACTORS["toilet_flush_lowflow_liter"]
        if low_flow_fixtures
        else EXTENDED_WATER_FACTORS["toilet_flush_standard_liter"]
    )
    daily_toilet = toilet_flushes_per_day * toilet_rate

    daily_cooking = cooking_drinking_liters_per_day

    car_wash_rate = (
        EXTENDED_WATER_FACTORS["car_wash_bucket_liter"]
        if low_flow_fixtures
        else EXTENDED_WATER_FACTORS["car_wash_hose_liter"]
    )
    daily_car_wash = (car_washes_per_month * car_wash_rate) / 30.0

    daily_cleaning = cleaning_liters_per_day

    total_daily = (
        daily_shower
        + daily_laundry
        + daily_dishwasher
        + daily_garden
        + daily_diet
        + daily_baths
        + daily_sink
        + daily_toilet
        + daily_cooking
        + daily_car_wash
        + daily_cleaning
    )

    contributors: dict[str, float] = {
        "Shower": daily_shower,
        "Laundry": daily_laundry,
        "Dishwasher": daily_dishwasher,
        "Garden": daily_garden,
        "Diet": daily_diet,
    }

    if daily_baths > 0:
        contributors["Baths"] = daily_baths
    if daily_sink > 0:
        contributors["Sink & Hygiene"] = daily_sink
    if daily_toilet > 0:
        contributors["Toilet Flushes"] = daily_toilet
    if daily_cooking > 0:
        contributors["Cooking & Drinking"] = daily_cooking
    if daily_car_wash > 0:
        contributors["Car Wash"] = daily_car_wash
    if daily_cleaning > 0:
        contributors["House Cleaning"] = daily_cleaning

    return total_daily, contributors


def get_activity_categories(contributors: dict[str, float]) -> dict[str, float]:
    """Group granular activities into top-level functional categories."""
    categories: dict[str, float] = {
        "Personal Hygiene": 0.0,
        "Kitchen & Laundry": 0.0,
        "Outdoor & Cleaning": 0.0,
        "Dietary Virtual Water": 0.0,
    }

    for name, liters in contributors.items():
        if name in {"Shower", "Baths", "Sink & Hygiene", "Toilet Flushes"}:
            categories["Personal Hygiene"] += liters
        elif name in {"Laundry", "Dishwasher", "Cooking & Drinking"}:
            categories["Kitchen & Laundry"] += liters
        elif name in {"Garden", "Car Wash", "House Cleaning"}:
            categories["Outdoor & Cleaning"] += liters
        elif name in {"Diet", "Dietary Virtual Water"}:
            categories["Dietary Virtual Water"] += liters
        else:
            categories["Kitchen & Laundry"] += liters

    return {k: v for k, v in categories.items() if v > 0}


def calculate_water_efficiency_score(total_daily_liters: float) -> dict[str, Any]:
    """Calculate water efficiency grade, score (0-100), and benchmark comparison."""
    baseline = GLOBAL_WATER_AVERAGE_LITERS
    ratio = total_daily_liters / baseline if baseline > 0 else 1.0

    if ratio <= 0.6:
        grade = "A+"
        score = 95
        status = "Water Conservation Champion"
        color = "#22c55e"
    elif ratio <= 0.85:
        grade = "A"
        score = 85
        status = "Highly Water-Efficient"
        color = "#4ade80"
    elif ratio <= 1.05:
        grade = "B"
        score = 72
        status = "Moderate Consumption (Near Global Average)"
        color = "#38bdf8"
    elif ratio <= 1.3:
        grade = "C"
        score = 58
        status = "Above Average Usage"
        color = "#facc15"
    elif ratio <= 1.6:
        grade = "D"
        score = 42
        status = "High Water Footprint"
        color = "#fb923c"
    else:
        grade = "F"
        score = 25
        status = "Critical Water Consumption"
        color = "#ef4444"

    diff_pct = ((total_daily_liters - baseline) / baseline) * 100.0

    return {
        "grade": grade,
        "score": score,
        "status": status,
        "color": color,
        "daily_liters": total_daily_liters,
        "baseline_liters": baseline,
        "diff_pct": diff_pct,
        "comparison_text": (
            f"{abs(diff_pct):.1f}% below global average"
            if diff_pct < 0
            else f"{diff_pct:.1f}% above global average"
        ),
    }


def calculate_potential_water_savings(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    """Compute quantifiable water savings for actionable habit and fixture changes."""
    savings: list[dict[str, Any]] = []

    shower_mins = float(inputs.get("shower_mins", 10.0))
    low_flow = bool(inputs.get("low_flow_fixtures", False))
    tap_running = bool(inputs.get("tap_running_while_brushing", False))
    laundry_loads = int(inputs.get("laundry_loads", 2))
    diet = normalize_diet(str(inputs.get("diet", "Omnivore")))
    baths_per_week = int(inputs.get("baths_per_week", 0))

    if shower_mins > 5:
        shortened_savings = (shower_mins - 5) * (6.0 if low_flow else 10.0)
        savings.append({
            "action": "Shorten Daily Showers to 5 Minutes",
            "daily_liters_saved": shortened_savings,
            "annual_liters_saved": shortened_savings * 365.0,
            "category": "Hygiene",
            "tip": "Cut shower time with a 5-minute playlist or timer.",
        })

    if not low_flow:
        fixture_savings = (shower_mins * 4.0) + ((laundry_loads * 15.0) / 7.0)
        savings.append({
            "action": "Install Low-Flow Aerators & Eco-Showerheads",
            "daily_liters_saved": fixture_savings,
            "annual_liters_saved": fixture_savings * 365.0,
            "category": "Fixtures",
            "tip": "High-efficiency aerators cut water throughput by 30-40% without reducing pressure.",
        })

    if tap_running:
        sink_savings = 6.0 * 2.0  # ~12 L/day saved by shutting tap
        savings.append({
            "action": "Turn Off Tap While Brushing Teeth & Soaping",
            "daily_liters_saved": sink_savings,
            "annual_liters_saved": sink_savings * 365.0,
            "category": "Habits",
            "tip": "A running tap wastes up to 8 liters per minute.",
        })

    if baths_per_week > 0:
        bath_swap_savings = (baths_per_week * (120.0 - (5.0 * 10.0))) / 7.0
        if bath_swap_savings > 0:
            savings.append({
                "action": "Swap Baths for 5-Minute Showers",
                "daily_liters_saved": bath_swap_savings,
                "annual_liters_saved": bath_swap_savings * 365.0,
                "category": "Hygiene",
                "tip": "A full bath uses ~120L compared to only ~50L for a standard 5-minute shower.",
            })

    if diet in {"Omnivore", "Heavy Meat"}:
        diet_delta = 1500.0 if diet == "Heavy Meat" else 1500.0  # Omnivore (4000) -> Veg (2500)
        savings.append({
            "action": "Adopt 2 Plant-Based Days per Week",
            "daily_liters_saved": (diet_delta * 2) / 7.0,
            "annual_liters_saved": ((diet_delta * 2) / 7.0) * 365.0,
            "category": "Diet",
            "tip": "Producing 1kg of beef requires ~15,000L of virtual water; plant protein requires ~80% less.",
        })

    return savings
