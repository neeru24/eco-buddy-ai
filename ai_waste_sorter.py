"""AI Waste Sorter & Recycling Guide.

Lets users upload a photo of a waste item and get:
  - Category classification (recyclable, compostable, landfill, e-waste, hazardous)
  - Confidence score
  - Location-aware disposal guidance
  - "Did you know" fact + disposal tip
  - History with accuracy feedback

Reuses the OCR + LLM vision pipeline from lifestyle_analysis.py.
Self-contained SQLite table for classification history.
"""

import os
import io
import json
import logging
import sqlite3
import datetime
from typing import Any

import requests
import streamlit as st
from PIL import Image

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

# Waste categories with display info
WASTE_CATEGORIES = {
    "recyclable": {
        "label": "♻️ Recyclable",
        "subcats": ["Plastic Packaging", "Paper & Cardboard", "Glass", "Metal (Cans)"],
        "color": "#2e7d32",
    },
    "compostable": {
        "label": "🍃 Compostable",
        "subcats": ["Food Scraps", "Textiles", "Paper & Cardboard"],
        "color": "#689f38",
    },
    "landfill": {
        "label": "🗑️ Landfill",
        "subcats": ["Other (Mixed Waste)", "Plastic Packaging", "Textiles"],
        "color": "#c62828",
    },
    "e_waste": {
        "label": "🔌 E-Waste",
        "subcats": ["Electronics (E-Waste)"],
        "color": "#e65100",
    },
    "hazardous": {
        "label": "☠️ Hazardous",
        "subcats": ["Batteries", "Chemicals", "Light Bulbs", "Medication"],
        "color": "#d84315",
    },
}

# Per-region disposal rules (simplified, extensible)
DISPOSAL_RULES = {
    "Global": {
        "recyclable": "Curbside recycling bin (check local accepted materials).",
        "compostable": "Compost bin or green waste collection if available.",
        "landfill": "General waste bin.",
        "e_waste": "E-waste drop-off point or retailer take-back program.",
        "hazardous": "Household hazardous waste collection event or facility.",
    },
    "US": {
        "recyclable": "Curbside single-stream (varies by municipality — check local .gov).",
        "compostable": "Yard waste bin or drop-off compost site.",
        "landfill": "Trash bin.",
        "e_waste": "Best Buy / Staples / local e-waste recycler.",
        "hazardous": "County HHW facility or retail take-back (batteries, bulbs).",
    },
    "EU": {
        "recyclable": "Yellow bin / blue bin per local scheme (packaging, paper, glass).",
        "compostable": "Bio-waste bin (brown) or home compost.",
        "landfill": "Residual waste bin (grey/black).",
        "e_waste": "Retailer take-back (WEEE) or municipal collection point.",
        "hazardous": "Recycling centre (milieupark / déchetterie / Wertstoffhof).",
    },
    "India": {
        "recyclable": "Dry waste bin (blue) — give to kabadiwala or municipal dry waste.",
        "compostable": "Wet waste bin (green) for composting / biogas.",
        "landfill": "Reject waste bin (red/black) — sanitary landfill.",
        "e_waste": "Authorized e-waste recycler (CPCB list) or producer take-back.",
        "hazardous": "TSDF / authorized hazardous waste facility.",
    },
}

# Quick facts per category
WASTE_FACTS = {
    "recyclable": [
        "Aluminum cans can be recycled infinitely with no loss of quality.",
        "Recycling one glass bottle saves enough energy to power a light bulb for 4 hours.",
        "Paper can be recycled 5–7 times before fibers become too short.",
    ],
    "compostable": [
        "Food waste in landfills generates methane, a greenhouse gas 28× stronger than CO₂.",
        "Composting returns nutrients to soil and reduces need for chemical fertilizers.",
        "A household can divert ~30% of its waste by composting organics.",
    ],
    "landfill": [
        "The average person sends ~1.5 kg of waste to landfill every day.",
        "Landfills are the 3rd largest source of human-related methane emissions.",
        "Reducing single-use items is the most effective way to shrink landfill waste.",
    ],
    "e_waste": [
        "E-waste is the world's fastest-growing waste stream — 50+ million tonnes/year.",
        "One smartphone contains ~30 mg of gold, ~300 mg of silver.",
        "Proper e-waste recycling recovers rare earths and prevents toxic leaching.",
    ],
    "hazardous": [
        "One button cell battery can contaminate 600,000 liters of water.",
        "CFL bulbs contain mercury — never put them in household trash.",
        "Unused medication should be returned to a pharmacy, not flushed.",
    ],
}

