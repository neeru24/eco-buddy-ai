"""Central secure logging configuration for EcoBuddy AI."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from typing import Any

from log_sanitizer import (
    get_operation_id,
    sanitize_data,
    sanitize_string,
)


LOG_DIR = os.environ.get("LOG_DIR", "logs")
LOG_FILE = os.path.join(LOG_DIR, "ecobuddy.log")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.environ.get("LOG_FORMAT", "text").strip().lower()
LOG_MASK_EMAILS = (
    os.environ.get("LOG_MASK_EMAILS", "true").strip().lower()
    not in {"0", "false", "no"}
)

_STANDARD_KEYS = set(logging.makeLogRecord({}).__dict__.keys())


class SecureLogFilter(logging.Filter):
    """Attach operation IDs and sanitize all record data."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.operation_id = get_operation_id() or "-"

        # Render first so secrets supplied through %-format arguments can be
        # recognized together with their key in the message template.
        try:
            rendered_message = record.getMessage()
        except (TypeError, ValueError):
            rendered_message = str(record.msg)

        record.msg = sanitize_string(
            rendered_message,
            mask_emails=LOG_MASK_EMAILS,
        )
        record.args = ()

        for key, value in list(record.__dict__.items()):
            if key in _STANDARD_KEYS or key in {
                "message",
                "asctime",
                "operation_id",
            }:
                continue
            record.__dict__[key] = sanitize_data(
                value,
                mask_emails=LOG_MASK_EMAILS,
            )

        if record.stack_info:
            record.stack_info = sanitize_string(
                record.stack_info,
                mask_emails=LOG_MASK_EMAILS,
            )

        return True


class SecureTextFormatter(logging.Formatter):
    """Text formatter that sanitizes the full rendered traceback."""

    def formatException(self, exc_info: tuple | None) -> str:
        return sanitize_string(
            super().formatException(exc_info),
            mask_emails=LOG_MASK_EMAILS,
        )

    def formatStack(self, stack_info: str) -> str:
        return sanitize_string(
            super().formatStack(stack_info),
            mask_emails=LOG_MASK_EMAILS,
        )


class JsonLogFormatter(logging.Formatter):
    """Format structured logs as one JSON object per line."""

    def formatException(self, exc_info: tuple | None) -> str:
        return sanitize_string(
            super().formatException(exc_info),
            mask_emails=LOG_MASK_EMAILS,
        )

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=timezone.utc,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "operation_id": getattr(record, "operation_id", "-"),
            "event": getattr(record, "event", None),
            "message": record.getMessage(),
        }

        context = {}
        for key, value in record.__dict__.items():
            if key in _STANDARD_KEYS or key in {
                "message",
                "asctime",
                "operation_id",
                "event",
            }:
                continue
            context[key] = sanitize_data(
                value,
                mask_emails=LOG_MASK_EMAILS,
            )

        if context:
            payload["context"] = context
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack"] = sanitize_string(
                record.stack_info,
                mask_emails=LOG_MASK_EMAILS,
            )

        return json.dumps(
            sanitize_data(payload, mask_emails=LOG_MASK_EMAILS),
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )


def _resolve_level(value: str | int) -> int:
    if isinstance(value, int):
        return value
    level = getattr(logging, str(value).upper(), logging.INFO)
    return level if isinstance(level, int) else logging.INFO


