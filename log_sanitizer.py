"""Security-focused log sanitization and operation correlation helpers."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
import hashlib
import re
import uuid
from typing import Any, Iterator, Mapping


REDACTED = "[REDACTED]"
MAX_LOG_VALUE_LENGTH = 2_000

_OPERATION_ID: ContextVar[str | None] = ContextVar(
    "eco_buddy_operation_id",
    default=None,
)

SENSITIVE_KEYS = {
    "access_token",
    "api_key",
    "apikey",
    "authorization",
    "client_secret",
    "cookie",
    "database_url",
    "db_url",
    "jwt",
    "otp",
    "password",
    "password_hash",
    "private_key",
    "refresh_token",
    "secret",
    "session",
    "session_id",
    "token",
}

_EMAIL_PATTERN = re.compile(
    r"(?<![\w.+-])([A-Za-z0-9._%+-]+)"
    r"@([A-Za-z0-9.-]+\.[A-Za-z]{2,})"
)
_BEARER_PATTERN = re.compile(
    r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"
)
_KEY_VALUE_SECRET_PATTERN = re.compile(
    r"(?i)\b("
    r"api[_-]?key|access[_-]?token|refresh[_-]?token|"
    r"authorization|password(?:_hash)?|secret|otp|jwt|token|"
    r"database[_-]?url|db[_-]?url|private[_-]?key"
    r")\b(\s*[:=]\s*)([^\s,;]+)"
)
_DATABASE_URL_PATTERN = re.compile(
    r"(?i)\b(postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis)"
    r"://[^@\s:/]+:[^@\s]+@[^\s]+"
)
_URL_QUERY_SECRET_PATTERN = re.compile(
    r"(?i)([?&](?:token|api_key|apikey|key|secret|password)=)"
    r"([^&#\s]+)"
)
_PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?"
    r"-----END [A-Z ]*PRIVATE KEY-----",
    re.DOTALL,
)


def get_operation_id() -> str | None:
    """Return the current operation correlation ID."""
    return _OPERATION_ID.get()


def new_operation_id() -> str:
    """Generate an opaque operation correlation ID."""
    return str(uuid.uuid4())


def _normalise_operation_id(value: str | None) -> str:
    if value is None or not value.strip():
        return new_operation_id()

    cleaned = value.strip()
    if len(cleaned) <= 128 and re.fullmatch(
        r"[A-Za-z0-9._:-]+",
        cleaned,
    ):
        return cleaned

    digest = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:24]
    return f"op-{digest}"


@contextmanager
def operation_context(
    operation_id: str | None = None,
) -> Iterator[str]:
    """Use one correlation ID for every log emitted in the context."""
    resolved = _normalise_operation_id(operation_id)
    token: Token[str | None] = _OPERATION_ID.set(resolved)
    try:
        yield resolved
    finally:
        _OPERATION_ID.reset(token)


def mask_email(value: str) -> str:
    """Mask an email while preserving its domain."""
    match = _EMAIL_PATTERN.fullmatch(value.strip())
    if not match:
        return value
    local, domain = match.groups()
    return f"{local[:1] or '*'}***@{domain}"


def sanitize_string(
    value: str,
    *,
    mask_emails: bool = True,
    max_length: int = MAX_LOG_VALUE_LENGTH,
) -> str:
    """Redact common secret patterns from one string."""
    sanitized = _PRIVATE_KEY_PATTERN.sub(
        f"{REDACTED} PRIVATE KEY",
        value,
    )
    sanitized = _BEARER_PATTERN.sub(
        f"Bearer {REDACTED}",
        sanitized,
    )
    sanitized = _DATABASE_URL_PATTERN.sub(
        lambda match: f"{match.group(1)}://{REDACTED}",
        sanitized,
    )
    sanitized = _KEY_VALUE_SECRET_PATTERN.sub(
        lambda match: f"{match.group(1)}{match.group(2)}{REDACTED}",
        sanitized,
    )
    sanitized = _URL_QUERY_SECRET_PATTERN.sub(
        lambda match: f"{match.group(1)}{REDACTED}",
        sanitized,
    )

    if mask_emails:
        sanitized = _EMAIL_PATTERN.sub(
            lambda match: mask_email(match.group(0)),
            sanitized,
        )

    sanitized = sanitized.replace("\r", "\\r").replace("\n", "\\n")
    if len(sanitized) > max_length:
        sanitized = sanitized[: max(0, max_length - 3)] + "..."
    return sanitized


def _is_sensitive_key(key: object) -> bool:
    normalized = str(key).strip().lower().replace("-", "_")
    return normalized in SENSITIVE_KEYS or any(
        marker in normalized
        for marker in (
            "password",
            "secret",
            "token",
            "api_key",
            "apikey",
            "authorization",
            "private_key",
            "otp",
        )
    )


def sanitize_data(
    value: Any,
    *,
    mask_emails: bool = True,
    _seen: set[int] | None = None,
) -> Any:
    """Return a sanitized copy without mutating caller-owned data."""
    seen = _seen if _seen is not None else set()

    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return sanitize_string(value, mask_emails=mask_emails)

    object_id = id(value)
    if object_id in seen:
        return "[CIRCULAR]"

    if isinstance(value, Mapping):
        seen.add(object_id)
        result = {}
        for key, nested in value.items():
            safe_key = sanitize_string(str(key), mask_emails=False)
            result[safe_key] = (
                REDACTED
                if _is_sensitive_key(key)
                else sanitize_data(
                    nested,
                    mask_emails=mask_emails,
                    _seen=seen,
                )
            )
        seen.remove(object_id)
        return result

    if isinstance(value, list):
        seen.add(object_id)
        result = [
            sanitize_data(item, mask_emails=mask_emails, _seen=seen)
            for item in value
        ]
        seen.remove(object_id)
        return result

    if isinstance(value, tuple):
        seen.add(object_id)
        result = tuple(
            sanitize_data(item, mask_emails=mask_emails, _seen=seen)
            for item in value
        )
        seen.remove(object_id)
        return result

    if isinstance(value, set):
        seen.add(object_id)
        result = {
            sanitize_data(item, mask_emails=mask_emails, _seen=seen)
            for item in value
        }
        seen.remove(object_id)
        return result

    if isinstance(value, BaseException):
        return sanitize_string(
            f"{value.__class__.__name__}: {value}",
            mask_emails=mask_emails,
        )

    if hasattr(value, "__dict__"):
        try:
            return sanitize_data(
                vars(value),
                mask_emails=mask_emails,
                _seen=seen,
            )
        except (TypeError, ValueError):
            pass

    return sanitize_string(repr(value), mask_emails=mask_emails)
