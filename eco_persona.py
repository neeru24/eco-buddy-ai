"""AI Eco Persona Generator.

Analyzes a user's behavior across EcoBuddy AI and assigns a unique,
personalized sustainability persona with strengths, weaknesses,
achievements, and improvement opportunities.

The generator is rule-based and fully deterministic: the same behavior
always produces the same persona, so a profile updates automatically the
moment the underlying data changes. No database schema changes are needed —
everything is computed from the existing assessments, gamification,
energy, water, waste, and offset records.
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

ACTIVE_TRANSPORT_MODES = ("Bike", "Walking")
PLANT_BASED_DIETS = {"Vegetarian", "Vegan", "vegetarian", "vegan"}

# Default metrics used for users with no recorded activity yet.
EMPTY_METRICS = {
    "assessment_count": 0,
    "latest_eco_score": 0,
    "best_eco_score": 0,
    "avg_eco_score": 0,
    "latest_footprint": None,
    "avg_footprint": None,
    "total_xp": 0,
    "level": 1,
    "level_progress": 0.0,
    "completed_challenges": 0,
    "enrolled_challenges": 0,
    "badges_count": 0,
    "streak": 0,
    "plant_based_days": 0,
    "plant_based_ratio": 0.0,
    "active_transport_ratio": 0.0,
    "assessments_with_transport": 0,
    "avg_electricity_kwh": None,
    "appliance_count": 0,
    "has_energy_audit": False,
    "water_assessment_count": 0,
    "waste_assessment_count": 0,
    "avg_recyclable_pct": 0.0,
    "total_offsets_tonnes": 0.0,
    "offset_count": 0,
    "skill_unlocked_count": 0,
    "skill_completed_count": 0,
    "milestone_count": 0,
}

PERSONAS = {
    "eco_rookie": {
        "name": "Eco Rookie",
        "icon": "🌱",
        "tagline": "Every eco journey starts with a single step",
        "description": (
            "You're just beginning your sustainability journey. There's no "
            "data yet to analyze, so the best next step is to complete your "
            "first carbon footprint assessment and start logging your habits."
        ),
        "rarity": "common",
        "color": (167, 199, 231),
        "accent": (76, 175, 80),
        "text_color": (21, 101, 48),
        "focus": "Foundation",
    },
    "earth_explorer": {
        "name": "Earth Explorer",
        "icon": "🌿",
        "tagline": "Exploring greener choices one habit at a time",
        "description": (
            "You've started tracking your environmental impact and are "
            "actively discovering which habits move the needle. Keep logging "
            "assessments and trying new eco-actions to unlock a specialized "
            "persona."
        ),
        "rarity": "common",
        "color": (216, 238, 218),
        "accent": (102, 187, 106),
        "text_color": (27, 94, 32),
        "focus": "Discovery",
    },
    "green_guardian": {
        "name": "Green Guardian",
        "icon": "🌳",
        "tagline": "Your footprint is small, your impact is mighty",
        "description": (
            "You consistently score high on your carbon footprint "
            "assessments, proving that thoughtful daily choices add up to "
            "real emissions savings."
        ),
        "rarity": "rare",
        "color": (216, 244, 216),
        "accent": (76, 175, 80),
        "text_color": (46, 125, 50),
        "focus": "Carbon Footprint",
    },
    "streak_star": {
        "name": "Streak Star",
        "icon": "🔥",
        "tagline": "Consistency is your superpower",
        "description": (
            "You keep showing up for the planet. Your sustained daily "
            "logging streak shows habits that stick — the backbone of real "
            "environmental change."
        ),
        "rarity": "rare",
        "color": (255, 236, 214),
        "accent": (255, 152, 0),
        "text_color": (230, 81, 0),
        "focus": "Consistency",
    },
    "challenge_champion": {
        "name": "Challenge Champion",
        "icon": "🏆",
        "tagline": "You turn eco challenges into victories",
        "description": (
            "You regularly complete eco challenges, transforming small "
            "commitments into measurable environmental wins and earning "
            "serious XP along the way."
        ),
        "rarity": "rare",
        "color": (255, 248, 216),
        "accent": (255, 152, 0),
        "text_color": (230, 81, 0),
        "focus": "Challenges",
    },
    "transport_titan": {
        "name": "Transport Titan",
        "icon": "🚲",
        "tagline": "Two wheels (or two feet) over four",
        "description": (
            "You favor active transport like biking and walking over "
            "single-occupancy car trips, cutting transport emissions and "
            "boosting your health in one move."
        ),
        "rarity": "uncommon",
        "color": (224, 242, 254),
        "accent": (3, 169, 244),
        "text_color": (2, 90, 130),
        "focus": "Transport",
    },
    "energy_mentor": {
        "name": "Energy Mentor",
        "icon": "💡",
        "tagline": "You keep the lights on and the watts low",
        "description": (
            "You've audited your home energy use and manage your appliances "
            "efficiently, showing that smarter energy habits are within "
            "everyone's reach."
        ),
        "rarity": "uncommon",
        "color": (255, 253, 231),
        "accent": (255, 193, 7),
        "text_color": (120, 96, 0),
        "focus": "Home Energy",
    },
    "plant_powered_pal": {
        "name": "Plant-Powered Pal",
        "icon": "🥗",
        "tagline": "Your plate is good for you and the planet",
        "description": (
            "Plant-based meals dominate your diet, dramatically reducing the "
            "food-related share of your footprint while supporting a "
            "healthier, more sustainable food system."
        ),
        "rarity": "uncommon",
        "color": (232, 245, 233),
        "accent": (139, 195, 74),
        "text_color": (51, 105, 30),
        "focus": "Diet",
    },
    "water_whisperer": {
        "name": "Water Whisperer",
        "icon": "💧",
        "tagline": "You make every drop count",
        "description": (
            "You track your water footprint — including the hidden 'virtual "
            "water' in food — and understand that water stewardship is just "
            "as important as carbon."
        ),
        "rarity": "uncommon",
        "color": (224, 242, 254),
        "accent": (3, 155, 229),
        "text_color": (0, 84, 130),
        "focus": "Water",
    },
    "waste_warrior": {
        "name": "Waste Warrior",
        "icon": "♻️",
        "tagline": "Nothing goes to waste on your watch",
        "description": (
            "You measure and minimize your waste, prioritizing recycling and "
            "reduction. A circular mindset is one of the highest-impact "
            "lifestyle shifts there is."
        ),
        "rarity": "uncommon",
        "color": (234, 245, 241),
        "accent": (0, 150, 136),
        "text_color": (0, 96, 87),
        "focus": "Waste",
    },
    "carbon_crusader": {
        "name": "Carbon Crusader",
        "icon": "🌍",
        "tagline": "You go beyond zero with offsets",
        "description": (
            "You purchase verified carbon offsets to neutralize what you "
            "can't yet reduce, funding real climate projects around the "
            "world — a hallmark of climate leadership."
        ),
        "rarity": "rare",
        "color": (230, 238, 252),
        "accent": (104, 111, 245),
        "text_color": (50, 54, 130),
        "focus": "Offsets",
    },
    "eco_legend": {
        "name": "Eco Legend",
        "icon": "⭐",
        "tagline": "Sustainability runs through everything you do",
        "description": (
            "You're active across nearly every dimension EcoBuddy tracks — "
            "carbon, energy, water, waste, challenges, streaks, and offsets. "
            "You are the living example of a low-impact lifestyle."
        ),
        "rarity": "legendary",
        "color": (255, 248, 216),
        "accent": (255, 152, 0),
        "text_color": (230, 81, 0),
        "focus": "Everything",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Behavior analysis
# ─────────────────────────────────────────────────────────────────────────────

def _parse_assessment_rows(rows: list[tuple]) -> list[dict[str, Any]]:
    """Turn raw assessment rows into normalized dicts."""
    parsed = []
    for row in rows:
        parsed.append({
            "date": row[1] if len(row) > 1 else None,
            "transport": row[2] if len(row) > 2 else None,
            "distance": row[3] if len(row) > 3 else None,
            "electricity": row[4] if len(row) > 4 else None,
            "diet": row[5] if len(row) > 5 else None,
            "flights": row[6] if len(row) > 6 else None,
            "footprint": row[7] if len(row) > 7 else None,
            "eco_score": row[8] if len(row) > 8 else None,
        })
    return parsed


def analyze_user_behavior(user_id: int) -> dict[str, Any]:
    """Gather and summarize a user's behavior across the whole app.

    Every read is defensive: missing tables or a brand-new user simply
    contribute zero values rather than raising.
    """
    from database import (
        get_assessments, get_total_xp, get_user_challenges,
        get_unlocked_badges, get_skill_tree_progress,
        get_water_assessments, get_waste_assessments,
        get_total_offsets, get_appliances, get_diet_history,
        get_offset_transactions, get_environmental_milestones,
    )

    metrics = dict(EMPTY_METRICS)

    try:
        assessments = _parse_assessment_rows(get_assessments(user_id))
    except Exception as exc:  # noqa: BLE001 - tolerate any backend hiccup
        logger.warning("Persona: unable to read assessments: %s", exc)
        assessments = []

    metrics["assessment_count"] = len(assessments)
    if assessments:
        scores = [a["eco_score"] for a in assessments if a["eco_score"] is not None]
        footprints = [a["footprint"] for a in assessments if a["footprint"] is not None]
        if scores:
            metrics["best_eco_score"] = int(max(scores))
            metrics["avg_eco_score"] = round(sum(scores) / len(scores), 1)
        if footprints:
            metrics["latest_footprint"] = round(footprints[0], 2)
            metrics["avg_footprint"] = round(sum(footprints) / len(footprints), 2)

    # Transport + electricity + diet signals from assessments
    transport_rows = [a for a in assessments if a.get("transport")]
    metrics["assessments_with_transport"] = len(transport_rows)
    if transport_rows:
        active = sum(
            1 for a in transport_rows
            if a["transport"] in ACTIVE_TRANSPORT_MODES
        )
        metrics["active_transport_ratio"] = round(active / len(transport_rows), 2)

    electric = [a["electricity"] for a in assessments if a.get("electricity") is not None]
    if electric:
        metrics["avg_electricity_kwh"] = round(sum(electric) / len(electric), 1)

    try:
        diet_logs = get_diet_history(user_id, limit=100) or []
    except Exception as exc:  # noqa: BLE001
        logger.warning("Persona: unable to read diet history: %s", exc)
        diet_logs = []
    if diet_logs:
        recent = diet_logs[:7]
        metrics["plant_based_days"] = sum(1 for _, diet in recent if diet in PLANT_BASED_DIETS)
        metrics["plant_based_ratio"] = round(
            sum(1 for _, diet in diet_logs if diet in PLANT_BASED_DIETS) / len(diet_logs), 2
        )

    try:
        metrics["total_xp"] = get_total_xp(user_id) or 0
    except Exception as exc:  # noqa: BLE001
        logger.warning("Persona: unable to read XP: %s", exc)

    from gamification import get_user_streak, calculate_level, calculate_level_progress
    try:
        metrics["streak"] = get_user_streak(user_id) or 0
    except Exception as exc:  # noqa: BLE001
        logger.warning("Persona: unable to read streak: %s", exc)

    metrics["level"] = calculate_level(metrics["total_xp"])
    metrics["level_progress"] = round(calculate_level_progress(metrics["total_xp"]), 3)

    try:
        challenges = get_user_challenges(user_id) or []
        metrics["completed_challenges"] = sum(
            1 for c in challenges if c.get("status") == "completed"
        )
        metrics["enrolled_challenges"] = sum(
            1 for c in challenges if c.get("status") == "enrolled"
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Persona: unable to read challenges: %s", exc)

    try:
        metrics["badges_count"] = len(get_unlocked_badges(user_id) or [])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Persona: unable to read badges: %s", exc)

    try:
        skills = get_skill_tree_progress(user_id) or []
        metrics["skill_unlocked_count"] = sum(
            1 for s in skills if s.get("status") in ("Unlocked", "Completed")
        )
        metrics["skill_completed_count"] = sum(
            1 for s in skills if s.get("status") == "Completed"
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Persona: unable to read skill tree: %s", exc)

    try:
        metrics["water_assessment_count"] = len(get_water_assessments(user_id) or [])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Persona: unable to read water data: %s", exc)

    try:
        waste = get_waste_assessments(user_id) or []
        metrics["waste_assessment_count"] = len(waste)
        if waste:
            pcts = [w.get("recyclable_pct") for w in waste if w.get("recyclable_pct") is not None]
            if pcts:
                metrics["avg_recyclable_pct"] = round(sum(pcts) / len(pcts), 1)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Persona: unable to read waste data: %s", exc)

    try:
        appliances = get_appliances(user_id) or []
        metrics["appliance_count"] = len(appliances)
        metrics["has_energy_audit"] = len(appliances) > 0
    except Exception as exc:  # noqa: BLE001
        logger.warning("Persona: unable to read energy data: %s", exc)

    try:
        metrics["total_offsets_tonnes"] = round(get_total_offsets(user_id) or 0.0, 2)
        metrics["offset_count"] = len(get_offset_transactions(user_id) or [])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Persona: unable to read offset data: %s", exc)

    try:
        metrics["milestone_count"] = len(get_environmental_milestones(user_id) or [])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Persona: unable to read milestones: %s", exc)

    return metrics


# ─────────────────────────────────────────────────────────────────────────────
# Persona assignment
# ─────────────────────────────────────────────────────────────────────────────

def _category_scores(metrics: dict[str, Any]) -> dict[str, float]:
    """Score each specialist persona domain from 0 to 1."""
    return {
        "green_guardian": min(1.0, metrics["avg_eco_score"] / 90.0)
            if metrics["assessment_count"] > 0 else 0.0,
        "streak_star": min(1.0, metrics["streak"] / 14.0),
        "challenge_champion": min(1.0, metrics["completed_challenges"] / 5.0),
        "transport_titan": metrics["active_transport_ratio"]
            if metrics["assessments_with_transport"] >= 2 else 0.0,
        "energy_mentor": 1.0 if metrics["has_energy_audit"] else 0.0,
        "plant_powered_pal": metrics["plant_based_ratio"],
        "water_whisperer": min(1.0, metrics["water_assessment_count"] / 3.0),
        "waste_warrior": min(1.0, metrics["waste_assessment_count"] / 3.0),
        "carbon_crusader": 1.0 if metrics["total_offsets_tonnes"] > 0 else 0.0,
    }


def _active_domains(metrics: dict[str, Any]) -> int:
    """Count how many distinct eco domains a user is active in."""
    domains = 0
    if metrics["assessment_count"] > 0:
        domains += 1
    if metrics["plant_based_days"] >= 3 or metrics["plant_based_ratio"] >= 0.5:
        domains += 1
    if metrics["active_transport_ratio"] >= 0.5:
        domains += 1
    if metrics["has_energy_audit"]:
        domains += 1
    if metrics["water_assessment_count"] > 0:
        domains += 1
    if metrics["waste_assessment_count"] > 0:
        domains += 1
    if metrics["total_offsets_tonnes"] > 0:
        domains += 1
    if metrics["completed_challenges"] >= 1:
        domains += 1
    if metrics["streak"] >= 3:
        domains += 1
    return domains


def _persona_rarity(persona_id: str, metrics: dict[str, Any]) -> str:
    """Promote common personas to higher rarities for exceptional metrics."""
    thresholds = {
        "streak_star": (30, "legendary", 14, "rare"),
        "challenge_champion": (10, "legendary", 5, "rare"),
        "green_guardian": (90, "legendary", 80, "rare"),
        "transport_titan": (1.0, "rare", None, None),
        "carbon_crusader": (10.0, "legendary", 1.0, "rare"),
        "eco_legend": (7, "legendary", 5, "rare"),
    }
    if persona_id not in thresholds:
        return PERSONAS[persona_id]["rarity"]
    high, high_rarity, low, low_rarity = thresholds[persona_id]
    if persona_id == "transport_titan" and high is not None:
        return high_rarity if metrics["active_transport_ratio"] >= high else PERSONAS[persona_id]["rarity"]
    value = (
        metrics["streak"] if persona_id == "streak_star" else
        metrics["completed_challenges"] if persona_id == "challenge_champion" else
        metrics["avg_eco_score"] if persona_id == "green_guardian" else
        metrics["total_offsets_tonnes"] if persona_id == "carbon_crusader" else
        _active_domains(metrics)
    )
    if high is not None and value >= high:
        return high_rarity
    if low is not None and value >= low:
        return low_rarity
    return PERSONAS[persona_id]["rarity"]


def assign_persona(metrics: dict[str, Any]) -> str:
    """Return the persona id that best matches the given metrics."""
    if metrics["assessment_count"] == 0 and metrics["total_xp"] == 0:
        return "eco_rookie"

    scores = _category_scores(metrics)
    domains = _active_domains(metrics)

    # Breadth-first: highly active users become Eco Legends.
    if domains >= 5:
        return "eco_legend"

    # Otherwise pick the strongest specialist persona above its threshold.
    thresholds = {
        "green_guardian": 0.8,
        "streak_star": 0.5,
        "challenge_champion": 0.6,
        "transport_titan": 0.5,
        "energy_mentor": 1.0,
        "plant_powered_pal": 0.7,
        "water_whisperer": 0.34,
        "waste_warrior": 0.34,
        "carbon_crusader": 1.0,
    }
    best_id = None
    best_score = 0.0
    for persona_id in PERSONAS:
        if persona_id in ("eco_rookie", "earth_explorer", "eco_legend"):
            continue
        score = scores[persona_id]
        if score >= thresholds[persona_id] and score > best_score:
            best_id = persona_id
            best_score = score

    if best_id is not None:
        return best_id

    return "earth_explorer"


# ─────────────────────────────────────────────────────────────────────────────
# Profile content
# ─────────────────────────────────────────────────────────────────────────────

def get_strengths(metrics: dict[str, Any]) -> list[str]:
    """Dynamic strengths derived from the user's actual behavior."""
    strengths = []
    if metrics["assessment_count"] > 0:
        strengths.append(
            f"You've completed {metrics['assessment_count']} footprint "
            "assessment(s) — self-awareness is the first step to change."
        )
    if metrics["avg_eco_score"] >= 70:
        strengths.append(
            f"Your average eco score of {metrics['avg_eco_score']:.0f} shows a "
            "consistently low-impact lifestyle."
        )
    if metrics["streak"] >= 7:
        strengths.append(
            f"A {metrics['streak']}-day logging streak — consistency is the "
            "strongest predictor of lasting change."
        )
    if metrics["completed_challenges"] >= 3:
        strengths.append(
            f"You've completed {metrics['completed_challenges']} eco "
            "challenges, converting commitments into real action."
        )
    if metrics["active_transport_ratio"] >= 0.5:
        strengths.append(
            f"{metrics['active_transport_ratio'] * 100:.0f}% of your recorded "
            "trips use active transport — you're cutting emissions and "
            "staying healthy."
        )
    if metrics["plant_based_ratio"] >= 0.7:
        strengths.append(
            "A predominantly plant-based diet keeps your food footprint low."
        )
    if metrics["has_energy_audit"]:
        strengths.append(
            "You've audited your home energy use and track your appliances."
        )
    if metrics["total_offsets_tonnes"] > 0:
        strengths.append(
            f"You've offset {metrics['total_offsets_tonnes']:.1f} tonnes of "
            "CO₂, funding verified climate projects."
        )
    if metrics["water_assessment_count"] > 0:
        strengths.append("You monitor your water footprint, including virtual water.")
    if metrics["waste_assessment_count"] > 0:
        strengths.append("You track and minimize your waste stream.")
    if not strengths:
        strengths.append("You're getting started — every expert was once a beginner.")
    return strengths


