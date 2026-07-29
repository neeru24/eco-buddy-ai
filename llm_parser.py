import os
import json
import time
import requests
import re
import streamlit as st
from cache import cached
from cache_config import TTL_LLM_RESPONSE

LLM_COOLDOWN_SECONDS = 2.0


def _check_rate_limit(provider):
    key = f"_llm_last_call_{provider}"
    now = time.time()
    last_call = st.session_state.get(key, 0.0)
    if now - last_call < LLM_COOLDOWN_SECONDS:
        return False
    st.session_state[key] = now
    return True


@cached(ttl=TTL_LLM_RESPONSE)
def parse_quick_log(text: str) -> dict:
    """
    Parses natural language into a structured JSON using Gemini 2.5 Flash,
    falling back to Groq if Gemini fails or is unavailable.
    
    Expected output keys: transport, distance, diet
    """
    system_prompt = '''You are a data extraction assistant. Extract the following information from the user's text:
1. "transport": Must be one of ["Car", "Bike", "Public Transport", "Walking"]. (Default to "Car" if unspecified).
2. "distance": The distance traveled in kilometers as a float. (Convert miles to km if necessary: 1 mile = 1.60934 km). Default to 10.0 if unspecified.
3. "diet": Must be one of ["Vegetarian", "Non-Vegetarian"]. (Default to "Vegetarian" if unspecified).

Output ONLY a raw JSON object (without markdown wrappers like ```json) with the keys: transport, distance, diet. 
Example Output:
{"transport": "Car", "distance": 24.1, "diet": "Non-Vegetarian"}
'''
    
    # Try Gemini First
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key and _check_rate_limit("gemini"):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            payload = {
                "systemInstruction": {
                    "parts": [{"text": system_prompt}]
                },
                "contents": [
                    {"parts": [{"text": text}]}
                ],
                "generationConfig": {
                    "responseMimeType": "application/json"
                }
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(raw_text)
            else:
                print(f"Gemini API Error: {response.text}")
        except Exception as e:
            print(f"Gemini Exception: {e}")

    # Fallback to Groq
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key and _check_rate_limit("groq"):
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                "response_format": {"type": "json_object"}
            }
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                raw_text = data["choices"][0]["message"]["content"]
                return json.loads(raw_text)
            else:
                print(f"Groq API Error: {response.text}")
        except Exception as e:
            print(f"Groq Exception: {e}")

    # If all fails, return a default fallback structure or raise an error
    return None
