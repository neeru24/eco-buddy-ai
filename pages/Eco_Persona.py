import streamlit as st
from styles.theme import apply_theme
from eco_persona import (
    generate_persona_profile, get_strengths, get_improvement_opportunities,
    get_achievements, get_persona_next_steps, generate_persona_card_png,
)

user_id = st.session_state.get('user_id')
if not user_id:
    st.warning('Please log in from the main application page.')
    st.stop()
apply_theme()

st.markdown("<div class='section-header'>🤖 AI Eco Persona Generator</div>", unsafe_allow_html=True)
st.markdown(
    "EcoBuddy analyzes your behavior across the app and assigns a unique "
    "sustainability persona — with strengths, weaknesses, achievements, and "
    "personalized improvement opportunities."
)

if st.button("🔄 Re-analyze My Eco Persona", use_container_width=True):
    st.rerun()

with st.spinner("Analyzing your sustainability data..."):
    profile = generate_persona_profile(user_id)
persona = profile["persona"]
metrics = profile["metrics"]

st.markdown("---")

if metrics["assessment_count"] == 0 and metrics["total_xp"] == 0:
    st.info(
        "There's no activity to analyze yet. Complete your first carbon "
        "footprint assessment on the main dashboard, then return here to "
        "unlock your eco persona!"
    )

# ─── Persona profile card ───────────────────────────────────────────────────
rarity = persona["rarity"]
st.markdown(
    f"""
    <div style="border:2px solid #2a3550;border-radius:20px;padding:24px 28px;
         background:linear-gradient(135deg,#141b2d,#1c2538);text-align:center;">
        <div style="font-size:56px;">{persona['icon']}</div>
        <div style="font-size:13px;letter-spacing:2px;color:#8896b3;margin-top:6px;">
            {rarity.upper()} PERSONA
        </div>
        <div style="font-size:30px;font-weight:800;color:#f1f5f9;margin-top:4px;">
            {persona['name']}
        </div>
        <div style="font-size:15px;color:#8896b3;margin-top:6px;">
            “{persona['tagline']}”
        </div>
        <div style="font-size:14px;color:#94a3b8;margin-top:14px;line-height:1.6;max-width:640px;margin-left:auto;margin-right:auto;">
            {persona['description']}
        </div>
        <div style="font-size:12px;color:#5a6b8a;margin-top:12px;">
            Focus area: <b>{persona['focus']}</b>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# ─── Metric strip ───────────────────────────────────────────────────────────
col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    st.metric("Level", metrics["level"])
with col2:
    st.metric("Total XP", metrics["total_xp"])
with col3:
    st.metric("Best Eco Score", metrics["best_eco_score"])
with col4:
    st.metric("Streak", f"{metrics['streak']} days")
with col5:
    st.metric("Challenges", metrics["completed_challenges"])
with col6:
    st.metric("Badges", metrics["badges_count"])

st.markdown("---")

# ─── Strengths / Improvements / Achievements ────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### 💪 Your Strengths")
    strengths = get_strengths(metrics)
    for item in strengths:
        st.markdown(f"- {item}")

    st.markdown("### 🎯 Improvement Opportunities")
    improvements = get_improvement_opportunities(metrics)
    for item in improvements:
        st.markdown(f"- {item}")

with col_b:
    st.markdown("### 🏅 Achievements")
    achievements = get_achievements(metrics)
    for item in achievements:
        st.markdown(f"- {item}")

    st.markdown("### 🧭 Recommended Next Steps")
    for step in get_persona_next_steps(metrics, profile["persona_id"]):
        st.markdown(f"- {step}")

st.markdown("---")

# ─── Behavior insights ──────────────────────────────────────────────────────
st.markdown("### 📊 What's Driving Your Persona")

left, right = st.columns(2)

with left:
    st.markdown("**🌍 Carbon Footprint**")
    if metrics["assessment_count"] > 0:
        st.markdown(
            f"- **Assessments:** {metrics['assessment_count']}"
        )
        if metrics["avg_eco_score"]:
            st.markdown(f"- **Average eco score:** {metrics['avg_eco_score']:.0f}")
        if metrics["avg_footprint"]:
            st.markdown(f"- **Average footprint:** {metrics['avg_footprint']} kg CO₂")
        st.markdown(
            f"- **Active transport share:** "
            f"{metrics['active_transport_ratio'] * 100:.0f}%"
        )
        if metrics["avg_electricity_kwh"] is not None:
            st.markdown(f"- **Avg electricity:** {metrics['avg_electricity_kwh']:.0f} kWh")
    else:
        st.markdown("No assessments yet.")

    st.markdown("**💧 Water & Waste**")
    st.markdown(f"- Water assessments: {metrics['water_assessment_count']}")
    st.markdown(f"- Waste assessments: {metrics['waste_assessment_count']}")
    if metrics["avg_recyclable_pct"]:
        st.markdown(f"- Avg recyclable share: {metrics['avg_recyclable_pct']:.0f}%")

with right:
    st.markdown("**🔥 Consistency & Growth**")
    st.markdown(f"- Current streak: {metrics['streak']} days")
    st.markdown(f"- Completed challenges: {metrics['completed_challenges']}")
    st.markdown(f"- Badges unlocked: {metrics['badges_count']}")
    st.markdown(f"- Skill tree nodes unlocked: {metrics['skill_unlocked_count']}")
    st.markdown(f"- Environmental milestones: {metrics['milestone_count']}")

    st.markdown("**🌍 Offsetting**")
    st.markdown(f"- Tonnes offset: {metrics['total_offsets_tonnes']} CO₂")
    st.markdown(f"- Offset transactions: {metrics['offset_count']}")

st.markdown("---")

# ─── Download persona card ──────────────────────────────────────────────────
st.markdown("### 🎴 Shareable Persona Card")
st.caption("Download a stylized PNG card to share your eco persona with friends.")
card_file = generate_persona_card_png(
    user_id, profile, filename=f"eco_persona_card_user{user_id}.png"
)
if card_file:
    with open(card_file, "rb") as fh:
        st.download_button(
            "⬇️ Download Persona Card (PNG)",
            data=fh.read(),
            file_name=f"eco_persona_card_user{user_id}.png",
            mime="image/png",
            use_container_width=True,
        )

st.markdown("---")

st.markdown("### 🎓 How the Persona Works")
with st.expander("How does EcoBuddy pick my persona?"):
    st.markdown(
        """
        EcoBuddy analyzes your recorded behavior across the whole app:
        footprint assessments (eco score, transport, electricity, diet),
        gamification (XP, level, streak, challenges, badges), energy audits,
        water and waste assessments, skill tree progress, and carbon offsets.

        Each domain is scored, and the strongest matching persona is
        assigned. If you're active across **five or more** domains you earn
        the **Eco Legend** persona. The persona updates automatically the
        moment any of this data changes — just hit **Re-analyze**.
        """
    )