def get_improvement_opportunities(metrics: dict[str, Any]) -> list[str]:
    """Weaknesses / improvement opportunities personalized to the user."""
    improvements = []
    if metrics["streak"] < 3 and metrics["assessment_count"] > 0:
        improvements.append(
            "Log your activities more regularly to build a longer streak — "
            "small daily check-ins compound into big habits."
        )
    if metrics["plant_based_ratio"] < 0.5:
        improvements.append(
            "Try swapping a few meals for plant-based options; diet is one of "
            "the largest levers on your footprint."
        )
    if metrics["avg_electricity_kwh"] is not None and metrics["avg_electricity_kwh"] > 200:
        improvements.append(
            f"Your average electricity use ({metrics['avg_electricity_kwh']:.0f} "
            "kWh) is on the high side — consider an energy audit and "
            "energy-efficient appliances."
        )
    if not metrics["has_energy_audit"]:
        improvements.append(
            "Run a home energy audit to find hidden electricity savings."
        )
    if metrics["active_transport_ratio"] < 0.5:
        improvements.append(
            "Swap short car trips for walking or cycling to cut transport "
            "emissions and boost fitness."
        )
    if metrics["water_assessment_count"] == 0:
        improvements.append("Track your water footprint to find virtual-water savings.")
    if metrics["waste_assessment_count"] == 0:
        improvements.append("Assess your waste stream and boost your recycling rate.")
    if metrics["total_offsets_tonnes"] == 0 and metrics["assessment_count"] > 0:
        improvements.append(
            "Neutralize the footprint you can't reduce yet by purchasing "
            "verified carbon offsets."
        )
    if not improvements:
        improvements.append(
            "You're covering all the basics — challenge yourself with a new "
            "domain like offsets, skill tree nodes, or harder challenges."
        )
    return improvements


