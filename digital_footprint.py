"""Digital carbon footprint tracking for online activity.

Estimates the annual CO2 emissions caused by a user's digital life: video and
music streaming, video calls, cloud storage, email, social media, gaming, AI
chat usage and general web browsing.

Emissions are modelled as::

    kg CO2 = usage_amount * energy_intensity_kwh_per_unit * grid_intensity

where ``grid_intensity`` is kg CO2 per kWh. Energy intensities are split into
three stages so the UI can show where the impact actually happens:

* ``device``      - the phone/laptop/TV consuming the content
* ``network``     - fixed line and mobile data transmission
* ``datacentre``  - servers, storage and encoding

Intensity figures are derived from published estimates (IEA data centre
energy reporting, the Carbon Trust streaming methodology and the Shift
Project) and are deliberately conservative. They are documented per activity
so they can be tuned without touching the calculation logic.

The module is self-contained: its SQLite table is created lazily and no
shared files are modified.
"""

import os
import json
import sqlite3
import logging
import datetime
from typing import Any

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

# Global average grid carbon intensity in kg CO2 per kWh. Users in cleaner
# grids can override this so the estimate reflects where their devices and
# data centres actually draw power.
DEFAULT_GRID_INTENSITY = 0.475

GRID_INTENSITY_BY_REGION = {
    "Global": 0.475,
    "US": 0.386,
    "UK": 0.233,
    "EU": 0.276,
    "India": 0.708,
    "China": 0.555,
    "Nordics": 0.045,
}

DAYS_PER_YEAR = 365

# Streaming quality multipliers applied to the base streaming intensity.
# Resolution drives bitrate, which drives network and data centre energy.
STREAMING_QUALITY_FACTORS = {
    "SD (480p)": 0.4,
    "HD (720p)": 0.7,
    "Full HD (1080p)": 1.0,
    "4K (2160p)": 3.2,
}

DEFAULT_STREAMING_QUALITY = "Full HD (1080p)"

# Each activity declares the unit its usage is measured in, how that unit maps
# to a yearly quantity, and the kWh consumed per unit at each stage.
DIGITAL_ACTIVITIES = {
    "video_streaming": {
        "label": "Video streaming",
        "icon": "📺",
        "unit": "hours/day",
        "periodicity": "daily",
        "kwh_per_unit": {"device": 0.052, "network": 0.020, "datacentre": 0.005},
        "quality_sensitive": True,
        "default": 2.0,
        "max": 24.0,
        "source": "Carbon Trust (2021) streaming methodology, 1080p baseline",
    },
    "video_calls": {
        "label": "Video calls",
        "icon": "🎥",
        "unit": "hours/day",
        "periodicity": "daily",
        "kwh_per_unit": {"device": 0.030, "network": 0.023, "datacentre": 0.008},
        "quality_sensitive": False,
        "default": 1.0,
        "max": 24.0,
        "source": "Obringer et al. (2021) videoconferencing footprint",
    },
    "music_streaming": {
        "label": "Music streaming",
        "icon": "🎧",
        "unit": "hours/day",
        "periodicity": "daily",
        "kwh_per_unit": {"device": 0.006, "network": 0.002, "datacentre": 0.001},
        "quality_sensitive": False,
        "default": 1.5,
        "max": 24.0,
        "source": "Audio bitrate ~0.14 GB/h at published network intensity",
    },
    "cloud_storage": {
        "label": "Cloud storage",
        "icon": "☁️",
        "unit": "GB stored",
        "periodicity": "annual",
        "kwh_per_unit": {"device": 0.0, "network": 0.002, "datacentre": 0.018},
        "quality_sensitive": False,
        "default": 50.0,
        "max": 10000.0,
        "source": "IEA data centre energy per stored GB-year, replicated storage",
    },
    "email": {
        "label": "Email",
        "icon": "📧",
        "unit": "messages/day",
        "periodicity": "daily",
        "kwh_per_unit": {"device": 0.0012, "network": 0.0004, "datacentre": 0.0004},
        "quality_sensitive": False,
        "default": 40.0,
        "max": 2000.0,
        "source": "Berners-Lee (2010) updated for modern device efficiency",
    },
    "social_media": {
        "label": "Social media",
        "icon": "📱",
        "unit": "hours/day",
        "periodicity": "daily",
        "kwh_per_unit": {"device": 0.024, "network": 0.014, "datacentre": 0.004},
        "quality_sensitive": False,
        "default": 2.0,
        "max": 24.0,
        "source": "Mixed video/image feed at mobile network intensity",
    },
    "online_gaming": {
        "label": "Online gaming",
        "icon": "🎮",
        "unit": "hours/day",
        "periodicity": "daily",
        "kwh_per_unit": {"device": 0.120, "network": 0.008, "datacentre": 0.006},
        "quality_sensitive": False,
        "default": 1.0,
        "max": 24.0,
        "source": "Mills et al. (2019) console and gaming PC draw",
    },
    "ai_chat": {
        "label": "AI chat & image generation",
        "icon": "🤖",
        "unit": "prompts/day",
        "periodicity": "daily",
        "kwh_per_unit": {"device": 0.0002, "network": 0.0001, "datacentre": 0.0027},
        "quality_sensitive": False,
        "default": 10.0,
        "max": 1000.0,
        "source": "Published inference energy estimates for large models",
    },
    "web_browsing": {
        "label": "Web browsing",
        "icon": "🌐",
        "unit": "hours/day",
        "periodicity": "daily",
        "kwh_per_unit": {"device": 0.020, "network": 0.006, "datacentre": 0.002},
        "quality_sensitive": False,
        "default": 2.0,
        "max": 24.0,
        "source": "Average page weight at fixed line network intensity",
    },
}

