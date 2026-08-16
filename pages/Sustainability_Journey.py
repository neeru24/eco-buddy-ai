"""Sustainability journey and personal progress page for EcoBuddy AI."""

import pandas as pd
import streamlit as st

from database import get_assessments, migrate
from styles.theme import apply_theme


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="Sustainability Journey · EcoBuddy AI",
    page_icon="🌱",
    layout="wide",
)


# ---------------------------------------------------------
# DATABASE INITIALIZATION
# ---------------------------------------------------------

success, message = migrate()

if not success:
    st.error(f"Database migration failed: {message}")
    st.stop()


apply_theme()


# ---------------------------------------------------------
# SESSION INFORMATION
# ---------------------------------------------------------

user_id = st.session_state.get("user_id")
username = st.session_state.get("username")


if not user_id:
    st.warning(
        "Sign in or continue as Guest from the main EcoBuddy page "
        "before opening your sustainability journey."
    )

    st.page_link(
        "app.py",
        label="Return to EcoBuddy",
        icon="🌱",
    )

    st.stop()


# ---------------------------------------------------------
# BREADCRUMB NAVIGATION
# ---------------------------------------------------------

st.markdown(
    """
    <nav class="breadcrumb" aria-label="Breadcrumb">
        <span class="breadcrumb-item">🏠 Home</span>
        <span class="breadcrumb-separator">›</span>
        <span class="breadcrumb-item">🌱 Sustainability</span>
        <span class="breadcrumb-separator">›</span>
        <span class="breadcrumb-item active">
            Journey
        </span>
    </nav>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------

st.markdown(
    "<div class='section-header'>🌱 My Sustainability Journey</div>",
    unsafe_allow_html=True,
)

st.caption(
    f"Track your environmental progress and sustainable habits, "
    f"{username or 'EcoBuddy user'}."
)


# ---------------------------------------------------------
# LOAD ASSESSMENT HISTORY
# ---------------------------------------------------------

assessments = get_assessments(int(user_id))

columns = [
    "id",
    "date",
    "transport",
    "distance",
    "electricity",
    "diet",
    "flights",
    "footprint",
    "eco_score",
]

frame = pd.DataFrame(assessments, columns=columns)


if not frame.empty:
    frame["date"] = pd.to_datetime(
        frame["date"],
        errors="coerce",
    )

    frame["footprint"] = pd.to_numeric(
        frame["footprint"],
        errors="coerce",
    )

    frame["eco_score"] = pd.to_numeric(
        frame["eco_score"],
        errors="coerce",
    )

    frame = frame.sort_values(
        "date",
        ascending=False,
    )


# ---------------------------------------------------------
# EMPTY STATE
# ---------------------------------------------------------

if frame.empty:

    st.info(
        "🌱 Your sustainability journey will appear here "
        "after you complete your first carbon assessment."
    )

    st.markdown("### 🚀 Start your journey")

    st.write(
        "Complete an assessment to discover your environmental "
        "impact, receive an eco score, and start tracking your "
        "progress over time."
    )

    st.page_link(
        "app.py",
        label="🌍 Start a Carbon Assessment",
        icon="🌱",
    )

    st.stop()


# ---------------------------------------------------------
# LATEST ASSESSMENT
# ---------------------------------------------------------

latest = frame.iloc[0]


# ---------------------------------------------------------
# JOURNEY OVERVIEW
# ---------------------------------------------------------

st.markdown("### 📊 Journey Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "🌍 Latest Footprint",
    f"{float(latest['footprint']):,.0f} kg CO₂",
)

col2.metric(
    "🏆 Latest Eco Score",
    f"{int(latest['eco_score'])}/100",
)

col3.metric(
    "📝 Assessments",
    str(len(frame)),
)

best_score = int(frame["eco_score"].max())

col4.metric(
    "⭐ Best Eco Score",
    f"{best_score}/100",
)


# ---------------------------------------------------------
# CURRENT PROGRESS
# ---------------------------------------------------------

st.markdown("### 🏆 Current Sustainability Level")

score = max(
    0,
    min(
        100,
        int(latest["eco_score"]),
    ),
)

st.progress(
    score / 100,
    text=f"Eco Score: {score}/100",
)


if score >= 85:
    level = "🌟 Eco Champion"
    message = (
        "Excellent work! Your sustainable habits are making "
        "a strong environmental impact."
    )
elif score >= 70:
    level = "🌿 Green Guardian"
    message = (
        "You're building strong sustainable habits. "
        "Keep improving one area at a time."
    )
elif score >= 50:
    level = "🌱 Eco Learner"
    message = (
        "You're on the right path. Small consistent changes "
        "can significantly improve your score."
    )
else:
    level = "🚀 Sustainability Starter"
    message = (
        "This is the beginning of your journey. Focus on "
        "the areas with the highest environmental impact."
    )


st.success(f"**{level}** — {message}")


# ---------------------------------------------------------
# FOOTPRINT TREND
# ---------------------------------------------------------

st.markdown("### 📈 Your Footprint Trend")

trend = frame.dropna(
    subset=["date", "footprint"],
).sort_values("date")


if len(trend) >= 2:

    chart_data = trend.set_index("date")["footprint"]

    st.line_chart(
        chart_data,
        use_container_width=True,
    )

    first_footprint = float(
        trend.iloc[0]["footprint"]
    )

    latest_footprint = float(
        trend.iloc[-1]["footprint"]
    )

    if latest_footprint < first_footprint:
        st.success(
            "🌿 Your carbon footprint has decreased "
            "compared with your earlier assessment."
        )
    elif latest_footprint > first_footprint:
        st.warning(
            "📌 Your latest footprint is higher than "
            "your earlier assessment. Consider reviewing "
            "your highest-impact habits."
        )
    else:
        st.info(
            "⚖️ Your carbon footprint has remained "
            "relatively stable."
        )

elif len(trend) == 1:

    st.info(
        "Complete another assessment to unlock your "
        "personal footprint trend."
    )

else:

    st.info(
        "Assessment dates are not available for "
        "your footprint history."
    )


# ---------------------------------------------------------
# LATEST LIFESTYLE ACTIVITY
# ---------------------------------------------------------

st.markdown("### 🧭 Latest Lifestyle Activity")

activity_col1, activity_col2 = st.columns(2)

with activity_col1:

    st.write("**🚗 Transportation**")
    st.write(str(latest["transport"]))

    st.write("**📏 Daily Distance**")
    st.write(f"{float(latest['distance']):g} km/day")

    st.write("**⚡ Electricity Usage**")
    st.write(
        f"{float(latest['electricity']):g} kWh/month"
    )


with activity_col2:

    st.write("**🍽️ Diet**")
    st.write(str(latest["diet"]))

    st.write("**✈️ Flights**")
    st.write(str(int(latest["flights"])))

    st.write("**📅 Assessment Date**")
    st.write(
        str(latest["date"].date())
        if pd.notna(latest["date"])
        else "Not available"
    )


# ---------------------------------------------------------
# RECENT ASSESSMENTS
# ---------------------------------------------------------

st.markdown("### 📋 Recent Assessments")

history = frame[
    [
        "date",
        "transport",
        "footprint",
        "eco_score",
    ]
].copy()

history["date"] = history["date"].dt.strftime(
    "%d %b %Y"
)

history.columns = [
    "Date",
    "Transport",
    "Footprint (kg CO₂)",
    "Eco Score",
]

st.dataframe(
    history.head(10),
    hide_index=True,
    use_container_width=True,
)


# ---------------------------------------------------------
# PERSONALIZED ECO TIPS
# ---------------------------------------------------------

st.markdown("### 💡 Tips for Your Next Step")

tips = [
    "🌱 Choose walking, cycling, or public transport for shorter journeys.",
    "⚡ Switch off unnecessary lights and standby appliances.",
    "🍽️ Plan meals carefully to reduce food waste.",
    "✈️ Consider reducing unnecessary flights where possible.",
]

if str(latest["transport"]).lower() == "car":
    tips.insert(
        0,
        "🚗 Consider car-sharing or combining multiple trips.",
    )

if float(latest["electricity"]) > 300:
    tips.insert(
        0,
        "⚡ Review your electricity consumption and reduce avoidable usage.",
    )

for tip in tips[:5]:
    st.markdown(f"- {tip}")


# ---------------------------------------------------------
# NAVIGATION
# ---------------------------------------------------------

st.markdown("### 🧭 Explore EcoBuddy")

nav_col1, nav_col2, nav_col3 = st.columns(3)

with nav_col1:
    st.page_link(
        "app.py",
        label="🌍 New Assessment",
        icon="🌱",
    )

with nav_col2:
    st.page_link(
        "pages/Achievements.py",
        label="🏆 Achievements",
        icon="🏆",
    )

with nav_col3:
    st.page_link(
        "pages/Assessment_History.py",
        label="📋 Assessment History",
        icon="📊",
    )