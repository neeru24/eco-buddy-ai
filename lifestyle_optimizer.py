"""
Lifestyle Optimization Engine for EcoBuddy AI.

Generates a personalized action plan recommending the minimum set of lifestyle changes
needed to achieve a user-defined carbon reduction target (e.g. 10%, 20%, 30%, 50%).
"""

from cache import cached
from cache_config import TTL_COMPUTED_ANALYTICS, CACHE_CATEGORY_COMPUTED
from config import normalize_diet

# Master catalog of quantifiable lifestyle actions with estimated annual CO2 savings (kg/year)
LIFESTYLE_ACTIONS_CATALOG = [
    {
        "id": "trans_ev",
        "category": "Transport",
        "title": "Switch to an Electric Vehicle (EV)",
        "annual_savings_kg": 1500.0,
        "impact": "High",
        "effort": "High",
        "description": "Replace a gasoline/diesel car with an electric vehicle charged on standard grid mix.",
        "requires_context": {"transport": ["Car"]}
    },
    {
        "id": "energy_solar",
        "category": "Electricity",
        "title": "Install Rooftop Solar Panels (5 kW)",
        "annual_savings_kg": 1400.0,
        "impact": "High",
        "effort": "High",
        "description": "Generate clean solar energy on-site to reduce household grid electricity reliance.",
        "requires_context": {}
    },
    {
        "id": "diet_vegan",
        "category": "Diet",
        "title": "Adopt a Plant-Based / Vegan Diet",
        "annual_savings_kg": 1200.0,
        "impact": "High",
        "effort": "Medium",
        "description": "Transition fully from animal products to plant-based nutrition.",
        "requires_context": {"diet": ["Non-Vegetarian", "Omnivore", "Heavy Meat"]}
    },
    {
        "id": "diet_vegetarian",
        "category": "Diet",
        "title": "Switch to a Vegetarian Diet",
        "annual_savings_kg": 800.0,
        "impact": "High",
        "effort": "Medium",
        "description": "Eliminate meat and poultry from daily meals.",
        "requires_context": {"diet": ["Non-Vegetarian", "Omnivore", "Heavy Meat"]}
    },
    {
        "id": "energy_heat_pump",
        "category": "Electricity",
        "title": "Upgrade to Energy Star Heat Pump HVAC",
        "annual_savings_kg": 800.0,
        "impact": "High",
        "effort": "High",
        "description": "Replace legacy resistance heating/cooling with an efficient heat pump system.",
        "requires_context": {}
    },
    {
        "id": "trans_transit_3d",
        "category": "Transport",
        "title": "Commute via Public Transit 3 Days/Week",
        "annual_savings_kg": 600.0,
        "impact": "Medium",
        "effort": "Medium",
        "description": "Replace solo car commuting with bus, train, or metro 3 days per week.",
        "requires_context": {"transport": ["Car"]}
    },
    {
        "id": "flight_staycation",
        "category": "Flights",
        "title": "Replace 1 Long-Haul Flight with Local Vacation",
        "annual_savings_kg": 500.0,
        "impact": "Medium",
        "effort": "Low",
        "description": "Opt for regional train travel or local staycation instead of flying.",
        "requires_context": {"min_flights": 1}
    },
    {
        "id": "trans_carpool",
        "category": "Transport",
        "title": "Carpool with Colleagues or Neighbors",
        "annual_savings_kg": 350.0,
        "impact": "Medium",
        "effort": "Low",
        "description": "Share car rides for daily commuting to split vehicle emissions.",
        "requires_context": {"transport": ["Car"]}
    },
    {
        "id": "trans_ebike",
        "category": "Transport",
        "title": "Walk or E-Bike for Trips Under 5 km",
        "annual_savings_kg": 300.0,
        "impact": "Medium",
        "effort": "Low",
        "description": "Replace short driving trips with active transport like e-biking or walking.",
        "requires_context": {"transport": ["Car", "Public Transport"]}
    },
    {
        "id": "energy_thermostat",
        "category": "Electricity",
        "title": "Install Smart Thermostat & Adjust 2°C",
        "annual_savings_kg": 250.0,
        "impact": "Medium",
        "effort": "Low",
        "description": "Optimize heating/cooling setpoints and eliminate conditioning idle rooms.",
        "requires_context": {}
    },
    {
        "id": "diet_meatless_monday",
        "category": "Diet",
        "title": "Adopt Meatless Mondays (1 Day/Week Plant-Based)",
        "annual_savings_kg": 200.0,
        "impact": "Low",
        "effort": "Low",
        "description": "Replace meat meals with plant-based alternatives one day each week.",
        "requires_context": {"diet": ["Non-Vegetarian", "Omnivore", "Heavy Meat"]}
    },
    {
        "id": "energy_led",
        "category": "Electricity",
        "title": "Switch 100% Home Lighting to LEDs",
        "annual_savings_kg": 180.0,
        "impact": "Low",
        "effort": "Low",
        "description": "Replace incandescent or halogen bulbs with energy-efficient LED lighting.",
        "requires_context": {}
    },
    {
        "id": "diet_meal_planning",
        "category": "Diet",
        "title": "Reduce Household Food Waste by 50%",
        "annual_savings_kg": 150.0,
        "impact": "Low",
        "effort": "Low",
        "description": "Plan weekly meals and store perishables properly to prevent food spoilage.",
        "requires_context": {}
    },
    {
        "id": "energy_vampire_load",
        "category": "Electricity",
        "title": "Unplug Standby Electronics & Smart Strips",
        "annual_savings_kg": 100.0,
        "impact": "Low",
        "effort": "Low",
        "description": "Eliminate phantom power draw from TVs, chargers, and gaming consoles on standby.",
        "requires_context": {}
    }
]


