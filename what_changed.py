import os
import json
import time
from typing import Any
import requests
import streamlit as st
from cache import cached
from cache_config import TTL_LLM_RESPONSE
from config import CATEGORY_WEIGHTS

LLM_COOLDOWN_SECONDS = 2.0


def _check_rate_limit(provider: str) -> bool:
    key = f"_llm_last_call_{provider}"
    now = time.time()
    last_call = st.session_state.get(key, 0.0)
    if now - last_call < LLM_COOLDOWN_SECONDS:
        return False
    st.session_state[key] = now
    return True


def compute_assessment_diff(current: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any] | None:
    if previous is None:
        return None

    fields = ["transport", "distance", "electricity", "diet", "flights"]

    changes = {}
    for fld in fields:
        old_val = previous.get(fld)
        new_val = current.get(fld)
        if old_val != new_val:
            changes[fld] = {"from": old_val, "to": new_val}

    footprint_old = previous.get("footprint", 0)
    footprint_new = current.get("footprint", 0)
    footprint_change = footprint_new - footprint_old
    pct_change = (
        (footprint_change / footprint_old * 100) if footprint_old else 0
    )

    score_old = previous.get("eco_score", 0)
    score_new = current.get("eco_score", 0)

    contributors_old = previous.get("contributors", {})
    contributors_new = current.get("contributors", {})
    category_deltas = {}
    all_cats = set(contributors_old.keys()) | set(contributors_new.keys())
    for cat in all_cats:
        old_val = contributors_old.get(cat, 0)
        new_val = contributors_new.get(cat, 0)
        delta = new_val - old_val
        if delta != 0:
            pct_of_total = (
                (abs(delta) / max(abs(footprint_change), 1)) * 100
                if footprint_change != 0
                else 0
            )
            category_deltas[cat] = {
                "from": old_val,
                "to": new_val,
                "delta": delta,
                "pct_of_change": pct_of_total,
                "direction": "increased" if delta > 0 else "decreased",
            }

    top_contributor = (
        max(category_deltas.items(), key=lambda x: abs(x[1]["delta"]))[0]
        if category_deltas
        else None
    )

    return {
        "changes": changes,
        "footprint": {
            "from": footprint_old,
            "to": footprint_new,
            "delta": footprint_change,
            "pct": round(pct_change, 1),
        },
        "eco_score": {
            "from": score_old,
            "to": score_new,
            "delta": score_new - score_old,
        },
        "category_deltas": category_deltas,
        "top_contributor": top_contributor,
    }


def _build_ai_prompt(diff: dict[str, Any]) -> str:
    lines = []
    lines.append("Compare the user's two most recent carbon footprint assessments and explain what changed, why it matters, and how to improve.")
    lines.append("")
    lines.append("Previous assessment:")
    lines.append(f"- Total footprint: {diff['footprint']['from']:.0f} kg CO₂")
    lines.append(f"- Eco score: {diff['eco_score']['from']}/100")
    lines.append("")
    lines.append("Current assessment:")
    lines.append(f"- Total footprint: {diff['footprint']['to']:.0f} kg CO₂")
    lines.append(f"- Eco score: {diff['eco_score']['to']}/100")
    lines.append(f"- Change: {diff['footprint']['pct']:+.1f}% ({diff['footprint']['delta']:+.0f} kg CO₂)")
    lines.append("")
    if diff["changes"]:
        lines.append("Input changes detected:")
        for field, change in diff["changes"].items():
            lines.append(f"- {field}: {change['from']} → {change['to']}")
        lines.append("")
    if diff["category_deltas"]:
        lines.append("Per-category CO₂ changes:")
        for cat, delta in sorted(diff["category_deltas"].items(), key=lambda x: abs(x[1]["delta"]), reverse=True):
            lines.append(f"- {cat}: {delta['from']:.0f} → {delta['to']:.0f} kg ({delta['delta']:+.0f} kg, {delta['direction']})")
        lines.append("")
    lines.append("Return a JSON object with these keys:")
    lines.append('1. "summary": A 2-3 sentence plain-English explanation of what changed and why it happened (mention specific categories and the net impact on total footprint).')
    lines.append('2. "biggest_driver": The single category that contributed most to the change and why.')
    lines.append('3. "suggestion": A specific, actionable recommendation tailored to the user\'s changes — what they should keep doing or what they should try next.')
    lines.append("")
    lines.append("Output ONLY a raw JSON object without markdown wrappers.")
    return "\n".join(lines)


def _call_llm(prompt: str) -> dict[str, Any] | None:
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key and _check_rate_limit("gemini"):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            payload = {
                "systemInstruction": {
                    "parts": [{"text": "You are a helpful carbon-footprint analysis assistant. Always output valid JSON."}]
                },
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"},
            }
            from request_logging import log_api_request
            response = requests.post(url, json=payload, timeout=10)
            log_api_request("POST", url, status_code=response.status_code)
            if response.status_code == 200:
                data = response.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(raw_text)
        except Exception as e:
            print(f"Gemini Exception in what_changed: {e}")

    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key and _check_rate_limit("groq"):
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
            payload = {
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": "You are a helpful carbon-footprint analysis assistant. Always output valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                "response_format": {"type": "json_object"},
            }
            from request_logging import log_api_request
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            log_api_request("POST", url, headers=headers, status_code=response.status_code)
            if response.status_code == 200:
                data = response.json()
                raw_text = data["choices"][0]["message"]["content"]
                return json.loads(raw_text)
        except Exception as e:
            print(f"Groq Exception in what_changed: {e}")

    return None


