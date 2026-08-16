import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from rainwater import (
    CLIMATE_ZONES,
    DEFAULT_CLIMATE_ZONE,
    DEFAULT_INSTALL_COST,
    DEFAULT_WATER_PRICE_PER_KL,
    MONTHS,
    ROOF_MATERIALS,
    SYSTEM_EFFICIENCY,
    TANK_SIZES,
    build_plan,
    delete_harvest_plan,
    get_climate_profile,
    get_harvest_plans,
    get_harvesting_tips,
    get_runoff_coefficient,
    list_roof_materials,
    save_harvest_plan,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()

apply_theme()

st.markdown(
    "<div class='section-header'>🌧️ Rainwater Harvesting Planner</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "The Water Footprint page measures what you use. This one measures what "
    "already lands on your roof — and whether a tank would pay for itself."
)

st.markdown("---")
st.markdown("### 🏠 Your Roof")

roof_col, material_col, zone_col = st.columns(3)
roof_area = roof_col.number_input(
    "Roof catchment area (m²)", min_value=1.0, max_value=10000.0, value=90.0, step=5.0,
    help="The footprint of the roof, not its sloped surface area.",
)
roof_material = material_col.selectbox("Roof material", list(ROOF_MATERIALS.keys()))
climate_zone = zone_col.selectbox(
    "Climate zone",
    list(CLIMATE_ZONES.keys()),
    index=list(CLIMATE_ZONES.keys()).index(DEFAULT_CLIMATE_ZONE),
)

st.caption(
    f"Runoff coefficient **{get_runoff_coefficient(roof_material)}** — "
    f"{ROOF_MATERIALS[roof_material]['note']} "
    f"System efficiency after first-flush and filter losses: **{SYSTEM_EFFICIENCY:.0%}**."
)

with st.expander("📏 Use my own monthly rainfall figures"):
    st.caption(
        "Climate-zone averages are used unless you override them. "
        "Enter millimetres of rain for each month."
    )
    use_custom = st.checkbox("Override with local rainfall data")
    profile = get_climate_profile(climate_zone)
    custom_rainfall = []
    rain_columns = st.columns(6)
    for index, month in enumerate(MONTHS):
        custom_rainfall.append(
            rain_columns[index % 6].number_input(
                month,
                min_value=0.0,
                max_value=3000.0,
                value=float(profile[index]),
                step=5.0,
                key=f"rain_{month}",
            )
        )

st.markdown("### 🚰 Your Demand")
people_col, garden_col = st.columns(2)
people = people_col.number_input("People in the household", min_value=1, max_value=30, value=3)
garden = garden_col.number_input(
    "Garden area to water (m²)", min_value=0.0, max_value=5000.0, value=20.0, step=5.0
)

st.markdown("### 💷 Costs")
price_col, install_col, tank_col = st.columns(3)
water_price = price_col.number_input(
    "Mains water price per 1000 L", min_value=0.0, max_value=100.0,
    value=DEFAULT_WATER_PRICE_PER_KL, step=0.25,
)
install_cost = install_col.number_input(
    "Installation cost", min_value=0.0, max_value=100000.0,
    value=DEFAULT_INSTALL_COST, step=50.0,
)
tank_choice = tank_col.selectbox(
    "Tank size",
    ["Recommend for me"] + [f"{size:,} L" for size in TANK_SIZES],
)

tank_litres = None
if tank_choice != "Recommend for me":
    tank_litres = TANK_SIZES[
        [f"{size:,} L" for size in TANK_SIZES].index(tank_choice)
    ]

plan = build_plan(
    roof_area_m2=roof_area,
    roof_material=roof_material,
    climate_zone=climate_zone,
    monthly_rainfall_mm=custom_rainfall if use_custom else None,
    people=people,
    garden_m2=garden,
    tank_litres=tank_litres,
    water_price_per_kl=water_price,
    install_cost=install_cost,
)

simulation = plan["simulation"]
savings = plan["savings"]

st.markdown("---")
st.markdown("### 📊 What Your Roof Can Collect")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Annual harvest", f"{plan['annual_harvest_l']:,.0f} L")
m2.metric("Demand covered", f"{simulation['coverage_pct']:.0f}%")
m3.metric("Recommended tank", f"{plan['tank_litres']:,.0f} L")
m4.metric(
    "Payback",
    f"{savings['payback_years']:,.1f} yrs" if savings["payback_years"] else "—",
)

balance_df = pd.DataFrame(simulation["months"])

st.markdown("#### Harvest vs demand, month by month")
balance_fig = go.Figure()
balance_fig.add_trace(
    go.Bar(x=balance_df["month"], y=balance_df["harvest_l"], name="Harvested",
           marker_color="#38bdf8")
)
balance_fig.add_trace(
    go.Scatter(x=balance_df["month"], y=balance_df["demand_l"], name="Demand",
               mode="lines+markers", line=dict(color="#f97316"))
)
balance_fig.add_trace(
    go.Scatter(x=balance_df["month"], y=balance_df["stored_l"], name="In tank",
               mode="lines", line=dict(color="#4ade80", dash="dot"))
)
balance_fig.update_layout(
    height=400, yaxis_title="Litres", margin=dict(l=10, r=10, t=30, b=10)
)
st.plotly_chart(balance_fig, use_container_width=True)

detail_left, detail_right = st.columns(2)
with detail_left:
    st.markdown("#### Where the water goes")
    flow_df = pd.DataFrame(
        [
            {"Outcome": "Used in the home", "Litres": simulation["total_supplied_l"]},
            {"Outcome": "Overflowed", "Litres": simulation["total_overflow_l"]},
            {"Outcome": "Still stored", "Litres": simulation["months"][-1]["stored_l"]},
        ]
    )
    flow_fig = px.pie(
        flow_df, names="Outcome", values="Litres", hole=0.45,
        color_discrete_sequence=px.colors.sequential.Blues_r,
    )
    flow_fig.update_layout(height=330, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(flow_fig, use_container_width=True)

with detail_right:
    st.markdown("#### Tank size trade-off")
    options_df = pd.DataFrame(plan["recommendation"]["options"])
    size_fig = px.line(
        options_df, x="tank_litres", y="coverage_pct", markers=True,
        labels={"tank_litres": "Tank size (L)", "coverage_pct": "Demand covered (%)"},
    )
    size_fig.add_vline(
        x=plan["tank_litres"], line_dash="dash", line_color="#4ade80",
        annotation_text="chosen",
    )
    size_fig.update_traces(line_color="#38bdf8")
    size_fig.update_layout(height=330, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(size_fig, use_container_width=True)

st.markdown("#### Monthly water balance")
st.dataframe(
    balance_df.rename(
        columns={
            "month": "Month",
            "harvest_l": "Harvested (L)",
            "demand_l": "Demand (L)",
            "supplied_l": "Supplied (L)",
            "shortfall_l": "Shortfall (L)",
            "overflow_l": "Overflow (L)",
            "stored_l": "In tank (L)",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")
st.markdown("### 💰 Money & Carbon")

money_one, money_two, money_three, money_four = st.columns(4)
money_one.metric("Annual saving", f"{savings['annual_saving']:,.2f}")
money_two.metric("Setup cost", f"{savings['setup_cost']:,.2f}")
money_three.metric("Net after 10 years", f"{savings['ten_year_net']:,.2f}")
money_four.metric("CO₂ avoided", f"{plan['carbon']['annual_kg']:,.1f} kg/yr")

st.caption(
    f"Avoiding mains treatment and pumping saves about "
    f"{plan['carbon']['ten_year_kg']:,.0f} kg CO₂ over ten years — "
    f"the work of {plan['carbon']['tree_equivalent']:,.1f} mature trees a year."
)

st.markdown("### 💡 Guidance")
for tip in get_harvesting_tips(plan):
    st.markdown(f"- {tip}")

st.markdown("---")
save_left, save_right = st.columns([2, 1])
plan_name = save_left.text_input("Plan name", value="My roof", key="rainwater_plan_name")
save_right.markdown("&nbsp;", unsafe_allow_html=True)
if save_right.button("💾 Save Plan", use_container_width=True):
    if save_harvest_plan(user_id, plan_name, plan):
        st.success("Harvesting plan saved.")
        st.rerun()
    else:
        st.error("Could not save this plan. Please try again.")

st.markdown("### 📚 Saved Plans")
saved = get_harvest_plans(user_id)
if not saved:
    st.caption("No saved plans yet. Save one above to compare roofs or tank sizes.")
else:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Plan": row["plan_name"],
                    "Roof (m²)": row["roof_area_m2"],
                    "Material": row["roof_material"],
                    "Tank (L)": row["tank_litres"],
                    "Harvest (L/yr)": row["annual_harvest_l"],
                    "Coverage %": row["coverage_pct"],
                    "Payback (yrs)": row["payback_years"] or "—",
                    "Saved": row["created_at"],
                }
                for row in saved
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
    for row in saved:
        if st.button(f"🗑️ Delete '{row['plan_name']}'", key=f"delete_rain_{row['id']}"):
            delete_harvest_plan(row["id"])
            st.rerun()

with st.expander("📖 Roof material reference"):
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Material": item["name"],
                    "Runoff coefficient": item["runoff"],
                    "Notes": item["note"],
                }
                for item in list_roof_materials()
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