STAGES = ("device", "network", "datacentre")

# Concrete actions the savings simulator can model. Each declares the
# activity it affects and the fraction of that activity's emissions removed.
REDUCTION_ACTIONS = {
    "downgrade_streaming": {
        "label": "Stream in HD instead of 4K",
        "activity": "video_streaming",
        "reduction": 0.78,
        "effort": "Low",
        "detail": "Dropping from 4K to 720p cuts streaming bitrate by roughly four fifths.",
    },
    "camera_off": {
        "label": "Turn the camera off in routine calls",
        "activity": "video_calls",
        "reduction": 0.85,
        "effort": "Low",
        "detail": "Audio-only calls avoid almost all video encoding and transmission energy.",
    },
    "cloud_cleanup": {
        "label": "Delete half of your cloud storage",
        "activity": "cloud_storage",
        "reduction": 0.50,
        "effort": "Medium",
        "detail": "Duplicate photos and old backups are stored, replicated and powered every hour of the year.",
    },
    "unsubscribe": {
        "label": "Unsubscribe from unread newsletters",
        "activity": "email",
        "reduction": 0.30,
        "effort": "Low",
        "detail": "Most inboxes carry a third more mail than the owner ever opens.",
    },
    "audio_only_music": {
        "label": "Play music without the video player",
        "activity": "music_streaming",
        "reduction": 0.40,
        "effort": "Low",
        "detail": "Streaming audio through a video app pulls a video stream you never watch.",
    },
    "social_limit": {
        "label": "Cut social media time by a third",
        "activity": "social_media",
        "reduction": 0.33,
        "effort": "Medium",
        "detail": "Autoplaying video feeds are the heaviest part of a mobile data diet.",
    },
    "batch_ai": {
        "label": "Batch AI prompts instead of retrying",
        "activity": "ai_chat",
        "reduction": 0.35,
        "effort": "Low",
        "detail": "One well-formed prompt costs far less than five iterations of the same question.",
    },
}

# Per-activity tips, shown in the order the user's own breakdown ranks them.
DIGITAL_TIPS = {
    "video_streaming": [
        "Match streaming quality to your screen - 4K on a phone is invisible but costs three times as much energy.",
        "Turn off autoplay so you stop streaming when you stop watching.",
        "Download shows you rewatch instead of streaming them again each time.",
    ],
    "video_calls": [
        "Default to camera-off for large internal meetings.",
        "Dial into long calls by audio when you are only listening.",
        "Shorten recurring meetings - half the call is half the footprint.",
    ],
    "music_streaming": [
        "Download favourite albums once instead of streaming them daily.",
        "Use an audio app rather than a video app for background music.",
    ],
    "cloud_storage": [
        "Delete duplicate photos and old device backups - stored data draws power every hour.",
        "Empty cloud trash folders; deleted files often stay billed and powered for 30 days.",
        "Turn off automatic video backup for footage you never revisit.",
    ],
    "email": [
        "Unsubscribe from newsletters you never open.",
        "Skip the reply-all thank-you on large threads.",
        "Share a link instead of attaching large files to many recipients.",
    ],
    "social_media": [
        "Disable video autoplay in your feed settings.",
        "Use the mobile web instead of the app for occasional browsing.",
    ],
    "online_gaming": [
        "Enable your console's power-saving mode instead of leaving it in standby.",
        "Cap the frame rate when you are not playing competitively.",
    ],
    "ai_chat": [
        "Give the model full context in one prompt instead of iterating five times.",
        "Use text generation rather than image generation when either would do.",
    ],
    "web_browsing": [
        "Bookmark sites you visit daily instead of searching for them each time.",
        "Close idle tabs that keep polling for updates in the background.",
    ],
}

