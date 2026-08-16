"""
Centralized error types and response helpers for EcoBuddy AI.

Several parts of the app talk to external services or parse user-supplied
files/text (the AI Quick Log parser, OCR bill extraction, GPX / Google
Takeout location parsing, etc.). Historically these "processing" functions
swallowed the *real* reason a call failed - printing to the console or
logging a warning - and returned a bare ``None`` / empty value instead.
That forced every caller to fall back to the same generic, unhelpful
message (e.g. "Could not parse the text. Please try again.") no matter
whether the real cause was a missing API key, a network error, a rate
limit, or a malformed response.

This module defines:

* A small hierarchy of :class:`AppError` exceptions. Each carries a
  short, stable ``code`` (for logs/tests) and a human-readable
  ``message`` that says *what* went wrong and, where possible, *what to
  do about it*.
* :func:`to_error_dict` / :func:`success_dict`, which build a consistent
  ``{"success": ..., "error_code": ..., "error": ...}`` envelope for
  functions that return a result dictionary instead of raising (e.g.
  ``location_parser.parse_and_segment_file_bytes``).

How to use this in a processing function
-----------------------------------------
* Raise the most specific :class:`AppError` subclass that fits the
  failure (see the subclasses below) instead of returning
  ``None`` / ``""`` / ``False`` or only logging the exception.
* Keep ``message`` short, specific, and actionable - "Set GEMINI_API_KEY
  or GROQ_API_KEY to enable AI Quick Log." rather than "Something went
  wrong."
* Put any raw technical detail (stack traces, upstream response bodies)
  in ``details`` instead of ``message`` - it's useful in logs but too
  noisy to show directly in the UI.
* Callers that invoke the function directly should catch ``AppError``
  and show ``error.message`` to the user (see ``app.py``'s AI Quick Log
  handler for an example).
* Callers that run the function through
  ``background_tasks.submit_background_task`` don't need to catch
  anything themselves: the background task runner already captures the
  exception and exposes it via ``task.error``, which
  ``render_task_progress`` displays automatically.
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base class for all application-level, user-facing errors.

    Attributes:
        code: Short, stable, machine-readable identifier
            (e.g. ``"LLM_NOT_CONFIGURED"``). Useful for logs, tests, and
            any future JSON API responses.
        message: Human-readable, actionable description meant to be
            shown directly to the user.
        details: Optional extra technical context (e.g. the raw
            upstream error text) that is safe to log but usually too
            noisy to show in the UI.
    """

    code = "APP_ERROR"

    def __init__(self, message: str, *, code: str | None = None, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.code
        self.details = details

    def __str__(self) -> str:
        # This is what shows up e.g. as BackgroundTask.error, since
        # background_tasks.py stores str(exc).
        return self.message

    def to_log_context(self) -> dict[str, Any]:
        """Return structured diagnostic payload suitable for logging."""
        ctx: dict[str, Any] = {
            "error_code": self.code,
            "error_type": self.__class__.__name__,
            "error_message": self.message,
        }
        if self.details:
            ctx["error_details"] = self.details
        return ctx

    def log(
        self,
        *,
        logger: Any | None = None,
        event: str | None = None,
        level: int | str = 40,
        context: dict[str, Any] | None = None,
        user_id: Any | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        """Log this error with structured runtime diagnostics."""
        from logging_config import log_runtime_error

        merged_context = self.to_log_context()
        if context:
            merged_context.update(context)
        if extra:
            merged_context.update(extra)

        return log_runtime_error(
            self,
            logger=logger,
            event=event or f"{self.code.lower()}_error",
            level=level,
            context=merged_context,
            user_id=user_id,
        )



class ConfigurationError(AppError):
    """A required setting (e.g. an API key) is missing or invalid."""

    code = "CONFIGURATION_ERROR"


class RateLimitError(AppError):
    """A call was rejected because of internal or external rate limiting."""

    code = "RATE_LIMITED"


class ExternalServiceError(AppError):
    """A downstream/third-party service failed, timed out, or was unreachable."""

    code = "EXTERNAL_SERVICE_ERROR"


class ValidationError(AppError):
    """User-supplied input failed validation before processing could start."""

    code = "VALIDATION_ERROR"


class ParsingError(AppError):
    """A response or file could not be parsed into the expected shape."""

    code = "PARSING_ERROR"


def to_error_dict(error: AppError) -> dict:
    """Builds the standard error envelope for dict-returning functions.

    Used by processing functions that report success/failure through a
    return value instead of raising (e.g.
    ``location_parser.parse_and_segment_file_bytes``), so that every such
    function produces the same shape:
    ``{"success": False, "error_code": ..., "error": ..., "details": ...}``.
    """
    result = {"success": False, "error_code": error.code, "error": error.message}
    if error.details:
        result["details"] = error.details
    return result


def success_dict(**data: Any) -> dict[str, Any]:
    """Builds the standard success envelope, merged with the payload fields.

    Pairs with :func:`to_error_dict` so callers can always check the same
    ``"success"`` / ``"error_code"`` / ``"error"`` keys regardless of the
    outcome.
    """
    return {"success": True, "error_code": None, "error": None, **data}
