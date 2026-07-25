import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from water import calculate_water_footprint, GLOBAL_WATER_AVERAGE_LITERS
from recommendations import generate_water_recommendations
from database import save_water_assessment

from styles.theme import apply_theme

user_id = st.session_state.get('user_id')
if not user_id:
    st.warning('Please log in from the main application page.')
    st.stop()
apply_theme()

WATER_DEFAULTS = {
    "water_shower": 10.0,
    "water_laundry": 2,
    "water_dishwasher": 3,
    "water_garden": 0.0,
    "water_diet": "Omnivore",
}

for key, value in WATER_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

st.markdown("<div class='section-header'>💧 Water Footprint Tracker</div>", unsafe_allow_html=True)
st.markdown("Track your daily water usage, including 'virtual water' from your diet.")

st.markdown("---")

st.markdown("### 🚰 Your Daily Habits")

col1, col2 = st.columns(2)
with col1:
    shower_mins = st.number_input("Average Shower Duration (minutes/day)", min_value=0.0, max_value=180.0, step=1.0, key="water_shower")
    laundry_loads = st.number_input("Laundry Loads (per week)", min_value=0, max_value=50, step=1, key="water_laundry")
    dishwasher_runs = st.number_input("Dishwasher Runs (per week)", min_value=0, max_value=50, step=1, key="water_dishwasher")

with col2:
    garden_mins = st.number_input("Garden Watering (minutes/week)", min_value=0.0, max_value=600.0, step=5.0, key="water_garden")
    diet = st.selectbox("Diet Type (Virtual Water)", ["Vegan", "Vegetarian", "Omnivore", "Heavy Meat"], key="water_diet")

st.markdown("---")
analyze_btn = st.button("💧 Calculate Water Footprint", use_container_width=True)

if analyze_btn:
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