# Disposal tips per category
DISPOSAL_TIPS = {
    "recyclable": [
        "Rinse containers — food residue contaminates the whole batch.",
        "Keep caps on bottles; loose caps fall through sorting screens.",
        "Flatten cardboard to save space in your bin and the truck.",
    ],
    "compostable": [
        "Chop large scraps — smaller pieces break down faster.",
        "Balance greens (food) with browns (dry leaves, paper) 1:2 by volume.",
        "Avoid meat, dairy, and oily foods in home compost (attracts pests).",
    ],
    "landfill": [
        "Wrap broken glass in paper before binning to protect collectors.",
        "Bag dust and light debris to prevent wind-blown litter.",
        "Consider if an item can be repaired, donated, or repurposed first.",
    ],
    "e_waste": [
        "Delete personal data before recycling devices.",
        "Keep cables and chargers with the device for complete recycling.",
        "Check if the manufacturer offers a free mail-back program.",
    ],
    "hazardous": [
        "Store batteries in a non-metal container until drop-off.",
        "Never mix chemicals — they can react dangerously.",
        "Use original containers for transport to hazardous waste site.",
    ],
}


def _get_conn():
    return sqlite3.connect(DB_NAME)


def init_waste_sorter_db() -> bool:
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS waste_classifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                image_hash TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                confidence REAL NOT NULL,
                region TEXT NOT NULL DEFAULT 'Global',
                user_feedback TEXT,
                correct_category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Waste sorter init error: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def _image_to_b64(uploaded_file: io.BytesIO) -> str:
    import base64
    return base64.b64encode(uploaded_file.getvalue()).decode("utf-8")


def _image_hash(uploaded_file: io.BytesIO) -> str:
    import hashlib
    return hashlib.sha256(uploaded_file.getvalue()).hexdigest()[:16]


