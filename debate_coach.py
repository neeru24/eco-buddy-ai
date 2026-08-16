"""AI Sustainability Debate Coach.

Allows users to debate environmental topics with an AI that provides
fact-based counterarguments and educational feedback.

This module is intentionally self-contained: the LLM client mirrors the
Gemini/Groq pattern used by llm_parser.py, and the SQLite table used to
persist debate history is created lazily (CREATE TABLE IF NOT EXISTS) so no
shared database files need to be modified.
"""

import os
import json
import time
import sqlite3
import logging
from typing import Any
import requests
import streamlit as st

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")
LLM_COOLDOWN_SECONDS = 2.0

DEBATE_TOPICS = {
    "climate_action": {
        "title": "Is individual climate action meaningful?",
        "icon": "🌍",
        "context": (
            "Proponents argue that personal changes (diet, transport, energy) "
            "compound into cultural shifts and signal demand for policy. Critics "
            "argue that a handful of corporations and the energy sector dominate "
            "emissions, so systemic change matters far more."
        ),
        "learning_resources": [
            "Drawdown: The Most Comprehensive Plan Ever Proposed to Reverse Global Warming — Paul Hawken",
            "IPCC Sixth Assessment Report (2021–2023) summary for policymakers",
            "How to Avoid a Climate Disaster — Bill Gates",
        ],
    },
    "carbon_tax": {
        "title": "Should governments impose a global carbon tax?",
        "icon": "💸",
        "context": (
            "A carbon price internalizes the external cost of emissions, making "
            "polluters pay. Opponents warn about regressive impacts on low-income "
            "households and competitiveness of domestic industry."
        ),
        "learning_resources": [
            "The Economics of Climate Change: The Stern Review (2006)",
            "Carbon Pricing Leadership Coalition — World Bank publications",
            "Why carbon taxes matter: William Nordhaus, Nobel Prize lecture",
        ],
    },
    "nuclear_energy": {
        "title": "Is nuclear power essential to decarbonization?",
        "icon": "⚛️",
        "context": (
            "Nuclear provides dense, low-carbon baseload power but carries "
            "waste-disposal, cost-overrun, and safety concerns. Renewables plus "
            "storage are advancing rapidly, reshaping the debate."
        ),
        "learning_resources": [
            "Our World in Data — Nuclear Energy data explorer",
            "World Nuclear Association — Climate Change and Nuclear Power reports",
            "The Uninhabitable Earth — David Wallace-Wells (context on energy trade-offs)",
        ],
    },
    "meat_consumption": {
        "title": "Should society reduce meat consumption?",
        "icon": "🍽️",
        "context": (
            "Livestock contributes roughly 14.5% of global greenhouse-gas "
            "emissions and large land/water use. Cultural, nutritional, and "
            "economic arguments complicate blanket policy approaches."
        ),
        "learning_resources": [
            "FAO — Livestock's Long Shadow (2006)",
            "EAT-Lancet Commission on Food, Planet, Health (2019)",
            "Food and Climate Change — Project Drawdown",
        ],
    },
    "air_travel": {
        "title": "Should air travel be taxed or rationed?",
        "icon": "✈️",
        "context": (
            "Aviation emits ~2.5% of global CO2 plus non-CO2 warming effects. "
            "Frequent-flyer taxes and demand reduction are debated against "
            "technological fixes like sustainable aviation fuel."
        ),
        "learning_resources": [
            "ICCT — CO2 emissions from commercial aviation reports",
            "International Council on Clean Transportation aviation analyses",
            "Staying Grounded — aviation climate research initiative",
        ],
    },
    "plastic_ban": {
        "title": "Should single-use plastics be banned?",
        "icon": "♻️",
        "context": (
            "Plastic pollution threatens oceans and food chains. Supporters of "
            "bans point to substitutes and behavior change; critics note "
            "inadequate alternatives and unintended substitution effects."
        ),
        "learning_resources": [
            "UNEP — Single-Use Plastics: A Roadmap for Sustainability (2018)",
            "Breaking the Plastic Wave — The Pew Charitable Trusts (2020)",
            "National Geographic — Planet or Plastic initiative",
        ],
    },
    "renewable_subsidies": {
        "title": "Should fossil-fuel subsidies be redirected to renewables?",
        "icon": "🌱",
        "context": (
            "Global fossil-fuel subsidies dwarf renewables support. Redirecting "
            "them could accelerate the energy transition but raises affordability "
            "and political-economy questions."
        ),
        "learning_resources": [
            "IMF — Fossil Fuel Subsidies data and analyses",
            "IEA World Energy Outlook — energy subsidies chapters",
            "Energy subsidies and the green transition — OECD publications",
        ],
    },
}


