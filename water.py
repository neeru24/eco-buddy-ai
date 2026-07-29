# water.py
import streamlit as st
from config import GLOBAL_WATER_AVERAGE_LITERS, WATER_FACTORS, DIET_VIRTUAL_WATER, normalize_diet
from cache import cached
from cache_config import TTL_COMPUTED_ANALYTICS, CACHE_CATEGORY_COMPUTED

def validate_water_inputs(shower_mins, laundry_loads, dishwasher_runs, garden_mins):
    warnings = []
    if shower_mins > 120:
        warnings.append("Shower duration exceeds 2 hours — please verify your input.")
    if laundry_loads > 30:
        warnings.append("Laundry loads exceed 30 per week — please verify your input.")
    if dishwasher_runs > 30:
        warnings.append("Dishwasher runs exceed 30 per week — please verify your input.")
    if garden_mins > 300:
        warnings.append("Garden watering exceeds 5 hours per week — please verify your input.")
    return warnings


@cached(category=CACHE_CATEGORY_COMPUTED, ttl=TTL_COMPUTED_ANALYTICS)
def calculate_water_footprint(shower_mins_per_day, laundry_loads_per_week, dishwasher_runs_per_week, garden_mins_per_week, diet):
    """
    Calculates the estimated daily water footprint in liters.
    """
    shower_mins_per_day = max(0.0, float(shower_mins_per_day))
    laundry_loads_per_week = max(0, int(laundry_loads_per_week))
    dishwasher_runs_per_week = max(0, int(dishwasher_runs_per_week))
    garden_mins_per_week = max(0.0, float(garden_mins_per_week))

    daily_shower = shower_mins_per_day * WATER_FACTORS["shower_liter_per_min"]
    daily_laundry = (laundry_loads_per_week * WATER_FACTORS["laundry_liter_per_load"]) / 7.0
    daily_dishwasher = (dishwasher_runs_per_week * WATER_FACTORS["dishwasher_liter_per_run"]) / 7.0
    daily_garden = (garden_mins_per_week * WATER_FACTORS["garden_liter_per_min"]) / 7.0
    
    diet = normalize_diet(diet)
    daily_diet = DIET_VIRTUAL_WATER.get(diet, DIET_VIRTUAL_WATER["Omnivore"])
    
    total_daily = daily_shower + daily_laundry + daily_dishwasher + daily_garden + daily_diet
    
    contributors = {
        "Shower": daily_shower,
        "Laundry": daily_laundry,
        "Dishwasher": daily_dishwasher,
        "Garden": daily_garden,
        "Diet": daily_diet
    }
    
    return total_daily, contributors