# Relatable equivalents, all in kg CO2.
KG_CO2_PER_KM_DRIVEN = 0.21
KG_CO2_ABSORBED_PER_TREE_YEAR = 21.0
KG_CO2_PER_SMARTPHONE_CHARGE = 0.008


def get_streaming_quality_factor(quality: str) -> float:
    """Return the bitrate multiplier for a streaming quality label."""
    if not quality:
        return STREAMING_QUALITY_FACTORS[DEFAULT_STREAMING_QUALITY]
    return STREAMING_QUALITY_FACTORS.get(
        quality, STREAMING_QUALITY_FACTORS[DEFAULT_STREAMING_QUALITY]
    )


def list_activities() -> list[dict[str, Any]]:
    """Return the activity catalogue as a list of dicts including the key."""
    return [dict(info, key=key) for key, info in DIGITAL_ACTIVITIES.items()]


def default_usage() -> dict[str, float]:
    """Return a usage dict pre-filled with typical values."""
    return {key: info["default"] for key, info in DIGITAL_ACTIVITIES.items()}


def get_grid_intensity(region: str | None = None) -> float:
    """Return the grid carbon intensity for a region, falling back to global."""
    if not region:
        return DEFAULT_GRID_INTENSITY
    return GRID_INTENSITY_BY_REGION.get(region, DEFAULT_GRID_INTENSITY)


def _sanitize_amount(activity_key: str, amount: Any) -> float:
    """Clamp a raw usage amount into the activity's valid range."""
    info = DIGITAL_ACTIVITIES[activity_key]
    try:
        value = float(amount)
    except (TypeError, ValueError):
        return 0.0
    if value != value or value in (float("inf"), float("-inf")):
        return 0.0
    return max(0.0, min(value, info["max"]))


def _annual_units(activity_key: str, amount: float) -> float:
    """Convert a usage amount into the yearly quantity used for the maths."""
    info = DIGITAL_ACTIVITIES[activity_key]
    if info["periodicity"] == "daily":
        return amount * DAYS_PER_YEAR
    return amount


def activity_emissions(activity_key: str, amount: float, grid_intensity: float | None = None, quality: str | None = None) -> dict[str, Any]:
    """Return the annual kg CO2 for a single activity, split by stage.

    ``amount`` is expressed in the activity's own unit (hours/day, GB, ...).
    """
    if activity_key not in DIGITAL_ACTIVITIES:
        raise KeyError(f"Unknown digital activity: {activity_key}")

    info = DIGITAL_ACTIVITIES[activity_key]
    intensity = grid_intensity if grid_intensity is not None else DEFAULT_GRID_INTENSITY
    intensity = max(0.0, float(intensity))

    clean_amount = _sanitize_amount(activity_key, amount)
    units = _annual_units(activity_key, clean_amount)

    multiplier = 1.0
    if info["quality_sensitive"]:
        multiplier = get_streaming_quality_factor(quality)

    stages = {}
    for stage in STAGES:
        kwh = units * info["kwh_per_unit"][stage] * multiplier
        stages[stage] = round(kwh * intensity, 3)

    total_kwh = sum(
        units * info["kwh_per_unit"][stage] * multiplier for stage in STAGES
    )

    return {
        "key": activity_key,
        "label": info["label"],
        "icon": info["icon"],
        "unit": info["unit"],
        "amount": round(clean_amount, 3),
        "annual_units": round(units, 2),
        "quality_multiplier": round(multiplier, 3),
        "annual_kwh": round(total_kwh, 3),
        "annual_kg": round(total_kwh * intensity, 3),
        "stages": stages,
    }