def _call_gemini_vision(uploaded_file: io.BytesIO) -> dict[str, Any] | None:
    """Call Gemini 2.5 Flash vision to classify the waste item."""
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        return None
    try:
        mime = uploaded_file.type or "image/jpeg"
        image_b64 = _image_to_b64(uploaded_file)
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.5-flash:generateContent?key={gemini_key}"
        )
        categories_desc = "\n".join(
            f"- {cat}: {info['label']} — e.g., {', '.join(info['subcats'])}"
            for cat, info in WASTE_CATEGORIES.items()
        )
        payload = {
            "systemInstruction": {
                "parts": [{
                    "text": (
                        "You are a waste-sorting expert. Look at the photo of a single "
                        "item and classify it into exactly ONE of these categories:\n"
                        f"{categories_desc}\n\n"
                        "Return ONLY valid JSON with keys:\n"
                        '{"category": "<one of the 5>", "subcategory": "<best match from subcats or null>", '
                        '"confidence": <0.0-1.0>, "explanation": "<1-sentence why>"}'
                    )
                }]
            },
            "contents": [
                {
                    "parts": [
                        {"inline_data": {"mime_type": mime, "data": image_b64}},
                        {"text": "Classify this waste item. Output JSON only."},
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
            parsed = json.loads(raw_text)
            if parsed.get("category") in WASTE_CATEGORIES:
                return parsed
            logger.warning("Gemini returned invalid category: %s", parsed)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gemini vision exception: %s", exc)
    return None


def _ocr_fallback(uploaded_file: io.BytesIO) -> dict[str, Any] | None:
    """Use OCR + keyword matching as a fallback when no LLM key."""
    try:
        from ocr_utils import extract_text_from_file
        text = (extract_text_from_file(uploaded_file) or "").lower()
        if not text:
            return None

        # Simple keyword-based classification
        keyword_map = {
            "recyclable": ["plastic", "bottle", "can", "aluminum", "glass", "paper", "cardboard", "jar", "tin"],
            "compostable": ["food", "vegetable", "fruit", "peel", "scrap", "coffee", "tea", "leaf", "grass"],
            "e_waste": ["phone", "battery", "charger", "cable", "laptop", "computer", "tablet", "electronic", "circuit"],
            "hazardous": ["chemical", "paint", "oil", "medicine", "pill", "bulb", "mercury", "cleaner", "pesticide"],
        }
        scores = {cat: sum(1 for kw in kws if kw in text) for cat, kws in keyword_map.items()}
        best = max(scores, key=scores.get) if any(scores.values()) else "landfill"
        confidence = min(0.4 + scores[best] * 0.1, 0.7)
        subcat = next((s for s in WASTE_CATEGORIES[best]["subcats"] if s.lower() in text), None)
        return {
            "category": best,
            "subcategory": subcat,
            "confidence": confidence,
            "explanation": f"Keyword match on OCR text (score {scores[best]})",
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("OCR fallback failed: %s", exc)
    return None


def classify_waste_image(uploaded_file: io.BytesIO, region: str = "Global") -> dict[str, Any]:
    """Classify an uploaded waste image.

    Returns a dict with category, subcategory, confidence, explanation,
    disposal_guidance, fact, tip, and region.
    """
    # Try LLM vision first
    result = _call_gemini_vision(uploaded_file)
    if not result:
        # Fallback to OCR + keywords
        result = _ocr_fallback(uploaded_file) or {
            "category": "landfill",
            "subcategory": "Other (Mixed Waste)",
            "confidence": 0.3,
            "explanation": "Unable to classify — defaulting to landfill.",
        }

    category = result["category"]
    rules = DISPOSAL_RULES.get(region, DISPOSAL_RULES["Global"])
    facts = WASTE_FACTS.get(category, [])
    tips = DISPOSAL_TIPS.get(category, [])

    return {
        "category": category,
        "label": WASTE_CATEGORIES[category]["label"],
        "subcategory": result.get("subcategory"),
        "confidence": float(result.get("confidence", 0.5)),
        "explanation": result.get("explanation", ""),
        "disposal_guidance": rules.get(category, rules["landfill"]),
        "fact": facts[0] if facts else "",
        "tip": tips[0] if tips else "",
        "region": region,
    }


def save_classification(
    user_id: int,
    image_hash: str,
    classification: dict[str, Any],
    user_feedback: str | None = None,
    correct_category: str | None = None,
) -> bool:
    init_waste_sorter_db()
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            INSERT INTO waste_classifications (
                user_id, image_hash, category, subcategory, confidence, region,
                user_feedback, correct_category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                image_hash,
                classification["category"],
                classification.get("subcategory"),
                classification["confidence"],
                classification["region"],
                user_feedback,
                correct_category,
            ),
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Unable to save classification: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def get_classification_history(user_id: int, limit: int = 20) -> list[dict[str, Any]]:
    init_waste_sorter_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, category, subcategory, confidence, region, user_feedback,
                   correct_category, created_at
            FROM waste_classifications
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        logger.error("Unable to load history: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def update_classification_feedback(
    classification_id: int, user_id: int, feedback: str, correct_category: str | None = None
) -> bool:
    init_waste_sorter_db()
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            UPDATE waste_classifications
            SET user_feedback = ?, correct_category = ?
            WHERE id = ? AND user_id = ?
            """,
            (feedback, correct_category, classification_id, user_id),
        )
        conn.commit()
        return conn.total_changes > 0
    except sqlite3.Error as exc:
        logger.error("Unable to update feedback: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def get_classification_accuracy(user_id: int) -> dict[str, Any]:
    """Calculate user's classification accuracy from feedback."""
    init_waste_sorter_db()
    conn = None
    try:
        conn = _get_conn()
        row = conn.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN correct_category IS NOT NULL AND correct_category = category THEN 1 ELSE 0 END) as correct
            FROM waste_classifications
            WHERE user_id = ? AND correct_category IS NOT NULL
            """,
            (user_id,),
        ).fetchone()
        total, correct = row[0] or 0, row[1] or 0
        return {
            "total_feedback": total,
            "correct": correct,
            "accuracy": round(correct / total * 100, 1) if total else None,
        }
    except sqlite3.Error as exc:
        logger.error("Unable to calculate accuracy: %s", exc)
        return {"total_feedback": 0, "correct": 0, "accuracy": None}
    finally:
        if conn:
            conn.close()


def add_classified_item_to_waste_assessment(user_id: int, classification: dict[str, Any]) -> bool:
    """Add a classified item to the user's weekly waste assessment.

    Maps the category/subcategory to waste.py categories and increments
    the weekly kg estimate.
    """
    from waste import calculate_waste_footprint, WASTE_CATEGORIES as WC
    from database import save_waste_assessment

    subcat = classification.get("subcategory") or classification["category"]
    # Map to waste.py categories
    mapping = {
        "Food Scraps": "Food Scraps",
        "Plastic Packaging": "Plastic Packaging",
        "Paper & Cardboard": "Paper & Cardboard",
        "Glass": "Glass",
        "Metal (Cans)": "Metal (Cans)",
        "Electronics (E-Waste)": "Electronics (E-Waste)",
        "Textiles": "Textiles",
        "Other (Mixed Waste)": "Other (Mixed Waste)",
    }
    waste_cat = mapping.get(subcat, "Other (Mixed Waste)")

    # Estimate kg for a single item (rough averages)
    item_kg_estimates = {
        "Food Scraps": 0.2,
        "Plastic Packaging": 0.05,
        "Paper & Cardboard": 0.1,
        "Glass": 0.3,
        "Metal (Cans)": 0.04,
        "Electronics (E-Waste)": 0.5,
        "Textiles": 0.2,
        "Other (Mixed Waste)": 0.15,
    }
    kg = item_kg_estimates.get(waste_cat, 0.1)

    # Load latest assessment to get current totals, or start fresh
    from database import get_waste_assessments
    history = get_waste_assessments(user_id)
    if history:
        latest = history[0]
        waste_data = {
            "Food Scraps": latest.get("food_scraps", 0),
            "Plastic Packaging": latest.get("plastic_packaging", 0),
            "Paper & Cardboard": latest.get("paper_cardboard", 0),
            "Glass": latest.get("glass", 0),
            "Metal (Cans)": latest.get("metal_cans", 0),
            "Electronics (E-Waste)": latest.get("e_waste", 0),
            "Textiles": latest.get("textiles", 0),
            "Other (Mixed Waste)": latest.get("mixed_waste", 0),
        }
    else:
        waste_data = {cat: 0.0 for cat in WC}

    waste_data[waste_cat] = waste_data.get(waste_cat, 0.0) + kg
    result = calculate_waste_footprint(waste_data)

    return save_waste_assessment(
        user_id, waste_data,
        result["total_weekly_kg"], result["annual_co2"], result["recyclable_pct"]
    )