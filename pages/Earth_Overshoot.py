import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date
from overshoot import (
    get_current_overshoot_day, get_next_overshoot_day,
    calculate_personal_overshoot_day, calculate_countdown,
    OVERSHOOT_HISTORY, GLOBAL_CO2_PER_PERSON_YEAR
)
from database import get_assessments
from styles.theme import apply_theme

apply_theme()

st.markdown("<div class='section-header'>🌍 Earth Overshoot Day Countdown</div>", unsafe_allow_html=True)
st.markdown("Earth Overshoot Day marks when humanity's demand exceeds Earth's annual regeneration capacity.")

today = date.today()
current_overshoot = get_current_overshoot_day()
next_overshoot = get_next_overshoot_day()

col_odds, col_evens = st.columns(2)
with col_odds:
    st.metric("Earth Overshoot Day", current_overshoot.strftime("%b %d, %Y"), delta=f"{today.year}")
with col_evens:
    cd = calculate_countdown(next_overshoot)
    if cd["passed"]:
        st.metric("Next Overshoot Day", next_overshoot.strftime("%b %d, %Y"), delta="Past")
    else:
        st.metric("Days Until Next Overshoot", cd["days_until"], delta="remaining")

st.markdown("---")
st.markdown("### 🌱 Your Personal Overshoot Day")
st.info("Based on your latest carbon footprint assessment, see when your personal overshoot day would fall.")

user_id = st.session_state.get("user_id", 1)
assessments = get_assessments(user_id)

if assessments:
    latest = assessments[0]
    annual_footprint = latest[7] * 365 if len(latest) > 7 else 0
    personal = calculate_personal_overshoot_day(annual_footprint)

    if personal:
        m1, m2, m3 = st.columns(3)
        m1.metric("Your Overshoot Day", personal["date"].strftime("%b %d"))
        m2.metric("Earths Needed", f"{personal['earths_needed']} 🌍")
        m3.metric("Days Until", f"{personal['days_until']}d" if personal["days_until"] > 0 else "Already passed")

        progress_pct = min(personal["earths_needed"] / 5, 1.0)
        st.progress(progress_pct, text=f"If everyone lived like you, we'd need {personal['earths_needed']} Earths")

        if personal["earths_needed"] > 1:
            st.warning(f"Your lifestyle requires **{personal['earths_needed']} Earths**. "
                       f"Small changes in diet, transport, and energy can make a big difference!")
        else:
            st.success(f"Your lifestyle requires **{personal['earths_needed']} Earths** — you're living sustainably!")

        st.markdown("### 📈 Your Overshoot Trend")
        if len(assessments) >= 2:
            trend_data = []
            for a in reversed(assessments):
                fp = a[7] * 365 if len(a) > 7 else 0
                if fp > 0:
                    p = calculate_personal_overshoot_day(fp)
                    if p:
                        trend_data.append({"date": a[1], "earths": p["earths_needed"]})
            if trend_data:
                df_trend = pd.DataFrame(trend_data)
                df_trend["date"] = pd.to_datetime(df_trend["date"])
                fig = px.line(df_trend, x="date", y="earths", markers=True,
                              title="Earths Needed Over Time",
                              labels={"date": "Date", "earths": "Earths Needed"},
                              color_discrete_sequence=["#22c55e"])
                fig.add_hline(y=1, line_dash="dash", line_color="#ef4444",
                              annotation_text="Sustainable (1 Earth)")
                fig.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)",
                                  paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Complete a carbon footprint assessment first to see your personal overshoot day.")

st.markdown("---")
st.markdown("### 📅 Historical Earth Overshoot Days")
df_hist = pd.DataFrame(sorted([
    {"Year": y, "Date": d.strftime("%b %d")}
    for y, d in OVERSHOOT_HISTORY.items()
], key=lambda x: -x["Year"]))
st.dataframe(df_hist, use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("### 💡 How to Push Back Your Overshoot Day")
st.markdown("""
- **Reduce food waste** — 1/3 of all food is wasted, contributing 8% of global emissions
- **Eat lower on the food chain** — plant-based meals have a fraction of meat's footprint
- **Ditch the car** — walk, bike, or use public transport for short trips
- **Switch to renewables** — green electricity cuts your carbon footprint by up to 50%
- **Fly less** — a single round-trip flight can emit more than your annual car commute
""")
