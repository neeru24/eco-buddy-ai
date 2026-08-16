import streamlit as st
import pandas as pd
import datetime
from carpooling import (
    SAFETY_PREFERENCES,
    match_commuters,
    save_commute_profile,
    get_commute_profile,
    get_commute_profiles,
    record_shared_trip,
    get_shared_trips,
    get_total_emissions_avoided,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()
apply_theme()

st.markdown("<div class='section-header'>🚗 Green Commute & Carpooling</div>", unsafe_allow_html=True)
st.markdown(
    "Match with nearby commuters sharing your route and schedule. Each shared "
    "trip avoids the emissions of a solo drive — tracked right here."
)

total_avoided = get_total_emissions_avoided(user_id)
m1, m2 = st.columns(2)
m1.metric("CO₂ Avoided (All Time)", f"{total_avoided} kg")
trips = get_shared_trips(user_id)
m2.metric("Shared Trips", len(trips))

st.markdown("---")
st.markdown("### 🧭 Your Commute Profile")

profile = get_commute_profile(user_id)

day_options = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
with st.form("commute_form"):
    c1, c2 = st.columns(2)
    origin = c1.text_input(
        "Origin / Pickup area", value=(profile or {}).get("origin_name", ""),
        placeholder="e.g., Downtown, Eastside"
    )
    destination = c2.text_input(
        "Destination", value=(profile or {}).get("destination_name", ""),
        placeholder="e.g., Tech Park, University"
    )

    c3, c4 = st.columns(2)
    distance_km = c3.number_input(
        "One-way distance (km)", min_value=0.0, max_value=500.0,
        value=float((profile or {}).get("distance_km") or 10.0), step=0.5
    )
    departure_time = c4.text_input(
        "Departure time (HH:MM)", value=(profile or {}).get("departure_time") or "08:00"
    )

    pref_default = (profile or {}).get("preferences") or []
    preferences = st.multiselect("Safety preferences", SAFETY_PREFERENCES, default=pref_default)

    c5, c6 = st.columns(2)
    weekly_days = c5.multiselect(
        "Travel days", day_options,
        default=(profile or {}).get("weekly_days", "Mon,Wed,Fri").split(",")
    )
    is_driver = c6.checkbox(
        "I can drive / offer rides", value=(profile or {}).get("is_driver", False)
    )

    submitted = st.form_submit_button("💾 Save Commute Profile", type="primary")

if submitted:
    if not origin.strip() or not destination.strip():
        st.warning("Please enter both origin and destination.")
    elif not weekly_days:
        st.warning("Please select at least one travel day.")
    else:
        try:
            hh, mm = departure_time.split(":")
            departure_minutes = int(hh) * 60 + int(mm)
        except ValueError:
            departure_minutes = 480

        save_commute_profile(user_id, {
            "origin_name": origin.strip(),
            "destination_name": destination.strip(),
            "distance_km": distance_km,
            "departure_time": departure_time,
            "departure_minutes": departure_minutes,
            "weekly_days": ",".join(weekly_days),
            "preferences": list(preferences),
            "is_driver": is_driver,
        })
        st.success("Commute profile saved!")
        st.rerun()

st.markdown("---")
st.markdown("### 🔍 Find Compatible Commuters")

profile = get_commute_profile(user_id)
if not profile:
    st.info("Save your commute profile above to get carpool matches.")
else:
    if st.button("🚀 Find Matches", type="primary"):
        with st.spinner("Matching you with nearby commuters..."):
            candidates = get_commute_profiles(exclude_user_id=user_id)
            matches = match_commuters(profile, candidates)

        if not matches:
            st.info("No compatible commuters found yet. Check back when more users add profiles!")
        else:
            st.success(f"Found {len(matches)} potential carpool partner(s)!")

            match_rows = []
            for m in matches:
                cand = m["commuter"]
                match_rows.append({
                    "Score": f"{m['match_score']:.0f}/100",
                    "Origin": cand.get("origin_name", ""),
                    "Destination": cand.get("destination_name", ""),
                    "Departure": cand.get("departure_time", ""),
                    "Days": cand.get("weekly_days", ""),
                    "Distance (km)": m["distance_km"] if m["distance_km"] is not None else "—",
                    "CO₂ Saved/Trip (kg)": m["emissions_avoided_kg"],
                })
            st.dataframe(pd.DataFrame(match_rows), use_container_width=True, hide_index=True)

            st.markdown("#### 🤝 Log a Shared Trip")
            st.caption("Logging a shared trip credits both you and your passenger with the avoided emissions.")

            with st.form("log_trip"):
                t1, t2, t3 = st.columns(3)
                passenger_id = t1.number_input(
                    "Your commuter's user ID", min_value=1, step=1,
                    help="See Community Leaderboard for user IDs."
                )
                trip_distance = t2.number_input(
                    "Average trip distance (km)", min_value=0.5, max_value=500.0, value=10.0, step=0.5
                )
                trip_date = t3.date_input("Trip date", value=datetime.date.today())

                if st.form_submit_button("✅ Record Shared Trip"):
                    if passenger_id == user_id:
                        st.warning("You can't log a trip with yourself.")
                    else:
                        avoided = record_shared_trip(user_id, passenger_id, trip_distance, str(trip_date))
                        st.success(f"Trip recorded! ~{avoided} kg CO₂ avoided 🎉")
                        st.rerun()

st.markdown("---")
st.markdown("### 📜 Shared Trip History")

if trips:
    trip_rows = []
    for t in trips:
        trip_rows.append({
            "Date": t["trip_date"],
            "Distance (km)": t["distance_km"],
            "CO₂ Avoided (kg)": t["emissions_avoided_kg"],
            "Date Logged": (t["created_at"] or "")[:10],
        })
    st.dataframe(pd.DataFrame(trip_rows), use_container_width=True, hide_index=True)
else:
    st.info("No shared trips logged yet.")

st.markdown("---")
st.markdown("### 💡 Why Carpool?")
st.markdown("""
- **Less traffic, less idling** — shared rides mean fewer cars on the road and lower congestion.
- **Up to 50% less per-person commute emissions** — one car carrying 2+ people beats each driving alone.
- **Built-in accountability** — every logged trip adds to your CO₂-avoided total.
""")