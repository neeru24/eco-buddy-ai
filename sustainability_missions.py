"""Sustainability Missions generated from real-world environmental events.

Generates timely eco challenges tied to real environmental events such as
Earth Day, World Environment Day, or World Water Day, tracks completion per
user, and awards bonus XP.

The module is self-contained: its SQLite table is created lazily and it uses
the existing database.award_xp helper for XP without modifying shared files.
"""

import os
import sqlite3
import logging
import datetime
from typing import Any

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

# Month-day of well-known environmental events. Uses (month, day) so the
# event fires every year without maintenance.
ENVIRONMENTAL_EVENTS = [
    {
        "key": "world_wetlands_day",
        "name": "World Wetlands Day",
        "month_day": (2, 2),
        "icon": "🌊",
        "description": "Wetlands filter water, store carbon, and host incredible biodiversity.",
        "mission": {
            "title": "Discover a Wetland Near You",
            "description": "Research a local wetland, lake, or river and identify one way it benefits your community.",
            "xp": 30,
        },
    },
    {
        "key": "world_wildlife_day",
        "name": "World Wildlife Day",
        "month_day": (3, 3),
        "icon": "🦁",
        "description": "Celebrating the world's wild animals and plants.",
        "mission": {
            "title": "Backyard Biodiversity Count",
            "description": "Spot and log 5 different wild species (birds, insects, plants) near your home.",
            "xp": 30,
        },
    },
    {
        "key": "world_water_day",
        "name": "World Water Day",
        "month_day": (3, 22),
        "icon": "💧",
        "description": "Focusing attention on the importance of freshwater and sustainable water management.",
        "mission": {
            "title": "30-Day Water Challenge",
            "description": "Cut your daily water use by 20% — shorter showers, fix a leak, or reuse cooking water.",
            "xp": 40,
        },
    },
    {
        "key": "earth_hour",
        "name": "Earth Hour",
        "month_day": (3, 29),
        "icon": "🕯️",
        "description": "A global movement encouraging individuals to switch off non-essential lights.",
        "mission": {
            "title": "Unplug for an Hour",
            "description": "Turn off all non-essential lights and electronics for a full hour today.",
            "xp": 35,
        },
    },
    {
        "key": "earth_day",
        "name": "Earth Day",
        "month_day": (4, 22),
        "icon": "🌍",
        "description": "The world's largest environmental movement, supporting action for our planet.",
        "mission": {
            "title": "Earth Day Action",
            "description": "Complete one meaningful eco action today — plant something, clean up litter, or switch to a green energy plan.",
            "xp": 50,
        },
    },
    {
        "key": "world_environment_day",
        "name": "World Environment Day",
        "month_day": (6, 5),
        "icon": "🌿",
        "description": "The UN's flagship day to encourage worldwide awareness and action for the environment.",
        "mission": {
            "title": "Plastic-Free Day",
            "description": "Avoid all single-use plastics for the entire day.",
            "xp": 45,
        },
    },
    {
        "key": "world_oceans_day",
        "name": "World Oceans Day",
        "month_day": (6, 8),
        "icon": "🐋",
        "description": "Celebrating the ocean and raising awareness about threats to marine ecosystems.",
        "mission": {
            "title": "Ocean-Friendly Choice",
            "description": "Choose sustainably sourced seafood or skip seafood entirely for one meal.",
            "xp": 30,
        },
    },
    {
        "key": "world_cleanup_day",
        "name": "World Cleanup Day",
        "month_day": (9, 20),
        "icon": "🧹",
        "description": "One of the largest civic actions in the world, uniting people to clean up litter.",
        "mission": {
            "title": "Pick Up 10 Pieces",
            "description": "Collect and properly dispose of at least 10 pieces of litter from your neighborhood.",
            "xp": 40,
        },
    },
    {
        "key": "world_car_free_day",
        "name": "World Car-Free Day",
        "month_day": (9, 22),
        "icon": "🚶",
        "description": "Encouraging motorists to give up their cars for a day in favor of alternative transport.",
        "mission": {
            "title": "Car-Free Commute",
            "description": "Travel one journey today by walking, cycling, or public transport instead of a car.",
            "xp": 35,
        },
    },
    {
        "key": "world_food_day",
        "name": "World Food Day",
        "month_day": (10, 16),
        "icon": "🍎",
        "description": "Promoting worldwide awareness and action for those who suffer from hunger.",
        "mission": {
            "title": "Zero Food Waste Meal",
            "description": "Cook a meal using only ingredients already in your home — nothing new bought, nothing wasted.",
            "xp": 40,
        },
    },
    {
        "key": "international_energy_saving_day",
        "name": "International Energy Saving Day",
        "month_day": (10, 21),
        "icon": "💡",
        "description": "A day dedicated to promoting energy-saving habits worldwide.",
        "mission": {
            "title": "Energy Audit Sprint",
            "description": "Complete a home energy audit and identify your top 3 energy hogs.",
            "xp": 35,
        },
    },
    {
        "key": "world_travel_day",
        "name": "World Travel Day",
        "month_day": (11, 5),
        "icon": "🧳",
        "description": "Celebrating travel and promoting sustainable tourism.",
        "mission": {
            "title": "Sustainable Trip Planner",
            "description": "Plan a low-impact trip — choose a train over a flight or a green-certified stay.",
            "xp": 30,
        },
    },
]

