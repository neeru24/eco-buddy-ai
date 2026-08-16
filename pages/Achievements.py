"""Dedicated sustainability achievement showcase page."""

import streamlit as st

st.set_page_config(
    page_title="Achievements · EcoBuddy AI",
    page_icon="🏆",
    layout="wide",
)

from achievement_showcase import render_achievement_showcase
from database import migrate
from styles.theme import apply_theme


success, message = migrate()
if not success:
    st.error(f"Database migration failed: {message}")
    st.stop()

apply_theme()

st.sidebar.title("🏆 Achievement Showcase")
st.sidebar.caption(
    "This page uses the active EcoBuddy session from the main application."
)

user_id = st.session_state.get("user_id")
username = st.session_state.get("username")

if not user_id:
    st.warning(
        "Sign in or continue as Guest from the main EcoBuddy page before "
        "opening the achievement showcase."
    )
    st.page_link("app.py", label="Return to EcoBuddy", icon="🌱")
    st.stop()

st.sidebar.success(f"Viewing achievements for {username or 'EcoBuddy user'}")
st.page_link("app.py", label="Back to EcoBuddy", icon="🌱")

render_achievement_showcase(int(user_id))
