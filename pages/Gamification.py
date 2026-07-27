import streamlit as st
import pandas as pd
import time
from database import *
from emissions import *
from recommendations import *
from ocr_utils import *
import os
import tempfile
import uuid
import plotly.graph_objects as go
import plotly.express as px
from report import generate_pdf
import gamification as gf
from marketplace import *
import energy_audit as ea
from notifications import success, error, warning, info

from styles.theme import apply_theme

user_id = st.session_state.get('user_id')
if not user_id:
    warning('Please log in from the main application page.')
    st.stop()
apply_theme()

st.markdown("<div class='section-header'>🎮 Your Eco Journey</div>", unsafe_allow_html=True)

# Header: Level, XP, Streak
total_xp = gf.get_total_xp(user_id)
level = gf.calculate_level(total_xp)
progress = gf.calculate_level_progress(total_xp)
history = get_assessments(user_id)
activities_dates = [row[1] for row in history]
streak = gf.calculate_streak(1, activities_dates)

g_col1, g_col2, g_col3 = st.columns(3)
g_col1.metric("Current Level", f"Lvl {level}")
g_col2.metric("Total XP", f"{total_xp} XP")
g_col3.metric("Current Streak", f"{streak} Days 🔥")

st.progress(progress, text=f"Progress to Level {level+1}")

st.markdown("---")
def render_challenge_card(ch_id, ch_data, user_challenges, enrolled_ids):
    with st.expander(
        f"{ch_data['title']} ({ch_data['xp']} XP) - {ch_data['category']}"
    ):
        st.write(f"Target: {ch_data['target']} {ch_data['unit']}")

        if ch_id in enrolled_ids:
            status = [
                c["status"]
                for c in user_challenges
                if c["challenge_id"] == ch_id
            ][-1]

            if status == "completed":
                success("Challenge Completed! 🎉")
            else:
                current_prog = [c["progress_value"] for c in user_challenges if c["challenge_id"] == ch_id][-1]
                remaining = max(ch_data["target"] - current_prog, 0)

                st.write(f"Progress: {current_prog} / {ch_data['target']}")

                prog_val = st.number_input(
                    f"Update Progress for {ch_id}",
                    min_value=0.0,
                    step=1.0,
                    value=0.0,
                    key=f"prog_{ch_id}",
                )

                is_valid = True

                if prog_val <= 0:
                    warning("⚠️ Progress must be greater than zero.")
                    is_valid = False
                elif prog_val > remaining:
                    warning(
                        f"⚠️ You can only add up to {remaining} {ch_data['unit']} to complete this challenge."
                    )
                    is_valid = False

                if st.button(
                    "Update",
                    key=f"btn_prog_{ch_id}",
                    disabled=not is_valid,
                ):
                    gf.update_challenge_progress(
                        1,
                        ch_id,
                        progress_increment=prog_val,
                    )
                    gf.validate_challenge_progress(1, ch_id)
                    success("Progress updated successfully!")
                    st.rerun()
        else:
            if st.button(
                "Enroll",
                key=f"enroll_{ch_id}",
            ):
                gf.enroll_challenge(user_id, ch_id)
                st.rerun()
st.markdown("### 🏆 Weekly Challenges")

user_challenges = gf.get_user_challenges(user_id)
enrolled_ids = [c['challenge_id'] for c in user_challenges if c['status'] != 'expired']

for ch_id, ch_data in gf.CHALLENGES.items():
    render_challenge_card(
        ch_id,
        ch_data,
        user_challenges,
        enrolled_ids,
    )

st.markdown("---")
st.markdown("### 🎖️ Achievement Badges")

unlocked = gf.get_unlocked_badges(user_id)
unlocked_ids = [b['badge_id'] for b in unlocked]

cols = st.columns(len(gf.BADGES))
for i, (b_id, b_data) in enumerate(gf.BADGES.items()):
    with cols[i % len(cols)]:
        if b_id in unlocked_ids:
            st.markdown(f"**✅ {b_data['name']}**")
            st.caption(b_data['desc'])
            if st.button("Share Card", key=f"share_{b_id}"):
                file_path = gf.generate_achievement_card(1, b_id, f"badge_{b_id}.png")
                if file_path:
                    with open(file_path, "rb") as f:
                        st.download_button("Download Card", f, file_name=f"badge_{b_id}.png", key=f"dl_{b_id}")
        else:
            st.markdown(f"**🔒 {b_data['name']}**")
            st.caption(b_data['desc'])


