
# ============================================================
# FILE: smart_home.py
# EcoBuddy AI+ Smart Home Energy Optimization
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random
import json
import math

# ============================================================
# ENERGY MONITOR
# ============================================================

class EnergyMonitor:
    """Real-time energy consumption monitoring"""
    
    def __init__(self):
        self.appliances = self._load_appliances()
        self.history = self._load_history()
    
    def _load_appliances(self):
        """Load appliances from session"""
        if "smart_appliances" not in st.session_state:
            st.session_state.smart_appliances = [
                {"id": "a1", "name": "Refrigerator", "watts": 150, "hours_per_day": 24, "smart": True},
                {"id": "a2", "name": "AC Unit", "watts": 2000, "hours_per_day": 6, "smart": True},
                {"id": "a3", "name": "TV", "watts": 100, "hours_per_day": 4, "smart": False},
                {"id": "a4", "name": "Washing Machine", "watts": 500, "hours_per_day": 1, "smart": True},
                {"id": "a5", "name": "Dishwasher", "watts": 1200, "hours_per_day": 1, "smart": False},
                {"id": "a6", "name": "Water Heater", "watts": 4500, "hours_per_day": 3, "smart": True}
            ]
        return st.session_state.smart_appliances
    
    def _load_history(self):
        """Load history from session"""
        if "smart_history" not in st.session_state:
            # Generate sample history
            history = []
            for i in range(24):
                hour = datetime.now().replace(hour=i, minute=0, second=0)
                total = random.randint(500, 3000)
                history.append({
                    "timestamp": hour.isoformat(),
                    "consumption": total,
                    "cost": total * 0.15 / 1000
                })
            st.session_state.smart_history = history
        return st.session_state.smart_history
    
    def get_current_consumption(self):
        """Get current total consumption"""
        total_watts = sum(a["watts"] * a["hours_per_day"] / 24 for a in self.appliances)
        return total_watts
    
    def get_daily_consumption(self):
        """Get daily consumption in kWh"""
        total = sum(a["watts"] * a["hours_per_day"] for a in self.appliances)
        return total / 1000
    
    def get_appliance_breakdown(self):
        """Get consumption breakdown by appliance"""
        breakdown = {}
        for a in self.appliances:
            daily = a["watts"] * a["hours_per_day"] / 1000
            breakdown[a["name"]] = daily
        return breakdown
    
    def get_cost(self):
        """Calculate daily cost"""
        rate_per_kwh = 0.15  # $0.15 per kWh
        daily_kwh = self.get_daily_consumption()
        return daily_kwh * rate_per_kwh
    
    def optimize_schedule(self):
        """Generate optimized schedule recommendations"""
        recommendations = []
        
        for a in self.appliances:
            if a["smart"]:
                peak_hours = [18, 19, 20, 21]  # Peak hours
                current_hour = datetime.now().hour
                
                if current_hour in peak_hours and a["hours_per_day"] > 2:
                    recommendations.append({
                        "appliance": a["name"],
                        "suggestion": f"Run {a['name']} during off-peak hours (10 AM - 4 PM)",
                        "potential_saving": a["watts"] * 2 / 1000 * 0.15 * 0.3
                    })
        
        return recommendations

# ============================================================
# AUTOMATION RULES
# ============================================================

class AutomationRules:
    """Smart automation rules for energy optimization"""
    
    RULES = [
        {
            "id": "r1",
            "name": "Auto-off Idle Devices",
            "trigger": "Device idle for 30 min",
            "action": "Turn off device",
            "status": "active",
            "saving": "8% monthly"
        },
        {
            "id": "r2",
            "name": "Peak-hour Optimization",
            "trigger": "Peak hours (6-9 PM)",
            "action": "Delay non-essential tasks",
            "status": "active",
            "saving": "12% monthly"
        },
        {
            "id": "r3",
            "name": "Weather-based HVAC",
            "trigger": "Temperature > 75°F",
            "action": "Pre-cool home",
            "status": "inactive",
            "saving": "15% monthly"
        },
        {
            "id": "r4",
            "name": "Daylight Harvesting",
            "trigger": "Sunlight detected",
            "action": "Dim lights, use natural light",
            "status": "active",
            "saving": "5% monthly"
        },
        {
            "id": "r5",
            "name": "Vacation Mode",
            "trigger": "No occupancy detected",
            "action": "Reduce heating/cooling",
            "status": "inactive",
            "saving": "20% monthly"
        }
    ]
    
    @staticmethod
    def get_rules():
        """Get automation rules"""
        return AutomationRules.RULES
    
    @staticmethod
    def toggle_rule(rule_id):
        """Toggle rule status"""
        for rule in AutomationRules.RULES:
            if rule["id"] == rule_id:
                rule["status"] = "active" if rule["status"] == "inactive" else "inactive"
                return True
        return False

