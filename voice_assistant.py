"""Voice-Activated Eco Assistant.

Lets users log daily eco-activities hands-free by speaking natural phrases
such as "I drove 10 km to work today" or "I recycled a plastic bottle".

Pipeline:
  1. Transcribe speech -> text (Groq Whisper when GROQ_API_KEY is set, or the
     browser Web Speech API via the page layer).
  2. Parse the transcript into structured activity data, extending the
     llm_parser.py approach to handle spoken-style phrasing and disfluencies
     ("um", "like", "about").
  3. Present a confirmation summary; only save after the user confirms.
  4. Persist using the same database functions as manual entry so voice logs
     are stored identically.

Self-contained SQLite table for voice log history. Uses database helpers for
persistence without modifying shared files.
"""

import os
import io
import json
import time
import logging
import sqlite3
from typing import Any

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

TRANSCRIPTION_MODEL = "whisper-large-v3-turbo"

# Common voice prompts the assistant can read aloud / suggest.
VOICE_PROMPTS = [
    "Log my assessment",
    "I drove 10 km to work today",
    "I recycled a plastic bottle",
    "Log my water use",
    "Complete a mission",
]

# Privacy notice shown wherever audio is captured.
PRIVACY_NOTICE = (
    "Voice is processed to produce a transcript only. Audio recorded with "
    "the browser is transcribed locally by your browser (Web Speech API) or "
    "sent to the configured cloud transcription provider for a few seconds; "
    "no audio is stored by Eco Buddy and transcripts are saved only after you "
    "confirm them."
)

# Transport aliases for spoken phrasing.
_TRANSPORT_ALIASES = {
    "car": "Car", "drove": "Car", "drive": "Car", "vehicle": "Car",
    "taxi": "Car", "uber": "Car", "auto": "Car",
    "bike": "Bike", "cycled": "Bike", "cycle": "Bike", "bicycle": "Bike", "motorcycle": "Bike",
    "bus": "Public Transport", "train": "Public Transport", "metro": "Public Transport",
    "subway": "Public Transport", "public transport": "Public Transport",
    "walk": "Walking", "walked": "Walking", "on foot": "Walking",
}

_DIET_ALIASES = {
    "vegan": "Vegan", "vegetarian": "Vegetarian", "veg": "Vegetarian",
    "non vegetarian": "Non-Vegetarian", "non-vegetarian": "Non-Vegetarian",
    "meat": "Non-Vegetarian", "omnivore": "Omnivore", "heavy meat": "Heavy Meat",
}

_RECYCLING_ITEMS = {
    "plastic bottle": "Plastic Packaging",
    "plastic": "Plastic Packaging",
    "bottle": "Plastic Packaging",
    "can": "Metal (Cans)",
    "soda can": "Metal (Cans)",
    "aluminum": "Metal (Cans)",
    "tin": "Metal (Cans)",
    "glass": "Glass",
    "paper": "Paper & Cardboard",
    "cardboard": "Paper & Cardboard",
    "box": "Paper & Cardboard",
    "food": "Food Scraps",
    "food scraps": "Food Scraps",
    "leftover": "Food Scraps",
    "electronics": "Electronics (E-Waste)",
    "e waste": "Electronics (E-Waste)",
    "phone": "Electronics (E-Waste)",
    "clothes": "Textiles",
    "clothing": "Textiles",
    "textiles": "Textiles",
}

# Minimal disfluency/filler words to strip before parsing.
_FILLERS = ("um", "uh", "er", "like", "hmm", "you know", "basically", "so ")


def _get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_voice_logs_db() -> bool:
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS voice_command_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                raw_text TEXT NOT NULL,
                action_type TEXT NOT NULL,
                parsed TEXT NOT NULL,
                confirmed INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Voice logs init error: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# Step 1: Speech-to-text
