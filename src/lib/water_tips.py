"""
Water Saving Tips for EcoBuddy AI
Provides personalized water conservation tips based on user behavior.
"""

import random
from typing import Dict, Any, List, Optional


class WaterTips:
    """
    Generates water saving tips based on user behavior and categories.
    """

    TIPS = {
        'general': [
            "💧 Fix leaky taps immediately - a dripping tap wastes 15L per day!",
            "🧊 Keep a jug of water in the fridge instead of running the tap.",
            "💡 Install water-efficient aerators on all taps.",
            "📊 Track your water usage weekly to stay aware.",
            "🌧️ Collect rainwater for gardening and outdoor cleaning.",
            "🚿 Install a water-efficient showerhead to save up to 15L per shower."
        ],
        'shower': [
            "🚿 Take shorter showers (aim for 5 minutes instead of 10). Save 25L per shower!",
            "💧 Turn off the water while soaping up. Save up to 20L per shower.",
            "🛁 If you bathe, fill the tub only halfway. Save 75L per bath!",
            "🚿 Install a low-flow showerhead. Save up to 25L per shower."
        ],
        'toilet': [
            "🚽 Install a dual-flush toilet system. Save up to 5L per flush!",
            "💧 Place a water-saving device (or brick) in your toilet tank.",
            "🚽 Don't use the toilet as a trash can. Save 6L per unnecessary flush!",
            "💦 Check for toilet leaks by adding food coloring to the tank."
        ],
        'washing_machine': [
            "👕 Only run the washing machine with full loads. Save 30L per load!",
            "🌡️ Use cold water for laundry when possible.",
            "🧺 Sort laundry to reduce the number of loads.",
            "💧 Upgrade to a water-efficient washing machine."
        ],
        'dishwasher': [
            "🍽️ Only run the dishwasher when full. Save 10L per cycle!",
            "💧 Scrape dishes instead of pre-rinsing with water.",
            "🌡️ Use the eco-cycle on your dishwasher.",
            "🧼 Hand wash dishes in a basin instead of running water."
        ],
        'garden': [
            "🌿 Water your garden early morning or evening to reduce evaporation.",
            "💧 Use a watering can instead of a hose. Save 20L per watering!",
            "🌱 Use mulch to retain moisture in the soil.",
            "🌧️ Install a rain barrel to collect rainwater for garden.",
            "💦 Use drip irrigation systems for efficient watering."
        ],
        'car': [
            "🚗 Use a commercial car wash that recycles water.",
            "💧 Wash your car on the lawn to water it at the same time!",
            "🪣 Use a bucket and sponge instead of a hose. Save 100L per wash!",
            "🚗 Use waterless car wash products."
        ],
        'kitchen': [
            "🧊 Keep water in the fridge instead of running the tap.",
            "💧 Use a basin to wash vegetables instead of running water.",
            "♻️ Reuse water from washing vegetables for watering plants.",
            "🍳 Use steam cooking to use less water."
        ],
        'outdoor': [
            "🧹 Use a broom instead of a hose to clean driveways.",
            "💧 Cover pools and spas to reduce evaporation.",
            "🌿 Water only when the soil is dry, not on a schedule.",
            "🌧️ Use a rain sensor for irrigation systems."
        ]
    }

    CATEGORY_MAP = {
        'shower': 'shower',
        'bath': 'shower',
        'toilet': 'toilet',
        'washing_machine': 'washing_machine',
        'dishwasher': 'dishwasher',
        'garden_watering': 'garden',
        'car_wash': 'car',
        'drinking': 'kitchen',
        'cooking': 'kitchen',
        'cleaning': 'kitchen'
    }

    @classmethod
    def get_tips(cls, category: str = None, count: int = 5) -> List[str]:
        """
        Get water saving tips for a specific category.
        
        Args:
            category: Category name (optional)
            count: Number of tips to return
        
        Returns:
            List of tips
        """
        if category and category in cls.CATEGORY_MAP:
            category_key = cls.CATEGORY_MAP[category]
            if category_key in cls.TIPS:
                tips = random.sample(cls.TIPS[category_key], min(count, len(cls.TIPS[category_key])))
                return tips

        # Get general tips
        all_tips = cls.TIPS['general'] + cls.TIPS['shower'] + cls.TIPS['toilet']
        return random.sample(all_tips, min(count, len(all_tips)))

    @classmethod
    def get_all_tips(cls) -> Dict[str, List[str]]:
        """Get all tips grouped by category."""
        return cls.TIPS

    @classmethod
    def get_tip_by_category(cls, category: str) -> List[str]:
        """Get tips for a specific category."""
        if category in cls.CATEGORY_MAP:
            category_key = cls.CATEGORY_MAP[category]
            return cls.TIPS.get(category_key, cls.TIPS['general'])
        return cls.TIPS['general']

    @classmethod
    def get_quick_tips(cls, count: int = 3) -> List[str]:
        """Get random quick tips."""
        all_tips = []
        for tips in cls.TIPS.values():
            all_tips.extend(tips)
        return random.sample(all_tips, min(count, len(all_tips)))

    @classmethod
    def get_daily_tip(cls) -> str:
        """Get a daily water tip."""
        import random
        all_tips = []
        for tips in cls.TIPS.values():
            all_tips.extend(tips)
        return random.choice(all_tips)

    @classmethod
    def get_personalized_tips(cls, category_usage: Dict[str, float]) -> List[str]:
        """
        Get personalized tips based on usage patterns.
        
        Args:
            category_usage: Dictionary of category usage in liters
        
        Returns:
            List of personalized tips
        """
        tips = []

        # Shower tips
        if category_usage.get('shower', 0) > 60:
            tips.extend([
                "🚿 You're using a lot of water for showers. Try reducing shower time by 2 minutes.",
                "💡 Consider installing a water-efficient showerhead."
            ])

        # Toilet tips
        if category_usage.get('toilet', 0) > 30:
            tips.extend([
                "🚽 Your toilet usage is high. Consider installing a dual-flush system.",
                "💧 Check for toilet leaks - they can waste up to 20L per day!"
            ])

        # Laundry tips
        if category_usage.get('washing_machine', 0) > 100:
            tips.extend([
                "👕 Run full loads in your washing machine to save water.",
                "💡 Use cold water cycles to save energy and water."
            ])

        # Dishwasher tips
        if category_usage.get('dishwasher', 0) > 30:
            tips.extend([
                "🍽️ Only run your dishwasher when it's completely full.",
                "💧 Scrape dishes instead of pre-rinsing with water."
            ])

        # Garden tips
        if category_usage.get('garden_watering', 0) > 100:
            tips.extend([
                "🌿 Water your garden in the early morning to reduce evaporation.",
                "💧 Use a watering can instead of a hose for small gardens."
            ])

        # General tips if no specific tips generated
        if not tips:
            tips.extend(cls.get_quick_tips(3))

        return tips[:5]

    @classmethod
    def get_challenge_tips(cls) -> List[Dict[str, str]]:
        """Get challenge-based tips."""
        return [
            {
                'title': '🚿 5-Minute Shower Challenge',
                'description': 'Try to reduce your shower time to 5 minutes this week.',
                'saving': 'Save up to 25L per shower!'
            },
            {
                'title': '💧 No-Leak Challenge',
                'description': 'Check all taps and toilets for leaks and fix them.',
                'saving': 'Save up to 50L per day!'
            },
            {
                'title': '🌿 Watering Wisdom Challenge',
                'description': 'Water your garden only when needed, not on a schedule.',
                'saving': 'Save up to 100L per week!'
            },
            {
                'title': '♻️ Reuse Water Challenge',
                'description': 'Reuse water from washing vegetables for watering plants.',
                'saving': 'Save up to 10L per day!'
            }
        ]