def get_achievements(metrics: dict[str, Any]) -> list[str]:
    """Milestones the user has unlocked, from strongest to weakest."""
    achievements = []
    if metrics["streak"] >= 30:
        achievements.append(f"🔥 {metrics['streak']}-day streak — an outstanding habit")
    elif metrics["streak"] >= 14:
        achievements.append(f"🔥 {metrics['streak']}-day streak — two weeks strong")
    elif metrics["streak"] >= 7:
        achievements.append(f"🔥 {metrics['streak']}-day logging streak")
    if metrics["completed_challenges"] >= 10:
        achievements.append(f"🏆 Completed {metrics['completed_challenges']} eco challenges")
    elif metrics["completed_challenges"] >= 5:
        achievements.append(f"🏆 Completed {metrics['completed_challenges']} eco challenges")
    elif metrics["completed_challenges"] >= 1:
        achievements.append(f"🏆 Completed {metrics['completed_challenges']} eco challenge(s)")
    if metrics["best_eco_score"] >= 85:
        achievements.append(f"🌳 Best eco score of {metrics['best_eco_score']}")
    if metrics["badges_count"] >= 4:
        achievements.append(f"🎖️ Unlocked {metrics['badges_count']} achievement badges")
    elif metrics["badges_count"] >= 1:
        achievements.append(f"🎖️ Unlocked {metrics['badges_count']} achievement badge(s)")
    if metrics["total_offsets_tonnes"] >= 10:
        achievements.append(f"🌍 Offset {metrics['total_offsets_tonnes']:.0f}+ tonnes of CO₂")
    elif metrics["total_offsets_tonnes"] > 0:
        achievements.append(f"🌍 Offset {metrics['total_offsets_tonnes']:.1f} tonnes of CO₂")
    if metrics["skill_completed_count"] >= 1:
        achievements.append(f"📚 Completed {metrics['skill_completed_count']} skill tree node(s)")
    if metrics["milestone_count"] >= 1:
        achievements.append(f"🌱 Reached {metrics['milestone_count']} environmental milestone(s)")
    if metrics["level"] >= 5:
        achievements.append(f"⭐ Reached level {metrics['level']}")
    if not achievements:
        achievements.append("Your first achievement is just an assessment away.")
    return achievements