def calculate_digital_footprint(usage: dict[str, Any], grid_intensity: float | None = None, streaming_quality: str | None = None) -> dict[str, Any]:
    """Calculate the full annual digital footprint for a usage dict.

    ``usage`` maps activity keys to amounts in each activity's own unit.
    Unknown keys are ignored, missing keys count as zero.
    """
    usage = usage or {}
    intensity = grid_intensity if grid_intensity is not None else DEFAULT_GRID_INTENSITY

    breakdown = {}
    total_kg = 0.0
    total_kwh = 0.0
    stage_totals = {stage: 0.0 for stage in STAGES}

    for key in DIGITAL_ACTIVITIES:
        result = activity_emissions(
            key, usage.get(key, 0.0), intensity, streaming_quality
        )
        breakdown[key] = result
        total_kg += result["annual_kg"]
        total_kwh += result["annual_kwh"]
        for stage in STAGES:
            stage_totals[stage] += result["stages"][stage]

    for result in breakdown.values():
        result["share_pct"] = (
            round(result["annual_kg"] / total_kg * 100, 1) if total_kg > 0 else 0.0
        )

    ranked = sorted(
        breakdown.values(), key=lambda item: item["annual_kg"], reverse=True
    )

    return {
        "annual_kg": round(total_kg, 2),
        "monthly_kg": round(total_kg / 12, 2),
        "daily_kg": round(total_kg / DAYS_PER_YEAR, 3),
        "annual_kwh": round(total_kwh, 2),
        "grid_intensity": round(float(intensity), 4),
        "streaming_quality": streaming_quality or DEFAULT_STREAMING_QUALITY,
        "breakdown": breakdown,
        "ranked": ranked,
        "stage_totals": {k: round(v, 2) for k, v in stage_totals.items()},
        "top_activity": ranked[0]["key"] if ranked and ranked[0]["annual_kg"] > 0 else None,
    }


def estimate_savings(usage: dict[str, Any], actions: list[str], grid_intensity: float | None = None, streaming_quality: str | None = None) -> dict[str, Any]:
    """Estimate the CO2 saved by applying a set of reduction actions."""
    baseline = calculate_digital_footprint(usage, grid_intensity, streaming_quality)
    action_keys = [key for key in (actions or []) if key in REDUCTION_ACTIONS]

    details = []
    for key in action_keys:
        action = REDUCTION_ACTIONS[key]
        current = baseline["breakdown"][action["activity"]]["annual_kg"]
        saved = current * action["reduction"]
        details.append(
            {
                "key": key,
                "label": action["label"],
                "activity": action["activity"],
                "effort": action["effort"],
                "detail": action["detail"],
                "current_kg": round(current, 2),
                "saved_kg": round(saved, 2),
            }
        )

    details.sort(key=lambda item: item["saved_kg"], reverse=True)
    total_saved = sum(item["saved_kg"] for item in details)
    total_saved = min(total_saved, baseline["annual_kg"])

    projected = max(0.0, baseline["annual_kg"] - total_saved)
    reduction_pct = (
        round(total_saved / baseline["annual_kg"] * 100, 1)
        if baseline["annual_kg"] > 0
        else 0.0
    )

    return {
        "baseline_kg": baseline["annual_kg"],
        "projected_kg": round(projected, 2),
        "total_saved_kg": round(total_saved, 2),
        "reduction_pct": reduction_pct,
        "actions": details,
    }


def recommend_actions(result: dict[str, Any], limit: int = 3) -> list[dict[str, Any]]:
    """Suggest the reduction actions that matter most for this user."""
    breakdown = result.get("breakdown", {})
    candidates = []
    for key, action in REDUCTION_ACTIONS.items():
        current = breakdown.get(action["activity"], {}).get("annual_kg", 0.0)
        if current <= 0:
            continue
        candidates.append(
            {
                "key": key,
                "label": action["label"],
                "activity": action["activity"],
                "effort": action["effort"],
                "detail": action["detail"],
                "saved_kg": round(current * action["reduction"], 2),
            }
        )
    candidates.sort(key=lambda item: item["saved_kg"], reverse=True)
    return candidates[: max(0, int(limit))]


def get_digital_tips(result: dict[str, Any], limit: int = 6) -> list[dict[str, Any]]:
    """Return tips ordered by the user's own highest-impact activities."""
    tips = []
    for activity in result.get("ranked", []):
        if activity["annual_kg"] <= 0:
            continue
        for tip in DIGITAL_TIPS.get(activity["key"], []):
            tips.append(
                {
                    "activity": activity["key"],
                    "label": activity["label"],
                    "icon": activity["icon"],
                    "tip": tip,
                }
            )
        if len(tips) >= limit:
            break
    return tips[: max(0, int(limit))]


def compare_to_physical(annual_kg: float) -> dict[str, float | int]:
    """Translate a digital footprint into relatable physical equivalents."""
    annual_kg = max(0.0, float(annual_kg or 0.0))
    return {
        "km_driven": round(annual_kg / KG_CO2_PER_KM_DRIVEN, 1),
        "trees_to_offset": round(annual_kg / KG_CO2_ABSORBED_PER_TREE_YEAR, 2),
        "phone_charges": round(annual_kg / KG_CO2_PER_SMARTPHONE_CHARGE),
    }