def _check_rate_limit(provider: str) -> bool:
    key = f"_debate_llm_last_call_{provider}"
    now = time.time()
    last_call = st.session_state.get(key, 0.0)
    if now - last_call < LLM_COOLDOWN_SECONDS:
        return False
    st.session_state[key] = now
    return True


def _call_llm(system_prompt: str, user_prompt: str, json_mode: bool = True) -> dict[str, Any] | str | None:
    """Call Gemini 2.5 Flash, falling back to Groq. Returns parsed content or None."""
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
            response = requests.post(url, json=payload, timeout=15)
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
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            log_api_request("POST", url, headers=headers, status_code=response.status_code)
            if response.status_code == 200:
                data = response.json()
                raw_text = data["choices"][0]["message"]["content"]
                return json.loads(raw_text) if json_mode else raw_text
            logger.warning("Groq API error: %s", response.text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Groq exception: %s", exc)

    return None


def generate_counterargument(topic_key: str, user_position: str, user_argument: str) -> dict[str, Any] | None:
    """Generate a fact-based counterargument to the user's stance."""
    topic = DEBATE_TOPICS[topic_key]
    system_prompt = (
        "You are a sustainability debate coach. You present balanced, "
        "fact-based counterarguments to sharpen the user's critical thinking. "
        "Cite plausible evidence, stay respectful, and never misrepresent facts. "
        'Return a JSON object with keys "counterargument", "strong_points", '
        'and "rebuttal_advice".'
    )
    user_prompt = (
        f"Debate topic: {topic['title']}\n"
        f"Context: {topic['context']}\n\n"
        f"The user's position: {user_position}\n"
        f"The user's argument: {user_argument}\n\n"
        "Please provide: counterargument (2-3 paragraphs), strong_points "
        "(the strongest parts of the user's argument), and rebuttal_advice "
        "(how the user can respond to this counterargument)."
    )
    result = _call_llm(system_prompt, user_prompt, json_mode=True)
    if result:
        return {
            "counterargument": result.get("counterargument", ""),
            "strong_points": result.get("strong_points", []),
            "rebuttal_advice": result.get("rebuttal_advice", ""),
        }
    return None


def score_argument(user_argument: str, topic_key: str) -> dict[str, Any] | None:
    """Score the user's argument on clarity, evidence, and logic (0-100)."""
    topic = DEBATE_TOPICS[topic_key]
    system_prompt = (
        "You are an evaluator of environmental debate arguments. Score the "
        "user's argument from 0 to 100 on clarity, use of evidence, logical "
        "reasoning, and persuasiveness. Be constructive and specific. "
        'Return a JSON object with keys "score", "clarity", "evidence", '
        '"logic", "feedback", and "suggestions" (list).'
    )
    user_prompt = (
        f"Debate topic: {topic['title']}\n"
        f"User's argument: {user_argument}\n\n"
        "Please evaluate this argument and return the requested JSON."
    )
    result = _call_llm(system_prompt, user_prompt, json_mode=True)
    if not result:
        return None
    try:
        score = max(0, min(100, int(result.get("score", 0))))
    except (TypeError, ValueError):
        score = 0
    return {
        "score": score,
        "clarity": result.get("clarity", ""),
        "evidence": result.get("evidence", ""),
        "logic": result.get("logic", ""),
        "feedback": result.get("feedback", ""),
        "suggestions": result.get("suggestions", []),
    }


def _get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_debate_db() -> bool:
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS debate_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                topic_key TEXT NOT NULL,
                user_position TEXT NOT NULL,
                user_argument TEXT NOT NULL,
                counterargument TEXT,
                score INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Debate history init error: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def save_debate(user_id: int, topic_key: str, user_position: str, user_argument: str, counterargument: str | None, score: int | None) -> int:
    init_debate_db()
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            INSERT INTO debate_history (
                user_id, topic_key, user_position, user_argument,
                counterargument, score
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, topic_key, user_position, user_argument, counterargument, score),
        )
        conn.commit()
        return conn.total_changes
    except sqlite3.Error as exc:
        logger.error("Unable to save debate: %s", exc)
        return 0
    finally:
        if conn:
            conn.close()


def get_debate_history(user_id: int, limit: int = 20) -> list[dict[str, Any]]:
    init_debate_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, topic_key, user_position, user_argument,
                   counterargument, score, created_at
            FROM debate_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        logger.error("Unable to load debate history: %s", exc)
        return []
    finally:
        if conn:
            conn.close()
