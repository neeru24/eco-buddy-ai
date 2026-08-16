# ============================================================
# FILE: weather_alerts.py
# EcoBuddy AI+ Weather & Sustainability Alerts System
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import math
from typing import Any

# ============================================================
# WEATHER DATA SIMULATOR
# ============================================================

class WeatherSimulator:
    """Simulate weather data for demo purposes"""
    
    CITIES = {
        "New York": {"lat": 40.7128, "lon": -74.0060},
        "London": {"lat": 51.5074, "lon": -0.1278},
        "Tokyo": {"lat": 35.6762, "lon": 139.6503},
        "Sydney": {"lat": -33.8688, "lon": 151.2093},
        "Mumbai": {"lat": 19.0760, "lon": 72.8777},
        "Singapore": {"lat": 1.3521, "lon": 103.8198},
        "Dubai": {"lat": 25.2048, "lon": 55.2708},
        "Paris": {"lat": 48.8566, "lon": 2.3522},
        "Berlin": {"lat": 52.5200, "lon": 13.4050},
        "Rome": {"lat": 41.9028, "lon": 12.4964}
    }
    
    @staticmethod
    def get_weather(city: str) -> dict[str, Any] | None:
        """Get simulated weather data for a city"""
        # Generate realistic-ish weather data
        base_temp = random.randint(-5, 35)
        humidity = random.randint(30, 90)
        wind_speed = random.randint(0, 30)
        precipitation = random.randint(0, 20)
        
        # Weather conditions
        conditions = ["☀️ Clear", "⛅ Partly Cloudy", "☁️ Cloudy", "🌧️ Rain", "⛈️ Thunderstorm", "🌤️ Mostly Sunny"]
        condition = random.choice(conditions)
        
        # Air quality (AQI)
        aqi = random.randint(20, 150)
        aqi_status = "Good" if aqi < 50 else "Moderate" if aqi < 100 else "Unhealthy"
        
        # UV Index
        uv_index = random.randint(1, 11)
        uv_status = "Low" if uv_index < 3 else "Moderate" if uv_index < 6 else "High" if uv_index < 8 else "Very High"
        
        # Solar generation potential (kWh/m²/day)
        solar_potential = round(random.uniform(2.0, 7.0), 1)
        
        # Recommended activities
        recommended = []
        if precipitation < 5 and uv_index < 6:
            recommended.append("🚲 Great day for cycling")
        if wind_speed > 15:
            recommended.append("💨 Good day for wind energy")
        if solar_potential > 4:
            recommended.append("☀️ Excellent solar generation day")
        if condition in ["☀️ Clear", "🌤️ Mostly Sunny"]:
            recommended.append("🌞 Perfect for outdoor activities")
        if uv_index > 8:
            recommended.append("🧴 High UV - wear sunscreen")
        
        return {
            "city": city,
            "temperature": base_temp,
            "condition": condition,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "precipitation": precipitation,
            "aqi": aqi,
            "aqi_status": aqi_status,
            "uv_index": uv_index,
            "uv_status": uv_status,
            "solar_potential": solar_potential,
            "recommended": recommended[:3],
            "timestamp": datetime.now().isoformat()
        }

# ============================================================
# SUSTAINABILITY ALERTS
# ============================================================