def filter_eligible_actions(context: dict) -> list:
    """Filter out actions that are irrelevant or already fulfilled based on user context."""
    user_transport = context.get("transport", "Car")
    user_diet = normalize_diet(context.get("diet", "Non-Vegetarian"))
    user_flights = int(context.get("flights", 0))

    eligible = []
    for action in LIFESTYLE_ACTIONS_CATALOG:
        reqs = action.get("requires_context", {})

        # Transport check
        if "transport" in reqs and user_transport not in reqs["transport"]:
            continue

        # Diet check
        if "diet" in reqs and user_diet not in reqs["diet"]:
            continue

        # Flights check
        if "min_flights" in reqs and user_flights < reqs["min_flights"]:
            continue

        eligible.append(action)

    return eligible


@cached(category=CACHE_CATEGORY_COMPUTED, ttl=TTL_COMPUTED_ANALYTICS)
def generate_optimized_lifestyle_plan(
    current_footprint_kg: float,
    target_reduction_pct: float,
    context: dict = None
) -> dict:
    """
    Greedy optimization algorithm to select the MINIMUM set of impactful lifestyle actions
    needed to achieve the target carbon reduction percentage.
    
    Args:
        current_footprint_kg: Baseline annual carbon emissions (kg CO2/year)
        target_reduction_pct: Goal percentage (e.g. 10.0, 20.0, 30.0)
        context: Optional dict with keys transport, electricity, diet, flights
        
    Returns:
        dict containing:
            - target_reduction_pct
            - required_reduction_kg
            - recommended_actions (list of minimum actions)
            - total_estimated_savings_kg
            - projected_footprint_kg
            - projected_reduction_pct
            - is_target_achieved
    """
    context = context or {}
    current_footprint = max(100.0, float(current_footprint_kg))
    target_pct = max(1.0, min(90.0, float(target_reduction_pct)))

    required_reduction_kg = current_footprint * (target_pct / 100.0)
    eligible = filter_eligible_actions(context)

    # Sort eligible actions by highest annual savings (greedy strategy to minimize number of actions required)
    sorted_actions = sorted(eligible, key=lambda a: a["annual_savings_kg"], reverse=True)

    recommended_actions = []
    accumulated_savings = 0.0
    selected_categories = set()

    for action in sorted_actions:
        if accumulated_savings >= required_reduction_kg:
            break

        # Prevent mutually redundant actions in the same category (e.g. don't suggest both Vegan AND Vegetarian, or both EV AND E-bike if EV already covers it)
        act_cat = action["category"]
        act_id = action["id"]

        if act_id in ("diet_vegan", "diet_vegetarian"):
            if any(a["id"] in ("diet_vegan", "diet_vegetarian") for a in recommended_actions):
                continue
        if act_id in ("trans_ev", "trans_transit_3d"):
            if any(a["id"] in ("trans_ev", "trans_transit_3d") for a in recommended_actions):
                continue

        recommended_actions.append(action)
        accumulated_savings += action["annual_savings_kg"]

    projected_footprint = max(0.0, current_footprint - accumulated_savings)
    achieved_pct = (accumulated_savings / current_footprint) * 100.0 if current_footprint > 0 else 0.0

    return {
        "baseline_footprint_kg": round(current_footprint, 2),
        "target_reduction_pct": round(target_pct, 1),
        "required_reduction_kg": round(required_reduction_kg, 2),
        "recommended_actions": recommended_actions,
        "actions_count": len(recommended_actions),
        "total_estimated_savings_kg": round(accumulated_savings, 2),
        "projected_footprint_kg": round(projected_footprint, 2),
        "projected_reduction_pct": round(achieved_pct, 1),
        "is_target_achieved": accumulated_savings >= required_reduction_kg
    }
