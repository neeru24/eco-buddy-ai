import streamlit as st
import gamification as gf
from database import get_leaderboard
from styles.theme import apply_theme

st.set_page_config(
    page_title="Community Eco Challenges",
    page_icon="🌱",
    layout="wide"
)

apply_theme()

user_id = st.session_state.get("user_id")

if user_id is None:
    st.info("Please open the main app and continue as Guest or log in first.")
    st.page_link("app.py", label="🌱 Open EcoBuddy App")
    st.stop()

st.title("🌱 Community Eco Challenges")
st.caption("Participate in sustainability challenges and compete with the community.")

# -----------------------------
# User Overview
# -----------------------------
total_xp = gf.get_total_xp(user_id)
streak = gf.get_user_streak(user_id)
badges = gf.get_unlocked_badges(user_id)
challenges = gf.get_user_challenges(user_id)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🏆 Active Challenges", len(challenges))

with col2:
    st.metric("⭐ Total XP", total_xp)

with col3:
    st.metric("🔥 Current Streak", streak)

with col4:
    st.metric("🎖️ Badges", len(badges))

    st.markdown("---")

st.subheader("🌍 Community Challenges")

challenge_filter = st.selectbox(
    "Challenge Type",
    [
        "All",
        "Weekly",
        "Completed"
    ]
)
user_challenges = gf.get_user_challenges(user_id)

enrolled_ids = [
    c["challenge_id"]
    for c in user_challenges
    if c["status"] != "expired"
]

for challenge_id, challenge in gf.CHALLENGES.items():

    if challenge_filter == "Completed":
        if challenge_id not in enrolled_ids:
            continue

    with st.container(border=True):

        st.subheader(challenge["title"])

        st.write(f"**Category:** {challenge['category']}")
        st.write(f"**Target:** {challenge['target']} {challenge['unit']}")
        st.write(f"**Reward:** ⭐ {challenge['xp']} XP")