import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from energy_audit import (
    calculate_solar_system_size, calculate_annual_solar_generation,
    calculate_solar_installation_cost, calculate_solar_payback_period,
    calculate_long_term_solar_savings, calculate_solar_carbon_offset,
)
from database import save_solar_config, get_solar_config
from styles.theme import apply_theme

apply_theme()

st.markdown("<div class='section-header'>☀️ Home Solar Savings Calculator</div>", unsafe_allow_html=True)
st.markdown("Estimate your electricity savings, carbon reduction, and ROI from installing rooftop solar panels.")

st.markdown("---")
st.markdown("### 📐 Your Roof & Utility Details")

col1, col2 = st.columns(2)

with col1:
    roof_area = st.number_input("Roof Area (m²)", min_value=1.0, max_value=500.0, value=50.0, step=5.0, key="solar_roof_area")
    peak_sun_hours = st.number_input("Peak Sun Hours per Day", min_value=1.0, max_value=8.0, value=4.5, step=0.5, key="solar_peak_sun")
    panel_efficiency = st.slider("Panel Efficiency (%)", min_value=10, max_value=25, value=20, key="solar_panel_eff")

with col2:
    utility_rate = st.number_input("Utility Rate ($/kWh)", min_value=0.05, max_value=0.60, value=0.12, step=0.01, key="solar_rate", format="%.2f")
    install_cost_per_kw = st.number_input("Installation Cost ($/kW)", min_value=500, max_value=5000, value=2500, step=100, key="solar_install_cost")
    maint_cost = st.number_input("Annual Maintenance ($)", min_value=0, max_value=2000, value=200, step=50, key="solar_maint")

with col2:
    rate_increase = st.number_input("Annual Rate Increase (%)", min_value=0.0, max_value=15.0, value=3.0, step=0.5, key="solar_rate_inc")
    analysis_years = st.slider("Analysis Period (years)", min_value=1, max_value=30, value=20, key="solar_years")

st.markdown("---")
analyze_btn = st.button("☀️ Calculate Solar Savings", use_container_width=True)

if analyze_btn:
    with st.spinner("Calculating solar potential..."):
        system_size = calculate_solar_system_size(roof_area, panel_efficiency)
        annual_gen = calculate_annual_solar_generation(system_size, peak_sun_hours)
        install_cost = calculate_solar_installation_cost(system_size, install_cost_per_kw)
        annual_savings = annual_gen * utility_rate
        payback = calculate_solar_payback_period(install_cost, annual_savings - maint_cost)
        total_savings = calculate_long_term_solar_savings(annual_gen, utility_rate, analysis_years, rate_increase, maint_cost)
        carbon_offset = calculate_solar_carbon_offset(annual_gen)

        save_solar_config(1, roof_area, peak_sun_hours, utility_rate, panel_efficiency, install_cost_per_kw, maint_cost, rate_increase)

        st.session_state.solar_results = {
            "system_size": system_size,
            "annual_gen": annual_gen,
            "install_cost": install_cost,
            "annual_savings": annual_savings,
            "payback": payback,
            "total_savings": total_savings,
            "carbon_offset": carbon_offset,
            "analysis_years": analysis_years,
            "utility_rate": utility_rate,
            "maint_cost": maint_cost,
            "rate_increase": rate_increase,
        }

if "solar_results" in st.session_state:
    r = st.session_state.solar_results
    st.success("✅ Solar savings calculated!")

    st.markdown("---")
    st.markdown("### 📊 Solar Investment Summary")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("System Size", f"{r['system_size']:.2f} kW")
    m2.metric("Annual Generation", f"{r['annual_gen']:,.0f} kWh")
    m3.metric("Installation Cost", f"${r['install_cost']:,.0f}")
    m4.metric("Payback Period", f"{r['payback']:.1f} yrs" if r['payback'] != float('inf') else "∞")

    m5, m6, m7 = st.columns(3)
    m5.metric("Annual Savings", f"${r['annual_savings']:,.0f}")
    m6.metric(f"Total Savings ({r['analysis_years']} yrs)", f"${r['total_savings']:,.0f}")
    m7.metric("CO₂ Offset / yr", f"{r['carbon_offset']:,.0f} kg")

    st.markdown("### 💰 Cumulative Savings Over Time")
    years = list(range(1, r['analysis_years'] + 1))
    cumulative = []
    current_rate = r['utility_rate']
    running_total = 0
    for y in years:
        yearly = (r['annual_gen'] * current_rate) - r['maint_cost']
        running_total += yearly
        cumulative.append(running_total)
        current_rate *= (1 + r['rate_increase'] / 100.0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=cumulative, mode='lines+markers', name='Cumulative Savings', line=dict(color='#fbbf24', width=3)))
    fig.add_hline(y=install_cost, line_dash="dash", line_color="#ef4444", annotation_text="Installation Cost")
    fig.update_layout(title="Cumulative Solar Savings Over Time", xaxis_title="Year", yaxis_title="Savings ($)", template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🌍 Environmental Impact")
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name="Annual CO₂ Offset", x=["CO₂ Reduction"], y=[r['carbon_offset']], marker_color="#22c55e"))
    fig2.update_layout(title="Carbon Offset from Solar Generation", yaxis_title="kg CO₂ / year", template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig2, use_container_width=True)

    st.info("🌱 Installing rooftop solar can reduce your carbon footprint by thousands of kg of CO₂ annually while saving money on electricity bills.")
