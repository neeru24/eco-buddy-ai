"""Unit tests for structured runtime error logging, decorator, and boundaries."""

from __future__ import annotations

import logging
import pytest

from errors import AppError, ConfigurationError, ExternalServiceError, ValidationError
from log_sanitizer import REDACTED, operation_context
from logging_config import (
    log_on_error,
    log_runtime_error,
    runtime_error_boundary,
)


class DummyLogHandler(logging.Handler):
    """Memory log handler capturing LogRecords for assertion."""

    def __init__(self):
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord):
        self.records.append(record)


@pytest.fixture
def capture_logger():
    test_logger = logging.getLogger("test.runtime_error_logger")
    test_logger.setLevel(logging.DEBUG)
    handler = DummyLogHandler()
    test_logger.addHandler(handler)
    yield test_logger, handler
    test_logger.removeHandler(handler)


def test_log_runtime_error_with_standard_exception(capture_logger):
    test_logger, handler = capture_logger

    try:
        raise ValueError("Invalid calculation multiplier password=secret")
    except ValueError as exc:
        payload = log_runtime_error(
            exc,
            logger=test_logger,
            event="calculation_failed",
            context={"multiplier": -1.5, "api_key": "raw-key-123"},
            user_id="user@example.com",
        )

    assert payload["event"] == "calculation_failed"
    assert payload["error_type"] == "ValueError"
    assert payload["error_code"] == "ValueError"
    assert "secret" not in payload["error_message"]
    assert REDACTED in payload["error_message"]
    assert payload["context"]["api_key"] == REDACTED
    assert payload["context"]["multiplier"] == -1.5
    assert payload["user_id"] == "u***@example.com"

    assert len(handler.records) == 1
    rec = handler.records[0]
    assert rec.levelno == logging.ERROR
    assert rec.event == "calculation_failed"


def test_log_runtime_error_with_app_error(capture_logger):
    test_logger, handler = capture_logger

    err = ExternalServiceError(
        "Climatiq API unreachable",
        details="Connection timed out after 5000ms authorization=Bearer secret_token",
    )

    with operation_context("op-calc-999"):
        payload = err.log(
            logger=test_logger,
            context={"endpoint": "/estimate"},
        )

    assert payload["event"] == "external_service_error_error"
    assert payload["error_code"] == "EXTERNAL_SERVICE_ERROR"
    assert payload["error_type"] == "ExternalServiceError"
    assert payload["error_message"] == "Climatiq API unreachable"
    assert payload["operation_id"] == "op-calc-999"
    assert "secret_token" not in payload["error_details"]
    assert REDACTED in payload["error_details"]


def test_log_runtime_error_with_string_message(capture_logger):
    test_logger, handler = capture_logger

    payload = log_runtime_error(
        "Critical background failure",
        logger=test_logger,
        event="background_crash",
        level=logging.CRITICAL,
    )

    assert payload["event"] == "background_crash"
    assert payload["error_code"] == "RUNTIME_ERROR"
    assert payload["error_type"] == "RuntimeError"
    assert len(handler.records) == 1
    assert handler.records[0].levelno == logging.CRITICAL


def test_log_on_error_decorator_reraise(capture_logger):
    test_logger, handler = capture_logger

    @log_on_error(logger=test_logger, event="custom_div_zero", reraise=True)
    def risky_divide(a, b):
        return a / b

    with pytest.raises(ZeroDivisionError):
        risky_divide(10, 0)

    assert len(handler.records) == 1
    rec = handler.records[0]
    assert rec.event == "custom_div_zero"
    assert rec.error_code == "ZeroDivisionError"
    assert rec.context["function"] == "test_log_on_error_decorator_reraise.<locals>.risky_divide"


def test_log_on_error_decorator_suppress_and_fallback(capture_logger):
    test_logger, handler = capture_logger

    @log_on_error(logger=test_logger, default_return={"status": "fallback"}, reraise=False)
    def faulty_fetch(url):
        raise ConnectionError("Server unavailable")

    result = faulty_fetch("https://api.example.com")
    assert result == {"status": "fallback"}
    assert len(handler.records) == 1
    assert handler.records[0].error_type == "ConnectionError"


def test_log_on_error_with_custom_context_fn(capture_logger):
    test_logger, handler = capture_logger

    def extract_ctx(item_id, count=1):
        return {"item_id": item_id, "count": count}

    @log_on_error(logger=test_logger, context_fn=extract_ctx, default_return=None, reraise=False)
    def process_item(item_id, count=1):
        raise ValueError("Invalid item count")

    process_item("item-42", count=10)
    assert len(handler.records) == 1
    assert handler.records[0].context["item_id"] == "item-42"
    assert handler.records[0].context["count"] == 10


def test_runtime_error_boundary_reraise(capture_logger):
    test_logger, handler = capture_logger

    with pytest.raises(KeyError):
        with runtime_error_boundary("session_lookup", logger=test_logger, reraise=True):
            _ = {}["nonexistent_key"]

    assert len(handler.records) == 1
    assert handler.records[0].event == "session_lookup_failed"
    assert handler.records[0].error_type == "KeyError"


def test_runtime_error_boundary_suppress(capture_logger):
    test_logger, handler = capture_logger

    executed_after = False
    with runtime_error_boundary("safe_section", logger=test_logger, reraise=False, context={"mode": "test"}):
        raise RuntimeError("Non-fatal step error")
    executed_after = True

    assert executed_after is True
    assert len(handler.records) == 1
    assert handler.records[0].context["mode"] == "test"
    assert handler.records[0].context["operation_name"] == "safe_section"
