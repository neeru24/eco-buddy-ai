"""Lightweight session state management utilities for EcoBuddy AI."""

from typing import Any, Mapping
import time
import streamlit as st


def ensure_session_state(defaults: Mapping[str, Any]) -> None:
    """Initialize missing key-value pairs in st.session_state from a defaults dictionary."""
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_session_state_if_changed(key: str, value: Any) -> bool:
    """Set a session state key only if its value actually changed, avoiding redundant reruns."""
    if key not in st.session_state or st.session_state[key] != value:
        st.session_state[key] = value
        return True
    return False


DEFAULT_SESSION_TIMEOUT = 30 * 60


def update_last_activity() -> None:
    """Update the last activity timestamp using monotonic-safe time.time()."""
    st.session_state["last_activity"] = time.time()


def check_session_timeout(timeout_seconds: int = DEFAULT_SESSION_TIMEOUT) -> bool:
    """Return True if the session has exceeded the timeout_seconds."""
    if "last_activity" not in st.session_state:
        return False
    return (time.time() - st.session_state["last_activity"]) > timeout_seconds


def clear_auth_session() -> None:
    """Clear only authentication-related session keys safely."""
    auth_keys = ["user_id", "username", "anonymous_leaderboard", "last_activity"]
    for key in auth_keys:
        st.session_state.pop(key, None)
