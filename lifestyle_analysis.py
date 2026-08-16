"""AI Image-Based Lifestyle Analysis.

Lets users upload photos of rooms, kitchens, or workspaces and receive
AI-powered sustainability suggestions. Detects energy-consuming items,
estimates potential improvements, and generates recommendations.

Approach: OCR extracts any visible labels/text, while the LLM (Gemini, which
supports vision, with a heuristic fallback) identifies energy-consuming items
in the scene. Self-contained SQLite table for analysis history.
"""

import os
import io
import json
import time
import base64
import sqlite3
import logging
from typing import Any
import requests
import streamlit as st
from PIL import Image

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")
LLM_COOLDOWN_SECONDS = 2.0

SPACE_TYPES = {
    "Kitchen": {
        "icon": "🍳",
        "hint": "Look for fridge, oven, microwave, dishwasher, kettle, toaster, coffee machine.",
    },
    "Living Room": {
        "icon": "🛋️",
        "hint": "Look for TV, gaming consoles, lamps, standing fans, AC units, chargers.",
    },
    "Bedroom": {
        "icon": "🛏️",
        "hint": "Look for AC, heaters, night lamps, phone chargers, TVs, dehumidifiers.",
    },
    "Home Office / Workspace": {
        "icon": "💻",
        "hint": "Look for monitors, desktops, laptops, printers, routers, desk lamps.",
    },
}

# Heuristic keyword -> item mapping used when no LLM key is configured.
KEYWORD_ITEMS = {
    "fridge": ("Refrigerator", 150, "Keep at 3-5°C, clear the vents, and defrost regularly."),
    "refrigerator": ("Refrigerator", 150, "Keep at 3-5°C, clear the vents, and defrost regularly."),
    "oven": ("Oven", 120, "Use the microwave or air-fryer for small meals and batch-cook."),
    "microwave": ("Microwave", 60, "It's efficient for small meals — use it more, preheat less."),
    "dishwasher": ("Dishwasher", 100, "Run only full loads and use the eco cycle."),
    "kettle": ("Kettle", 40, "Only boil the water you need — it saves up to 30% energy."),
    "toaster": ("Toaster", 25, "Small appliance — use it instead of the oven grill."),
    "coffee": ("Coffee Machine", 45, "Switch it off after brewing instead of leaving it on standby."),
    "television": ("TV", 80, "Turn it off at the wall — standby still draws power."),
    "tv": ("TV", 80, "Turn it off at the wall — standby still draws power."),
    "console": ("Gaming Console", 50, "Enable power-saving mode and quit apps you aren't playing."),
    "lamp": ("Lamp", 15, "Swap remaining bulbs to LEDs — 80% more efficient."),
    "air conditioner": ("Air Conditioner", 350, "Set it 2°C warmer and use ceiling fans first."),
    "ac": ("Air Conditioner", 350, "Set it 2°C warmer and use ceiling fans first."),
    "heater": ("Heater", 300, "Dress warmly, seal drafts, and zone-heat only occupied rooms."),
    "computer": ("Desktop Computer", 90, "Sleep the monitor and switch to a laptop for casual use."),
    "laptop": ("Laptop", 50, "Unplug when charged and enable battery-saver mode."),
    "monitor": ("Monitor", 60, "Sleep after 5 minutes idle and dim brightness to 60%."),
    "printer": ("Printer", 20, "Keep it off unless printing — standby wastes power."),
    "router": ("Wi-Fi Router", 15, "Mostly unavoidable, but a timer can cut overnight standby."),
    "charger": ("Charger", 10, "Unplug chargers when not in use — they still draw 'vampire' power."),
    "fan": ("Fan", 60, "It uses far less energy than AC — use it first."),
    "dehumidifier": ("Dehumidifier", 200, "Empty the tank often and keep doors closed while running."),
}


def _check_rate_limit(provider: str) -> bool:
    key = f"_lifestyle_llm_last_call_{provider}"
    now = time.time()
    last_call = st.session_state.get(key, 0.0)
    if now - last_call < LLM_COOLDOWN_SECONDS:
        return False
    st.session_state[key] = now
    return True


def _image_to_b64(uploaded_file: io.BytesIO) -> str:
    return base64.b64encode(uploaded_file.getvalue()).decode("utf-8")


