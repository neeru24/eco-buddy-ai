"""
Unit tests for request_logging module.
"""

from datetime import datetime
import logging
import pytest
from unittest.mock import patch

from request_logging import (
    log_api_request,
    sanitize_headers,
    sanitize_url,
)


def test_sanitize_headers_redacts_sensitive_keys():
    raw_headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer secret_token_123",
        "x-api-key": "my_super_secret_key",
        "x-goog-api-key": "goog_secret_key",
        "Cookie": "sessionid=xyz123",
        "User-Agent": "EcoBuddyClient/1.0",
    }
    sanitized = sanitize_headers(raw_headers)

    assert sanitized["Content-Type"] == "application/json"
    assert sanitized["User-Agent"] == "EcoBuddyClient/1.0"
    assert sanitized["Authorization"] == "[REDACTED]"
    assert sanitized["x-api-key"] == "[REDACTED]"
    assert sanitized["x-goog-api-key"] == "[REDACTED]"
    assert sanitized["Cookie"] == "[REDACTED]"


def test_sanitize_url_redacts_sensitive_query_params():
    url_with_key = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=AIzaSySecretKey"
    sanitized = sanitize_url(url_with_key)

    assert "key=[REDACTED]" in sanitized
    assert "AIzaSySecretKey" not in sanitized


def test_log_api_request_get():
    with patch("request_logging.logger.info") as mock_log:
        url = "https://api.climatiq.io/data/v1/estimate"
        headers = {"Authorization": "Bearer token123"}
        log_msg = log_api_request("GET", url, headers=headers, status_code=200)

        assert "[GET]" in log_msg
        assert url in log_msg
        assert "Status: 200" in log_msg
        assert "token123" not in log_msg
        assert "[REDACTED]" in log_msg

        # Verify ISO-8601 timestamp presence
        timestamp_part = log_msg.split("]")[0].replace("[", "")
        # Parse ISO-8601 format to verify timestamp validity
        parsed_dt = datetime.fromisoformat(timestamp_part)
        assert parsed_dt is not None
        mock_log.assert_called_once()


def test_log_api_request_post():
    with patch("request_logging.logger.info") as mock_log:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer groq_key_abc",
        }
        log_msg = log_api_request("POST", url, headers=headers, status_code=200)

        assert "[POST]" in log_msg
        assert url in log_msg
        assert "Status: 200" in log_msg
        assert "groq_key_abc" not in log_msg
        assert "[REDACTED]" in log_msg
        mock_log.assert_called_once()


def test_log_api_request_without_optional_status_or_headers():
    with patch("request_logging.logger.info") as mock_log:
        url = "https://api.example.com/v1/resource"
        log_msg = log_api_request("DELETE", url)

        assert "[DELETE]" in log_msg
        assert url in log_msg
        assert "Status:" not in log_msg
        mock_log.assert_called_once()
