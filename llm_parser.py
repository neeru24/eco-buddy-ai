import os
import json
import time
from typing import Any
import streamlit as st
from cache import cached
from cache_config import TTL_LLM_RESPONSE
from errors import ConfigurationError, RateLimitError, ExternalServiceError, ParsingError, AppError

LLM_COOLDOWN_SECONDS = 2.0

# Keys the parsed AI response must contain to be considered usable.
_REQUIRED_KEYS = ("transport", "distance", "diet")


def __getattr__(name):
    if name == "requests":
        import requests
        return requests
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def _check_rate_limit(provider: str) -> bool:
    key = f"_llm_last_call_{provider}"
    now = time.time()
    last_call = st.session_state.get(key, 0.0)
    if now - last_call < LLM_COOLDOWN_SECONDS:
        return False
    st.session_state[key] = now
    return True


def _validate_parsed_payload(raw: dict[str, Any], provider_name: str) -> dict[str, Any]:
    """Ensures the AI returned the fields the rest of the app relies on.

    Raises:
        ParsingError: if `raw` isn't a dict, or is missing one of the
            required keys (transport, distance, diet).
    """
    if not isinstance(raw, dict) or not all(k in raw for k in _REQUIRED_KEYS):
        raise ParsingError(
            f"{provider_name} responded, but the reply was missing expected fields "
            f"({', '.join(_REQUIRED_KEYS)}). Try rephrasing your description.",
            details=str(raw)[:300],
        )
    return raw


def _call_gemini(text: str, system_prompt: str, api_key: str) -> dict[str, Any]:
    """Calls the Gemini API and returns the parsed JSON payload.

    Raises:
        ExternalServiceError: the request couldn't reach Gemini, or Gemini
            responded with a non-200 status.
        ParsingError: Gemini responded with 200 but the body wasn't the
            JSON shape we expect.
    """
    import requests

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
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
    try:
        from request_logging import log_api_request
        response = requests.post(url, json=payload, timeout=10)
        log_api_request("POST", url, status_code=response.status_code)
    except requests.exceptions.RequestException as exc:
        log_api_request("POST", url)
        raise ExternalServiceError(
            "Could not reach the Gemini API (network error).", details=str(exc)
        ) from exc

    if response.status_code != 200:
        raise ExternalServiceError(
            f"Gemini API returned an error (HTTP {response.status_code}).",
            details=response.text[:500],
        )

    try:
        data = response.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(raw_text)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ParsingError(
            "Gemini returned a response that wasn't valid JSON.", details=str(exc)
        ) from exc


def _call_groq(text: str, system_prompt: str, api_key: str) -> dict[str, Any]:
    """Calls the Groq API and returns the parsed JSON payload.

    Raises:
        ExternalServiceError: the request couldn't reach Groq, or Groq
            responded with a non-200 status.
        ParsingError: Groq responded with 200 but the body wasn't the
            JSON shape we expect.
    """
    import requests

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
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
    try:
        from request_logging import log_api_request
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        log_api_request("POST", url, headers=headers, status_code=response.status_code)
    except requests.exceptions.RequestException as exc:
        log_api_request("POST", url, headers=headers)
        raise ExternalServiceError(
            "Could not reach the Groq API (network error).", details=str(exc)
        ) from exc

    if response.status_code != 200:
        raise ExternalServiceError(
            f"Groq API returned an error (HTTP {response.status_code}).",
            details=response.text[:500],
        )

    try:
        data = response.json()
        raw_text = data["choices"][0]["message"]["content"]
        return json.loads(raw_text)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ParsingError(
            "Groq returned a response that wasn't valid JSON.", details=str(exc)
        ) from exc


_PROVIDERS = (
    ("Gemini", "GEMINI_API_KEY", "gemini", _call_gemini),
    ("Groq", "GROQ_API_KEY", "groq", _call_groq),
)


@cached(ttl=TTL_LLM_RESPONSE)
def parse_quick_log(text: str) -> dict:
    """
    Parses natural language into a structured JSON using Gemini 2.5 Flash,
    falling back to Groq if Gemini fails or is unavailable.

    On success, returns a dict with keys: transport, distance, diet.

    Raises:
        ConfigurationError: neither GEMINI_API_KEY nor GROQ_API_KEY is set,
            so AI Quick Log can't run at all.
        RateLimitError: every configured provider was skipped because a
            request was already made within the last
            LLM_COOLDOWN_SECONDS.
        ExternalServiceError: at least one provider was actually called,
            but none of them could be reached or all returned an error
            response.
        ParsingError: a provider responded successfully, but its response
            could not be parsed into the expected transport/distance/diet
            shape.
    """
    system_prompt = '''You are a data extraction assistant. Extract the following information from the user's text:
1. "transport": Must be one of ["Car", "Bike", "Public Transport", "Walking"]. (Default to "Car" if unspecified).
2. "distance": The distance traveled in kilometers as a float. (Convert miles to km if necessary: 1 mile = 1.60934 km). Default to 10.0 if unspecified.
3. "diet": Must be one of ["Vegetarian", "Non-Vegetarian"]. (Default to "Vegetarian" if unspecified).

Output ONLY a raw JSON object (without markdown wrappers like ```json) with the keys: transport, distance, diet. 
Example Output:
{"transport": "Car", "distance": 24.1, "diet": "Non-Vegetarian"}
'''

    # (provider_name, error) for every provider that was actually attempted
    # (i.e. had a key configured and wasn't skipped for being called too
    # soon). Used to build a specific, useful message if every attempt fails.
    attempts: list[tuple[str, AppError]] = []

    for provider_name, env_var, rate_limit_key, call_fn in _PROVIDERS:
        api_key = os.environ.get(env_var)
        if not api_key:
            continue

        if not _check_rate_limit(rate_limit_key):
            attempts.append((
                provider_name,
                RateLimitError(f"{provider_name} was skipped: requests are limited to one every "
                                f"{LLM_COOLDOWN_SECONDS:g}s."),
            ))
            continue

        try:
            raw = call_fn(text, system_prompt, api_key)
            return _validate_parsed_payload(raw, provider_name)
        except AppError as exc:
            attempts.append((provider_name, exc))
            continue

    if not attempts:
        raise ConfigurationError(
            "AI Quick Log isn't set up yet. Ask the site administrator to configure "
            "GEMINI_API_KEY or GROQ_API_KEY."
        )

    if all(isinstance(err, RateLimitError) for _, err in attempts):
        raise RateLimitError(
            "You're sending AI Quick Log requests too quickly. Wait a couple of seconds and try again."
        )

    details = "; ".join(f"{name}: {err.message}" for name, err in attempts)
    _, last_error = attempts[-1]

    if isinstance(last_error, ParsingError):
        raise ParsingError(
            "The AI understood your text but its reply wasn't in the expected format. "
            "Try rephrasing your description.",
            details=details,
        )

    raise ExternalServiceError(
        "AI Quick Log couldn't get a response from any configured AI provider right now. "
        "Please try again in a moment.",
        details=details,
    )
