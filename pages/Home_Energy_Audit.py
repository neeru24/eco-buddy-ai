import html
h = html.escape
import streamlit as st
import pandas as pd
import time
from database import *
from emissions import *
from recommendations import *
from ocr_utils import *
import os
import tempfile
import uuid
import plotly.graph_objects as go
import plotly.express as px
from report import generate_pdf
import gamification as gf
from marketplace import *
import energy_audit as ea
from notifications import success, error, warning, info

from styles.theme import (
    apply_theme,
    render_empty_state,
    render_info_card,
    render_appliance_table,
)

apply_theme()

import database as db
import energy_audit as ea
import plotly.graph_objects as go

user_id = st.session_state.get('user_id')
if not user_id:
    warning('Please log in from the main application page.')
    st.stop()

st.markdown("<div class='section-header'>⚡ Home Energy Audit</div>", unsafe_allow_html=True)

# Init energy db
db.init_energy_db()

st.markdown("### 🔌 Appliance Registry")
with st.expander("➕ Add New Appliance", expanded=False):
    with st.form("appliance_form"):
        c1, c2, c3 = st.columns(3)
        app_name = c1.text_input("Appliance Name")
        app_cat = c2.selectbox("Category", ["AC", "EV Charger", "Heat Pump", "Refrigerator", "Lighting", "Other"])
        app_qty = c3.number_input("Quantity", min_value=1, value=1)

        c4, c5, c6 = st.columns(3)
        app_power = c4.number_input("Power Rating (Watts)", min_value=0.0, value=100.0)
        app_hours = c5.number_input("Hours Used/Day", min_value=0.0, max_value=24.0, value=1.0)
        app_standby = c6.number_input("Standby Draw (Watts)", min_value=0.0, value=0.0)

        submit_app = st.form_submit_button("Add Appliance")

if submit_app:
    errors = []

    # Validate appliance name
    if not app_name.strip():
        errors.append("Please enter an appliance name.")

    # Check for duplicate appliance
    existing_appliances = db.get_appliances(user_id)
    duplicate = any(
        appliance["name"].strip().lower() == app_name.strip().lower()
        for appliance in existing_appliances
    )

    if duplicate:
        errors.append("An appliance with this name already exists.")

    # Validate power rating
    if app_power <= 0:
        errors.append("Power rating must be greater than 0 W.")
    elif app_power > 10000:
        errors.append("Power rating cannot exceed 10,000 W.")

    # Validate usage hours
    if app_hours <= 0:
        errors.append("Hours used per day must be greater than 0.")
    elif app_hours > 24:
        errors.append("Hours used per day cannot exceed 24.")

    # Validate quantity
    if app_qty <= 0:
        errors.append("Quantity must be at least 1.")
    elif app_qty > 100:
        errors.append("Quantity cannot exceed 100.")

    # Show errors or save appliance
    if errors:
        for err in errors:
            error(err)
    else:
        db.add_appliance(user_id, 
            app_name.strip(),
            app_cat,
            app_qty,
            app_power,
            app_hours,
            app_standby
        )
        success(f"Added {app_name.strip()}")
        st.rerun()