# ---------------------------------------------------------------------------
def transcribe_audio(audio_bytes: bytes, filename: str = "recording.webm") -> str | None:
    """Transcribe audio bytes using Groq Whisper.

    Returns the transcript text, or None if no GROQ_API_KEY is configured or
    the request fails. The page layer falls back to browser Web Speech API and
    finally to plain text input.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        import requests
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}
        files = {"file": (filename, io.BytesIO(audio_bytes), "audio/webm")}
        data = {"model": TRANSCRIPTION_MODEL, "language": "en"}
        from request_logging import log_api_request
        response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
        log_api_request("POST", url, headers=headers, status_code=response.status_code)
        if response.status_code == 200:
            return (response.json().get("text") or "").strip() or None
        logger.warning("Transcription error: %s", response.text[:300])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Transcription exception: %s", exc)
    return None


# ---------------------------------------------------------------------------
# Step 2: Parse spoken text into structured data
# ---------------------------------------------------------------------------
def _clean_spoken_text(text: str) -> str:
    """Normalize spoken phrasing: lowercase, strip fillers and extra spaces."""
    cleaned = " ".join(text.lower().split())
    for filler in _FILLERS:
        cleaned = cleaned.replace(f" {filler} ", " ").replace(f" {filler}.", " ")
    return " ".join(cleaned.split())


def _extract_number(text: str) -> float | None:
    """Extract the first number (decimal or integer) from text."""
    import re
    match = re.search(r"\d+(?:\.\d+)?", text)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None


def _parse_transport(text: str) -> dict[str, Any] | None:
    import re
    for alias, canonical in _TRANSPORT_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", text):
            distance = _extract_number(text)
            if "mile" in text and distance is not None:
                distance = round(distance * 1.60934, 2)
            return {
                "action_type": "transport",
                "transport": canonical,
                "distance": distance or 10.0,
            }
    return None


def _parse_water(text: str) -> dict[str, Any] | None:
    if "shower" in text:
        return {
            "action_type": "water",
            "activity": "shower",
            "shower_minutes": _extract_number(text) or 8.0,
        }
    if "laundry" in text or "wash" in text and "clothes" in text:
        return {"action_type": "water", "activity": "laundry", "laundry_loads": _extract_number(text) or 1.0}
    if "dish" in text or "dishes" in text:
        return {"action_type": "water", "activity": "dishes", "dishwasher_runs": _extract_number(text) or 1.0}
    return None


def _parse_recycling(text: str) -> dict[str, Any] | None:
    import re
    if not any(k in text for k in ("recycl", "compost", "bin", "throw", "dispose", "waste")):
        return None
    for keyword, category in _RECYCLING_ITEMS.items():
        if re.search(rf"\b{re.escape(keyword)}\b", text):
            qty = _extract_number(text)
            return {
                "action_type": "recycling",
                "item": category,
                "quantity_kg": qty or 0.1,
            }
    return None


def _parse_mission(text: str) -> dict[str, Any] | None:
    if not any(k in text for k in ("mission", "challenge", "complete")):
        return None
    return {"action_type": "mission", "mission_hint": text.strip()}


def parse_voice_command(text: str) -> dict[str, Any]:
    """Parse spoken-style phrasing into structured activity data.

    Tries Gemini/Groq first (best at disfluencies), then falls back to a
    deterministic keyword parser so voice logging works without any API keys.
    """
    cleaned = _clean_spoken_text(text)
    if not cleaned:
        return {"action_type": "unknown", "raw": text}

    parsed = _try_llm_parse(cleaned)
    if parsed and parsed.get("action_type") != "unknown":
        parsed["source"] = "llm"
        return parsed

    for parser in (_parse_transport, _parse_water, _parse_recycling, _parse_mission):
        result = parser(cleaned)
        if result:
            result["source"] = "keyword"
            return result

    return {"action_type": "unknown", "raw": text}


def _try_llm_parse(text: str) -> dict[str, Any] | None:
    """Optional LLM parse reusing the Gemini+Groq provider pattern."""
    try:
        import requests
        import json as _json
    except ImportError:  # noqa: BLE001
        return None

    system_prompt = (
        "You turn spoken eco-logging phrases into a structured JSON object. "
        "Handle fillers and rephrasing. Return EXACTLY one of these shapes "
        "based on the intent:\n"
        '{"action_type": "transport", "transport": "Car|Bike|Public Transport|Walking", "distance": float}\n'
        '{"action_type": "water", "activity": "shower|laundry|dishes", "minutes": float, "loads": float}\n'
        '{"action_type": "recycling", "item": "<waste category>", "quantity_kg": float}\n'
        '{"action_type": "mission", "mission_hint": "<short description>"}\n'
        'If unclear return {"action_type": "unknown"}. Output ONLY JSON.'
    )

    for env_var, url, headers, payload_builder in (
        (
            "GEMINI_API_KEY",
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}",
            {},
            None,
        ),
        (
            "GROQ_API_KEY",
            "https://api.groq.com/openai/v1/chat/completions",
            {"Content-Type": "application/json"},
            None,
        ),
    ):
        api_key = os.environ.get(env_var)
        if not api_key:
            continue
        try:
            from request_logging import log_api_request
            if env_var == "GEMINI_API_KEY":
                payload = {
                    "systemInstruction": {"parts": [{"text": system_prompt}]},
                    "contents": [{"parts": [{"text": text}]}],
                    "generationConfig": {"responseMimeType": "application/json"},
                }
                url = url.format(key=api_key)
            else:
                payload = {
                    "model": "llama3-8b-8192",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text},
                    ],
                    "response_format": {"type": "json_object"},
                }
                headers["Authorization"] = f"Bearer {api_key}"
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            log_api_request("POST", url, headers=headers, status_code=response.status_code)
            if response.status_code == 200:
                data = response.json()
                if env_var == "GEMINI_API_KEY":
                    raw = data["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    raw = data["choices"][0]["message"]["content"]
                parsed = _json.loads(raw)
                if isinstance(parsed, dict):
                    return parsed
        except Exception as exc:  # noqa: BLE001
            logger.warning("Voice LLM parse failed (%s): %s", env_var, exc)
    return None


# ---------------------------------------------------------------------------
# Step 3/4: Confirmation + persistence
# ---------------------------------------------------------------------------
def build_confirmation_summary(parsed: dict[str, Any]) -> str:
    """Human-readable summary shown before saving."""
    action = parsed.get("action_type")
    if action == "transport":
        return f"Log a **{parsed.get('distance')} km** trip by **{parsed.get('transport')}**."
    if action == "water":
        return f"Log **{parsed.get('activity')}** ({parsed.get('shower_minutes') or parsed.get('minutes') or ''} min)."
    if action == "recycling":
        return f"Log **{parsed.get('quantity_kg')} kg** of **{parsed.get('item')}** recycled."
    if action == "mission":
        return f"Complete mission: *{parsed.get('mission_hint', '')}*"
    return "I couldn't parse that into a supported action."


def save_voice_log(user_id: int, parsed: dict[str, Any]) -> tuple[bool, str]:
    """Persist a confirmed voice log identically to manual entry.

    Delegates to the same database functions used by the manual pages so the
    voice log feeds the same footprints, history, and leaderboards.
    """
    action = parsed.get("action_type")
    try:
        if action == "transport":
            from database import save_assessment
            from emissions import calculate_footprint, calculate_eco_score
            from gamification import check_badge_eligibility
            transport = parsed.get("transport", "Car")
            distance = float(parsed.get("distance") or 10.0)
            electricity = float(parsed.get("electricity") or 0.0)
            diet = parsed.get("diet", "Vegetarian")
            flights = int(parsed.get("flights") or 0)
            total, contributors, audit = calculate_footprint(
                transport, distance, electricity, diet, flights, "Global", return_audit=True
            )
            eco_score = calculate_eco_score(total, contributors)
            ok = save_assessment(
                user_id, transport, distance, electricity, diet, flights,
                total, eco_score, factor_version=audit.get("factor_version"),
            )
            if ok:
                check_badge_eligibility(user_id)
            return ok, "Transport activity saved to your carbon footprint."

        if action == "water":
            from database import save_water_assessment
            shower = float(parsed.get("shower_minutes") or parsed.get("minutes") or 8.0)
            ok = save_water_assessment(
                user_id, shower, 0.0, 0.0, 0.0, "Omnivore", round(shower * 10, 1)
            )
            return ok, "Water activity saved to your water footprint."

        if action == "recycling":
            from database import save_waste_assessment
            from waste import calculate_waste_footprint
            category = parsed.get("item", "Plastic Packaging")
            qty = float(parsed.get("quantity_kg") or 0.1)
            waste_data = {category: qty}
            result = calculate_waste_footprint(waste_data)
            ok = save_waste_assessment(
                user_id, waste_data, result["total_weekly_kg"],
                result["annual_co2"], result["recyclable_pct"],
            )
            return ok, f"{qty} kg of {category} recorded in your waste assessment."

        if action == "mission":
            from sustainability_missions import complete_mission
            hint = (parsed.get("mission_hint") or "").lower()
            mission_key = next(
                (k for k in _RECYCLING_ITEMS if k in hint),
                None,
            )
            ok, msg = complete_mission(user_id, mission_key or "reduce_reuse_recycle")
            return ok, msg

        return False, "Unknown action type."
    except Exception as exc:  # noqa: BLE001
        logger.error("Voice log save failed: %s", exc)
        return False, f"Could not save log: {exc}"


def record_voice_log_history(user_id: int, raw_text: str, parsed: dict[str, Any], confirmed: bool) -> bool:
    init_voice_logs_db()
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            "INSERT INTO voice_command_logs (user_id, raw_text, action_type, parsed, confirmed) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, raw_text, parsed.get("action_type", "unknown"), json.dumps(parsed), 1 if confirmed else 0),
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Unable to record voice log: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def get_voice_log_history(user_id: int, limit: int = 20) -> list[dict[str, Any]]:
    init_voice_logs_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, raw_text, action_type, parsed, confirmed, created_at "
            "FROM voice_command_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        logger.error("Unable to load voice logs: %s", exc)
        return []
    finally:
        if conn:
            conn.close()