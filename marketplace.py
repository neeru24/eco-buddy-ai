from cache import cached
from cache_config import TTL_COMPUTED_ANALYTICS, CACHE_CATEGORY_COMPUTED, CACHE_CATEGORY_STATIC

# Emissions factors (kg CO2e per passenger-km)
# Assumptions based on typical global averages, can be refined based on regional data
EMISSION_FACTORS = {
    "Single-occupancy car": 0.192,
    "Shared car or carpool": 0.096, # Assuming 2 people
    "Electric vehicle": 0.053, # Depends heavily on grid, this is a standard mix average
    "Bus": 0.105,
    "High-speed rail": 0.035,
    "Conventional rail": 0.041,
    "Flight": 0.255, # Short haul economy average
    "Walking": 0.0,
    "Cycling": 0.0
}

OFFSET_PROJECTS = [
    {
        "id": "proj_reforest_01",
        "name": "Amazon Reforestation Initiative",
        "category": "Reforestation",
        "description": "Restoring degraded land in the Amazon basin by planting native tree species.",
        "region": "South America",
        "cost_per_tonne": 15.00,
        "available_capacity": 50000,
        "quality_rating": "Gold Standard",
        "co_benefits": "Biodiversity protection, local employment",
        "image": "🌲"
    },
    {
        "id": "proj_mangrove_02",
        "name": "Coastal Mangrove Restoration",
        "category": "Mangrove restoration",
        "description": "Planting mangroves to protect coastlines and sequester carbon efficiently.",
        "region": "Southeast Asia",
        "cost_per_tonne": 22.50,
        "available_capacity": 25000,
        "quality_rating": "Verra",
        "co_benefits": "Flood protection, fisheries support",
        "image": "🌊"
    },
    {
        "id": "proj_methane_03",
        "name": "Landfill Methane Capture",
        "category": "Methane capture",
        "description": "Capturing methane emissions from landfills and converting it to energy.",
        "region": "North America",
        "cost_per_tonne": 8.00,
        "available_capacity": 100000,
        "quality_rating": "Climate Action Reserve",
        "co_benefits": "Air quality improvement, local energy generation",
        "image": "🏭"
    },
    {
        "id": "proj_cookstoves_04",
        "name": "Clean Cookstoves for Communities",
        "category": "Clean cookstoves",
        "description": "Distributing efficient cookstoves to reduce biomass burning and indoor air pollution.",
        "region": "Sub-Saharan Africa",
        "cost_per_tonne": 12.00,
        "available_capacity": 75000,
        "quality_rating": "Gold Standard",
        "co_benefits": "Health improvement, reduced deforestation",
        "image": "🍳"
    },
    {
        "id": "proj_solar_05",
        "name": "Community Solar Farm",
        "category": "Renewable energy",
        "description": "Building solar farms to displace fossil fuel energy on the grid.",
        "region": "India",
        "cost_per_tonne": 10.50,
        "available_capacity": 150000,
        "quality_rating": "Verra",
        "co_benefits": "Energy independence, job creation",
        "image": "☀️"
    },
    {
        "id": "proj_wind_06",
        "name": "Offshore Wind Project",
        "category": "Offshore wind",
        "description": "Large-scale offshore wind turbines to provide clean electricity.",
        "region": "Europe",
        "cost_per_tonne": 18.00,
        "available_capacity": 200000,
        "quality_rating": "Gold Standard",
        "co_benefits": "Large scale decarbonization, marine ecosystem creation (artificial reefs)",
        "image": "💨"
    },
    {
        "id": "proj_dac_07",
        "name": "Direct Air Capture Facility",
        "category": "Direct air capture",
        "description": "Technological removal of CO2 directly from the atmosphere for permanent geological storage.",
        "region": "Iceland",
        "cost_per_tonne": 350.00,
        "available_capacity": 1000,
        "quality_rating": "Puro.earth",
        "co_benefits": "Permanent removal, high additionality",
        "image": "🌬️"
    }
]


def calculate_trip_emissions(distance_km: float, transport_mode: str, passenger_count: int = 1) -> float:
    """Calculates emissions for a single trip in kg CO2e."""
    if distance_km < 0 or passenger_count < 1:
        raise ValueError("Distance must be non-negative and passenger count must be at least 1.")
    
    factor = EMISSION_FACTORS.get(transport_mode)
    if factor is None:
        raise ValueError(f"Unknown transport mode: {transport_mode}")
    
    if transport_mode == "Single-occupancy car" and passenger_count > 1:
        factor = factor / passenger_count
        
    trip_emissions = distance_km * factor
    return round(trip_emissions, 2)


def calculate_recurring_trip_emissions(trip_emissions: float, trips_per_week: int) -> dict:
    """Calculates weekly, monthly, and annual emissions based on trip frequency."""
    weekly = trip_emissions * trips_per_week
    monthly = weekly * (52 / 12)
    annual = weekly * 52
    
    return {
        "weekly": round(weekly, 2),
        "monthly": round(monthly, 2),
        "annual": round(annual, 2)
    }


@cached(category=CACHE_CATEGORY_COMPUTED, ttl=TTL_COMPUTED_ANALYTICS)
def compare_transit_modes(distance_km: float, passenger_count: int = 1) -> list:
    """Compares emissions across all supported transit modes for a given distance."""
    results = []
    for mode in EMISSION_FACTORS.keys():
        try:
            emissions = calculate_trip_emissions(distance_km, mode, passenger_count)
            results.append({
                "mode": mode,
                "emissions_kg": emissions
            })
        except ValueError:
            pass
            
    # Sort by emissions (lowest first)
    results.sort(key=lambda x: x["emissions_kg"])
    return results


@cached(category=CACHE_CATEGORY_STATIC)
def get_offset_projects() -> list:
    """Returns the list of available simulated offset projects."""
    return OFFSET_PROJECTS


def get_project_by_id(project_id: str) -> dict:
    """Helper to find a project by its ID."""
    for p in OFFSET_PROJECTS:
        if p["id"] == project_id:
            return p
    return None


def calculate_offset_cost(tonnes: float, cost_per_tonne: float) -> float:
    """Calculates the total cost for offsetting a given amount of carbon."""
    if tonnes < 0:
        raise ValueError("Offset amount cannot be negative.")
    return round(tonnes * cost_per_tonne, 2)


def validate_offset_transaction(tonnes: float, available_capacity: float = None) -> bool:
    """Validates if an offset transaction is valid."""
    if tonnes <= 0:
        return False, "Offset amount must be greater than zero."
    if available_capacity is not None and tonnes > available_capacity:
        return False, f"Requested offset ({tonnes}t) exceeds project capacity ({available_capacity}t)."
    return True, "Valid transaction"


def calculate_net_emissions(estimated_lifetime_footprint: float, total_offsets_purchased: float) -> float:
    """Calculates remaining footprint after offsets."""
    net = estimated_lifetime_footprint - total_offsets_purchased
    return round(max(0.0, net), 2)


def calculate_net_zero_progress(estimated_lifetime_footprint: float, total_offsets_purchased: float) -> float:
    """Calculates percentage progress towards net-zero."""
    if estimated_lifetime_footprint <= 0:
        return 100.0 if total_offsets_purchased > 0 else 0.0
    progress = (total_offsets_purchased / estimated_lifetime_footprint) * 100
    return round(min(100.0, progress), 2)