# ============================================================
# WEATHER INTEGRATION
# ============================================================

class WeatherEnergyOptimizer:
    """Weather-based energy optimization"""
    
    @staticmethod
    def get_weather_impact(temp, humidity):
        """Calculate weather impact on energy usage"""
        # Heating/cooling demand
        heating_demand = max(0, 18 - temp) * 100
        cooling_demand = max(0, temp - 22) * 100
        
        # Humidity impact
        humidity_factor = humidity / 50 * 100
        
        return {
            "heating_demand": heating_demand,
            "cooling_demand": cooling_demand,
            "humidity_impact": humidity_factor,
            "total_impact": heating_demand + cooling_demand + humidity_factor
        }
    
    @staticmethod
    def get_recommendations(temp, humidity, wind_speed):
        """Get weather-based recommendations"""
        recommendations = []
        
        if temp > 28:
            recommendations.append("☀️ High temperature - use fans instead of AC when possible")
            recommendations.append("💡 Close blinds/curtains during peak sun hours")
        elif temp < 10:
            recommendations.append("❄️ Cold weather - wear warm clothes before turning up heat")
            recommendations.append("🔧 Check door/window seals for drafts")
        
        if humidity > 70:
            recommendations.append("💧 High humidity - use dehumidifier to improve AC efficiency")
        elif humidity < 30:
            recommendations.append("💨 Low humidity - use humidifier to improve comfort at lower temps")
        
        if wind_speed > 20:
            recommendations.append("💨 Windy - use natural ventilation instead of AC")
        
        return recommendations

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_smart_home():
    """Render the complete smart home interface"""
    st.markdown("<div class='section-header'>🏠 Eco-Smart Home & Energy Optimization</div>", unsafe_allow_html=True)
    
    # Initialize energy monitor
    if "energy_monitor" not in st.session_state:
        st.session_state.energy_monitor = EnergyMonitor()
    
    monitor = st.session_state.energy_monitor
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "⚡ Energy Monitor",
        "📊 Analytics",
        "🤖 Automation",
        "☀️ Weather Optimization"
    ])
    
    with tab1:
        render_energy_monitor(monitor)
    
    with tab2:
        render_energy_analytics(monitor)
    
    with tab3:
        render_automation()
    
    with tab4:
        render_weather_optimization()

def render_energy_monitor(monitor):
    """Render energy monitor"""
    st.markdown("### ⚡ Real-time Energy Monitor")
    
    # Current consumption
    current_watts = monitor.get_current_consumption()
    daily_kwh = monitor.get_daily_consumption()
    daily_cost = monitor.get_cost()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Load", f"{current_watts:.0f} W")
    col2.metric("Daily Usage", f"{daily_kwh:.1f} kWh")
    col3.metric("Daily Cost", f"${daily_cost:.2f}")
    col4.metric("Annual Cost", f"${daily_cost * 365:.2f}")
    
    # Gauge chart for current usage
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=current_watts,
        title={'text': "Current Power Usage"},
        gauge={
            'axis': {'range': [None, 5000], 'tickwidth': 1},
            'bar': {'color': "#4ade80"},
            'steps': [
                {'range': [0, 1000], 'color': "#4ade80"},
                {'range': [1000, 3000], 'color': "#fbbf24"},
                {'range': [3000, 5000], 'color': "#f87171"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 3500
            }
        }
    ))
    fig.update_layout(height=250, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig, use_container_width=True)
    
    # Appliance breakdown
    st.markdown("#### 📊 Appliance Breakdown")
    
    breakdown = monitor.get_appliance_breakdown()
    
    fig = go.Figure(data=[go.Pie(
        labels=list(breakdown.keys()),
        values=list(breakdown.values()),
        hole=0.3,
        marker=dict(colors=['#4ade80', '#fbbf24', '#60a5fa', '#a78bfa', '#f87171', '#34d399'])
    )])
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)
    
    # Optimization suggestions
    st.markdown("#### 💡 Optimization Suggestions")
    
    suggestions = monitor.optimize_schedule()
    if suggestions:
        for s in suggestions:
            st.success(f"💡 {s['suggestion']} - Potential saving: ${s['potential_saving']:.2f}/day")
    else:
        st.info("✅ Your devices are already optimized!")

