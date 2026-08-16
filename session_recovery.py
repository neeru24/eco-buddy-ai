"""Automatic assessment session recovery helpers."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

import streamlit as st

from database import (
    delete_assessment_draft,
    get_assessment_draft,
    save_assessment_draft,
)


DRAFT_FIELDS = (
    "region",
    "transport",
    "distance",
    "electricity",
    "diet",
    "flights",
)


@dataclass(frozen=True)
class DraftSaveResult:
    """Result of one automatic draft-save attempt."""

    saved: bool
    reason: str
    fingerprint: str | None = None


def normalise_draft(
    values: Mapping[str, Any],
    defaults: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a complete, serialisable assessment draft."""
    draft = {
        field: values.get(field, defaults[field])
        for field in DRAFT_FIELDS
    }

    draft["region"] = str(draft["region"])
    draft["transport"] = str(draft["transport"])
    draft["diet"] = str(draft["diet"])
    draft["distance"] = max(0.0, float(draft["distance"]))
    draft["electricity"] = max(0.0, float(draft["electricity"]))
    draft["flights"] = max(0, int(draft["flights"]))
    return draft


def draft_fingerprint(draft: Mapping[str, Any]) -> str:
    """Create a stable fingerprint used to avoid redundant database writes."""
    payload = json.dumps(
        {field: draft[field] for field in DRAFT_FIELDS},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def is_meaningful_draft(
    draft: Mapping[str, Any],
    defaults: Mapping[str, Any],
) -> bool:
    """Return whether a draft differs from the untouched form defaults."""
    default_draft = normalise_draft(defaults, defaults)
    current_draft = normalise_draft(draft, defaults)
    return current_draft != default_draft


def save_draft_if_changed(
    user_id: int | None,
    values: Mapping[str, Any],
    defaults: Mapping[str, Any],
    previous_fingerprint: str | None = None,
) -> DraftSaveResult:
    """Persist a meaningful draft only when its values changed."""
    if not user_id:
        return DraftSaveResult(False, "anonymous-user")

    try:
        draft = normalise_draft(values, defaults)
    except (TypeError, ValueError, KeyError):
        return DraftSaveResult(False, "invalid-values")

    if not is_meaningful_draft(draft, defaults):
        return DraftSaveResult(False, "unchanged-defaults")

    fingerprint = draft_fingerprint(draft)
    if fingerprint == previous_fingerprint:
        return DraftSaveResult(False, "already-saved", fingerprint)

    saved = save_assessment_draft(
        user_id,
        draft["transport"],
        draft["distance"],
        draft["electricity"],
        draft["diet"],
        draft["flights"],
        draft["region"],
    )

    return DraftSaveResult(
        saved=bool(saved),
        reason="saved" if saved else "database-error",
        fingerprint=fingerprint if saved else previous_fingerprint,
    )


def restore_draft_into_session(
    draft: Mapping[str, Any],
    session_state: Any,
    defaults: Mapping[str, Any],
) -> None:
    """Restore a validated draft into Streamlit session state."""
    cleaned = normalise_draft(draft, defaults)
    for field, value in cleaned.items():
        session_state[field] = value


def clear_recovery_state(session_state: Any) -> None:
    """Remove transient draft-recovery state from the active session."""
    for key in (
        "draft_recovery_prompted",
        "draft_recovery_dismissed",
        "last_draft_fingerprint",
    ):
        session_state.pop(key, None)


def render_draft_recovery_prompt(
    user_id: int | None,
    defaults: Mapping[str, Any],
) -> None:
    """Show restore/discard controls when a saved draft is available."""
    if not user_id or st.session_state.get("draft_recovery_dismissed"):
        return

    draft = get_assessment_draft(user_id)
    if not draft:
        return

    st.info(
        "📝 An unfinished assessment was recovered from your previous "
        "session. Restore it or discard it before continuing."
    )

    restore_col, discard_col, _ = st.columns([1, 1, 3])

    with restore_col:
        if st.button(
            "✅ Restore Session",
            key="restore_assessment_draft",
            use_container_width=True,
        ):
            restore_draft_into_session(
                draft,
                st.session_state,
                defaults,
            )
            st.session_state["last_draft_fingerprint"] = draft_fingerprint(
                normalise_draft(draft, defaults)
            )
            st.session_state["draft_recovery_dismissed"] = True
            st.success("Your unfinished assessment has been restored.")
            st.rerun()

    with discard_col:
        if st.button(
            "🗑️ Discard Draft",
            key="discard_assessment_draft",
            use_container_width=True,
        ):
            if delete_assessment_draft(user_id):
                st.session_state["draft_recovery_dismissed"] = True
                st.session_state.pop("last_draft_fingerprint", None)
                st.success("The saved draft has been discarded.")
                st.rerun()
            else:
                st.error("The saved draft could not be discarded.")


def autosave_session_draft(
    user_id: int | None,
    defaults: Mapping[str, Any],
) -> DraftSaveResult:
    """Save current assessment values after Streamlit widget changes."""
    result = save_draft_if_changed(
        user_id,
        st.session_state,
        defaults,
        st.session_state.get("last_draft_fingerprint"),
    )

    if result.saved and result.fingerprint:
        st.session_state["last_draft_fingerprint"] = result.fingerprint

    return result


def discard_current_draft(
    user_id: int | None,
    session_state: Any,
) -> bool:
    """Delete the persisted draft and clear recovery bookkeeping."""
    deleted = True if not user_id else delete_assessment_draft(user_id)
    if deleted:
        clear_recovery_state(session_state)
    return bool(deleted)