def _call_gemini_vision(uploaded_file: io.BytesIO, space_type: str, hint: str) -> dict[str, Any] | None:
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key or not _check_rate_limit("gemini"):
        return None
    try:
        mime = uploaded_file.type or "image/jpeg"
        image_b64 = _image_to_b64(uploaded_file)
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.5-flash:generateContent?key={gemini_key}"
        )
        payload = {
            "systemInstruction": {
                "parts": [{
                    "text": (
                        "You are a sustainability analyst. Look at the photo of a "
                        f"{space_type} and identify energy-consuming items. "
                        "For each item return a JSON object: "
                        '{"items": [{"name": string, "energy_w": number, '
                        '"improvement": string, "recommendation": string}]}. '
                        "energy_w is the average standby/active power in watts. "
                        "Return ONLY valid JSON."
                    )
                }]
            },
            "contents": [
                {
                    "parts": [
                        {"inline_data": {"mime_type": mime, "data": image_b64}},
                        {"text": f"Space: {space_type}. Hint: {hint}. Analyze this photo."},
                    ]
                }
            ],
            "generationConfig": {"responseMimeType": "application/json"},
        }
        from request_logging import log_api_request
        response = requests.post(url, json=payload, timeout=30)
        log_api_request("POST", url, status_code=response.status_code)
        if response.status_code == 200:
            data = response.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_text)
        logger.warning("Gemini vision error: %s", response.text)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gemini vision exception: %s", exc)
    return None


def _extract_text_ocr(uploaded_file: io.BytesIO) -> str:
    """Extract text from the image via OCR to support heuristic detection."""
    try:
        from ocr_utils import extract_text_from_file
        return extract_text_from_file(uploaded_file) or ""
    except Exception as exc:  # noqa: BLE001
        logger.warning("OCR extraction failed: %s", exc)
        return ""


def _heuristic_detection(ocr_text: str) -> list[dict[str, Any]]:
    """Detect items by keyword matching on OCR text."""
    detected = []
    text_lower = ocr_text.lower()
    seen = set()
    for keyword, (name, watts, recommendation) in KEYWORD_ITEMS.items():
        if keyword in text_lower and name not in seen:
            seen.add(name)
            detected.append({
                "name": name,
                "energy_w": watts,
                "improvement": "Reduce standby and usage time",
                "recommendation": recommendation,
            })
    return detected


def analyze_image(uploaded_file: io.BytesIO, space_type: str) -> dict[str, Any]:
    """Analyze an uploaded image and return detected items + summary."""
    space = SPACE_TYPES.get(space_type, {"icon": "🏠", "hint": ""})

    ocr_text = _extract_text_ocr(uploaded_file)

    llm_items = None
    if os.environ.get("GEMINI_API_KEY"):
        llm_items = _call_gemini_vision(uploaded_file, space_type, space["hint"])
        if llm_items and llm_items.get("items"):
            items = llm_items["items"]
        else:
            items = _heuristic_detection(ocr_text)
    else:
        items = _heuristic_detection(ocr_text)

    items = items or [
        {
            "name": "General household appliances",
            "energy_w": 100,
            "improvement": "Review the items in this room",
            "recommendation": "Complete a full home energy audit for itemized savings.",
        }
    ]

    total_watts = sum(item.get("energy_w", 0) for item in items)
    annual_kwh = round(total_watts * 4 * 365 / 1000, 1)  # assume ~4h/day active use
    annual_co2_kg = round(annual_kwh * 0.48, 1)
    potential_savings_pct = 25 if total_watts > 0 else 0
    savings_kwh = round(annual_kwh * potential_savings_pct / 100, 1)
    savings_co2_kg = round(savings_kwh * 0.48, 1)

    return {
        "space_type": space_type,
        "icon": space["icon"],
        "ocr_text": ocr_text[:300],
        "items": items,
        "total_watts": total_watts,
        "annual_kwh": annual_kwh,
        "annual_co2_kg": annual_co2_kg,
        "potential_savings_pct": potential_savings_pct,
        "savings_kwh": savings_kwh,
        "savings_co2_kg": savings_co2_kg,
    }


def _get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_lifestyle_db() -> bool:
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lifestyle_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                space_type TEXT NOT NULL,
                items TEXT NOT NULL,
                annual_co2_kg REAL NOT NULL,
                savings_co2_kg REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Lifestyle analysis init error: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def save_analysis(user_id: int, space_type: str, items: list[dict[str, Any]], annual_co2_kg: float, savings_co2_kg: float) -> bool:
    init_lifestyle_db()
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            INSERT INTO lifestyle_analyses (
                user_id, space_type, items, annual_co2_kg, savings_co2_kg
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, space_type, json.dumps(items), annual_co2_kg, savings_co2_kg),
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Unable to save lifestyle analysis: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def get_analysis_history(user_id: int, limit: int = 20) -> list[dict[str, Any]]:
    init_lifestyle_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, space_type, items, annual_co2_kg, savings_co2_kg, created_at
            FROM lifestyle_analyses
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        logger.error("Unable to load lifestyle analyses: %s", exc)
        return []
    finally:
        if conn:
            conn.close()