class SustainabilityAlerts:
    """Generate sustainability alerts based on weather and user data"""
    
    ALERT_TYPES = {
        "energy": {
            "icon": "⚡",
            "title": "Energy Alert",
            "color": "#fbbf24"
        },
        "water": {
            "icon": "💧",
            "title": "Water Alert",
            "color": "#60a5fa"
        },
        "transport": {
            "icon": "🚗",
            "title": "Transport Alert",
            "color": "#4ade80"
        },
        "health": {
            "icon": "🏥",
            "title": "Health Alert",
            "color": "#f87171"
        },
        "solar": {
            "icon": "☀️",
            "title": "Solar Alert",
            "color": "#fbbf24"
        }
    }
    
    @staticmethod
    def generate_alerts(weather_data: dict[str, Any], user_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate alerts based on weather and user data"""
        alerts = []
        
        # Energy alerts based on temperature
        temp = weather_data["temperature"]
        if temp > 30:
            alerts.append({
                "type": "energy",
                "priority": "High",
                "message": "🌡️ High temperature alert! Use fans instead of AC to save energy",
                "saving": "Save up to 20% on electricity bills",
                "action": "Set AC to 24°C and use ceiling fans"
            })
        elif temp < 5:
            alerts.append({
                "type": "energy",
                "priority": "Medium",
                "message": "❄️ Cold weather alert! Layer up before turning up the heat",
                "saving": "Save 15% on heating costs",
                "action": "Wear warm clothes and lower thermostat by 2°C"
            })
        
        # Solar alerts
        if weather_data["solar_potential"] > 5:
            alerts.append({
                "type": "solar",
                "priority": "High",
                "message": f"☀️ Excellent solar day! {weather_data['solar_potential']} kWh/m²/day potential",
                "saving": "Maximize solar energy generation",
                "action": "Charge devices and run appliances during peak sunlight"
            })
        
        # Water alerts based on precipitation
        if weather_data["precipitation"] < 5:
            alerts.append({
                "type": "water",
                "priority": "Medium",
                "message": "🌵 Dry conditions alert! Conserve water today",
                "saving": "Save up to 30 gallons of water",
                "action": "Take shorter showers and avoid watering plants"
            })
        elif weather_data["precipitation"] > 15:
            alerts.append({
                "type": "water",
                "priority": "Medium",
                "message": "🌧️ Rainy day! Collect rainwater for plants",
                "saving": "Free water for gardening",
                "action": "Set up rain barrels to collect water"
            })
        
        # Transport alerts based on air quality
        if weather_data["aqi"] > 100:
            alerts.append({
                "type": "health",
                "priority": "High",
                "message": f"🌫️ Poor air quality (AQI: {weather_data['aqi']}). Limit outdoor activities",
                "saving": "Protect your health",
                "action": "Wear N95 mask and stay indoors when possible"
            })
        elif weather_data["aqi"] < 50:
            alerts.append({
                "type": "transport",
                "priority": "Low",
                "message": "🌿 Great air quality! Consider cycling or walking today",
                "saving": "Zero emissions transport",
                "action": "Leave the car at home and enjoy fresh air"
            })
        
        # Weather-based transport recommendations
        if weather_data["condition"] in ["☀️ Clear", "🌤️ Mostly Sunny"]:
            if weather_data["temperature"] > 15 and weather_data["temperature"] < 30:
                alerts.append({
                    "type": "transport",
                    "priority": "Low",
                    "message": "🚲 Perfect weather for cycling! Save emissions and stay healthy",
                    "saving": "Save 2.5kg CO₂ per trip",
                    "action": "Cycle or walk to your destination today"
                })
        
        # Wind alerts
        if weather_data["wind_speed"] > 20:
            alerts.append({
                "type": "energy",
                "priority": "Medium",
                "message": f"💨 Windy day! Wind speed: {weather_data['wind_speed']} km/h",
                "saving": "Great potential for wind energy",
                "action": "Consider using wind energy if available"
            })
        
        # UV alerts
        if weather_data["uv_index"] > 8:
            alerts.append({
                "type": "health",
                "priority": "High",
                "message": f"☀️ Very high UV index ({weather_data['uv_index']}). Protect your skin!",
                "saving": "Prevent skin damage",
                "action": "Apply sunscreen, wear hat, and stay in shade"
            })
        
        # Limit to top 5 alerts
        return alerts[:5]

# ============================================================
# ECO-FRIENDLY ACTIVITY SUGGESTIONS
# ============================================================

class EcoActivities:
    """Suggest eco-friendly activities based on weather"""
    
    ACTIVITIES = {
        "☀️ Clear": [
            "🌳 Plant a tree in your garden",
            "☀️ Install solar lights outdoors",
            "🚲 Go for a bike ride instead of driving",
            "🌿 Start a small herb garden",
            "♻️ Sort and recycle household waste"
        ],
        "☁️ Cloudy": [
            "💡 Replace bulbs with LEDs",
            "📊 Review your energy bills",
            "📝 Plan your sustainability goals",
            "🛒 Shop for eco-friendly products",
            "🧹 Clean and organize recycling area"
        ],
        "🌧️ Rain": [
            "💧 Set up rain barrels",
            "🏠 Check for water leaks at home",
            "📖 Read about sustainability",
            "🌱 Plan your garden layout",
            "♻️ Learn about composting indoors"
        ],
        "🌤️ Mostly Sunny": [
            "☀️ Calculate your solar potential",
            "🌿 Visit a local park",
            "🚶 Take a nature walk",
            "📸 Document local wildlife",
            "🌳 Join a community cleanup"
        ]
    }
    
    @staticmethod
    def get_activities(weather_condition: str, eco_score: float) -> list[str]:
        """Get personalized eco activities based on weather and eco score"""
        # Get activities for weather condition
        activities = EcoActivities.ACTIVITIES.get(weather_condition, EcoActivities.ACTIVITIES["🌤️ Mostly Sunny"])
        
        # Add advanced activities for high eco score users
        if eco_score > 70:
            advanced = [
                "🌍 Organize a community sustainability event",
                "📊 Start a sustainability blog or vlog",
                "🤝 Mentor others in sustainable living",
                "🌿 Create a permaculture garden design",
                "♻️ Start a zero-waste challenge"
            ]
            activities.extend(advanced)
        
        return activities[:5]

# ============================================================
# WEATHER IMPACT CALCULATOR
# ============================================================

class WeatherImpactCalculator:
    """Calculate environmental impact based on weather"""
    
    @staticmethod
    def calculate_impact(weather_data: dict[str, Any], user_data: dict[str, Any]) -> dict[str, Any]:
        """Calculate impact metrics based on weather"""
        
        # Energy consumption impact
        temp = weather_data["temperature"]
        if temp > 25:
            energy_impact = "High cooling demand - AC usage will increase emissions"
            energy_saving = 20
        elif temp < 10:
            energy_impact = "High heating demand - consider insulation improvements"
            energy_saving = 15
        else:
            energy_impact = "Moderate energy demand - ideal for energy savings"
            energy_saving = 10
        
        # Solar generation potential
        solar_kwh = weather_data["solar_potential"] * 10  # Approximate daily generation
        
        # Carbon footprint impact
        if weather_data["condition"] in ["☀️ Clear", "🌤️ Mostly Sunny"]:
            co2_impact = "Low impact - good conditions for renewable energy"
            co2_saving = 25
        elif weather_data["condition"] in ["☁️ Cloudy", "🌧️ Rain"]:
            co2_impact = "Higher impact - increased grid reliance"
            co2_saving = 10
        else:
            co2_impact = "Moderate impact"
            co2_saving = 15
        
        # Water conservation
        if weather_data["precipitation"] < 10:
            water_impact = "Dry conditions - conserve water"
            water_saving = 30
        else:
            water_impact = "Wet conditions - collect rainwater"
            water_saving = 20
        
        return {
            "energy_impact": energy_impact,
            "energy_saving_percent": energy_saving,
            "solar_generation_kwh": solar_kwh,
            "co2_impact": co2_impact,
            "co2_saving_percent": co2_saving,
            "water_impact": water_impact,
            "water_saving_percent": water_saving,
            "overall_impact": "Excellent" if (energy_saving + co2_saving + water_saving) > 60 else "Good"
        }

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_weather_alerts() -> None:
    """Render the complete weather & alerts interface"""
    st.markdown("<div class='section-header'>🌤️ Eco-Weather & Alerts</div>", unsafe_allow_html=True)
    
    # Initialize session state
    if "weather_location" not in st.session_state:
        st.session_state.weather_location = "New York"
    if "weather_data" not in st.session_state:
        weather = WeatherSimulator()
        st.session_state.weather_data = weather.get_weather("New York")
    
    # City selector
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        city = st.selectbox(
            "📍 Select City",
            list(WeatherSimulator.CITIES.keys()),
            index=list(WeatherSimulator.CITIES.keys()).index(st.session_state.weather_location)
        )
        
        if city != st.session_state.weather_location:
            st.session_state.weather_location = city
            weather = WeatherSimulator()
            st.session_state.weather_data = weather.get_weather(city)
            st.rerun()
    
    with col2:
        if st.button("🔄 Refresh Weather", use_container_width=True):
            weather = WeatherSimulator()
            st.session_state.weather_data = weather.get_weather(st.session_state.weather_location)
            st.rerun()
    
    with col3:
        if st.button("🗺️ My Location", use_container_width=True):
            # Simulate getting user location
            cities = list(WeatherSimulator.CITIES.keys())
            random_city = random.choice(cities)
            st.session_state.weather_location = random_city
            weather = WeatherSimulator()
            st.session_state.weather_data = weather.get_weather(random_city)
            st.rerun()
    
    # Display weather data
    weather = st.session_state.weather_data
    
    # Weather metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div style='font-size: 28px;'>{weather['condition']}</div>
            <div style='font-size: 22px; font-weight: 700; color: #4ade80;'>{weather['temperature']}°C</div>
            <div style='font-size: 12px; color: #6b7280;'>Temperature</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div style='font-size: 28px;'>💧</div>
            <div style='font-size: 22px; font-weight: 700; color: #60a5fa;'>{weather['humidity']}%</div>
            <div style='font-size: 12px; color: #6b7280;'>Humidity</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div style='font-size: 28px;'>💨</div>
            <div style='font-size: 22px; font-weight: 700; color: #a78bfa;'>{weather['wind_speed']} km/h</div>
            <div style='font-size: 12px; color: #6b7280;'>Wind Speed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        aqi_color = "#4ade80" if weather['aqi'] < 50 else "#fbbf24" if weather['aqi'] < 100 else "#f87171"
        st.markdown(f"""
        <div class='metric-card'>
            <div style='font-size: 28px;'>🌫️</div>
            <div style='font-size: 22px; font-weight: 700; color: {aqi_color};'>{weather['aqi']}</div>
            <div style='font-size: 12px; color: #6b7280;'>AQI - {weather['aqi_status']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        uv_color = "#4ade80" if weather['uv_index'] < 3 else "#fbbf24" if weather['uv_index'] < 6 else "#f87171"
        st.markdown(f"""
        <div class='metric-card'>
            <div style='font-size: 28px;'>☀️</div>
            <div style='font-size: 22px; font-weight: 700; color: {uv_color};'>{weather['uv_index']}</div>
            <div style='font-size: 12px; color: #6b7280;'>UV - {weather['uv_status']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Recommended activities
    st.markdown("### 🌿 Recommended Eco-Activities")
    
    eco_score = st.session_state.get("eco_score", 50)
    activities = EcoActivities.get_activities(weather['condition'], eco_score)
    
    cols = st.columns(len(activities))
    for i, activity in enumerate(activities):
        with cols[i]:
            st.markdown(f"""
            <div class='card' style='text-align: center; padding: 15px;'>
                <div style='font-size: 32px;'>{activity.split()[0]}</div>
                <div style='font-size: 13px;'>{activity}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Sustainability Alerts
    st.markdown("### 🚨 Sustainability Alerts")
    
    user_data = {
        "transport": st.session_state.get("transport", "Car"),
        "electricity": st.session_state.get("electricity", 200),
        "eco_score": eco_score
    }
    
    alerts = SustainabilityAlerts.generate_alerts(weather, user_data)
    
    if alerts:
        for alert in alerts:
            alert_type = SustainabilityAlerts.ALERT_TYPES.get(alert['type'], {})
            color = alert_type.get('color', '#6b7280')
            icon = alert_type.get('icon', 'ℹ️')
            
            priority_color = "#ef4444" if alert['priority'] == "High" else "#fbbf24" if alert['priority'] == "Medium" else "#4ade80"
            
            st.markdown(f"""
            <div class='card' style='border-left: 4px solid {color};'>
                <div style='display: flex; align-items: start; gap: 12px;'>
                    <div style='font-size: 28px;'>{icon}</div>
                    <div style='flex: 1;'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <span style='font-weight: 700;'>{alert['message']}</span>
                            <span style='background: {priority_color}; color: white; padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 700;'>
                                {alert['priority']}
                            </span>
                        </div>
                        <div style='font-size: 14px; color: #4ade80; margin: 6px 0;'>{alert['saving']}</div>
                        <div style='font-size: 13px; color: #6b7280;'>💡 {alert['action']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ No active sustainability alerts. Enjoy your eco-friendly day!")
    
    st.markdown("---")
    
    # Weather Impact Analysis
    st.markdown("### 📊 Weather Impact on Sustainability")
    
    impact = WeatherImpactCalculator.calculate_impact(weather, user_data)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div style='font-size: 14px; color: #6b7280;'>⚡ Energy Impact</div>
            <div style='font-size: 18px; font-weight: 700; color: #fbbf24;'>{impact['energy_impact']}</div>
            <div style='font-size: 12px; color: #4ade80;'>Saving: {impact['energy_saving_percent']}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div style='font-size: 14px; color: #6b7280;'>☀️ Solar Generation</div>
            <div style='font-size: 18px; font-weight: 700; color: #fbbf24;'>{impact['solar_generation_kwh']:.1f} kWh</div>
            <div style='font-size: 12px; color: #6b7280;'>Potential today</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        impact_color = "#4ade80" if impact['overall_impact'] == "Excellent" else "#fbbf24"
        st.markdown(f"""
        <div class='metric-card'>
            <div style='font-size: 14px; color: #6b7280;'>🌍 Overall Impact</div>
            <div style='font-size: 18px; font-weight: 700; color: {impact_color};'>{impact['overall_impact']}</div>
            <div style='font-size: 12px; color: #4ade80;'>CO₂ saving: {impact['co2_saving_percent']}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Weekly forecast
    st.markdown("### 📅 5-Day Eco-Forecast")
    
    forecast_data = []
    for i in range(5):
        day = datetime.now() + timedelta(days=i)
        forecast = WeatherSimulator.get_weather(st.session_state.weather_location)
        forecast_data.append({
            "Day": day.strftime("%a"),
            "Temperature": forecast['temperature'],
            "Condition": forecast['condition'],
            "Solar": forecast['solar_potential'],
            "AQI": forecast['aqi']
        })
    
    df = pd.DataFrame(forecast_data)
    
    # Create a nice table
    for _, row in df.iterrows():
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1.5, 1, 1])
        with col1:
            st.markdown(f"**{row['Day']}**")
        with col2:
            st.markdown(f"{row['Temperature']}°C")
        with col3:
            st.markdown(f"{row['Condition']}")
        with col4:
            st.markdown(f"☀️ {row['Solar']:.1f} kWh")
        with col5:
            aqi_color = "#4ade80" if row['AQI'] < 50 else "#fbbf24" if row['AQI'] < 100 else "#f87171"
            st.markdown(f"<span style='color: {aqi_color};'>{row['AQI']}</span>", unsafe_allow_html=True)
    
    st.caption("🌤️ Plan your sustainable activities based on the forecast")

# ============================================================
# INTEGRATION
# ============================================================

def render_weather_hub() -> None:
    """Render the complete weather hub"""
    render_weather_alerts()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from weather_alerts import render_weather_hub

# Add as a new tab
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13 = st.tabs([
    "🌍 Carbon Footprint",
    "⚡ Home Energy Audit",
    "🎮 Gamification",
    "🗺️ Route Planning & Offsets",
    "🏆 Community Leaderboard",
    "🔮 Future Self",
    "🌿 Sustainability Hub",
    "🌍 Eco-Social",
    "📖 Eco-Stories",
    "♻️ Waste Manager",
    "💰 Eco-Finance",
    "🎤 Voice Assessment",
    "🌤️ Eco-Weather"  # NEW
])

with tab13:
    render_weather_hub()
"""