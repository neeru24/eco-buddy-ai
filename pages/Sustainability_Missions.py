import streamlit as st
import pandas as pd
import datetime
from sustainability_missions import (
    get_active_events, get_all_events, get_user_missions, get_active_mission,
    save_mission, complete_mission, build_mission_from_event, DEFAULT_DAILY_MISSIONS,
)
from database import get_total_xp
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()
apply_theme()

st.markdown("<div class='section-header'>🎯 Sustainability Missions</div>", unsafe_allow_html=True)
st.markdown(
    "Timely eco-challenges generated from real-world environmental events — "
    "complete them to earn bonus XP throughout the year."
)

total_xp = get_total_xp(user_id)
st.caption(f"Current total XP: **{total_xp}**")

today = datetime.date.today()
active_events = get_active_events(today)

st.markdown("---")

if active_events["today"]:
    event = active_events["today"]
    st.markdown(f"### 🎉 Today: {event['icon']} {event['name']}")
    st.markdown(event["description"])
    mission = build_mission_from_event(event, today)

    active = get_active_mission(user_id)
    already_completed = any(m["mission_key"] == mission["key"] for m in get_user_missions(user_id))

    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Mission", mission["title"])
    m_col2.metric("Reward", f"+{mission['xp']} XP")
    m_col3.metric("Event", event["name"])

    if not already_completed:
        st.markdown(mission["description"])
        if st.button("📥 Accept Mission", type="primary"):
            save_mission(user_id, mission)
            st.success("Mission accepted! Complete it before the event ends.")
            st.rerun()
    else:
        completed = next(
            (m for m in get_user_missions(user_id) if m["mission_key"] == mission["key"]), None
        )
        if completed and completed["status"] == "completed":
            st.success("✅ You completed today's event mission! Bonus XP already awarded.")
        else:
            st.markdown(mission["description"])
            if st.button("🏁 Mark Mission Complete", type="primary"):
                success, msg = complete_mission(user_id, mission["key"])
                if success:
                    st.balloons()
                    st.success(msg)
                else:
                    st.warning(msg)
                st.rerun()
else:
    st.info("No major environmental event today — but your daily missions are always active!")

st.markdown("---")
st.markdown("### 🗓️ Next Environmental Event")

if active_events["upcoming"]:
    upcoming = active_events["upcoming"]
    event = upcoming["event"]
    days_until = (upcoming["date"] - today).days
    st.markdown(
        f"**{event['icon']} {event['name']}** — in **{days_until} day{'s' if days_until != 1 else ''}** "
        f"({upcoming['date'].strftime('%b %d')})"
    )
    st.markdown(event["description"])
    st.caption(f"Mission reward: +{event['mission']['xp']} XP")
else:
    st.info("No upcoming environmental events found in the next year.")

st.markdown("---")
st.markdown("### 📌 Active Missions")

active = get_active_mission(user_id)
if active:
    st.markdown(f"**{active['title']}**")
    st.markdown(active["description"])
    st.markdown(f"Reward: **+{active['xp']} XP**")
    if st.button("🏁 Mark Complete", key="complete_active"):
        success, msg = complete_mission(user_id, active["mission_key"])
        if success:
            st.balloons()
            st.success(msg)
        else:
            st.warning(msg)
        st.rerun()
else:
    if not active_events["today"]:
        st.info("No active missions right now. Check back on an environmental event day!")
    else:
        st.info("Accept today's event mission to get started!")

st.markdown("---")
st.markdown("### 🏅 Mission History")

user_missions = get_user_missions(user_id)
if user_missions:
    rows = []
    for m in user_missions:
        rows.append({
            "Mission": m["title"],
            "XP": m["xp"],
            "Status": "✅ Completed" if m["status"] == "completed" else "⏳ Active",
            "Completed At": (m["completed_at"] or "")[:10],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("No missions yet — accept today's event mission above!")

st.markdown("---")
st.markdown("### 📅 All Environmental Events This Year")
events_df = pd.DataFrame([
    {
        "Date": datetime.date(2026, m, d).strftime("%b %d"),
        "Event": e["name"],
        "Mission": e["mission"]["title"],
        "XP": e["mission"]["xp"],
    }
    for e in get_all_events()
    for m, d in [e["month_day"]]
])
st.dataframe(events_df, use_container_width=True, hide_index=True)