def get_persona_next_steps(metrics: dict[str, Any], persona_id: str) -> list[str]:
    """Recommended next actions tailored to the persona and data."""
    steps = []
    if persona_id == "eco_rookie":
        steps.append("Complete your first carbon footprint assessment from the main dashboard.")
        steps.append("Explore the Eco Score & Badge system to start earning XP.")
    elif persona_id == "earth_explorer":
        steps.append("Log more assessments to sharpen your persona.")
        steps.append("Try a weekly challenge from the Gamification tab.")
    if metrics["completed_challenges"] < 5:
        steps.append("Complete 5 eco challenges to strengthen your Challenge Champion side.")
    if metrics["streak"] < 7:
        steps.append("Aim for a 7-day streak to earn the Streak Star badge.")
    if metrics["total_offsets_tonnes"] == 0:
        steps.append("Visit Route Planning & Offsets to neutralize your remaining footprint.")
    if metrics["water_assessment_count"] == 0:
        steps.append("Complete a Water Footprint assessment.")
    if metrics["waste_assessment_count"] == 0:
        steps.append("Complete a Waste Footprint assessment.")
    if not metrics["has_energy_audit"]:
        steps.append("Run a Home Energy Audit to find savings.")
    if not steps:
        steps.append("Maintain your momentum and take on an advanced skill tree node.")
    return steps


