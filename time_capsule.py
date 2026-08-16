from datetime import datetime, date
from typing import Sequence

import streamlit as st

from database import (
    get_time_capsules,
    update_time_capsule_unlock,
    update_time_capsule_progress,
    get_assessments,
    award_xp,
)

CAPSULE_CATEGORIES = {
    "general": "🌍 General",
    "transport": "🚗 Transport",
    "energy": "⚡ Energy",
    "diet": "🥗 Diet",
    "waste": "♻️ Waste",
    "water": "💧 Water",
}

CAPSULE_XP_REWARD = 25


def check_and_unlock_capsules(user_id: int) -> list[dict]:
    capsules = get_time_capsules(user_id)
    today = date.today()
    newly_unlocked = []

    for capsule in capsules:
        if capsule["is_unlocked"]:
            continue
        try:
            unlock = datetime.strptime(capsule["unlock_date"], "%Y-%m-%d").date()
            if unlock <= today:
                update_time_capsule_unlock(capsule["id"])
                capsule["is_unlocked"] = 1
                award_xp(
                    user_id, "time_capsule", str(capsule["id"]),
                    CAPSULE_XP_REWARD, f"Time Capsule unlocked: {capsule['title']}"
                )
                newly_unlocked.append(capsule)
        except (ValueError, TypeError):
            continue

    return newly_unlocked


def get_progress_summary(user_id: int) -> dict:
    assessments = get_assessments(user_id)
    if not assessments:
        return {}

    scores = [row[8] for row in assessments if len(row) > 8 and row[8] is not None]
    footprints = [row[7] for row in assessments if len(row) > 7 and row[7] is not None]

    return {
        "total_assessments": len(assessments),
        "latest_eco_score": scores[0] if scores else None,
        "best_eco_score": max(scores) if scores else None,
        "latest_footprint": footprints[0] if footprints else None,
        "lowest_footprint": min(footprints) if footprints else None,
    }


def generate_comparison(capsule: dict, progress: dict) -> str | None:
    if not progress:
        return None

    lines = []
    eco_score = progress.get("latest_eco_score")
    if eco_score is not None:
        lines.append(f"Your latest Eco Score is **{eco_score}/100**.")
    best = progress.get("best_eco_score")
    if best is not None:
        lines.append(f"Your best Eco Score ever was **{best}/100**.")
    footprint = progress.get("latest_footprint")
    if footprint is not None:
        lines.append(f"Your latest carbon footprint was **{footprint:.0f} kg CO₂**.")
    lowest = progress.get("lowest_footprint")
    if lowest is not None:
        lines.append(f"Your lowest carbon footprint was **{lowest:.0f} kg CO₂**.")
    total = progress.get("total_assessments")
    if total is not None:
        lines.append(f"You've completed **{total}** assessments in total.")

    return "\n\n".join(lines) if lines else None