def generate_what_changed_analysis(current: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any] | None:
    diff = compute_assessment_diff(current, previous)
    if diff is None:
        return None

    if diff["footprint"]["delta"] == 0 and not diff["changes"]:
        return {
            "summary": "Your footprint hasn't changed since your last assessment — your inputs and total are identical.",
            "biggest_driver": "No change detected.",
            "suggestion": "Try adjusting one behavior at a time (e.g., switching transport or reducing electricity) to see its impact on your footprint.",
        }

    prompt = _build_ai_prompt(diff)
    ai_result = _call_llm(prompt)

    if ai_result is not None and "summary" in ai_result:
        return {
            "summary": ai_result.get("summary", ""),
            "biggest_driver": ai_result.get("biggest_driver", ""),
            "suggestion": ai_result.get("suggestion", ""),
            "diff": diff,
        }

    return _fallback_analysis(diff)


def _fallback_analysis(diff: dict[str, Any]) -> dict[str, Any]:
    parts = []
    if diff["footprint"]["delta"] > 0:
        parts.append(f"Your carbon footprint increased by {diff['footprint']['pct']}% ({diff['footprint']['delta']:+.0f} kg CO₂) compared to your last assessment.")
    elif diff["footprint"]["delta"] < 0:
        parts.append(f"Great work! Your carbon footprint decreased by {abs(diff['footprint']['pct'])}% ({diff['footprint']['delta']:+.0f} kg CO₂) compared to your last assessment.")
    else:
        parts.append("Your carbon footprint stayed the same as your last assessment.")

    if diff["changes"]:
        changed = [f"{fld.replace('_', ' ')} ({ch['from']} → {ch['to']})" for fld, ch in diff["changes"].items()]
        parts.append(f"The main changes were in: {', '.join(changed)}.")

    driver_text = ""
    if diff["top_contributor"]:
        cd = diff["category_deltas"][diff["top_contributor"]]
        driver_text = f"The biggest factor was **{diff['top_contributor']}**, which {cd['direction']} by {abs(cd['delta']):.0f} kg CO₂."

    suggestion = _generate_fallback_suggestion(diff)

    return {
        "summary": " ".join(parts),
        "biggest_driver": driver_text,
        "suggestion": suggestion,
        "diff": diff,
    }


def _generate_fallback_suggestion(diff: dict[str, Any]) -> str:
    suggestions = []
    for field in diff.get("changes", {}):
        ch = diff["changes"][field]
        if field == "transport" and ch["to"] == "Car" and ch["from"] in ("Bike", "Public Transport", "Walking"):
            suggestions.append("Consider switching back to public transport or active commute options to reduce emissions.")
        elif field == "distance" and isinstance(ch["to"], (int, float)) and isinstance(ch["from"], (int, float)) and ch["to"] > ch["from"]:
            suggestions.append("Try to reduce your daily travel distance where possible — carpooling or combining trips can help.")
        elif field == "electricity" and isinstance(ch["to"], (int, float)) and isinstance(ch["from"], (int, float)) and ch["to"] > ch["from"]:
            suggestions.append("Your electricity usage went up. Consider energy-efficient appliances and turning off devices when not in use.")
        elif field == "diet" and ch["to"] == "Non-Vegetarian" and ch["from"] == "Vegetarian":
            suggestions.append("Switching back to a plant-based diet can significantly lower your food-related carbon footprint.")
        elif field == "flights" and isinstance(ch["to"], (int, float)) and isinstance(ch["from"], (int, float)) and ch["to"] > ch["from"]:
            suggestions.append("Try to consolidate trips or choose alternative transport for shorter distances.")

    if diff["footprint"]["delta"] < 0 and not suggestions:
        suggestions.append("You're on the right track! Keep up these eco-friendly habits and look for one more area to improve.")

    if not suggestions:
        suggestions.append("Review each category in your breakdown to identify one small change you can make this week.")

    return " ".join(suggestions)


def render_what_changed_ui(diff_result: dict[str, Any] | None) -> None:
    if diff_result is None:
        return

    diff = diff_result.get("diff")

    with st.container():
        st.markdown("### What Changed?")

        col1, col2, col3 = st.columns(3)
        with col1:
            arrow = "🔺" if diff["footprint"]["delta"] > 0 else "🔻" if diff["footprint"]["delta"] < 0 else "➖"
            st.metric(
                "Footprint Change",
                f"{diff['footprint']['to']:.0f} kg",
                delta=f"{diff['footprint']['delta']:+.0f} kg ({diff['footprint']['pct']:+.1f}%)",
            )
        with col2:
            st.metric(
                "Eco Score Change",
                f"{diff['eco_score']['to']}/100",
                delta=f"{diff['eco_score']['delta']:+d}",
            )
        with col3:
            if diff["top_contributor"]:
                cd = diff["category_deltas"][diff["top_contributor"]]
                st.metric(
                    "Biggest Driver",
                    diff["top_contributor"],
                    delta=f"{cd['delta']:+.0f} kg",
                )

        st.markdown("---")

        if diff["changes"]:
            st.markdown("**Input Changes**")
            for field, change in diff["changes"].items():
                st.markdown(f"- {field.replace('_', ' ')}: **{change['from']}** → **{change['to']}**")

        st.markdown("**AI Summary**")
        st.info(diff_result["summary"])

        if diff_result.get("biggest_driver"):
            st.markdown("**Key Driver**")
            st.markdown(diff_result["biggest_driver"])

        if diff_result.get("suggestion"):
            st.markdown("**Suggestion**")
            st.success(diff_result["suggestion"])

        st.markdown("---")
