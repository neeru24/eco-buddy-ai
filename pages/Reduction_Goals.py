import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from database import (
    archive_goal,
    complete_goal,
    get_active_goal,
    get_assessments,
    get_goal_history,
    save_reduction_goal,
)
from goals import (
    GOAL_ACTIVE,
    STATUS_ACHIEVED,
    GoalValidationError,
    allocate_reduction,
    build_pathway,
    create_goal,
    evaluate_progress,
    goal_to_dict,
    latest_footprint,
    pathway_to_series,
    reduction_percentage,
    required_monthly_reduction,
    suggest_feasible_target,
    summarize_goal,
)
from styles.theme import apply_theme

user_id = st.session_state.get('user_id')
if not user_id:
    st.warning('Please log in from the main application page.')
    st.stop()
apply_theme()

st.markdown("<div class='section-header'>🎯 Reduction Goals</div>", unsafe_allow_html=True)
st.markdown(
    "Commit to a target footprint and a date. EcoBuddy then tracks whether you are "
    "reducing fast enough to actually get there."
)
st.markdown("---")

assessments = get_assessments(user_id)
current_footprint = latest_footprint(assessments)
active_goal_row = get_active_goal(user_id)


def _contributors_from_session():
    """
    Reuse the category breakdown from the most recent analysis when the user
    has one in session, so the allocation table is specific to them rather
    than a generic split.
    """
    analysis = st.session_state.get("analysis") or {}
    contributors = analysis.get("contributors")
    if isinstance(contributors, dict) and contributors:
        return contributors
    return None


# --- Active goal ------------------------------------------------------------

