import streamlit as st
import plotly.graph_objects as go
import json
from styles.theme import apply_theme
from lifestyle_optimizer import generate_optimized_lifestyle_plan, LIFESTYLE_ACTIONS_CATALOG
from database import get_latest_assessment

apply_theme()

st.title("🎯 Lifestyle Optimization Engine")
st.subheader("Personalized Action Plan for Target Carbon Reduction")

st.markdown("""
Rather than giving generic sustainability tips, the **Lifestyle Optimization Engine** calculates the **minimum set of high-impact lifestyle changes** required to reach your exact carbon reduction goal.
""")

# Fetch user's latest assessment if available
latest_assessment = get_latest_assessment()
default_footprint = 3500.0
user_context = {"transport": "Car", "electricity": 250.0, "diet": "Non-Vegetarian", "flights": 2}

if latest_assessment:
    if isinstance(latest_assessment, (list, tuple)) and len(latest_assessment) >= 8:
        user_context["transport"] = str(latest_assessment[2])
        user_context["electricity"] = float(latest_assessment[4])
        user_context["diet"] = str(latest_assessment[5])
        user_context["flights"] = int(latest_assessment[6])
        default_footprint = float(latest_assessment[7])

col1, col2 = st.columns([1, 1])

with col1:
    baseline_input = st.number_input(
        "Current Baseline Footprint (kg CO₂/year)",
        min_value=100.0,
        max_value=25000.0,
        value=float(default_footprint),
        step=100.0
    )

with col2:
    target_pct = st.slider(
        "Select Reduction Goal Target (%)",
        min_value=5,
        max_value=60,
        value=20,
        step=5,
        format="%d%%"
    )

plan = generate_optimized_lifestyle_plan(
    current_footprint_kg=baseline_input,
    target_reduction_pct=target_pct,
    context=user_context
)

st.markdown("---")

# Summary Metrics Banner
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("Baseline Footprint", f"{plan['baseline_footprint_kg']:,.0f} kg CO₂/yr")

with m2:
    st.metric("Target Reduction Goal", f"{plan['target_reduction_pct']}%", f"-{plan['required_reduction_kg']:,.0f} kg CO₂/yr")

with m3:
    st.metric("Estimated Savings", f"{plan['total_estimated_savings_kg']:,.0f} kg CO₂/yr", f"{plan['projected_reduction_pct']:.1f}% cut")

with m4:
    status_color = "green" if plan['is_target_achieved'] else "orange"
    status_label = "✅ Target Reached" if plan['is_target_achieved'] else "⚠️ Partial Plan"
    st.metric("Projected Footprint", f"{plan['projected_footprint_kg']:,.0f} kg CO₂/yr", status_label)

st.markdown("---")

# Visual Chart: Before vs After
st.subheader("📊 Projected Carbon Footprint Impact")

fig = go.Figure()
fig.add_trace(go.Bar(
    x=["Current Baseline", "Projected Footprint"],
    y=[plan['baseline_footprint_kg'], plan['projected_footprint_kg']],
    text=[f"{plan['baseline_footprint_kg']:,.0f} kg", f"{plan['projected_footprint_kg']:,.0f} kg"],
    textposition="auto",
    marker_color=["#e5484d", "#2e9e5b"]
))

fig.update_layout(
    title=f"Carbon Footprint Reduction ({plan['target_reduction_pct']}% Goal)",
    yaxis_title="Annual Emissions (kg CO₂/year)",
    template="plotly_white",
    height=400
)

st.plotly_chart(fig, use_container_width=True)

# Recommended Action Plan Cards
st.subheader(f"💡 Recommended Minimum Action Plan ({plan['actions_count']} High-Impact Steps)")

if not plan["recommended_actions"]:
    st.info("Your baseline is already extremely low or your target is 0%. No extra actions required!")
else:
    for idx, act in enumerate(plan["recommended_actions"], 1):
        with st.expander(f"Step {idx}: {act['title']} — Saves ~{act['annual_savings_kg']:,.0f} kg CO₂/yr ({act['category']})", expanded=True):
            c_a, c_b, c_c = st.columns([3, 1, 1])
            with c_a:
                st.write(f"**Description:** {act['description']}")
            with c_b:
                st.markdown(f"**Impact Level:** `{act['impact']}`")
            with c_c:
                st.markdown(f"**Effort Level:** `{act['effort']}`")

st.markdown("---")

# Export Action Plan
st.subheader("📄 Export Your Action Plan")
json_str = json.dumps(plan, indent=2)
st.download_button(
    label="Download Action Plan (JSON)",
    data=json_str,
    file_name="lifestyle_action_plan.json",
    mime="application/json",
    use_container_width=True
)
