import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from digital_footprint import (
    DIGITAL_ACTIVITIES,
    GRID_INTENSITY_BY_REGION,
    STREAMING_QUALITY_FACTORS,
    DEFAULT_STREAMING_QUALITY,
    REDUCTION_ACTIONS,
    build_summary_text,
    calculate_digital_footprint,
    compare_to_physical,
    default_usage,
    delete_digital_assessment,
    estimate_savings,
    get_digital_assessments,
    get_digital_tips,
    get_digital_trend,
    get_grid_intensity,
    recommend_actions,
    save_digital_assessment,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()

apply_theme()

st.markdown(
    "<div class='section-header'>💻 Digital Carbon Footprint</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "Streaming, cloud storage, calls and AI prompts all run on powered hardware. "
    "Estimate what your online life costs the planet each year."
)

if "digital_usage" not in st.session_state:
    st.session_state.digital_usage = default_usage()

st.markdown("---")
st.markdown("### ⚙️ Where your power comes from")

grid_col, quality_col = st.columns(2)
with grid_col:
    region = st.selectbox(
        "Electricity grid region",
        list(GRID_INTENSITY_BY_REGION.keys()),
        help="Cleaner grids make the same online habits far less carbon intensive.",
    )
    grid_intensity = get_grid_intensity(region)
    st.caption(f"Grid intensity: **{grid_intensity} kg CO₂ / kWh**")

with quality_col:
    streaming_quality = st.selectbox(
        "Default video streaming quality",
        list(STREAMING_QUALITY_FACTORS.keys()),
        index=list(STREAMING_QUALITY_FACTORS.keys()).index(DEFAULT_STREAMING_QUALITY),
        help="Resolution drives bitrate, which drives network and data centre energy.",
    )
    st.caption(
        f"Bitrate multiplier: **×{STREAMING_QUALITY_FACTORS[streaming_quality]}**"
    )

st.markdown("---")
st.markdown("### 📶 Your online activity")

usage = {}
left, right = st.columns(2)
activity_items = list(DIGITAL_ACTIVITIES.items())
midpoint = (len(activity_items) + 1) // 2

for index, (key, info) in enumerate(activity_items):
    container = left if index < midpoint else right
    with container:
        usage[key] = st.number_input(
            f"{info['icon']} {info['label']} ({info['unit']})",
            min_value=0.0,
            max_value=float(info["max"]),
            value=float(st.session_state.digital_usage.get(key, info["default"])),
            step=1.0 if info["max"] > 100 else 0.5,
            key=f"digital_{key}",
            help=info["source"],
        )

st.session_state.digital_usage = usage

st.markdown("---")
calculate = st.button(
    "💻 Calculate Digital Footprint", use_container_width=True, type="primary"
)

if calculate:
    st.session_state.digital_result = calculate_digital_footprint(
        usage, grid_intensity, streaming_quality
    )

result = st.session_state.get("digital_result")

if result:
    equivalents = compare_to_physical(result["annual_kg"])

    st.markdown("### 📊 Your Digital Footprint")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Annual CO₂", f"{result['annual_kg']:,.1f} kg")
    m2.metric("Electricity used", f"{result['annual_kwh']:,.1f} kWh")
    m3.metric("Equivalent driving", f"{equivalents['km_driven']:,.0f} km")
    m4.metric("Trees to offset", f"{equivalents['trees_to_offset']:,.1f}")

    st.info(build_summary_text(result))

    chart_left, chart_right = st.columns(2)

    with chart_left:
        st.markdown("#### By activity")
        activity_df = pd.DataFrame(
            [
                {
                    "Activity": f"{item['icon']} {item['label']}",
                    "kg CO₂": item["annual_kg"],
                    "Share %": item["share_pct"],
                }
                for item in result["ranked"]
                if item["annual_kg"] > 0
            ]
        )
        if activity_df.empty:
            st.caption("Add some usage above to see a breakdown.")
        else:
            fig = px.bar(
                activity_df,
                x="kg CO₂",
                y="Activity",
                orientation="h",
                color="kg CO₂",
                color_continuous_scale="Greens",
                text="Share %",
            )
            fig.update_traces(texttemplate="%{text}%", textposition="outside")
            fig.update_layout(
                height=380,
                showlegend=False,
                coloraxis_showscale=False,
                yaxis={"categoryorder": "total ascending"},
                margin=dict(l=10, r=10, t=30, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)

    with chart_right:
        st.markdown("#### Where the energy is spent")
        stage_labels = {
            "device": "Your devices",
            "network": "Network transmission",
            "datacentre": "Data centres",
        }
        stage_df = pd.DataFrame(
            [
                {"Stage": stage_labels[stage], "kg CO₂": value}
                for stage, value in result["stage_totals"].items()
                if value > 0
            ]
        )
        if stage_df.empty:
            st.caption("Add some usage above to see the stage split.")
        else:
            pie = px.pie(
                stage_df,
                names="Stage",
                values="kg CO₂",
                hole=0.45,
                color_discrete_sequence=px.colors.sequential.Greens_r,
            )
            pie.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(pie, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎯 Savings Simulator")
    st.caption("Tick the changes you are willing to make and see the new total.")

    suggested = {item["key"] for item in recommend_actions(result, limit=3)}
    selected_actions = []
    action_left, action_right = st.columns(2)
    action_items = list(REDUCTION_ACTIONS.items())
    action_mid = (len(action_items) + 1) // 2

    for index, (action_key, action) in enumerate(action_items):
        container = action_left if index < action_mid else action_right
        with container:
            label = action["label"]
            if action_key in suggested:
                label = f"⭐ {label}"
            if st.checkbox(label, key=f"digital_action_{action_key}", help=action["detail"]):
                selected_actions.append(action_key)

    savings = estimate_savings(usage, selected_actions, grid_intensity, streaming_quality)

    s1, s2, s3 = st.columns(3)
    s1.metric("Current", f"{savings['baseline_kg']:,.1f} kg")
    s2.metric(
        "After changes",
        f"{savings['projected_kg']:,.1f} kg",
        delta=f"-{savings['total_saved_kg']:,.1f} kg" if savings["total_saved_kg"] else None,
        delta_color="inverse",
    )
    s3.metric("Reduction", f"{savings['reduction_pct']}%")

    if savings["actions"]:
        comparison = go.Figure(
            data=[
                go.Bar(
                    name="Now",
                    x=["Annual digital CO₂"],
                    y=[savings["baseline_kg"]],
                    marker_color="#94a3b8",
                ),
                go.Bar(
                    name="After changes",
                    x=["Annual digital CO₂"],
                    y=[savings["projected_kg"]],
                    marker_color="#4ade80",
                ),
            ]
        )
        comparison.update_layout(
            barmode="group",
            height=300,
            yaxis_title="kg CO₂ per year",
            margin=dict(l=10, r=10, t=30, b=10),
        )
        st.plotly_chart(comparison, use_container_width=True)

        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Action": item["label"],
                        "Effort": item["effort"],
                        "Saves (kg CO₂/yr)": item["saved_kg"],
                    }
                    for item in savings["actions"]
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")
    st.markdown("### 💡 Tips For Your Biggest Categories")
    tips = get_digital_tips(result)
    if not tips:
        st.caption("Enter some usage above to get personalised tips.")
    for tip in tips:
        st.markdown(f"- {tip['icon']} **{tip['label']}** — {tip['tip']}")

    st.markdown("---")
    if st.button("💾 Save This Assessment", use_container_width=True):
        if save_digital_assessment(user_id, usage, result):
            st.success("Digital footprint assessment saved.")
            st.rerun()
        else:
            st.error("Could not save your assessment. Please try again.")

st.markdown("---")
st.markdown("### 📈 History")

history = get_digital_assessments(user_id, limit=12)
if not history:
    st.caption("No saved assessments yet. Calculate and save one to start tracking.")
else:
    trend = get_digital_trend(user_id, limit=12)
    if trend["entries"] >= 2:
        direction = "down" if trend["improving"] else "up"
        st.caption(
            f"Your digital footprint is {direction} "
            f"{abs(trend['change_pct'])}% since your first saved assessment."
        )
        trend_df = pd.DataFrame(trend["series"])
        line = px.line(
            trend_df,
            x="date",
            y="annual_kg",
            markers=True,
            labels={"date": "Saved on", "annual_kg": "kg CO₂ per year"},
        )
        line.update_traces(line_color="#4ade80")
        line.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(line, use_container_width=True)

    for entry in history:
        with st.expander(
            f"{entry['created_at']} — {entry['annual_kg']:,.1f} kg CO₂ / year"
        ):
            rows = [
                {
                    "Activity": DIGITAL_ACTIVITIES[key]["label"],
                    "kg CO₂": value.get("annual_kg", 0.0),
                    "Share %": value.get("share_pct", 0.0),
                }
                for key, value in entry["breakdown"].items()
                if key in DIGITAL_ACTIVITIES
            ]
            if rows:
                st.dataframe(
                    pd.DataFrame(rows).sort_values("kg CO₂", ascending=False),
                    use_container_width=True,
                    hide_index=True,
                )
            st.caption(
                f"Grid intensity {entry['grid_intensity']} kg CO₂/kWh · "
                f"{entry['annual_kwh']:,.1f} kWh · {entry['streaming_quality']}"
            )
            if st.button("🗑️ Delete", key=f"delete_digital_{entry['id']}"):
                delete_digital_assessment(entry["id"])
                st.rerun()
