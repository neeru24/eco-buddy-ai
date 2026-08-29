"""
Regional Benchmarking Page
==========================
Compare your carbon footprint against regional and global averages.
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta

from src.utils.regional_benchmarking import (
    get_region_data, calculate_percentile, calculate_regional_gap,
    compare_categories, generate_insights, calculate_monthly_trend,
    generate_benchmarking_summary, REGIONAL_AVERAGES,
)


def render_percentile_gauge(pdata: dict) -> None:
    """Render a Plotly gauge showing percentile position."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=pdata["percentile"],
        title={"text": "Percentile Ranking", "font": {"size": 18}},
        number={"suffix": "%", "font": {"size": 36}},
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": pdata["bracket_color"]},
               "steps": [{"range": [0, 25], "color": "#dc2626"}, {"range": [25, 50], "color": "#f97316"},
                         {"range": [50, 75], "color": "#eab308"}, {"range": [75, 100], "color": "#22c55e"}],
               "threshold": {"line": {"color": "white", "width": 4}, "thickness": 0.8, "value": pdata["percentile"]}},
    ))
    fig.update_layout(height=300, margin=dict(t=60, b=20, l=30, r=30))
    st.plotly_chart(fig, use_container_width=True)


def render_gap_chart(gap: dict) -> None:
    """Horizontal bar comparing user vs averages."""
    labels = ["Your Footprint", "Regional Average", "2030 Target", "2050 Target"]
    values = [gap["user_kg"], gap["regional_average_kg"], gap["target_2030_kg"], gap["target_2050_kg"]]
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h", marker_color=["#3b82f6", "#6b7280", "#22c55e", "#15803d"],
                           text=[f"{v:,.0f} kg" for v in values], textposition="auto"))
    fig.update_layout(height=250, margin=dict(t=20, b=20, l=10, r=20), xaxis_title="kg CO₂/year", yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)


def render_category_chart(comparisons: list[dict]) -> None:
    """Grouped bar chart for category comparison."""
    cats = [c["category"] for c in comparisons]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="You", x=cats, y=[c["user_kg"] for c in comparisons], marker_color="#3b82f6"))
    fig.add_trace(go.Bar(name="Regional Avg", x=cats, y=[c["regional_average_kg"] for c in comparisons], marker_color="#d1d5db"))
    fig.update_layout(barmode="group", height=350, margin=dict(t=30, b=30), yaxis_title="kg CO₂/year")
    st.plotly_chart(fig, use_container_width=True)


def render_trend_chart(assessments: list[dict]) -> None:
    """Line chart of monthly footprint trend."""
    data = sorted(assessments, key=lambda a: a["month"])
    fig = go.Figure(go.Scatter(x=[a["month"] for a in data], y=[a["footprint"] for a in data],
                               mode="lines+markers", line=dict(color="#3b82f6", width=3), fill="tozeroy",
                               fillcolor="rgba(59,130,246,0.1)"))
    fig.update_layout(height=300, margin=dict(t=30, b=30), xaxis_title="Month", yaxis_title="kg CO₂/year")
    st.plotly_chart(fig, use_container_width=True)


def render_pathway_chart(pathway: dict) -> None:
    """Line chart showing reduction pathway."""
    ms = pathway.get("quarterly_milestones", [])
    if not ms: return
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0] + [m["month"] for m in ms],
                             y=[pathway["current_kg"]] + [m["target_kg"] for m in ms],
                             mode="lines+markers", line=dict(color="#22c55e", width=3, dash="dot")))
    fig.add_hline(y=pathway["target_kg"], line_dash="dash", line_color="#15803d",
                  annotation_text=f"Target: {pathway['target_kg']:,.0f} kg")
    fig.update_layout(height=300, margin=dict(t=30, b=30), xaxis_title="Months", yaxis_title="kg CO₂/year")
    st.plotly_chart(fig, use_container_width=True)