appliances = db.get_appliances(user_id)
df = pd.DataFrame(appliances)
if appliances:
    # Build a styled HTML table instead of st.dataframe
    category_icons = {"AC": "❄️", "EV Charger": "🔋", "Heat Pump": "🌡️", "Refrigerator": "🧊", "Lighting": "💡", "Other": "🔌"}
    table_rows = ""
    for a in appliances:
        icon = category_icons.get(a['category'], '🔌')
        table_rows += f"""
        <tr>
            <td>{icon} {h(a['name'])}</td>
            <td><span style='background:rgba(74,222,128,0.15); padding:4px 10px; border-radius:8px; font-size:13px;'>{h(a['category'])}</span></td>
            <td style='text-align:center;'>{a['quantity']}</td>
            <td style='text-align:right;'>{a['power_rating_watts']:.0f} W</td>
            <td style='text-align:right;'>{a['hours_used_per_day']:.1f} h</td>
            <td style='text-align:right;'>{a['standby_draw_watts']:.1f} W</td>
        </tr>"""
    st.download_button(
        "📥 Download Appliance Inventory (CSV)",
        data=df.to_csv(index=False),
        file_name="appliance_inventory.csv",
        mime="text/csv",
    )

    render_appliance_table(table_rows)

    # Delete appliance controls
    st.markdown("")
    del_cols = st.columns([3, 1])
    with del_cols[0]:
        del_id = st.selectbox("Select appliance to remove", options=[(a['id'], a['name']) for a in appliances], format_func=lambda x: x[1], label_visibility="collapsed")
    with del_cols[1]:
        if st.button("🗑️ Remove", key="del_app"):
            db.delete_appliance(del_id[0])
            st.rerun()

    # Calculate summaries
    daily_kwh, monthly_kwh, yearly_kwh = ea.calculate_home_energy_summary(appliances)
    summary_df = pd.DataFrame({
    "Metric": [
        "Daily Consumption",
        "Monthly Consumption",
        "Yearly Consumption"
    ],
    "Value": [
        daily_kwh,
        monthly_kwh,
        yearly_kwh
    ]
})
    st.download_button(
    "📥 Download Energy Summary (CSV)",
    summary_df.to_csv(index=False),
    "energy_summary.csv",
    "text/csv",
)

    st.markdown("### 📊 Energy Patterns")
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Daily Consumption", f"{daily_kwh:.2f} kWh")
    sc2.metric("Monthly Consumption", f"{monthly_kwh:.2f} kWh")
    sc3.metric("Yearly Consumption", f"{yearly_kwh:.2f} kWh")

    # Hourly profile chart
    profile = ea.generate_hourly_energy_profile(appliances)
    profile_df = pd.DataFrame({
    "Hour": list(range(24)),
    "Energy (kWh)": profile
})
    st.download_button(
    "📥 Download Hourly Profile (CSV)",
    profile_df.to_csv(index=False),
    "hourly_profile.csv",
    "text/csv",
)
    fig_hr = go.Figure(data=[go.Bar(x=list(range(24)), y=profile, marker_color='#fbbf24')])
    fig_hr.update_layout(title="Hourly Energy Demand (kWh)", xaxis_title="Hour of Day", yaxis_title="kWh", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_hr, width="stretch")

else:
    render_empty_state(
    icon="🔌",
    title="No Appliances Yet",
    message='Click <b>"➕ Add New Appliance"</b> above to register your first household appliance and start tracking energy consumption.'
)

st.markdown("---")
st.markdown("### ☀️ Solar ROI Calculator")

sc_form1, sc_form2 = st.columns(2)
with sc_form1:
    roof_space = st.number_input("Available Roof Space (m²)", min_value=0.0, value=30.0)
    panel_eff = st.number_input("Panel Efficiency (%)", min_value=0.0, max_value=100.0, value=20.0)
    sun_hours = st.number_input("Peak Sun Hours/Day", min_value=0.0, value=4.5)
    install_cost = st.number_input("Installation Cost per kW ($)", min_value=0.0, value=2500.0)
with sc_form2:
    util_rate = st.number_input("Utility Rate ($/kWh)", min_value=0.0, value=0.15)
    maint_cost = st.number_input("Annual Maintenance Cost ($)", min_value=0.0, value=100.0)
    rate_inc = st.number_input("Annual Rate Increase (%)", min_value=0.0, value=3.0)

sys_size = ea.calculate_solar_system_size(roof_space, panel_eff)
ann_gen = ea.calculate_annual_solar_generation(sys_size, sun_hours)
inst_cost = ea.calculate_solar_installation_cost(sys_size, install_cost)
ann_savings = ann_gen * util_rate
payback = ea.calculate_solar_payback_period(inst_cost, ann_savings)
savings_20y = ea.calculate_long_term_solar_savings(ann_gen, util_rate, 20, rate_inc, maint_cost) - inst_cost
carbon_offset = ea.calculate_solar_carbon_offset(ann_gen)

st.markdown("#### 📈 Solar Simulation Results")
r1, r2, r3, r4 = st.columns(4)
r1.metric("System Size", f"{sys_size:.1f} kW")
r2.metric("Annual Generation", f"{ann_gen:.0f} kWh")
r3.metric("Est. Installation", f"${inst_cost:,.0f}")
r4.metric("Payback Period", f"{payback:.1f} years" if payback != float('inf') else "N/A")

render_info_card(
    f'Over 20 years, you could save <b style="color:#4ade80;">${savings_20y:,.0f}</b> and offset <b style="color:#4ade80;">{carbon_offset:,.0f} kg CO₂</b> annually.'
)

solar_df = pd.DataFrame({
    "Metric": [
        "System Size",
        "Annual Generation",
        "Installation Cost",
        "Payback Period",
        "20-Year Savings",
        "Carbon Offset"
    ],
    "Value": [
        sys_size,
        ann_gen,
        inst_cost,
        payback,
        savings_20y,
        carbon_offset
    ]
})
st.download_button(
    "📥 Download Solar ROI (CSV)",
    solar_df.to_csv(index=False),
    "solar_roi.csv",
    "text/csv",
)

