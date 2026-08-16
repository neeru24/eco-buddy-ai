"""
Carbon Payback Calculator Engine for EcoBuddy AI.

Calculates the time required for eco-friendly purchases (LED bulbs, solar panels, reusable bottles, EVs, etc.)
to offset their manufacturing/embodied carbon emissions through operational carbon savings over time.
"""

from cache import cached
from cache_config import TTL_COMPUTED_ANALYTICS, CACHE_CATEGORY_COMPUTED

PRESET_ECO_PRODUCTS = {
    "led_bulbs_10pack": {
        "name": "LED Bulbs (Pack of 10)",
        "category": "Lighting",
        "embodied_carbon_kg": 12.0,
        "default_daily_usage": 5.0,  # hours per day
        "usage_unit": "hours/day",
        "savings_per_unit": 0.045,   # kg CO2 saved per hour vs incandescent
        "description": "10 LED bulbs replacing 60W incandescent bulbs operating 5 hrs/day."
    },
    "solar_5kw": {
        "name": "Rooftop Solar System (5 kW)",
        "category": "Renewable Energy",
        "embodied_carbon_kg": 2500.0,
        "default_daily_usage": 4.5,  # peak sun hours per day
        "usage_unit": "peak sun hrs/day",
        "savings_per_unit": 3.69,    # kg CO2 saved per peak sun hour (5 kW * 0.82 kg/kWh)
        "description": "5 kW rooftop solar PV installation offsetting fossil grid electricity."
    },
    "reusable_bottle": {
        "name": "Stainless Steel Reusable Bottle",
        "category": "Waste Reduction",
        "embodied_carbon_kg": 3.5,
        "default_daily_usage": 1.0,  # single-use bottle avoided per day
        "usage_unit": "bottles avoided/day",
        "savings_per_unit": 0.082,   # kg CO2 saved per single-use PET plastic bottle
        "description": "Durable steel bottle replacing single-use plastic water bottles."
    },
    "ev_car": {
        "name": "Electric Vehicle (EV vs Gas Sedan)",
        "category": "Transportation",
        "embodied_carbon_kg": 8500.0, # manufacturing carbon premium (battery + body)
        "default_daily_usage": 35.0, # km driven per day
        "usage_unit": "km driven/day",
        "savings_per_unit": 0.15,    # kg CO2 saved per km driven vs internal combustion car
        "description": "Electric passenger vehicle displacing gasoline car emissions."
    },
    "smart_thermostat": {
        "name": "Smart Programmable Thermostat",
        "category": "Smart Home",
        "embodied_carbon_kg": 8.0,
        "default_daily_usage": 24.0, # hours per day active
        "usage_unit": "hours/day",
        "savings_per_unit": 0.03,    # kg CO2 saved per hour via smart HVAC optimization
        "description": "Intelligent thermostat reducing home HVAC energy by 10-15%."
    },
    "heat_pump_water_heater": {
        "name": "Heat Pump Water Heater",
        "category": "Home Appliances",
        "embodied_carbon_kg": 350.0,
        "default_daily_usage": 4.0,  # hours heating per day
        "usage_unit": "hrs active/day",
        "savings_per_unit": 0.45,    # kg CO2 saved per hour vs resistance water heater
        "description": "High-efficiency hybrid heat pump water heater."
    }
}


@cached(category=CACHE_CATEGORY_COMPUTED, ttl=TTL_COMPUTED_ANALYTICS)
def calculate_carbon_payback(
    embodied_carbon_kg: float,
    daily_usage: float,
    savings_per_unit: float,
    usage_unit: str = "units/day",
    product_name: str = "Custom Eco Purchase"
) -> dict:
    """
    Calculate carbon payback period and cumulative carbon savings over time.
    
    Args:
        embodied_carbon_kg: Manufacturing/upfront carbon emissions (kg CO2)
        daily_usage: Usage intensity per day
        savings_per_unit: kg CO2 saved per unit of usage
        usage_unit: Label for unit of usage
        product_name: Display name of the product
        
    Returns:
        dict containing payback period in days, months, years, and 1-10 year net savings projection
    """
    embodied = max(0.01, float(embodied_carbon_kg))
    usage = max(0.0, float(daily_usage))
    savings_rate = max(0.0, float(savings_per_unit))

    daily_savings_kg = usage * savings_rate
    annual_savings_kg = daily_savings_kg * 365.25

    if daily_savings_kg > 0:
        payback_days = embodied / daily_savings_kg
        payback_months = payback_days / 30.4375
        payback_years = payback_days / 365.25
    else:
        payback_days = float('inf')
        payback_months = float('inf')
        payback_years = float('inf')

    # Cumulative net savings trajectory over 10 years
    yearly_projections = []
    for year in range(1, 11):
        gross_savings = annual_savings_kg * year
        net_savings = gross_savings - embodied
        yearly_projections.append({
            "year": year,
            "gross_savings_kg": round(gross_savings, 2),
            "net_savings_kg": round(net_savings, 2),
            "is_payback_achieved": net_savings >= 0
        })

    return {
        "product_name": product_name,
        "embodied_carbon_kg": round(embodied, 2),
        "daily_usage": round(usage, 2),
        "savings_per_unit": round(savings_rate, 4),
        "usage_unit": usage_unit,
        "daily_savings_kg": round(daily_savings_kg, 4),
        "annual_savings_kg": round(annual_savings_kg, 2),
        "payback_days": round(payback_days, 1) if payback_days != float('inf') else None,
        "payback_months": round(payback_months, 1) if payback_months != float('inf') else None,
        "payback_years": round(payback_years, 2) if payback_years != float('inf') else None,
        "net_savings_5yr_kg": round((annual_savings_kg * 5) - embodied, 2),
        "net_savings_10yr_kg": round((annual_savings_kg * 10) - embodied, 2),
        "yearly_projections": yearly_projections
    }


def calculate_preset_payback(preset_key: str, custom_daily_usage: float = None) -> dict:
    """Calculate payback for a preset eco product."""
    if preset_key not in PRESET_ECO_PRODUCTS:
        raise ValueError(f"Unknown preset product '{preset_key}'. Choose from: {list(PRESET_ECO_PRODUCTS.keys())}")

    p = PRESET_ECO_PRODUCTS[preset_key]
    usage = custom_daily_usage if custom_daily_usage is not None else p["default_daily_usage"]
    return calculate_carbon_payback(
        embodied_carbon_kg=p["embodied_carbon_kg"],
        daily_usage=usage,
        savings_per_unit=p["savings_per_unit"],
        usage_unit=p["usage_unit"],
        product_name=p["name"]
    )


def compare_multiple_products(product_inputs: list) -> list:
    """
    Compare payback periods and 5-year/10-year net carbon ROI for multiple products.
    
    Args:
        product_inputs: list of dicts with calculation results or inputs
        
    Returns:
        list of payback dicts sorted by fastest payback period (years)
    """
    results = []
    for item in product_inputs:
        if "payback_years" in item:
            results.append(item)
        elif isinstance(item, dict) and "embodied_carbon_kg" in item:
            res = calculate_carbon_payback(
                embodied_carbon_kg=item.get("embodied_carbon_kg", 10.0),
                daily_usage=item.get("daily_usage", 1.0),
                savings_per_unit=item.get("savings_per_unit", 0.1),
                usage_unit=item.get("usage_unit", "units/day"),
                product_name=item.get("product_name", "Eco Product")
            )
            results.append(res)

    results.sort(key=lambda r: r["payback_years"] if r["payback_years"] is not None else float('inf'))
    return results