def _get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_digital_footprint_db() -> bool:
    """Create the digital footprint table if it does not exist yet."""
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS digital_footprint_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                annual_kg REAL NOT NULL,
                annual_kwh REAL NOT NULL,
                grid_intensity REAL NOT NULL,
                streaming_quality TEXT,
                usage_json TEXT NOT NULL,
                breakdown_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Digital footprint init error: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def save_digital_assessment(user_id: int, usage: dict[str, Any], result: dict[str, Any]) -> int | None:
    """Persist one digital footprint assessment. Returns the new row id."""
    init_digital_footprint_db()
    conn = None
    try:
        summary = {
            key: {
                "annual_kg": item["annual_kg"],
                "share_pct": item.get("share_pct", 0.0),
            }
            for key, item in result.get("breakdown", {}).items()
        }
        conn = _get_conn()
        cursor = conn.execute(
            """
            INSERT INTO digital_footprint_assessments (
                user_id, annual_kg, annual_kwh, grid_intensity,
                streaming_quality, usage_json, breakdown_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                result.get("annual_kg", 0.0),
                result.get("annual_kwh", 0.0),
                result.get("grid_intensity", DEFAULT_GRID_INTENSITY),
                result.get("streaming_quality", DEFAULT_STREAMING_QUALITY),
                json.dumps(usage or {}),
                json.dumps(summary),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as exc:
        logger.error("Unable to save digital assessment: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def get_digital_assessments(user_id: int, limit: int = 50) -> list[dict[str, Any]]:
    """Return a user's saved digital assessments, newest first."""
    init_digital_footprint_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, annual_kg, annual_kwh, grid_intensity, streaming_quality,
                   usage_json, breakdown_json, created_at
            FROM digital_footprint_assessments
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT ?
            """,
            (user_id, int(limit)),
        ).fetchall()

        assessments = []
        for row in rows:
            record = dict(row)
            record["usage"] = _safe_json(record.pop("usage_json"))
            record["breakdown"] = _safe_json(record.pop("breakdown_json"))
            assessments.append(record)
        return assessments
    except sqlite3.Error as exc:
        logger.error("Unable to load digital assessments: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def _safe_json(raw: Any) -> Any:
    try:
        return json.loads(raw) if raw else {}
    except (TypeError, ValueError):
        return {}


def get_digital_trend(user_id: int, limit: int = 12) -> dict[str, Any]:
    """Return a chronological trend series plus the change since the first entry."""
    assessments = get_digital_assessments(user_id, limit=limit)
    series = [
        {
            "date": item.get("created_at"),
            "annual_kg": item.get("annual_kg", 0.0),
        }
        for item in reversed(assessments)
    ]

    change_kg = 0.0
    change_pct = 0.0
    if len(series) >= 2:
        first = series[0]["annual_kg"]
        last = series[-1]["annual_kg"]
        change_kg = round(last - first, 2)
        if first > 0:
            change_pct = round((last - first) / first * 100, 1)

    return {
        "series": series,
        "entries": len(series),
        "change_kg": change_kg,
        "change_pct": change_pct,
        "improving": change_kg < 0,
    }


def delete_digital_assessment(assessment_id: int) -> bool:
    """Delete a single saved assessment."""
    init_digital_footprint_db()
    conn = None
    try:
        conn = _get_conn()
        cursor = conn.execute(
            "DELETE FROM digital_footprint_assessments WHERE id = ?",
            (assessment_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as exc:
        logger.error("Unable to delete digital assessment: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def build_summary_text(result: dict[str, Any]) -> str:
    """Build a short human readable summary of a digital footprint result."""
    annual = result.get("annual_kg", 0.0)
    equivalents = compare_to_physical(annual)
    top_key = result.get("top_activity")

    if not top_key:
        return "No digital activity recorded yet - add your usage to see an estimate."

    top = result["breakdown"][top_key]
    return (
        f"Your digital life emits about {annual:,.1f} kg CO2 a year - "
        f"the same as driving {equivalents['km_driven']:,.0f} km. "
        f"{top['label']} is your biggest contributor at {top['share_pct']}% "
        f"({top['annual_kg']:,.1f} kg)."
    )


def usage_from_assessment(assessment: dict[str, Any]) -> dict[str, float]:
    """Rebuild a usage dict from a saved assessment row."""
    stored = (assessment or {}).get("usage", {})
    usage = default_usage()
    for key in usage:
        if key in stored:
            usage[key] = _sanitize_amount(key, stored[key])
    return usage


def today_iso() -> str:
    """Return today's date as an ISO string (kept here for easy patching)."""
    return datetime.date.today().isoformat()