def setup_logging(
    *,
    log_format: str | None = None,
    force: bool = True,
) -> logging.Logger:
    """Configure secure console and rotating-file logging."""
    os.makedirs(LOG_DIR, exist_ok=True)

    selected = (
        log_format.strip().lower()
        if log_format is not None
        else LOG_FORMAT
    )
    if selected not in {"text", "json"}:
        selected = "text"

    secure_filter = SecureLogFilter()
    formatter: logging.Formatter
    if selected == "json":
        formatter = JsonLogFormatter()
    else:
        formatter = SecureTextFormatter(
            "%(asctime)s | %(levelname)s | %(name)s | "
            "operation_id=%(operation_id)s | %(message)s"
        )

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(secure_filter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(secure_filter)

    root_logger = logging.getLogger()
    root_logger.setLevel(_resolve_level(LOG_LEVEL))
    if force:
        root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    return root_logger


def log_runtime_error(
    error: BaseException | str,
    *,
    logger: logging.Logger | None = None,
    event: str = "runtime_error",
    level: int | str = logging.ERROR,
    context: dict[str, Any] | None = None,
    user_id: Any | None = None,
    operation_id: str | None = None,
    exc_info: bool | tuple | None = True,
    message: str | None = None,
    stack_info: bool = False,
    **extra_kwargs: Any,
) -> dict[str, Any]:
    """Log a structured runtime error with sanitized diagnostics and correlation metadata.

    Args:
        error: The exception instance or error string to log.
        logger: Target logger instance (defaults to 'eco_buddy.runtime').
        event: Stable machine-readable event identifier (e.g. 'db_query_failed').
        level: Logging level (e.g. logging.ERROR).
        context: Optional dictionary of structured context attributes.
        user_id: Optional user identifier for correlation.
        operation_id: Optional explicit operation ID.
        exc_info: Whether to attach exception traceback info.
        message: Optional custom log message (defaults to error string).
        stack_info: Whether to attach caller stack info.
        **extra_kwargs: Additional structured metadata fields.

    Returns:
        The sanitized structured payload attached to the log record.
    """
    target_logger = logger or logging.getLogger("eco_buddy.runtime")
    resolved_level = _resolve_level(level)

    if isinstance(error, BaseException):
        error_type = error.__class__.__name__
        error_code = getattr(error, "code", error_type)
        error_message = getattr(error, "message", str(error))
        error_details = getattr(error, "details", None)
        exc = error if exc_info is True else exc_info
    else:
        error_type = "RuntimeError"
        error_code = "RUNTIME_ERROR"
        error_message = str(error)
        error_details = None
        exc = None if exc_info is True else exc_info

    log_msg = message or f"Runtime error [{error_code}]: {error_message}"

    payload: dict[str, Any] = {
        "event": event,
        "error_code": str(error_code),
        "error_type": error_type,
        "error_message": sanitize_string(str(error_message), mask_emails=LOG_MASK_EMAILS),
    }

    if error_details:
        payload["error_details"] = sanitize_data(error_details, mask_emails=LOG_MASK_EMAILS)

    if user_id is not None:
        payload["user_id"] = sanitize_data(user_id, mask_emails=LOG_MASK_EMAILS)

    op_id = operation_id or get_operation_id()
    if op_id:
        payload["operation_id"] = op_id

    merged_context: dict[str, Any] = {}
    if context:
        merged_context.update(context)
    if extra_kwargs:
        merged_context.update(extra_kwargs)

    if merged_context:
        payload["context"] = sanitize_data(merged_context, mask_emails=LOG_MASK_EMAILS)

    target_logger.log(
        resolved_level,
        log_msg,
        extra=payload,
        exc_info=exc,
        stack_info=stack_info,
    )

    return payload


def log_on_error(
    *,
    logger: logging.Logger | None = None,
    event: str | None = None,
    level: int | str = logging.ERROR,
    default_return: Any = None,
    reraise: bool = True,
    context_fn: Any | None = None,
    exclude_exceptions: tuple[type[BaseException], ...] = (),
):
    """Decorator to catch and log runtime errors in functions with structured telemetry.

    Args:
        logger: Logger to receive structured error record.
        event: Custom event name. Defaults to '{func_name}_failed'.
        level: Logging level (default logging.ERROR).
        default_return: Value returned when reraise=False and an exception occurs.
        reraise: If True, re-raises the caught exception after logging.
        context_fn: Optional callable (args, kwargs) -> dict for custom context.
        exclude_exceptions: Tuple of exception types to bypass without logging.
    """
    import functools

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BaseException as exc:
                if exclude_exceptions and isinstance(exc, exclude_exceptions):
                    raise

                evt = event or f"{func.__name__}_failed"
                ctx = {
                    "function": func.__qualname__,
                    "module": func.__module__,
                }
                if context_fn is not None:
                    try:
                        custom_ctx = context_fn(*args, **kwargs)
                        if isinstance(custom_ctx, dict):
                            ctx.update(custom_ctx)
                    except Exception:
                        pass

                log_runtime_error(
                    exc,
                    logger=logger or logging.getLogger(func.__module__),
                    event=evt,
                    level=level,
                    context=ctx,
                    exc_info=True,
                )
                if reraise:
                    raise
                return default_return

        return wrapper

    return decorator


from contextlib import contextmanager


@contextmanager
def runtime_error_boundary(
    name: str = "runtime_operation",
    *,
    logger: logging.Logger | None = None,
    event: str | None = None,
    level: int | str = logging.ERROR,
    reraise: bool = True,
    context: dict[str, Any] | None = None,
    user_id: Any | None = None,
):
    """Context manager that catches, logs structured telemetry for, and optionally suppresses runtime errors."""
    try:
        yield
    except BaseException as exc:
        evt = event or f"{name}_failed"
        merged_ctx = {"operation_name": name}
        if context:
            merged_ctx.update(context)

        log_runtime_error(
            exc,
            logger=logger or logging.getLogger("eco_buddy.boundary"),
            event=evt,
            level=level,
            context=merged_ctx,
            user_id=user_id,
            exc_info=True,
        )
        if reraise:
            raise

