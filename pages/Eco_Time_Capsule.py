from datetime import datetime, timedelta, date
import streamlit as st

st.set_page_config(
    page_title="Eco Time Capsule · EcoBuddy AI",
    page_icon="⏳",
    layout="wide",
)

from database import migrate, create_time_capsule, get_time_capsules, delete_time_capsule, update_time_capsule_progress
from time_capsule import (
    CAPSULE_CATEGORIES,
    check_and_unlock_capsules,
    get_progress_summary,
    generate_comparison,
)
from styles.theme import apply_theme

success, message = migrate()
if not success:
    st.error(f"Database migration failed: {message}")
    st.stop()

apply_theme()

st.sidebar.title("⏳ Eco Time Capsule")
st.sidebar.caption(
    "Write sustainability promises to your future self."
)

user_id = st.session_state.get("user_id")
username = st.session_state.get("username")

if not user_id:
    st.warning("Sign in or continue as Guest from the main EcoBuddy page.")
    st.page_link("app.py", label="Return to EcoBuddy", icon="🌱")
    st.stop()

st.sidebar.success(f"Logged in as {username or 'EcoBuddy user'}")
st.page_link("app.py", label="Back to EcoBuddy", icon="🌱")

newly_unlocked = check_and_unlock_capsules(user_id)
for cap in newly_unlocked:
    st.balloons()
    st.success(f"🎉 **Time Capsule Unlocked!** \"{cap['title']}\" +{25} XP earned!")

st.markdown("<div class='section-header'>⏳ Eco Time Capsule</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='subtitle'>Write sustainability promises to your future self. "
    "Set a future date, and when it arrives, see how your eco-progress compares!</div>",
    unsafe_allow_html=True,
)

tab_create, tab_my_capsules = st.tabs(["✉️ Create a Capsule", "📦 My Capsules"])

progress = get_progress_summary(user_id)

with tab_create:
    st.markdown("### ✉️ Write a Promise to Your Future Self")
    with st.form("time_capsule_form", clear_on_submit=True):
        title = st.text_input(
            "Capsule Title",
            placeholder="e.g., My zero-waste goal",
            help="Give your capsule a memorable name.",
        )
        promise_text = st.text_area(
            "Your Sustainability Promise",
            placeholder="e.g., I promise to reduce my single-use plastic waste to zero within 6 months...",
            height=150,
            help="Write a detailed promise about what you want to achieve.",
        )
        cat_options = list(CAPSULE_CATEGORIES.keys())
        category = st.selectbox(
            "Category",
            options=cat_options,
            format_func=lambda x: CAPSULE_CATEGORIES.get(x, x),
            index=0,
        )
        min_date = date.today() + timedelta(days=1)
        unlock_date = st.date_input(
            "Unlock Date",
            value=min_date,
            min_value=min_date,
            help="Choose a future date when this capsule will unlock.",
        )
        submitted = st.form_submit_button("🔒 Seal the Capsule", use_container_width=True)

        if submitted:
            if not title or not promise_text:
                st.error("Please provide both a title and a promise.")
            else:
                create_time_capsule(
                    user_id, title, promise_text, category, unlock_date.isoformat()
                )
                st.success("✅ Your time capsule has been sealed! See you on " + unlock_date.strftime("%d %b %Y") + "!")
                st.rerun()

    st.markdown("---")
    st.markdown("### 💡 Ideas for Your Capsule")
    ideas = [
        "🌱 **Go Plastic-Free** — \"I will stop buying bottled water and carry a reusable bottle.\"",
        "🚲 **Green Commute** — \"I will bike to work at least 3 days a week.\"",
        "🥗 **Diet Change** — \"I will try a plant-based diet for one month.\"",
        "⚡ **Energy Saver** — \"I will reduce my monthly electricity usage by 20%.\"",
        "♻️ **Zero Waste** — \"I will start composting and eliminate food waste.\"",
        "💧 **Water Conscious** — \"I will reduce my shower time by 3 minutes.\"",
    ]
    for idea in ideas:
        st.markdown(f"- {idea}")

with tab_my_capsules:
    st.markdown("### 📦 Your Capsules")

    capsules = get_time_capsules(user_id)

    if not capsules:
        st.info("No time capsules yet. Create one in the tab above!")
    else:
        locked = [c for c in capsules if not c["is_unlocked"]]
        unlocked = [c for c in capsules if c["is_unlocked"]]

        if locked:
            st.markdown("#### 🔒 Sealed Capsules")
            cols = st.columns(2)
            for i, cap in enumerate(locked):
                with cols[i % 2]:
                    cat_icon = list(CAPSULE_CATEGORIES.values())[list(CAPSULE_CATEGORIES.keys()).index(cap.get("category", "general"))].split()[0]
                    st.markdown(f"""
                    <div class='card'>
                        <div style='font-size: 14px; color: #94a3b8;'>{cat_icon} {CAPSULE_CATEGORIES.get(cap.get("category", "general"), "🌍")}</div>
                        <div style='font-size: 18px; font-weight: 800; margin: 8px 0;'>{cap['title']}</div>
                        <div style='font-size: 14px; opacity: 0.8; margin-bottom: 8px;'>{cap['promise_text'][:120]}{'...' if len(cap['promise_text']) > 120 else ''}</div>
                        <div style='font-size: 13px; color: #fbbf24;'>🔒 Unlocks {datetime.strptime(cap['unlock_date'], '%Y-%m-%d').strftime('%d %b %Y')}</div>
                    </div>
                    """, unsafe_allow_html=True)

        if unlocked:
            st.markdown("#### 🎉 Unlocked Capsules")
            for i, cap in enumerate(unlocked):
                cat_icon = list(CAPSULE_CATEGORIES.values())[list(CAPSULE_CATEGORIES.keys()).index(cap.get("category", "general"))].split()[0]
                comparison = generate_comparison(cap, progress)

                with st.expander(f"{cat_icon} {cap['title']} — Unlocked {datetime.strptime(cap['unlock_date'], '%Y-%m-%d').strftime('%d %b %Y')}", expanded=(i == 0)):
                    st.markdown(f"**Your Promise:**")
                    st.markdown(f"> {cap['promise_text']}")

                    if comparison:
                        st.markdown("**📊 Your Progress So Far:**")
                        st.markdown(comparison)

                        if progress.get("best_eco_score") and progress.get("latest_eco_score"):
                            st.markdown("**📈 Progress Check:**")
                            st.info(
                                f"Your best eco score is **{progress['best_eco_score']}/100** "
                                f"and your latest is **{progress['latest_eco_score']}/100**. "
                                + (
                                    "You're making great strides! 🌟"
                                    if progress['latest_eco_score'] >= progress['best_eco_score']
                                    else "Keep working towards your goal! 💪"
                                )
                            )
                    else:
                        st.info("Complete some assessments to see your progress compared to this promise!")

                    with st.form(key=f"progress_form_{cap['id']}"):
                        notes = st.text_area(
                            "Reflection Notes",
                            value=cap.get("progress_notes") or "",
                            placeholder="How have you done on this promise? Any thoughts?",
                            key=f"notes_{cap['id']}",
                        )
                        if st.form_submit_button("💾 Save Reflection"):
                            update_time_capsule_progress(cap["id"], notes)
                            st.success("Notes saved!")
                            st.rerun()

                    if st.button("🗑️ Delete Capsule", key=f"del_{cap['id']}"):
                        delete_time_capsule(cap["id"])
                        st.success("Capsule deleted.")
                        st.rerun()

        if not locked and not unlocked:
            st.info("No time capsules yet. Create one in the tab above!")