DEFAULT_DAILY_MISSIONS = [
    {
        "key": "daily_eco_log",
        "title": "Daily Eco Log",
        "description": "Log today's carbon footprint assessment to keep your data fresh.",
        "xp": 20,
    },
    {
        "key": "daily_plant_meal",
        "title": "One Plant-Based Meal",
        "description": "Swap one meat meal today for a plant-based alternative.",
        "xp": 25,
    },
]


def _event_for_date(target_date: datetime.date) -> dict[str, Any] | None:
    for event in ENVIRONMENTAL_EVENTS:
        month, day = event["month_day"]
        if (target_date.month, target_date.day) == (month, day):
            return event
    return None


def get_active_events(reference_date: datetime.date | None = None) -> dict[str, Any]:
    """Return today's event (if any) plus the next upcoming event."""
    reference_date = reference_date or datetime.date.today()
    today_event = _event_for_date(reference_date)

    upcoming = None
    for offset in range(1, 366):
        candidate = reference_date + datetime.timedelta(days=offset)
        event = _event_for_date(candidate)
        if event:
            upcoming = {"event": event, "date": candidate}
            break

    return {"today": today_event, "upcoming": upcoming}


def get_all_events() -> list[dict[str, Any]]:
    return list(ENVIRONMENTAL_EVENTS)


def _get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_missions_db() -> bool:
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS eco_missions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                mission_key TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                xp INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, mission_key)
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Eco missions init error: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def save_mission(user_id: int, mission: dict[str, Any]) -> bool:
    """Persist an event-specific mission for the user (idempotent by key)."""
    init_missions_db()
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            INSERT OR IGNORE INTO eco_missions (
                user_id, mission_key, title, description, xp
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                mission["key"],
                mission["title"],
                mission["description"],
                mission["xp"],
            ),
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Unable to save eco mission: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def get_user_missions(user_id: int) -> list[dict[str, Any]]:
    init_missions_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, mission_key, title, description, xp, status,
                   completed_at, created_at
            FROM eco_missions
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        logger.error("Unable to load eco missions: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def get_active_mission(user_id: int) -> dict[str, Any] | None:
    missions = get_user_missions(user_id)
    for mission in missions:
        if mission["status"] == "active":
            return mission
    return None


def complete_mission(user_id: int, mission_key: str) -> tuple[bool, str]:
    """Mark a mission complete and award bonus XP once."""
    init_missions_db()
    conn = None
    try:
        conn = _get_conn()
        row = conn.execute(
            """
            SELECT id, xp, status FROM eco_missions
            WHERE user_id = ? AND mission_key = ?
            """,
            (user_id, mission_key),
        ).fetchone()
        if not row or row[2] == "completed":
            return False, "Mission not found or already completed."

        conn.execute(
            """
            UPDATE eco_missions
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND mission_key = ?
            """,
            (user_id, mission_key),
        )
        conn.commit()

        from database import award_xp

        awarded = award_xp(
            user_id,
            "eco_mission",
            mission_key,
            row[1],
            f"Completed mission: {mission_key}",
        )
        return True, f"Mission complete! +{row[1]} XP awarded."
    except sqlite3.Error as exc:
        logger.error("Unable to complete eco mission: %s", exc)
        return False, "Could not complete mission."
    finally:
        if conn:
            conn.close()


def build_mission_from_event(event: dict[str, Any], reference_date: datetime.date | None = None) -> dict[str, Any]:
    reference_date = reference_date or datetime.date.today()
    mission = event["mission"]
    return {
        "key": event["key"],
        "title": f"{event['icon']} {mission['title']}",
        "description": mission["description"],
        "xp": mission["xp"],
        "event_name": event["name"],
        "event_description": event["description"],
        "event_date": f"{event['month_day'][0]:02d}/{event['month_day'][1]:02d}",
    }


def build_mission_dict(mission: dict[str, Any], key_prefix: str = "") -> dict[str, Any]:
    return {
        "key": mission["key"],
        "title": mission["title"],
        "description": mission["description"],
        "xp": mission["xp"],
    }
