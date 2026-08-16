SKILL_TREE_NODES = {
    "start_composting": {
        "id": "start_composting",
        "label": "Start Composting",
        "description": "Begin recycling organic waste to create nutrient-rich soil.",
        "xp_reward": 50,
        "prerequisites": [],
        "content": """
### How to Start Composting
1. **Choose a Bin:** Get a compost bin for your backyard or a smaller one for indoors.
2. **Greens and Browns:** Mix 'greens' (vegetable scraps, coffee grounds) with 'browns' (dry leaves, paper).
3. **Moisture & Aeration:** Keep it moist like a wrung-out sponge and turn it occasionally.
        """
    },
    "grow_herbs": {
        "id": "grow_herbs",
        "label": "Grow Your Own Herbs",
        "description": "Plant a small herb garden in your kitchen or balcony.",
        "xp_reward": 80,
        "prerequisites": ["start_composting"],
        "content": """
### Growing Your Own Herbs
Use the compost you started to plant some basil, mint, or cilantro!
1. **Pots & Soil:** Get small pots with drainage and fill with a mix of potting soil and your homemade compost.
2. **Light:** Place them in a sunny window or balcony (at least 4-6 hours of sunlight).
3. **Watering:** Water when the top inch of soil feels dry.
        """
    },
    "zero_waste_grocery": {
        "id": "zero_waste_grocery",
        "label": "Zero-Waste Grocery Shopping",
        "description": "Use reusable bags, jars, and buy in bulk to eliminate packaging waste.",
        "xp_reward": 100,
        "prerequisites": [],
        "content": """
### Zero-Waste Grocery Shopping
1. **Bring Bags:** Always keep reusable bags in your car or near the door.
2. **Bulk Bins:** Use your own jars or cloth bags to buy grains, nuts, and spices from bulk bins.
3. **Avoid Plastic:** Choose products packaged in glass, metal, or paper instead of plastic.
        """
    },
    "plant_based_diet": {
        "id": "plant_based_diet",
        "label": "Transition to a Plant-Based Diet",
        "description": "Eat primarily plant-based meals to drastically reduce your carbon footprint.",
        "xp_reward": 150,
        "prerequisites": ["grow_herbs", "zero_waste_grocery"],
        "content": """
### Plant-Based Diet Transition
1. **Start Small:** Try 'Meatless Mondays' and gradually increase plant-based days.
2. **Incorporate Fresh Herbs:** Use the herbs you grow to flavor your meals!
3. **Whole Foods:** Focus on legumes, whole grains, nuts, and fresh produce.
        """
    },
    "solar_panels": {
        "id": "solar_panels",
        "label": "Install Solar Panels",
        "description": "Generate your own renewable energy.",
        "xp_reward": 300,
        "prerequisites": ["plant_based_diet"],
        "content": """
### Solar Energy Transition
1. **Assessment:** Get a professional assessment of your roof's solar potential.
2. **Financing:** Explore local tax incentives and financing options.
3. **Installation:** Work with certified installers to set up your system and connect to the grid.
        """
    }
}
