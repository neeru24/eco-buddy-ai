"""Tests for secure logging and operation correlation IDs."""

from __future__ import annotations

import copy
import json
import logging
import sys

from log_sanitizer import (
    REDACTED,
    get_operation_id,
    mask_email,
    operation_context,
    sanitize_data,
    sanitize_string,
)
from logging_config import (
    JsonLogFormatter,
    SecureLogFilter,
    SecureTextFormatter,
)


def test_sensitive_keys_are_redacted_recursively():
    original = {
        "user": {
            "email": "jane@example.com",
            "password": "do-not-log",
            "profile": {
                "api_key": "secret-key",
                "display_name": "Jane",
            },
        },
        "items": [
            {"token": "abc123"},
            {"safe": "value"},
        ],
    }
    snapshot = copy.deepcopy(original)

    sanitized = sanitize_data(original)

    assert sanitized["user"]["password"] == REDACTED
    assert sanitized["user"]["profile"]["api_key"] == REDACTED
    assert sanitized["items"][0]["token"] == REDACTED
    assert sanitized["user"]["email"] == "j***@example.com"
    assert sanitized["user"]["profile"]["display_name"] == "Jane"
    assert original == snapshot


def test_common_string_patterns_are_redacted():
    value = (
        "Authorization: Bearer abc.def.ghi "
        "api_key=super-secret password=hunter2 "
        "database_url=postgresql://admin:pass@db.example.com/app "
        "https://example.com/callback?token=url-secret "
        "contact jane@example.com"
    )
    sanitized = sanitize_string(value)

    for secret in (
        "abc.def.ghi",
        "super-secret",
        "hunter2",
        "admin:pass",
        "url-secret",
        "jane@example.com",
    ):
        assert secret not in sanitized
    assert sanitized.count(REDACTED) >= 5
    assert "j***@example.com" in sanitized


def test_private_key_is_redacted():
    value = (
        "-----BEGIN PRIVATE KEY-----\n"
        "very-secret-key-material\n"
        "-----END PRIVATE KEY-----"
    )
    sanitized = sanitize_string(value)
    assert "very-secret-key-material" not in sanitized
    assert REDACTED in sanitized


def test_safe_values_remain_unchanged():
    assert sanitize_string(
        "Assessment saved successfully for user 42"
    ) == "Assessment saved successfully for user 42"
    assert sanitize_data({"status": "ok", "count": 3}) == {
        "status": "ok",
        "count": 3,
    }


def test_email_masking():
    assert mask_email("jidnyasa@example.com") == "j***@example.com"
    assert mask_email("a@example.com") == "a***@example.com"


def test_operation_context_reuses_id_and_restores_parent():
    assert get_operation_id() is None
    with operation_context("assessment-42") as outer:
        assert get_operation_id() == outer
        with operation_context() as inner:
            assert inner != outer
            assert get_operation_id() == inner
        assert get_operation_id() == outer
    assert get_operation_id() is None


def test_independent_contexts_receive_different_ids():
    with operation_context() as first:
        pass
    with operation_context() as second:
        pass
    assert first != second


def test_untrusted_operation_id_is_normalised():
    with operation_context("bad\nvalue with spaces") as operation_id:
        assert operation_id.startswith("op-")
        assert "\n" not in operation_id
        assert " " not in operation_id


def test_secure_filter_sanitizes_rendered_message_and_extras():
    record = logging.LogRecord(
        name="eco_buddy.test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="Login failed for %s using token=%s",
        args=("jane@example.com", "secret-token"),
        exc_info=None,
    )
    record.event = "login_failed"
    record.context = {
        "password": "secret-password",
        "safe": "kept",
    }

    with operation_context("op-123"):
        assert SecureLogFilter().filter(record)

    rendered = record.getMessage()
    assert "jane@example.com" not in rendered
    assert "j***@example.com" in rendered
    assert "secret-token" not in rendered
    assert REDACTED in rendered
    assert record.operation_id == "op-123"
    assert record.context["password"] == REDACTED
    assert record.context["safe"] == "kept"


def test_text_formatter_redacts_full_traceback():
    try:
        raise RuntimeError(
            "provider failed with api_key=provider-secret"
        )
    except RuntimeError:
        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="eco_buddy.provider",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="Provider request failed",
        args=(),
        exc_info=exc_info,
    )
    SecureLogFilter().filter(record)
    output = SecureTextFormatter(
        "%(levelname)s %(operation_id)s %(message)s"
    ).format(record)

    assert "provider-secret" not in output
    assert REDACTED in output
    assert "Traceback" in output


def test_json_formatter_emits_expected_fields():
    record = logging.LogRecord(
        name="eco_buddy.background_tasks",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="External provider request failed for %s",
        args=("jane@example.com",),
        exc_info=None,
    )
    record.event = "task_failed"
    record.task_id = "task-7"
    record.authorization = "Bearer secret-value"

    with operation_context("operation-7"):
        SecureLogFilter().filter(record)

    payload = json.loads(JsonLogFormatter().format(record))

    assert payload["level"] == "ERROR"
    assert payload["logger"] == "eco_buddy.background_tasks"
    assert payload["operation_id"] == "operation-7"
    assert payload["event"] == "task_failed"
    assert "jane@example.com" not in payload["message"]
    assert payload["context"]["task_id"] == "task-7"
    assert payload["context"]["authorization"] == REDACTED


def test_plain_text_formatter_includes_operation_id():
    record = logging.LogRecord(
        name="eco_buddy.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Safe event",
        args=(),
        exc_info=None,
    )
    with operation_context("operation-text"):
        SecureLogFilter().filter(record)

    formatter = SecureTextFormatter(
        "%(levelname)s %(operation_id)s %(message)s"
    )
    assert formatter.format(record) == (
        "INFO operation-text Safe event"
    )


def test_circular_data_is_handled_without_mutation():
    original = {"safe": "value"}
    original["self"] = original
    sanitized = sanitize_data(original)
    assert sanitized["safe"] == "value"
    assert sanitized["self"] == "[CIRCULAR]"
    assert original["self"] is original
