"""AI Carbon Consultant.

A conversational sustainability advisor. Instead of static recommendations,
users can ask questions like "How can I reduce my footprint by 30%?" and
receive personalized action plans grounded in their own assessment history.

Self-contained module: uses the same Gemini/Groq pattern as llm_parser.py and
persists conversations in its own lazily-created SQLite table.
"""

import os
import json
import time
import sqlite3
import logging
from typing import Any
import requests
import streamlit as st
from cache import cached
from cache_config import TTL_LLM_RESPONSE

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")
LLM_COOLDOWN_SECONDS = 2.0

QUICK_QUESTIONS = [
    "How can I reduce my footprint by 30%?",
    "What is my biggest source of emissions?",
    "Which change gives me the most impact for the least effort?",
    "How can I make my diet more sustainable?",
    "Is it better to fly or drive for my next trip?",
    "How much can I save by switching to renewable energy?",
]


def _check_rate_limit(provider: str) -> bool:
    key = f"_consultant_llm_last_call_{provider}"
    now = time.time()
    last_call = st.session_state.get(key, 0.0)
    if now - last_call < LLM_COOLDOWN_SECONDS:
        return False
    st.session_state[key] = now
    return True


def _call_llm(system_prompt: str, user_prompt: str, json_mode: bool = False) -> dict[str, Any] | str | None:
    """Call Gemini 2.5 Flash, falling back to Groq. Returns text (or dict in JSON mode)."""
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key and _check_rate_limit("gemini"):
        try:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"gemini-2.5-flash:generateContent?key={gemini_key}"
            )
            payload = {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"parts": [{"text": user_prompt}]}],
            }
            if json_mode:
                payload["generationConfig"] = {"responseMimeType": "application/json"}
            from request_logging import log_api_request
            response = requests.post(url, json=payload, timeout=20)
            log_api_request("POST", url, status_code=response.status_code)
            if response.status_code == 200:
                data = response.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(raw_text) if json_mode else raw_text
            logger.warning("Gemini API error: %s", response.text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Gemini exception: %s", exc)

    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key and _check_rate_limit("groq"):
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
            payload = {
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
            if json_mode:
                payload["response_format"] = {"type": "json_object"}
            from request_logging import log_api_request
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            log_api_request("POST", url, headers=headers, status_code=response.status_code)
            if response.status_code == 200:
                data = response.json()
                raw_text = data["choices"][0]["message"]["content"]
                return json.loads(raw_text) if json_mode else raw_text
            logger.warning("Groq API error: %s", response.text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Groq exception: %s", exc)

    return None


def build_user_context(user_id: int) -> str:
    """Build a compact sustainability profile from the user's assessment history."""
    from database import get_assessments

    assessments = get_assessments(user_id)
    if not assessments:
        return "The user has not completed any assessments yet."

    latest = assessments[0]
    try:
        footprint_kg_per_day = float(latest[7])
        footprint_tonnes_per_year = footprint_kg_per_day * 365 / 1000
    except (TypeError, ValueError):
        footprint_tonnes_per_year = None

    transport = latest[2] or "unknown"
    distance = latest[3] or 0
    electricity = latest[4] or 0
    diet = latest[5] or "unknown"
    flights = latest[6] or 0

    context = (
        f"Latest carbon footprint assessment (per day): {footprint_kg_per_day} kg CO2 "
        f"≈ {footprint_tonnes_per_year:.2f} tonnes per year. "
        f"Transport: {transport} ({distance} km/day). "
        f"Electricity: {electricity} kWh/month. "
        f"Diet: {diet}. Flights: {flights} per year. "
        f"Number of assessments on record: {len(assessments)}."
    )
    return context


@cached(ttl=TTL_LLM_RESPONSE)
def ask_consultant(question: str, user_context: dict[str, Any]) -> str | None:
    """Ask the carbon consultant a question given the user's context."""
    system_prompt = (
        "You are EcoBuddy's AI Carbon Consultant — a friendly, data-informed "
        "sustainability advisor. Use the user's context to give personalized, "
        "actionable advice. Prioritize high-impact, low-effort changes. Give "
        "specific numbers where you can and keep answers concise (3-6 short "
        "sections with bullet points). Always end with one concrete 'next step'."
    )
    user_prompt = (
        f"User context:\n{user_context}\n\n"
        f"User question: {question}\n\n"
        "Please answer helpfully and concisely."
    )
    return _call_llm(system_prompt, user_prompt, json_mode=False)


def _get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_consultant_db() -> bool:
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS consultant_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Consultant conversation init error: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def save_message(user_id: int, role: str, message: str) -> bool:
    init_consultant_db()
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            "INSERT INTO consultant_conversations (user_id, role, message) VALUES (?, ?, ?)",
            (user_id, role, message),
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Unable to save consultant message: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def get_conversation(user_id: int, limit: int = 50) -> list[dict[str, Any]]:
    init_consultant_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, role, message, created_at
            FROM consultant_conversations
            WHERE user_id = ?
            ORDER BY created_at ASC
            """,
            (user_id,),
        ).fetchall()
        messages = [dict(row) for row in rows]
        if limit and len(messages) > limit:
            messages = messages[-limit:]
        return messages
    except sqlite3.Error as exc:
        logger.error("Unable to load consultant conversation: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def clear_conversation(user_id: int) -> bool:
    init_consultant_db()
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            "DELETE FROM consultant_conversations WHERE user_id = ?", (user_id,)
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Unable to clear consultant conversation: %s", exc)
        return False
    finally:
        if conn:
            conn.close()
