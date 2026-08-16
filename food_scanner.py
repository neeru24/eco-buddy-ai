from typing import Any

FOOD_EMISSION_FACTORS = {
    "Beef (per 100g)": {"co2_kg": 27.0, "category": "Meat", "serving_g": 150},
    "Lamb (per 100g)": {"co2_kg": 22.0, "category": "Meat", "serving_g": 150},
    "Pork (per 100g)": {"co2_kg": 7.0, "category": "Meat", "serving_g": 150},
    "Chicken (per 100g)": {"co2_kg": 6.0, "category": "Meat", "serving_g": 150},
    "Fish (farmed, per 100g)": {"co2_kg": 5.0, "category": "Meat", "serving_g": 150},
    "Fish (wild caught, per 100g)": {"co2_kg": 3.0, "category": "Meat", "serving_g": 150},
    "Eggs (per 100g)": {"co2_kg": 4.5, "category": "Dairy & Eggs", "serving_g": 100},
    "Cheese (per 100g)": {"co2_kg": 6.0, "category": "Dairy & Eggs", "serving_g": 50},
    "Milk (per 100ml)": {"co2_kg": 0.3, "category": "Dairy & Eggs", "serving_g": 200},
    "Yogurt (per 100g)": {"co2_kg": 0.8, "category": "Dairy & Eggs", "serving_g": 150},
    "Rice (white, per 100g)": {"co2_kg": 0.9, "category": "Grains & Starches", "serving_g": 200},
    "Rice (brown, per 100g)": {"co2_kg": 0.8, "category": "Grains & Starches", "serving_g": 200},
    "Bread (wheat, per 100g)": {"co2_kg": 0.6, "category": "Grains & Starches", "serving_g": 60},
    "Pasta (dried, per 100g)": {"co2_kg": 0.5, "category": "Grains & Starches", "serving_g": 100},
    "Potatoes (per 100g)": {"co2_kg": 0.3, "category": "Grains & Starches", "serving_g": 200},
    "Tofu (per 100g)": {"co2_kg": 1.0, "category": "Protein Alternatives", "serving_g": 150},
    "Legumes (lentils, beans, per 100g)": {"co2_kg": 0.5, "category": "Protein Alternatives", "serving_g": 150},
    "Nuts (per 100g)": {"co2_kg": 1.0, "category": "Protein Alternatives", "serving_g": 50},
    "Tomatoes (per 100g)": {"co2_kg": 1.0, "category": "Vegetables", "serving_g": 100},
    "Broccoli (per 100g)": {"co2_kg": 0.4, "category": "Vegetables", "serving_g": 100},
    "Leafy greens (per 100g)": {"co2_kg": 0.3, "category": "Vegetables", "serving_g": 75},
    "Apples (per 100g)": {"co2_kg": 0.3, "category": "Fruits", "serving_g": 150},
    "Bananas (per 100g)": {"co2_kg": 0.4, "category": "Fruits", "serving_g": 120},
    "Berries (per 100g)": {"co2_kg": 0.5, "category": "Fruits", "serving_g": 100},
    "Chocolate (dark, per 100g)": {"co2_kg": 2.5, "category": "Snacks & Drinks", "serving_g": 40},
    "Coffee (per cup)": {"co2_kg": 0.3, "category": "Snacks & Drinks", "serving_g": 10},
    "Beer (per pint)": {"co2_kg": 0.6, "category": "Snacks & Drinks", "serving_g": 240},
    "Wine (per glass)": {"co2_kg": 0.5, "category": "Snacks & Drinks", "serving_g": 150},
}

CATEGORIES = ["Meat", "Dairy & Eggs", "Grains & Starches", "Protein Alternatives", "Vegetables", "Fruits", "Snacks & Drinks"]


def calculate_food_footprint(selected_items: dict[str, int]) -> dict[str, Any]:
    total_co2 = 0.0
    breakdown = []
    for item_name, servings in selected_items.items():
        if item_name in FOOD_EMISSION_FACTORS and servings > 0:
            info = FOOD_EMISSION_FACTORS[item_name]
            base_qty = 100 if "per 100" in item_name or "per cup" in item_name or "per pint" in item_name or "per glass" in item_name else 100
            co2 = info["co2_kg"] * servings * (info["serving_g"] / base_qty) if "per cup" not in item_name and "per pint" not in item_name and "per glass" not in item_name else info["co2_kg"] * servings
            total_co2 += co2
            breakdown.append({
                "item": item_name,
                "category": info["category"],
                "servings": servings,
                "co2_kg": round(co2, 2),
            })
    return {"total_co2": round(total_co2, 2), "breakdown": breakdown}


def get_comparison_context(total_co2: float) -> list[dict[str, Any]]:
    benchmarks = [
        ("Driving 1 km (avg car)", 0.19),
        ("Charging a smartphone", 0.01),
        ("Watching TV for 1 hour", 0.08),
        ("A 5 km bus ride", 0.35),
        ("Boiling 1 L of water", 0.15),
    ]
    comparisons = []
    for label, value in benchmarks:
        comparisons.append({"label": label, "equivalent": round(total_co2 / value, 1) if value > 0 else 0})
    return comparisons