def render_energy_analytics(monitor):
    """Render energy analytics"""
    st.markdown("### 📊 Energy Analytics")
    
    # Historical trend
    history = monitor.history
    
    if history:
        df = pd.DataFrame(history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Consumption trend
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['consumption'],
            mode='lines+markers',
            name='Consumption (Wh)',
            line=dict(color='#4ade80', width=2),
            fill='tozeroy',
            fillcolor='rgba(74, 222, 128, 0.2)'
        ))
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['cost'],
            mode='lines+markers',
            name='Cost ($)',
            line=dict(color='#fbbf24', width=2, dash='dash'),
            yaxis='y2'
        ))
        fig.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=20, b=0),
            hovermode='x unified',
            yaxis=dict(title='Consumption (Wh)'),
            yaxis2=dict(
                title='Cost ($)',
                overlaying='y',
                side='right'
            )
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistics
        st.markdown("#### 📊 Statistics")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Average Consumption", f"{df['consumption'].mean():.0f} Wh")
        col2.metric("Peak Consumption", f"{df['consumption'].max():.0f} Wh")
        col3.metric("Average Cost", f"${df['cost'].mean():.2f}")
    
    # Energy saving tips
    st.markdown("#### 💡 Energy Saving Tips")
    
    tips = [
        "💡 Replace incandescent bulbs with LEDs - saves 75% energy",
        "🔌 Unplug devices when not in use - saves 5-10% on electricity",
        "🌡️ Set thermostat to 68°F in winter, 78°F in summer",
        "🧺 Wash clothes in cold water - saves 90% of washing energy",
        "🧹 Clean/replace HVAC filters monthly - improves efficiency by 15%"
    ]
    
    for tip in tips:
        st.info(tip)