if active_goal_row:
    try:
        goal = create_goal(
            active_goal_row["baseline_kg"],
            active_goal_row["target_kg"],
            active_goal_row["start_date"],
            active_goal_row["target_date"],
            goal_id=active_goal_row["id"],
            user_id=user_id,
            status=active_goal_row["status"],
        )
    except GoalValidationError as exc:
        st.error(f"Your stored goal could not be read: {exc}")
        st.stop()

    progress = evaluate_progress(goal, assessments)

    st.markdown(
        f"<div style='padding:1rem 1.25rem;border-radius:10px;"
        f"border-left:6px solid {progress['status_color']};"
        f"background:rgba(128,128,128,0.08);margin-bottom:1rem;'>"
        f"<strong style='color:{progress['status_color']};font-size:1.05rem;'>"
        f"{progress['status_label']}</strong><br>{summarize_goal(goal, progress)}</div>",
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current", f"{progress['current_kg']:,.0f} kg")
    col2.metric("Target", f"{progress['target_kg']:,.0f} kg")
    col3.metric(
        "Progress",
        f"{progress['percent_complete']:.0f}%",
        delta=f"{-progress['variance_kg']:,.0f} kg vs pathway",
    )
    col4.metric("Days left", f"{progress['days_remaining']}")

    st.progress(min(1.0, progress["percent_complete"] / 100.0))

    # --- Pathway chart ------------------------------------------------------
    st.markdown("### 📈 Pathway vs Reality")

    pathway = build_pathway(goal)
    pathway_dates, pathway_values = pathway_to_series(pathway)

    figure = go.Figure()
    figure.add_trace(go.Scatter(
        x=pathway_dates,
        y=pathway_values,
        mode="lines",
        name="Ideal pathway",
        line=dict(color="#4caf50", width=3, dash="dash"),
    ))

    history = [
        (datetime.datetime.fromisoformat(str(row[1]).replace(" ", "T")).date(), row[7])
        for row in assessments
        if row[1] is not None and row[7] is not None
    ]
    history.sort(key=lambda item: item[0])
    if history:
        figure.add_trace(go.Scatter(
            x=[point[0] for point in history],
            y=[point[1] for point in history],
            mode="lines+markers",
            name="Your footprint",
            line=dict(color="#2196f3", width=3),
        ))

        figure.add_trace(go.Scatter(
            x=[progress["as_of"], goal["target_date"]],
            y=[progress["current_kg"], progress["projected_final_kg"]],
            mode="lines",
            name="Projection at current pace",
            line=dict(color=progress["status_color"], width=2, dash="dot"),
        ))

    figure.add_hline(
        y=goal["target_kg"],
        line_dash="dot",
        line_color="#0cb93d",
        annotation_text="Target",
    )
    figure.update_layout(
        height=430,
        margin=dict(l=10, r=10, t=30, b=10),
        yaxis_title="kg CO₂ / year",
        xaxis_title="Date",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    st.plotly_chart(figure, use_container_width=True)

    # --- Pace breakdown -----------------------------------------------------
    pace_left, pace_right = st.columns(2)
    with pace_left:
        st.markdown("**Required pace**")
        st.write(f"{progress['required_pace_kg_per_month']:,.0f} kg CO₂ per month")
        st.caption("Averaged across the whole goal window.")
    with pace_right:
        st.markdown("**Your pace so far**")
        st.write(f"{progress['observed_pace_kg_per_month']:,.0f} kg CO₂ per month")
        st.caption(
            f"From {progress['record_count']} assessment(s). "
            f"You now need {progress['pace_needed_from_now_kg_per_month']:,.0f} kg/month to finish on time."
        )

    # --- Category allocation ------------------------------------------------
    contributors = _contributors_from_session()
    if contributors:
        st.markdown("### 🧮 Where the reduction has to come from")
        allocation = allocate_reduction(goal, contributors)

        if not allocation["feasible"]:
            st.warning(
                f"This goal asks for {allocation['total_required_kg']:,.0f} kg but only "
                f"{allocation['total_allocated_kg']:,.0f} kg is realistically reducible "
                "from your current categories. Consider a less aggressive target."
            )

        rows = [
            {
                "Category": category,
                "Current (kg)": item["current_kg"],
                "Reduce by (kg)": item["reduce_by_kg"],
                "New target (kg)": item["target_kg"],
                "Cut": f"{item['percent_cut_of_category']:.0f}%",
                "Share of goal": f"{item['percent_of_total_reduction']:.0f}%",
            }
            for category, item in allocation["allocations"].items()
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption(
            "Each category's share is weighted by how much of it can realistically be "
            "cut, not just by how big it is — so the plan stays actionable."
        )
    else:
        st.info(
            "Run an assessment on the Carbon Footprint page to see a per-category "
            "breakdown of where your reduction should come from."
        )

    # --- Goal actions -------------------------------------------------------
    st.markdown("---")
    action_left, action_right = st.columns(2)
    with action_left:
        if progress["status"] == STATUS_ACHIEVED:
            if st.button("🏆 Mark goal as completed", use_container_width=True):
                complete_goal(goal["id"])
                st.success("Goal marked as completed. Time to set a tougher one!")
                st.rerun()
    with action_right:
        if st.button("🗄️ Archive this goal", use_container_width=True):
            archive_goal(goal["id"])
            st.info("Goal archived.")
            st.rerun()

    with st.expander("🔍 Goal details"):
        st.json(goal_to_dict(goal))

# --- Goal creation ----------------------------------------------------------

st.markdown("---")
heading = "🎯 Replace with a new goal" if active_goal_row else "🎯 Set your first goal"
st.markdown(f"### {heading}")

if current_footprint is None:
    st.info(
        "No assessments recorded yet. You can still set a goal, but the baseline "
        "will not be pre-filled from your history."
    )

default_baseline = float(current_footprint) if current_footprint else 5000.0

with st.form("reduction_goal_form"):
    form_left, form_right = st.columns(2)
    with form_left:
        baseline_input = st.number_input(
            "Baseline footprint (kg CO₂/year)",
            min_value=1.0,
            max_value=200000.0,
            value=round(default_baseline, 1),
            step=50.0,
            help="Where you are starting from. Pre-filled from your latest assessment.",
        )
        start_input = st.date_input("Start date", value=datetime.date.today())
    with form_right:
        target_input = st.number_input(
            "Target footprint (kg CO₂/year)",
            min_value=0.0,
            max_value=200000.0,
            value=round(default_baseline * 0.7, 1),
            step=50.0,
            help="What you are committing to reach.",
        )
        target_date_input = st.date_input(
            "Target date",
            value=datetime.date.today() + datetime.timedelta(days=365),
        )

    submitted = st.form_submit_button("💾 Save goal", use_container_width=True)

if submitted:
    try:
        new_goal = create_goal(
            baseline_input, target_input, start_input, target_date_input, user_id=user_id
        )
    except GoalValidationError as exc:
        st.error(str(exc))
    else:
        contributors = _contributors_from_session()
        if contributors:
            feasible = suggest_feasible_target(baseline_input, contributors)
            if target_input < feasible:
                st.warning(
                    f"A target of {target_input:,.0f} kg is below what your current "
                    f"categories can realistically deliver (~{feasible:,.0f} kg). "
                    "Saving anyway — just be aware it will read as off track."
                )

        goal_id = save_reduction_goal(
            user_id,
            new_goal["baseline_kg"],
            new_goal["target_kg"],
            new_goal["start_date"].isoformat(),
            new_goal["target_date"].isoformat(),
        )
        if goal_id:
            st.success(
                f"Goal saved — a {reduction_percentage(new_goal):.0f}% cut, which needs "
                f"about {required_monthly_reduction(new_goal):,.0f} kg CO₂ off every month."
            )
            st.rerun()
        else:
            st.error("Could not save the goal. Please try again.")

# --- History ----------------------------------------------------------------

history_rows = [row for row in get_goal_history(user_id) if row["status"] != GOAL_ACTIVE]
if history_rows:
    st.markdown("---")
    st.markdown("### 🗂️ Past goals")
    st.dataframe(
        pd.DataFrame([
            {
                "Baseline (kg)": row["baseline_kg"],
                "Target (kg)": row["target_kg"],
                "From": row["start_date"],
                "To": row["target_date"],
                "Status": row["status"].title(),
            }
            for row in history_rows
        ]),
        use_container_width=True,
        hide_index=True,
    )
