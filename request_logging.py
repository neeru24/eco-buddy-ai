"""
Lightweight Request Logging Utility for EcoBuddy AI.

Provides sanitized API request logging integrated with the project's
logging configuration (logging_config.py). Ensures sensitive headers,
auth tokens, and confidential query credentials are never written to logs.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Mapping, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse, unquote

logger = logging.getLogger("api_request")

SENSITIVE_HEADER_KEYS = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-goog-api-key",
    "api-key",
    "apikey",
    "token",
    "bearer",
    "secret",
    "proxy-authorization",
}

SENSITIVE_QUERY_PARAMS = {
    "key",
    "api_key",
    "apikey",
    "token",
    "access_token",
    "secret",
    "password",
    "auth",
}


def sanitize_headers(headers: Optional[Mapping[str, Any]]) -> dict[str, str]:
    """Return a copy of headers with sensitive authorization/key values redacted."""
    if not headers:
        return {}
    sanitized = {}
    for key, value in headers.items():
        if str(key).lower() in SENSITIVE_HEADER_KEYS:
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = str(value)
    return sanitized


def sanitize_url(url: str) -> str:
    """Return a URL with sensitive query parameter values (e.g. key, api_key) redacted."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        if not parsed.query:
            return url
        query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
        sanitized_pairs = []
        for k, v in query_pairs:
            if k.lower() in SENSITIVE_QUERY_PARAMS:
                sanitized_pairs.append((k, "[REDACTED]"))
            else:
                sanitized_pairs.append((k, v))
        new_query = unquote(urlencode(sanitized_pairs, safe="[]"))
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        ))
    except Exception:
        return url


def log_api_request(
    method: str,
    url: str,
    headers: Optional[Mapping[str, Any]] = None,
    status_code: Optional[int] = None,
) -> str:
    """
    Log an API request with ISO-8601 timestamp, HTTP method, sanitized endpoint path,
    sanitized headers, and optional status code.

    Returns the formatted log message string.
    """
    iso_timestamp = datetime.now(timezone.utc).isoformat()
    sanitized_endpoint = sanitize_url(url)
    sanitized_hdrs = sanitize_headers(headers)

    method_str = (method or "GET").upper()
    status_part = f" - Status: {status_code}" if status_code is not None else ""
    headers_part = f" - Headers: {sanitized_hdrs}" if sanitized_hdrs else ""

    log_msg = f"[{iso_timestamp}] [{method_str}] {sanitized_endpoint}{status_part}{headers_part}"
    logger.info(log_msg)
    return log_msg
