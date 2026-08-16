"""Weekly sustainability challenges.

The generator and the storage functions for this feature were already in the
codebase; the page that drives them was not — the Streamlit calls had been
pasted into ``database.py`` at module scope, where they ran on import and
referenced names that do not exist there. This page is that UI, given a file
of its own and the session context it needs.
"""

import streamlit as st

from challenge_generator import generate_weekly_challenges
from database import (
    complete_weekly_challenge,
    get_completed_challenges,
    get_weekly_challenges,
    save_weekly_challenge,
    unlock_badge_in_db,
    weekly_challenges_exist,
    award_xp,
)
from styles.theme import apply_theme

# Column positions in the rows returned by get_weekly_challenges().
COL_ID = 0
COL_TITLE = 2
COL_DIFFICULTY = 3
COL_XP = 4
COL_CATEGORY = 5
COL_STATUS = 6

BADGE_THRESHOLDS = [
    (5, "eco_beginner"),
    (15, "eco_master"),
]

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()

apply_theme()

st.markdown(
    "<div class='section-header'>🏆 Weekly Challenges</div>",
    unsafe_allow_html=True,
)
st.caption(
    "Six challenges a week, picked from your own footprint rather than from a "
    "generic list."
)


def _profile():
    """The inputs the generator needs, from the last assessment if there is one."""
    analysis = st.session_state.get("analysis", {})
    return {
        "footprint": analysis.get("total", 0),
        "transport": analysis.get("transport", st.session_state.get("transport", "Car")),
        "electricity": analysis.get(
            "electricity", st.session_state.get("electricity", 200.0)
        ),
        "diet": analysis.get("diet", st.session_state.get("diet", "Vegetarian")),
        "flights": analysis.get("flights", st.session_state.get("flights", 0)),
    }


def _generate_for(user_id):
    """Generate a week's challenges and store them. Returns how many were saved."""
    profile = _profile()
    challenges = generate_weekly_challenges(
        profile["footprint"],
        profile["transport"],
        profile["electricity"],
        profile["diet"],
        profile["flights"],
    )

    for challenge in challenges:
        save_weekly_challenge(
            user_id,
            challenge["title"],
            challenge["difficulty"],
            challenge["xp"],
            challenge["category"],
        )

    return len(challenges)


if not weekly_challenges_exist(user_id):
    st.info(
        "You have no challenges for this week yet. Generate a set to get started."
    )

if st.button("🎲 Generate Weekly Challenges", type="primary"):
    if weekly_challenges_exist(user_id):
        st.info("Weekly challenges have already been generated for this week.")
    else:
        count = _generate_for(user_id)
        st.success(f"Generated {count} challenges for this week.")
        st.rerun()

st.markdown("---")

challenges = get_weekly_challenges(user_id)

if not challenges:
    st.stop()

completed = sum(1 for row in challenges if row[COL_STATUS] == "Completed")
total = len(challenges)

progress_col, xp_col = st.columns(2)
with progress_col:
    st.metric("Weekly Progress", f"{completed}/{total}")
with xp_col:
    earned_xp = sum(
        row[COL_XP] for row in challenges if row[COL_STATUS] == "Completed"
    )
    st.metric("XP Earned", earned_xp)

if total > 0:
    st.progress(completed / total)

st.markdown("### This Week")

for row in challenges:
    with st.container(border=True):
        st.subheader(row[COL_TITLE])
        st.write(f"**Difficulty:** {row[COL_DIFFICULTY]}")
        st.write(f"**XP:** {row[COL_XP]}")
        st.write(f"**Category:** {row[COL_CATEGORY]}")
        st.write(f"**Status:** {row[COL_STATUS]}")

        # The button has to be inside the loop and keyed per challenge —
        # otherwise every row renders the same widget and only the last
        # challenge can ever be completed.
        if row[COL_STATUS] != "Completed":
            if st.button(
                "Mark as Completed",
                key=f"complete_challenge_{row[COL_ID]}",
            ):
                complete_weekly_challenge(row[COL_ID])
                award_xp(
                    user_id,
                    "challenge",
                    row[COL_ID],
                    row[COL_XP],
                    row[COL_TITLE],
                )
                st.success("Challenge completed!")
                st.rerun()

st.markdown("---")
st.markdown("### 🎯 Recommended Next Step")

outstanding = [row for row in challenges if row[COL_STATUS] != "Completed"]
if outstanding:
    highest = max(outstanding, key=lambda row: row[COL_XP])
    st.success(
        f"Focus on: **{highest[COL_TITLE]}** — worth {highest[COL_XP]} XP, "
        f"the most of anything still open."
    )
else:
    st.success("Everything for this week is done. Nothing left to recommend.")

st.markdown("---")
st.markdown("### 📜 Challenge History")

history = get_completed_challenges(user_id)

if not history:
    st.info("No completed challenges yet.")
else:
    for title, difficulty, created_at in history:
        st.write(f"✅ {title} ({difficulty}) — {created_at}")

    total_completed = len(history)
    for threshold, badge_id in BADGE_THRESHOLDS:
        if total_completed >= threshold:
            unlock_badge_in_db(user_id, badge_id)
