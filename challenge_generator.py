"""
AI Sustainability Challenge Generator

Generates personalized weekly sustainability challenges
based on the user's carbon footprint and lifestyle.
"""

import random
from typing import Any


def generate_weekly_challenges(
    footprint: float,
    transport: str,
    electricity: float,
    diet: str,
    flights: int,
) -> list[dict[str, Any]]:
    """
    Generate personalized weekly sustainability challenges.

    Returns:
        list[dict]
    """

    challenges = []

    # -------------------------------
    # Transport Challenge
    # -------------------------------

    if transport.lower() in ["car", "taxi"]:

        challenges.append(
            {
                "title": "Use public transport for at least 3 trips",
                "difficulty": "Medium",
                "xp": 100,
                "category": "Transport",
            }
        )

    elif transport.lower() in ["bike", "walking"]:

        challenges.append(
            {
                "title": "Walk or cycle 15 km this week",
                "difficulty": "Easy",
                "xp": 75,
                "category": "Transport",
            }
        )

    # -------------------------------
    # Electricity Challenge
    # -------------------------------

    if electricity >= 300:

        challenges.append(
            {
                "title": "Reduce electricity usage by 10%",
                "difficulty": "Hard",
                "xp": 200,
                "category": "Energy",
            }
        )

    elif electricity >= 150:

        challenges.append(
            {
                "title": "Turn off unused appliances every day",
                "difficulty": "Medium",
                "xp": 100,
                "category": "Energy",
            }
        )

    else:

        challenges.append(
            {
                "title": "Maintain your low electricity usage",
                "difficulty": "Easy",
                "xp": 50,
                "category": "Energy",
            }
        )

    # -------------------------------
    # Diet Challenge
    # -------------------------------

    if diet.lower() in ["non vegetarian", "mixed", "omnivore"]:

        challenges.append(
            {
                "title": "Eat vegetarian meals for 3 days",
                "difficulty": "Medium",
                "xp": 120,
                "category": "Diet",
            }
        )

    else:

        challenges.append(
            {
                "title": "Continue your sustainable diet this week",
                "difficulty": "Easy",
                "xp": 60,
                "category": "Diet",
            }
        )

    # -------------------------------
    # Flight Challenge
    # -------------------------------

    if flights > 0:

        challenges.append(
            {
                "title": "Avoid unnecessary flights this month",
                "difficulty": "Hard",
                "xp": 250,
                "category": "Travel",
            }
        )

    # -------------------------------
    # Carbon Footprint Challenge
    # -------------------------------

    if footprint > 300:

        challenges.append(
            {
                "title": "Reduce your carbon footprint by 15%",
                "difficulty": "Hard",
                "xp": 250,
                "category": "Overall",
            }
        )

    elif footprint > 150:

        challenges.append(
            {
                "title": "Reduce your carbon footprint by 10%",
                "difficulty": "Medium",
                "xp": 150,
                "category": "Overall",
            }
        )

    else:

        challenges.append(
            {
                "title": "Keep your footprint below this week's average",
                "difficulty": "Easy",
                "xp": 80,
                "category": "Overall",
            }
        )

    # -------------------------------
    # Fill Remaining Slots
    # -------------------------------

    bonus_challenges = [
        {
            "title": "Carry a reusable water bottle all week",
            "difficulty": "Easy",
            "xp": 50,
            "category": "Lifestyle",
        },
        {
            "title": "Plant a tree or care for a plant",
            "difficulty": "Medium",
            "xp": 100,
            "category": "Environment",
        },
        {
            "title": "Spend one full day without single-use plastics",
            "difficulty": "Medium",
            "xp": 120,
            "category": "Lifestyle",
        },
        {
            "title": "Recycle household waste for one week",
            "difficulty": "Easy",
            "xp": 60,
            "category": "Waste",
        },
    ]

    random.shuffle(bonus_challenges)

    while len(challenges) < 6:
        challenges.append(bonus_challenges.pop())

    random.shuffle(challenges)

    return challenges[:6]