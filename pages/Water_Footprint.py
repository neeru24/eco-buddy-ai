import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from water import calculate_water_footprint, validate_water_inputs, GLOBAL_WATER_AVERAGE_LITERS
from recommendations import generate_water_recommendations
from database import save_water_assessment, get_water_assessments

from styles.theme import apply_theme

user_id = st.session_state.get('user_id')
if not user_id:
    st.warning('Please log in from the main application page.')
    st.stop()
apply_theme()

st.markdown("<div class='section-header'>💧 Water Footprint Tracker</div>", unsafe_allow_html=True)
st.markdown("Track your daily water usage, including 'virtual water' from your diet.")

st.markdown("---")

st.markdown("### 🚰 Your Daily Habits")

st.info(
    "Typical ranges — Shower: 5–15 min/day · Laundry: 2–7 loads/week "
    "· Dishwasher: 3–14 runs/week · Garden: 0–60 min/week"
)

col1, col2 = st.columns(2)
with col1:
    shower_mins = st.number_input(
        "Average Shower Duration (minutes/day)",
        min_value=0.0, max_value=180.0, value=10.0, step=1.0
    )
    laundry_loads = st.number_input(
        "Laundry Loads (per week)",
        min_value=0, max_value=50, value=2, step=1
    )
    dishwasher_runs = st.number_input(
        "Dishwasher Runs (per week)",
        min_value=0, max_value=50, value=3, step=1
    )

with col2:
    garden_mins = st.number_input(
        "Garden Watering (minutes/week)",
        min_value=0.0, max_value=600.0, value=0.0, step=5.0
    )
    diet = st.selectbox("Diet Type (Virtual Water)", ["Vegan", "Vegetarian", "Omnivore", "Heavy Meat"], index=2)

st.markdown("---")
analyze_btn = st.button("💧 Calculate Water Footprint", use_container_width=True)

if analyze_btn:
    warnings = validate_water_inputs(shower_mins, laundry_loads, dishwasher_runs, garden_mins)
    for w in warnings:
        st.warning(w)

    with st.spinner("Calculating your water footprint..."):
        total_daily, contributors = calculate_water_footprint(
            shower_mins, laundry_loads, dishwasher_runs, garden_mins, diet
        )
        insight, recommendations = generate_water_recommendations(contributors, total_daily, diet)
        
        save_water_assessment(user_id, shower_mins, laundry_loads, dishwasher_runs, garden_mins, diet, total_daily)
        
        st.session_state.water_analysis = {
            "total_daily": total_daily,
            "contributors": contributors,
            "insight": insight,
            "recommendations": recommendations,
        }

if "water_analysis" in st.session_state:
    data = st.session_state.water_analysis
    st.success("✅ Water footprint calculated!")
    
    st.markdown("---")
    st.markdown("<div class='section-header'>📊 Your Water Footprint Analysis</div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.metric("💧 Daily Water Footprint", f"{data['total_daily']:.0f} Liters")
    with c2:
        st.metric("🌍 Global Average", f"{GLOBAL_WATER_AVERAGE_LITERS:.0f} Liters")
        
    st.markdown("### 📈 Usage Breakdown")
    # Plotly pie chart
    df_contrib = pd.DataFrame(list(data['contributors'].items()), columns=['Category', 'Liters'])
    fig = px.pie(df_contrib, values='Liters', names='Category', title="Daily Water Usage by Category", hole=0.4, color_discrete_sequence=px.colors.sequential.Blues_r)
    st.plotly_chart(fig, use_container_width=True)
    
    # Comparison chart
    fig_bar = go.Figure(data=[
        go.Bar(name='You', x=['Water Footprint'], y=[data['total_daily']], marker_color='#4ade80'),
        go.Bar(name='Global Average', x=['Water Footprint'], y=[GLOBAL_WATER_AVERAGE_LITERS], marker_color='#cbd5e1')
    ])
    fig_bar.update_layout(barmode='group', title="Comparison with Global Average")
    st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("### 💡 Insight")
    st.info(data["insight"])
    
    st.markdown("### 🌱 Recommendations")
    for rec in data["recommendations"]:
        st.success(rec)

    st.markdown("---")
    st.markdown("<div class='section-header'>📈 Historical Water Trends</div>", unsafe_allow_html=True)

    water_history = get_water_assessments(1)
    if len(water_history) < 2:
        st.info("Complete at least 2 assessments to see historical trends.")
    else:
        df_hist = pd.DataFrame(
            water_history,
            columns=["id", "user_id", "shower_mins", "laundry_loads", "dishwasher_runs",
                     "garden_mins", "diet", "total_liters", "created_at"]
        )
        df_hist["created_at"] = pd.to_datetime(df_hist["created_at"])
        df_hist = df_hist.sort_values("created_at")

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=df_hist["created_at"], y=df_hist["total_liters"],
            mode="lines+markers", name="Total Daily Liters",
            line=dict(color="#3b82f6", width=3)
        ))
        fig_trend.add_hline(
            y=GLOBAL_WATER_AVERAGE_LITERS,
            line_dash="dash", line_color="#ef4444",
            annotation_text="Global Average"
        )
        fig_trend.update_layout(
            title="Water Footprint Over Time",
            xaxis_title="Date",
            yaxis_title="Liters / Day",
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_trend, use_container_width=True)
