"""Peer-to-Peer Carpooling & Green Commute Matching.

Matches users with nearby commuters traveling the same route at the same
time, encouraging carpooling as a low-carbon alternative to solo driving.
Each shared trip records the emissions avoided vs. driving alone.

The module is self-contained: its SQLite tables are created lazily and it
reuses existing transport emission factors via database read-only helpers.
"""

import os
import math
import sqlite3
import logging
import datetime

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

DEFAULT_SPEED_KMH = 30.0

# References used by the emission estimate. Values in kg CO2 / km.
CAR_EMISSION_PER_KM = 0.19
PUBLIC_TRANSIT_EMISSION_PER_KM = 0.07

SAFETY_PREFERENCES = ["verified_users_only", "same_gender", "no_smoking", "pet_friendly"]


def _emissions_avoided(distance_km, car_kg_per_km=CAR_EMISSION_PER_KM):
    """kg CO2 avoided per shared trip vs driving solo."""
    return round(max(distance_km * car_kg_per_km, 0.0), 3)


def _route_overlap(distance_km):
    """Rough route proximity heuristic (0-1). Longer routes allow more flex."""
    return min(max(1.0 - (distance_km * 0.02), 0.3), 1.0)


def _time_compatibility(minutes_diff):
    """Score how well departure windows align (0-1)."""
    return max(0.0, 1.0 - (minutes_diff / 60.0))


def match_commuters(user_profile, candidates, max_results=10):
    """Rank candidate commuters by route/time overlap and preference fit.

    Each result includes a match score (0-100) and the emissions avoided if
    the pair shares one trip.
    """
    if not user_profile or not candidates:
        return []

    user_lat, user_lng = user_profile.get("origin_lat"), user_profile.get("origin_lng")
    user_time = user_profile.get("departure_minutes")

    scored = []
    for cand in candidates:
        score_components = []
        distance_km = None

        # Route overlap
        if user_lat is not None and user_lng is not None and "origin_lat" in cand:
            distance_km = _haversine_km(
                user_lat, user_lng, cand.get("origin_lat"), cand.get("origin_lng")
            )
            score_components.append(_route_overlap(distance_km) * 50.0)

        # Time compatibility
        if user_time is not None and "departure_minutes" in cand:
            diff = abs(user_time - cand["departure_minutes"])
            if diff > 720:
                diff = 1440 - diff
            score_components.append(_time_compatibility(diff) * 35.0)

        # Preference fit (count of shared safety preferences)
        user_prefs = set(user_profile.get("preferences", []))
        cand_prefs = set(cand.get("preferences", []))
        if user_prefs:
            overlap_pct = len(user_prefs & cand_prefs) / len(user_prefs)
            score_components.append(overlap_pct * 15.0)

        total = round(sum(score_components), 1) if score_components else 0.0
        avoided = _emissions_avoided(cand.get("distance_km") or distance_km or 0.0)

        scored.append({
            "commuter": cand,
            "match_score": total,
            "distance_km": round(distance_km, 1) if distance_km is not None else None,
            "emissions_avoided_kg": avoided,
        })

    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return scored[:max_results]


def _haversine_km(lat1, lng1, lat2, lng2):
    """Great-circle distance between two coordinates in km."""
    try:
        lat1, lng1, lat2, lng2 = float(lat1), float(lng1), float(lat2), float(lng2)
    except (TypeError, ValueError):
        return None

    radius = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def _get_conn():
    return sqlite3.connect(DB_NAME)


def init_carpool_db():
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS commute_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                origin_name TEXT NOT NULL,
                destination_name TEXT NOT NULL,
                origin_lat REAL,
                origin_lng REAL,
                destination_lat REAL,
                destination_lng REAL,
                distance_km REAL NOT NULL,
                departure_time TEXT NOT NULL,
                departure_minutes INTEGER NOT NULL,
                weekly_days TEXT NOT NULL,
                preferences TEXT NOT NULL,
                is_driver INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shared_trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_user_id INTEGER NOT NULL,
                passenger_user_id INTEGER NOT NULL,
                distance_km REAL NOT NULL,
                emissions_avoided_kg REAL NOT NULL,
                trip_date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Carpool init error: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def _profile_to_dict(row):
    return {
        "id": row[0],
        "user_id": row[1],
        "origin_name": row[2],
        "destination_name": row[3],
        "origin_lat": row[4],
        "origin_lng": row[5],
        "destination_lat": row[6],
        "destination_lng": row[7],
        "distance_km": row[8],
        "departure_time": row[9],
        "departure_minutes": row[10],
        "weekly_days": row[11],
        "preferences": row[12].split(",") if row[12] else [],
        "is_driver": bool(row[13]),
        "created_at": row[14],
    }