def generate_persona_profile(user_id: int) -> dict[str, Any]:
    """Build the full persona profile for a user.

    The profile recomputes from live data on every call, so it updates
    dynamically as the user's behavior changes.
    """
    metrics = analyze_user_behavior(user_id)
    persona_id = assign_persona(metrics)
    persona = dict(PERSONAS[persona_id])
    persona["rarity"] = _persona_rarity(persona_id, metrics)

    return {
        "user_id": user_id,
        "persona": persona,
        "persona_id": persona_id,
        "metrics": metrics,
        "strengths": get_strengths(metrics),
        "improvement_opportunities": get_improvement_opportunities(metrics),
        "achievements": get_achievements(metrics),
        "next_steps": get_persona_next_steps(metrics, persona_id),
        "active_domains": _active_domains(metrics),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Persona card image
# ─────────────────────────────────────────────────────────────────────────────

def generate_persona_card_png(user_id: int, profile: dict[str, Any], filename: str = "eco_persona_card.png") -> str | None:
    """Render a downloadable persona profile card as a PNG."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None

    persona = profile["persona"]
    metrics = profile["metrics"]
    rarity = persona["rarity"]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(base_dir, "assets", "fonts", "DejaVuSans.ttf")

    width, height = 560, 760
    img = Image.new("RGB", (width, height), persona["color"])
    draw = ImageDraw.Draw(img)
    accent = persona["accent"]
    text_color = persona["text_color"]

    try:
        icon_font = ImageFont.truetype(font_path, 56)
        title_font = ImageFont.truetype(font_path, 30)
        rarity_font = ImageFont.truetype(font_path, 17)
        text_font = ImageFont.truetype(font_path, 16)
        small_font = ImageFont.truetype(font_path, 13)
    except (IOError, OSError):
        icon_font = title_font = rarity_font = text_font = small_font = ImageFont.load_default()

    draw.rounded_rectangle([12, 12, width - 12, height - 12], radius=20, outline=accent, width=5)
    draw.rounded_rectangle([20, 20, width - 20, height - 20], radius=16, outline=accent, width=2)

    draw.rounded_rectangle(
        [width // 2 - 85, 34, width // 2 + 85, 66], radius=12,
        fill=accent, outline=accent, width=2,
    )
    draw.text((width // 2, 50), rarity.upper(), fill=(255, 255, 255), font=rarity_font, anchor="mm")

    draw.text((width // 2, 145), persona["icon"], fill=text_color, font=icon_font, anchor="mm")
    draw.text((width // 2, 240), persona["name"], fill=text_color, font=title_font, anchor="mm")
    draw.text((width // 2, 300), persona["tagline"], fill=(90, 100, 110), font=text_font, anchor="mm")
    draw.text((width // 2, 345), f"Focus: {persona['focus']}", fill=(110, 120, 130), font=small_font, anchor="mm")

    draw.line([(110, 390), (width - 110, 390)], fill=accent, width=3)

    stats = [
        f"Level {metrics['level']}  ·  {metrics['total_xp']} XP",
        f"Eco Score  {metrics['best_eco_score']}",
        f"Streak  {metrics['streak']} days  ·  Challenges  {metrics['completed_challenges']}",
        f"Badges  {metrics['badges_count']}  ·  Domains  {profile['active_domains']}",
    ]
    y = 420
    for line in stats:
        draw.text((width // 2, y), line, fill=text_color, font=text_font, anchor="mm")
        y += 34

    draw.text((width // 2, 640), "EcoBuddy AI · Eco Persona · User #{}".format(user_id), fill=(130, 140, 150), font=small_font, anchor="mm")
    draw.text((width // 2, 700), "Generated with EcoBuddy AI", fill=(150, 160, 170), font=small_font, anchor="mm")

    img.save(filename)
    return filename