def render_automation():
    """Render automation rules"""
    st.markdown("### 🤖 Smart Automation Rules")
    
    # Automation stats
    rules = AutomationRules.get_rules()
    active = sum(1 for r in rules if r["status"] == "active")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Rules", len(rules))
    col2.metric("Active Rules", active)
    col3.metric("Potential Savings", "15% monthly")
    
    st.markdown("---")
    
    # Display rules
    for rule in rules:
        status_color = "#4ade80" if rule["status"] == "active" else "#6b7280"
        status_emoji = "✅" if rule["status"] == "active" else "⏸️"
        
        st.markdown(f"""
        <div class='card' style='border-left: 4px solid {status_color};'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <div style='font-weight: 600;'>{rule['name']}</div>
                    <div style='font-size: 13px; color: #6b7280;'>
                        {rule['trigger']} → {rule['action']}
                    </div>
                    <div style='font-size: 12px; color: #4ade80;'>
                        💚 Saves {rule['saving']}
                    </div>
                </div>
                <div>
                    <span style='background: {status_color}; padding: 2px 10px; border-radius: 12px; font-size: 12px; color: #111827; font-weight: 700;'>
                        {status_emoji} {rule['status'].upper()}
                    </span>
                    <button onclick="st.session_state.toggle_rule('{rule['id']}')" style='background: none; border: 1px solid #4ade80; padding: 4px 12px; border-radius: 8px; cursor: pointer; margin-left: 8px;'>
                        Toggle
                    </button>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Toggle {rule['name']}", key=f"toggle_{rule['id']}"):
            AutomationRules.toggle_rule(rule['id'])
            st.rerun()
    
    # Create custom rule
    st.markdown("---")
    st.markdown("#### ➕ Create Custom Rule")
    
    with st.form("custom_rule_form"):
        col1, col2 = st.columns(2)
        with col1:
            rule_name = st.text_input("Rule Name", placeholder="e.g., Night Mode")
            trigger = st.selectbox("Trigger", ["Time-based", "Temperature-based", "Occupancy-based", "Manual"])
        with col2:
            action = st.selectbox("Action", ["Turn off", "Reduce power", "Delay task", "Notify user"])
            saving = st.number_input("Estimated Saving (%)", min_value=0, max_value=100, value=10)
        
        if st.form_submit_button("Create Rule"):
            st.success("✅ Custom rule created successfully!")
            st.info("Your rule will be reviewed and activated shortly.")

def render_weather_optimization():
    """Render weather-based optimization"""
    st.markdown("### ☀️ Weather-Based Energy Optimization")
    
    # Simulated weather data
    temp = random.randint(5, 35)
    humidity = random.randint(30, 80)
    wind_speed = random.randint(0, 30)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🌡️ Temperature", f"{temp}°C")
    col2.metric("💧 Humidity", f"{humidity}%")
    col3.metric("💨 Wind Speed", f"{wind_speed} km/h")
    
    # Weather impact
    impact = WeatherEnergyOptimizer.get_weather_impact(temp, humidity)
    
    st.markdown("#### 📊 Weather Impact on Energy Usage")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Heating Demand", f"{impact['heating_demand']:.0f} W")
    col2.metric("Cooling Demand", f"{impact['cooling_demand']:.0f} W")
    col3.metric("Humidity Impact", f"{impact['humidity_impact']:.0f} W")
    
    st.progress(min(impact['total_impact'] / 500, 1.0))
    
    # Recommendations
    st.markdown("#### 💡 Weather-Based Recommendations")
    
    recommendations = WeatherEnergyOptimizer.get_recommendations(temp, humidity, wind_speed)
    
    for rec in recommendations:
        st.success(f"💡 {rec}")
    
    # Forecast impact
    st.markdown("#### 📅 7-Day Forecast Impact")
    
    forecast_data = []
    for i in range(7):
        day = datetime.now() + timedelta(days=i)
        temp_forecast = random.randint(5, 35)
        humid_forecast = random.randint(30, 80)
        forecast_impact = WeatherEnergyOptimizer.get_weather_impact(temp_forecast, humid_forecast)
        
        forecast_data.append({
            "Day": day.strftime("%a"),
            "Impact": forecast_impact['total_impact']
        })
    
    df_forecast = pd.DataFrame(forecast_data)
    
    fig = go.Figure(data=[go.Bar(
        x=df_forecast['Day'],
        y=df_forecast['Impact'],
        marker_color=['#4ade80', '#fbbf24', '#f87171', '#60a5fa', '#a78bfa', '#34d399', '#fbbf24']
    )])
    fig.update_layout(
        height=250,
        margin=dict(l=0, r=0, t=20, b=0),
        yaxis_title="Energy Impact"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Energy saving tips
    st.markdown("#### 🌿 Weather-Specific Tips")
    
    if temp > 25:
        st.info("☀️ Hot weather: Use fans instead of AC when possible. Close blinds during peak sun.")
    elif temp < 10:
        st.info("❄️ Cold weather: Lower thermostat by 2°C at night. Wear warm clothes indoors.")
    
    if humidity > 70:
        st.info("💧 High humidity: Use dehumidifier to improve AC efficiency and comfort.")
    
    if wind_speed > 20:
        st.info("💨 Windy: Open windows for natural ventilation instead of using AC.")

# ============================================================
# INTEGRATION
# ============================================================

def render_smart_home_hub():
    """Render the complete smart home hub"""
    render_smart_home()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from smart_home import render_smart_home_hub

# Add as a new tab
with tab30:
    render_smart_home_hub()
"""