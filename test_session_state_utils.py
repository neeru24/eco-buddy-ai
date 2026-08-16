"""Unit tests for session_state_utils module."""

import pytest
from unittest.mock import patch
import session_state_utils as ssu


def test_ensure_session_state():
    mock_state = {"a": 1}
    with patch("session_state_utils.st.session_state", mock_state):
        ssu.ensure_session_state({"a": 10, "b": 20})
        assert mock_state["a"] == 1
        assert mock_state["b"] == 20


def test_set_session_state_if_changed():
    mock_state = {"foo": "bar"}
    with patch("session_state_utils.st.session_state", mock_state):
        # Value unchanged -> returns False
        changed = ssu.set_session_state_if_changed("foo", "bar")
        assert not changed
        assert mock_state["foo"] == "bar"

        # Value changed -> returns True
        changed = ssu.set_session_state_if_changed("foo", "baz")
        assert changed
        assert mock_state["foo"] == "baz"

        # New key -> returns True
        changed = ssu.set_session_state_if_changed("new_key", 100)
        assert changed
        assert mock_state["new_key"] == 100


@patch("session_state_utils.time")
def test_update_last_activity(mock_time):
    mock_time.time.return_value = 1000.0
    mock_state = {}
    with patch("session_state_utils.st.session_state", mock_state):
        ssu.update_last_activity()
        assert mock_state["last_activity"] == 1000.0


@patch("session_state_utils.time")
def test_check_session_timeout_active(mock_time):
    # Session is active (timeout not exceeded)
    mock_time.time.return_value = 2000.0
    mock_state = {"last_activity": 1000.0}
    with patch("session_state_utils.st.session_state", mock_state):
        # 1000 seconds elapsed, timeout is 1800
        assert not ssu.check_session_timeout()


@patch("session_state_utils.time")
def test_check_session_timeout_expired(mock_time):
    # Session is expired (timeout exceeded)
    mock_time.time.return_value = 3000.0
    mock_state = {"last_activity": 1000.0}
    with patch("session_state_utils.st.session_state", mock_state):
        # 2000 seconds elapsed, timeout is 1800
        assert ssu.check_session_timeout()


def test_check_session_timeout_no_activity():
    # Session with no last_activity initializes correctly
    mock_state = {}
    with patch("session_state_utils.st.session_state", mock_state):
        assert not ssu.check_session_timeout()


@patch("session_state_utils.time")
def test_check_session_timeout_boundary(mock_time):
    # Timeout boundary (exactly timeout_seconds)
    mock_time.time.return_value = ssu.DEFAULT_SESSION_TIMEOUT
    mock_state = {"last_activity": 0.0}
    with patch("session_state_utils.st.session_state", mock_state):
        assert not ssu.check_session_timeout()


def test_clear_auth_session():
    # clear_auth_session() is safe when auth keys are already missing
    mock_state = {
        "user_id": 123,
        "username": "testuser",
        "anonymous_leaderboard": False,
        "last_activity": 1000.0,
        "draft_data": "important",
        "theme": "dark"
    }
    with patch("session_state_utils.st.session_state", mock_state):
        ssu.clear_auth_session()
        assert "user_id" not in mock_state
        assert "username" not in mock_state
        assert "anonymous_leaderboard" not in mock_state
        assert "last_activity" not in mock_state
        assert mock_state["draft_data"] == "important"
        assert mock_state["theme"] == "dark"

        # Safe to call again
        ssu.clear_auth_session()
