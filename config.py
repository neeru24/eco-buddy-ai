import os

# Base line and sensitivity for total footprint (if not using categories)
ECO_SCORE_BASELINE = float(os.environ.get("SCORING_BASELINE", 4000.0))
ECO_SCORE_SENSITIVITY = float(os.environ.get("SCORING_SENSITIVITY", 1000.0))

# Category weights for the eco score calculation
CATEGORY_WEIGHTS = {
    "Transport": float(os.environ.get("WEIGHT_TRANSPORT", 0.3)),
    "Electricity": float(os.environ.get("WEIGHT_ELECTRICITY", 0.3)),
    "Diet": float(os.environ.get("WEIGHT_DIET", 0.25)),
    "Flights": float(os.environ.get("WEIGHT_FLIGHTS", 0.15)),
}

# Canonical diet type constants
DIET_TYPES = ["Vegetarian", "Non-Vegetarian", "Vegan", "Omnivore", "Heavy Meat"]

DIET_NORMALIZE_MAP = {
    "vegetarian": "Vegetarian", "vegan": "Vegan",
    "non-vegetarian": "Non-Vegetarian",
    "omnivore": "Omnivore", "heavy meat": "Heavy Meat",
    "non veg": "Non-Vegetarian", "non-veg": "Non-Vegetarian",
    "plant based": "Vegan", "plant-based": "Vegan",
}


def normalize_diet(diet):
    if not diet:
        return "Vegetarian"
    lower = diet.strip().lower()
    if lower in DIET_NORMALIZE_MAP:
        return DIET_NORMALIZE_MAP[lower]
    if diet in DIET_TYPES:
        return diet
    return "Vegetarian"

# Water footprint constants
GLOBAL_WATER_AVERAGE_LITERS = float(os.environ.get("WATER_AVERAGE_LITERS", 3800.0))

WATER_FACTORS = {
    "shower_liter_per_min": float(os.environ.get("WATER_SHOWER_RATE", 10.0)),
    "laundry_liter_per_load": float(os.environ.get("WATER_LAUNDRY_RATE", 50.0)),
    "dishwasher_liter_per_run": float(os.environ.get("WATER_DISHWASHER_RATE", 15.0)),
    "garden_liter_per_min": float(os.environ.get("WATER_GARDEN_RATE", 20.0)),
}

DIET_VIRTUAL_WATER = {
    "Vegan": 2000.0,
    "Vegetarian": 2500.0,
    "Omnivore": 4000.0,
    "Heavy Meat": 5000.0,
}

# Emission calculation constants
VALID_TRANSPORT = {"Car", "Bike", "Public Transport", "Walking"}
VALID_DIET = {"Vegetarian", "Non-Vegetarian"}
VALID_REGIONS = {"Global", "US", "UK", "EU"}

MAX_DISTANCE = 500
MAX_ELECTRICITY = 10000
MAX_FLIGHTS = 365

TRANSPORT_EMISSION_FACTORS = {
    "Car": 0.21,
    "Bike": 0.0,
    "Public Transport": 0.08,
    "Walking": 0.0,
}

DIET_EMISSION_FACTORS = {
    "Vegetarian": 1000,
    "Non-Vegetarian": 1800,
}

# Energy audit constants
HOURS_PER_DAY = 24
DAYS_PER_YEAR = 365
MONTHS_PER_YEAR = 12
WATTS_TO_KW = 1000.0
