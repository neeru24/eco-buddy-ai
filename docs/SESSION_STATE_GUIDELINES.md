# EcoBuddy AI — Session State Guidelines

This guide summarizes best practices for using Streamlit's `st.session_state` across the project.

---

## 1. Naming Conventions

- Use `snake_case` for all session state keys (e.g., `user_id`, `transport`, `show_reset_confirm`).
- Prefix modal or page-specific state flags clearly (e.g., `show_reset_confirm`, `draft_recovery_dismissed`).
- Avoid duplicate or inconsistent keys for the same feature.

---

## 2. Initialization Patterns

- Consolidate default state initializations using `ensure_session_state(defaults)` from `session_state_utils.py`.
- Do not repeat `if "key" not in st.session_state:` checks across multiple files for shared data structures.
- Do not initialize transient state keys at app startup if they are only populated dynamically (e.g. OCR results).

```python
from session_state_utils import ensure_session_state

ensure_session_state(DEFAULT_VALUES)
```

---

## 3. Updating Session State

- Update state inside event callbacks or action handlers, avoiding unconditional writes during page rendering.
- For state values updated repeatedly in UI loops or form handlers, use `set_session_state_if_changed(key, value)` to prevent redundant state mutations and unnecessary Streamlit reruns.

```python
from session_state_utils import set_session_state_if_changed

if set_session_state_if_changed("anonymous_leaderboard", new_pref):
    update_user_leaderboard_preference(user_id, new_pref)
```

---

## 4. Common Anti-Patterns to Avoid

- **Subpage Auth Mutation**: Do not mutate global authentication state (`st.session_state["user_id"] = 1`) inside subpages. Always read via `st.session_state.get("user_id")` or provide local fallback values.
- **Redundant Render Writes**: Avoid writing to `st.session_state` inside render loops unless the value has legitimately changed.
- **Duplicate Initialization Checks**: Avoid repeating `if key not in st.session_state:` inside the same file or across page components.
