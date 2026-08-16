import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from waste import calculate_waste_footprint, WASTE_CATEGORIES, WASTE_REDUCTION_TIPS
from database import save_waste_assessment, get_waste_assessments
from styles.theme import apply_theme

apply_theme()

st.markdown("<div class='section-header'>🗑️ Waste Footprint Calculator</div>", unsafe_allow_html=True)
st.markdown("Estimate your weekly household waste generation and its environmental impact.")

if "waste_defaults" not in st.session_state:
    st.session_state.waste_defaults = {cat: info["avg_weekly_kg"] for cat, info in WASTE_CATEGORIES.items()}

st.markdown("---")
st.markdown("### 📦 Weekly Waste by Category")
st.info("Adjust the estimated kg of waste you generate per week for each category.")

col1, col2 = st.columns(2)
waste_inputs = {}
cats = list(WASTE_CATEGORIES.items())
mid = len(cats) // 2
for i, (cat, info) in enumerate(cats):
    with col1 if i < mid else col2:
        key_map = {
            "Food Scraps": "waste_food_scraps",
            "Plastic Packaging": "waste_plastic",
            "Paper & Cardboard": "waste_paper",
            "Glass": "waste_glass",
            "Metal (Cans)": "waste_metal",
            "Electronics (E-Waste)": "waste_ewaste",
            "Textiles": "waste_textiles",
            "Other (Mixed Waste)": "waste_mixed",
        }
        waste_inputs[cat] = st.number_input(
            f"{cat} (kg/week)",
            min_value=0.0, max_value=100.0,
            value=st.session_state.waste_defaults.get(cat, info["avg_weekly_kg"]),
            step=0.5,
            key=key_map.get(cat, f"waste_{i}")
        )

st.markdown("---")
analyze_btn = st.button("🗑️ Calculate Waste Footprint", use_container_width=True)

if analyze_btn:
    with st.spinner("Calculating waste footprint..."):
        results = calculate_waste_footprint(waste_inputs)
        save_waste_assessment(1, waste_inputs, results["total_weekly_kg"], results["annual_co2"], results["recyclable_pct"])
        st.session_state.waste_results = results
        st.session_state.waste_inputs = waste_inputs

if "waste_results" in st.session_state:
    r = st.session_state.waste_results
    inputs = st.session_state.waste_inputs
    st.success("✅ Waste footprint calculated!")

    st.markdown("---")
    st.markdown("### 📊 Waste Summary")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Weekly Waste", f"{r['total_weekly_kg']:.1f} kg")
    m2.metric("Weekly CO₂ Impact", f"{r['total_co2_weekly']:.1f} kg")
    m3.metric("Annual CO₂ Impact", f"{r['annual_co2']:,.0f} kg")
    m4.metric("Recyclable", f"{r['recyclable_pct']:.0f}%")

    st.markdown("### 🥧 Waste Composition")
    df = pd.DataFrame([
        {"Category": cat, "kg/week": details["weekly_kg"], "kg CO₂/week": details["co2_weekly"]}
        for cat, details in r["breakdown"].items() if details["weekly_kg"] > 0
    ])
    if not df.empty:
        fig = px.pie(df, values="kg/week", names="Category", title="Waste by Category (kg/week)", hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🌱 Waste Reduction Tips")
    for cat, weekly_kg in sorted(inputs.items(), key=lambda x: -x[1]):
        if weekly_kg > 0 and cat in WASTE_REDUCTION_TIPS:
            with st.expander(f"{cat} ({weekly_kg:.1f} kg/week)"):
                for tip in WASTE_REDUCTION_TIPS[cat]:
                    st.markdown(f"- {tip}")

    st.markdown("---")
    st.markdown("### 📈 Historical Waste Trends")
    history = get_waste_assessments(1)
    if len(history) >= 2:
        df_hist = pd.DataFrame(history)
        df_hist["created_at"] = pd.to_datetime(df_hist["created_at"])
        df_hist = df_hist.sort_values("created_at")

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=df_hist["created_at"], y=df_hist["total_weekly_kg"], mode="lines+markers", name="Total Weekly Waste", line=dict(color="#ef4444", width=3)))
        fig_trend.update_layout(title="Waste Over Time", xaxis_title="Date", yaxis_title="kg / week", template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Complete at least 2 assessments to see historical trends.")
