import os
import requests
import streamlit as st

VALID_TRANSPORT = {"Car", "Bike", "Public Transport", "Walking"}
VALID_DIET = {"Vegetarian", "Non-Vegetarian"}
VALID_REGIONS = {"Global", "US", "UK", "EU"}
MAX_DISTANCE = 500
MAX_ELECTRICITY = 10000
MAX_FLIGHTS = 365


@st.cache_data(ttl=86400)
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
    transport_factors = {
        "Car": 0.21,
        "Bike": 0.0,
        "Public Transport": 0.08,
        "Walking": 0.0
    }

    transport_emission = (
        transport_factors[transport] *
        distance *        # km per day
        365               # yearly estimate
    )

    contributors["Transport"] = round(transport_emission, 2)

    # Fetch dynamic factors (with fallback and caching)
    dynamic_factors = fetch_emission_factors(region)

    # Electricity
    electricity_emission = electricity * dynamic_factors["electricity"] * 12
    contributors["Electricity"] = round(electricity_emission, 2)

    # Diet (annual estimate)
    diet_factors = {
        "Vegetarian": 1000,
        "Non-Vegetarian": 1800
    }

    diet_emission = diet_factors[diet]
    contributors["Diet"] = diet_emission

    # Flights
    flight_emission = flights * dynamic_factors["flight"]
    contributors["Flights"] = flight_emission

    total = sum(contributors.values())

    return round(total, 2), contributors

def calculate_eco_score(total_footprint):
    """
    Higher score = better sustainability
    """
    if total_footprint <= 2000:
        return 95
    elif total_footprint <= 3000:
        return 80
    elif total_footprint <= 4000:
        return 65
    elif total_footprint <= 5000:
        return 50
    else:
        return 35