def save_commute_profile(user_id, profile):
    """Insert or update the user's commute profile (one per user)."""
    init_carpool_db()
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            INSERT INTO commute_profiles (
                user_id, origin_name, destination_name, origin_lat, origin_lng,
                destination_lat, destination_lng, distance_km, departure_time,
                departure_minutes, weekly_days, preferences, is_driver
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                origin_name = excluded.origin_name,
                destination_name = excluded.destination_name,
                origin_lat = excluded.origin_lat,
                origin_lng = excluded.origin_lng,
                destination_lat = excluded.destination_lat,
                destination_lng = excluded.destination_lng,
                distance_km = excluded.distance_km,
                departure_time = excluded.departure_time,
                departure_minutes = excluded.departure_minutes,
                weekly_days = excluded.weekly_days,
                preferences = excluded.preferences,
                is_driver = excluded.is_driver
            """,
            (
                user_id,
                profile.get("origin_name", ""),
                profile.get("destination_name", ""),
                profile.get("origin_lat"),
                profile.get("origin_lng"),
                profile.get("destination_lat"),
                profile.get("destination_lng"),
                profile.get("distance_km", 0.0),
                profile.get("departure_time", "08:00"),
                profile.get("departure_minutes", 480),
                profile.get("weekly_days", "Mon,Wed,Fri"),
                ",".join(profile.get("preferences", [])),
                1 if profile.get("is_driver") else 0,
            ),
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Unable to save commute profile: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def get_commute_profile(user_id):
    init_carpool_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM commute_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None
    except sqlite3.Error as exc:
        logger.error("Unable to load commute profile: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def get_commute_profiles(exclude_user_id=None):
    init_carpool_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        query = "SELECT * FROM commute_profiles"
        params = []
        if exclude_user_id is not None:
            query += " WHERE user_id != ?"
            params.append(exclude_user_id)
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        logger.error("Unable to load commute profiles: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def record_shared_trip(driver_user_id, passenger_user_id, distance_km, trip_date=None):
    """Record a completed shared ride and its emissions avoidance."""
    init_carpool_db()
    conn = None
    try:
        conn = _get_conn()
        avoided = _emissions_avoided(distance_km)
        trip_date = trip_date or datetime.date.today().isoformat()
        conn.execute(
            """
            INSERT INTO shared_trips (
                driver_user_id, passenger_user_id, distance_km, emissions_avoided_kg, trip_date
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (driver_user_id, passenger_user_id, distance_km, avoided, trip_date),
        )
        conn.commit()
        return avoided
    except sqlite3.Error as exc:
        logger.error("Unable to record shared trip: %s", exc)
        return 0.0
    finally:
        if conn:
            conn.close()


def get_total_emissions_avoided(user_id):
    """Total kg CO2 the user avoided by carpooling (as driver or passenger)."""
    init_carpool_db()
    conn = None
    try:
        conn = _get_conn()
        row = conn.execute(
            """
            SELECT COALESCE(SUM(emissions_avoided_kg), 0)
            FROM shared_trips
            WHERE driver_user_id = ? OR passenger_user_id = ?
            """,
            (user_id, user_id),
        ).fetchone()
        return round(row[0], 2)
    except sqlite3.Error as exc:
        logger.error("Unable to load emissions avoided: %s", exc)
        return 0.0
    finally:
        if conn:
            conn.close()


def get_shared_trips(user_id, limit=20):
    init_carpool_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, driver_user_id, passenger_user_id, distance_km,
                   emissions_avoided_kg, trip_date, created_at
            FROM shared_trips
            WHERE driver_user_id = ? OR passenger_user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, user_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        logger.error("Unable to load shared trips: %s", exc)
        return []
    finally:
        if conn:
            conn.close()