def render_benchmarking_hub() -> None:
    """Main render function."""
    st.markdown("<div class='section-header'>📊 Regional Benchmarking</div>", unsafe_allow_html=True)
    st.markdown("Compare your carbon footprint against regional and global averages.")

    region = st.selectbox("🌍 Select Region", list(REGIONAL_AVERAGES.keys()), index=0)
    rdata = get_region_data(region)

    st.subheader("📋 Region Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Regional Average", f"{rdata['average_footprint_kg']:,.0f} kg")
    c2.metric("2030 Target", f"{rdata['target_2030_kg']:,.0f} kg")
    c3.metric("2050 Target", f"{rdata['target_2050_kg']:,.0f} kg")
    c4.metric("Population", f"{rdata['population_billion']:.2f}B")
    st.caption(rdata["description"])
    st.divider()

    st.subheader("🔧 Your Footprint Data")
    ci, cc = st.columns([1, 1])
    with ci:
        user_footprint = st.number_input("Annual Carbon Footprint (kg CO₂)", min_value=0.0, max_value=50000.0, value=4500.0, step=100.0)
    with cc:
        st.markdown("**Per-Category Breakdown (optional)**")
        cat_t = st.number_input("Transport (kg)", min_value=0.0, value=1500.0, step=50.0)
        cat_e = st.number_input("Electricity (kg)", min_value=0.0, value=1200.0, step=50.0)
        cat_d = st.number_input("Diet (kg)", min_value=0.0, value=800.0, step=50.0)
        cat_f = st.number_input("Flights (kg)", min_value=0.0, value=400.0, step=50.0)
    contributors = {"Transport": cat_t, "Electricity": cat_e, "Diet": cat_d, "Flights": cat_f}

    if st.button("📊 Analyze My Benchmark", use_container_width=True):
        summary = generate_benchmarking_summary(user_footprint, contributors, region)

        # Percentile
        st.divider()
        st.subheader("🎯 Percentile Ranking")
        cg, cb = st.columns([1, 1])
        with cg: render_percentile_gauge(summary["percentile"])
        with cb:
            p = summary["percentile"]
            st.markdown(f"### {p['bracket_label']}")
            st.markdown(f"Your **{user_footprint:,.0f} kg CO₂/year** places you at the **{p['percentile']:.1f}th percentile** in {region}.")
            g = summary["regional_gap"]
            if g["gap_vs_average_kg"] < 0:
                st.success(f"✅ {abs(g['gap_vs_average_kg']):,.0f} kg below regional average.")
            else:
                st.warning(f"⚠️ {g['gap_vs_average_kg']:,.0f} kg above regional average.")

        # Gap analysis
        st.divider()
        st.subheader("📐 Gap Analysis")
        render_gap_chart(summary["regional_gap"])
        g = summary["regional_gap"]
        m1, m2, m3 = st.columns(3)
        m1.metric("vs Regional Avg", f"{g['percent_of_average']:.0f}%", delta=f"{-g['gap_vs_average_kg']:,.0f} kg", delta_color="inverse")
        m2.metric("vs 2030 Target", f"{g['percent_of_2030_target']:.0f}%", delta=f"{-g['gap_vs_2030_kg']:,.0f} kg", delta_color="inverse")
        pct50 = round(user_footprint / g["target_2050_kg"] * 100, 1) if g["target_2050_kg"] > 0 else 0
        m3.metric("vs 2050 Target", f"{pct50:.0f}%", delta=f"{-g['gap_vs_2050_kg']:,.0f} kg", delta_color="inverse")

        # Categories
        if summary["category_comparisons"]:
            st.divider()
            st.subheader("🏷️ Category Breakdown")
            render_category_chart(summary["category_comparisons"])

        # Insights
        st.divider()
        st.subheader("💡 Insights")
        for i, insight in enumerate(summary["insights"], 1):
            st.markdown(f"**{i}.** {insight}")

        # Reduction pathway
        st.divider()
        st.subheader("🛤️ Reduction Pathway to 2030")
        pw = summary["reduction_pathway"]
        p1, p2 = st.columns([2, 1])
        with p1: render_pathway_chart(pw)
        with p2:
            st.metric("Total Reduction", f"{pw['total_reduction_kg']:,.0f} kg")
            st.metric("Monthly", f"{pw['monthly_reduction_kg']:,.0f} kg/mo")
            st.metric("Timeline", f"{pw['timeline_months']} months")
            icon = {"moderate": "🟢", "realistic": "🟡", "ambitious": "🟠", "aggressive": "🔴"}.get(pw["feasibility"], "⚪")
            st.markdown(f"**Feasibility:** {icon} {pw['feasibility'].title()}")
            st.caption(pw["feasibility_message"])

        # Trend
        st.divider()
        st.subheader("📈 Monthly Trend")
        demo = [{"month": (datetime.now() - timedelta(days=30 * (5 - i))).strftime("%Y-%m"),
                 "footprint": max(100, user_footprint + (i * -40) + (hash(str(i)) % 200 - 100))} for i in range(6)]
        trend = calculate_monthly_trend(demo)
        render_trend_chart(demo)
        t1, t2, t3 = st.columns(3)
        t1.metric("Trend", trend["trend_direction"].title())
        t2.metric("Monthly Δ", f"{trend['monthly_change_kg']:+.1f} kg")
        t3.metric("Projected Next", f"{trend.get('projected_next_month_kg', 0):,.0f} kg")
        st.caption(trend["trend_description"])

        # Next steps
        st.divider()
        st.subheader("🚀 Next Steps")
        for step in [
            f"Set a reduction goal to reach {g['target_2030_kg']:,.0f} kg by 2030." if g["gap_vs_2030_kg"] > 0 else None,
            f"Focus on **{summary['category_comparisons'][0]['category']}** — largest excess." if summary["category_comparisons"] and summary["category_comparisons"][0]["gap_kg"] > 0 else None,
            "Use **Route Planning** for lower-carbon commute alternatives.",
            "Check **Home Energy Audit** for electricity reductions.",
            "Track monthly to build a trend baseline.",
        ]:
            if step: st.markdown(f"• {step}")
    else:
        st.info("👆 Enter your data and click **Analyze My Benchmark** to compare against regional averages.")


if __name__ == "__main__":
    st.set_page_config(page_title="Regional Benchmarking — EcoBuddy AI", page_icon="📊", layout="wide")
    render_benchmarking_hub()
else:
    render_benchmarking_hub()
