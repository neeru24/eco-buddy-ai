import os
import requests
import streamlit as st
import math
from config import (
    ECO_SCORE_BASELINE, ECO_SCORE_SENSITIVITY, CATEGORY_WEIGHTS,
    VALID_TRANSPORT, VALID_DIET, VALID_REGIONS,
    MAX_DISTANCE, MAX_ELECTRICITY, MAX_FLIGHTS,
    TRANSPORT_EMISSION_FACTORS, DIET_EMISSION_FACTORS,
    normalize_diet,
)
from cache import cached
from cache_config import TTL_EXTERNAL_API, CACHE_CATEGORY_API


@cached(ttl=TTL_EXTERNAL_API, category=CACHE_CATEGORY_API)
def fetch_emission_factors(region: str) -> dict:
    """
    Fetches dynamic emission factors from a third-party Carbon API.
    Provides graceful fallback to static factors if the API fails.
    """
    # Static fallbacks
    factors = {
        "electricity": 0.82, # kg CO2 per kWh
        "flight": 250.0      # kg CO2 per flight
    }
    
    api_key = os.environ.get("CARBON_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        return factors
        
    try:
        url = "https://api.climatiq.io/data/v1/estimate"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        payload = {
            "emission_factor": {
                "activity_id": "electricity-energy_source_grid_mix",
                "region": region if region != "Global" else "earth"
            },
            "parameters": {"energy": 1, "energy_unit": "kWh"}
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            factors["electricity"] = data.get("co2e", factors["electricity"])
            
        flight_payload = {
            "emission_factor": {
                "activity_id": "passenger_flight-route_type_domestic",
                "region": region if region != "Global" else "earth"
            },
            "parameters": {"passengers": 1}
        }
        f_response = requests.post(url, json=flight_payload, headers=headers, timeout=5)
        if f_response.status_code == 200:
            f_data = f_response.json()
            factors["flight"] = f_data.get("co2e", factors["flight"])
            
    except Exception as e:
        print(f"API Error, falling back to static factors: {e}")
        
    return factors


def calculate_footprint(
    transport,
    distance,
    electricity,
    diet,
    flights,
    region="Global"
):
    diet = normalize_diet(diet)
    if transport not in VALID_TRANSPORT:
        raise ValueError(
            f"Invalid transport '{transport}'. Must be one of: {', '.join(sorted(VALID_TRANSPORT))}"
        )
    if diet not in VALID_DIET:
        raise ValueError(
            f"Invalid diet '{diet}'. Must be one of: {', '.join(sorted(VALID_DIET))}"
        )
    if region not in VALID_REGIONS:
        region = "Global"

    distance = max(0.0, min(float(distance), MAX_DISTANCE))
    electricity = max(0.0, min(float(electricity), MAX_ELECTRICITY))
    flights = max(0, min(int(flights), MAX_FLIGHTS))

    contributors = {}

    # Transport emissions (kg CO₂ per km)
    transport_emission = (
        TRANSPORT_EMISSION_FACTORS[transport] *
        distance * 365
    )

    contributors["Transport"] = round(transport_emission, 2)

    # Fetch dynamic factors (with fallback and caching)
    dynamic_factors = fetch_emission_factors(region)

    # Electricity
    electricity_emission = electricity * dynamic_factors["electricity"] * 12
    contributors["Electricity"] = round(electricity_emission, 2)

    # Diet (annual estimate)
    diet_emission = DIET_EMISSION_FACTORS[diet]
    contributors["Diet"] = diet_emission

    # Flights
    flight_emission = flights * dynamic_factors["flight"]
    contributors["Flights"] = flight_emission

    total = sum(contributors.values())

    return round(total, 2), contributors

def calculate_eco_score(total_footprint, contributors=None):
    """
    Higher score = better sustainability
    Calculates a continuous score based on a sigmoid function.
    Supports per-category weighting if contributors are provided.
    """
    if contributors:
        weighted_score = 0.0
        for category, cat_total in contributors.items():
            weight = CATEGORY_WEIGHTS.get(category, 0.0)
            if weight > 0:
                cat_baseline = ECO_SCORE_BASELINE * weight
                cat_sensitivity = ECO_SCORE_SENSITIVITY * weight
                cat_score = 100 / (1 + math.exp((cat_total - cat_baseline) / cat_sensitivity))
                weighted_score += weight * cat_score
        return int(round(weighted_score))
    else:
        # Fallback to overall continuous score
        score = 100 / (1 + math.exp((total_footprint - ECO_SCORE_BASELINE) / ECO_SCORE_SENSITIVITY))
        return int(round(score))