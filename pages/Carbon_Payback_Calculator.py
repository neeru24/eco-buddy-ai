import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from styles.theme import apply_theme
from carbon_payback import (
    PRESET_ECO_PRODUCTS,
    calculate_carbon_payback,
    calculate_preset_payback,
    compare_multiple_products
)

apply_theme()

st.title("⏱️ Carbon Payback Calculator")
st.subheader("Evaluate Manufacturing vs. Operational Carbon Savings")

st.markdown("""
Eco-friendly purchases (like LED bulbs, solar panels, reusable bottles, or EVs) require carbon emissions to manufacture.
This calculator estimates **how long it takes for operational savings to offset manufacturing emissions** and projects long-term net carbon return.
""")

tabs = st.tabs(["🛒 Single Product Calculator", "📊 Multi-Product Comparison"])

# TAB 1: Single Product Calculator
with tabs[0]:
    st.markdown("### Select or Customize an Eco-Friendly Purchase")
    
    preset_names = {"Custom Product": "custom"}
    preset_names.update({v["name"]: k for k, v in PRESET_ECO_PRODUCTS.items()})
    
    selected_name = st.selectbox("Choose Product Preset", list(preset_names.keys()))
    preset_key = preset_names[selected_name]

    if preset_key != "custom":
        preset_info = PRESET_ECO_PRODUCTS[preset_key]
        c1, c2, c3 = st.columns(3)
        with c1:
            embodied = st.number_input(
                "Embodied / Manufacturing Carbon (kg CO₂)",
                value=float(preset_info["embodied_carbon_kg"]),
                min_value=0.1
            )
        with c2:
            usage = st.number_input(
                f"Daily Usage ({preset_info['usage_unit']})",
                value=float(preset_info["default_daily_usage"]),
                min_value=0.0
            )
        with c3:
            savings = st.number_input(
                "Operational CO₂ Savings per Unit (kg CO₂)",
                value=float(preset_info["savings_per_unit"]),
                format="%.4f"
            )
        product_title = preset_info["name"]
        unit_label = preset_info["usage_unit"]
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            embodied = st.number_input("Embodied / Manufacturing Carbon (kg CO₂)", value=50.0, min_value=0.1)
        with c2:
            usage = st.number_input("Daily Usage Intensity", value=2.0, min_value=0.0)
        with c3:
            savings = st.number_input("Operational CO₂ Savings per Unit (kg CO₂)", value=0.15, format="%.4f")
        product_title = "Custom Eco Purchase"
        unit_label = "units/day"

    res = calculate_carbon_payback(
        embodied_carbon_kg=embodied,
        daily_usage=usage,
        savings_per_unit=savings,
        usage_unit=unit_label,
        product_name=product_title
    )

    st.markdown("---")

    # Metrics Summary
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Manufacturing Carbon", f"{res['embodied_carbon_kg']:,.1f} kg CO₂")
    with m2:
        st.metric("Annual Operational Savings", f"{res['annual_savings_kg']:,.1f} kg CO₂/yr")
    with m3:
        if res['payback_months'] is not None:
            payback_str = f"{res['payback_months']:.1f} Months" if res['payback_months'] < 24 else f"{res['payback_years']:.1f} Years"
        else:
            payback_str = "Never"
        st.metric("Carbon Payback Period", payback_str)
    with m4:
        st.metric("Net 5-Year Carbon Return", f"{res['net_savings_5yr_kg']:,.1f} kg CO₂")

    st.markdown("---")

    # Cumulative Carbon Savings Trajectory Chart
    st.subheader("📈 Cumulative Carbon Savings Over Time (10-Year Horizon)")

    years = [p["year"] for p in res["yearly_projections"]]
    gross = [p["gross_savings_kg"] for p in res["yearly_projections"]]
    net = [p["net_savings_kg"] for p in res["yearly_projections"]]
    embodied_line = [res["embodied_carbon_kg"]] * len(years)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=embodied_line, mode="lines", name="Manufacturing Debt", line=dict(color="#e5484d", dash="dash")))
    fig.add_trace(go.Scatter(x=years, y=gross, mode="lines+markers", name="Gross Operational Savings", line=dict(color="#3b82f6")))
    fig.add_trace(go.Scatter(x=years, y=net, mode="lines+markers", name="Net Carbon Saved", line=dict(color="#2e9e5b", width=3)))

    fig.update_layout(
        xaxis_title="Years of Product Use",
        yaxis_title="Carbon (kg CO₂)",
        hovermode="x unified",
        template="plotly_white",
        height=420
    )
    st.plotly_chart(fig, use_container_width=True)

# TAB 2: Multi-Product Comparison
with tabs[1]:
    st.markdown("### Compare Payback & Net Carbon ROI Across Eco Purchases")
    
    # Calculate preset payback list
    comparison_data = []
    for k, info in PRESET_ECO_PRODUCTS.items():
        comp_res = calculate_preset_payback(k)
        comparison_data.append(comp_res)

    sorted_comp = compare_multiple_products(comparison_data)

    df_data = []
    for item in sorted_comp:
        df_data.append({
            "Product": item["product_name"],
            "Embodied Carbon (kg CO₂)": item["embodied_carbon_kg"],
            "Annual Savings (kg CO₂/yr)": item["annual_savings_kg"],
            "Payback Period (Months)": item["payback_months"] if item["payback_months"] else "N/A",
            "5-Yr Net Savings (kg CO₂)": item["net_savings_5yr_kg"],
            "10-Yr Net Savings (kg CO₂)": item["net_savings_10yr_kg"]
        })

    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True)

    # Comparison Bar Chart
    st.markdown("### 📊 Payback Period Comparison (Months)")
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(
        x=[d["Product"] for d in df_data],
        y=[d["Payback Period (Months)"] if isinstance(d["Payback Period (Months)"], (int, float)) else 0 for d in df_data],
        text=[f"{d['Payback Period (Months)']} mos" for d in df_data],
        textposition="auto",
        marker_color="#0cb93d"
    ))
    fig_comp.update_layout(
        yaxis_title="Months to Reach Carbon Neutrality",
        template="plotly_white",
        height=400
    )
    st.plotly_chart(fig_comp, use_container_width=True)
