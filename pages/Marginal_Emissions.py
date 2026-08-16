"""Consequential (marginal) emissions.

Every factor elsewhere in the app is an average. This page shows what a
change actually causes, and — more usefully — where the two answers disagree
enough to change the advice.
"""

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from marginal_emissions import (
    DECARBONISATION_RATES,
    DEFAULT_DECARBONISATION,
    DEFAULT_STACK,
    HOUR_LABELS,
    average_curve,
    compare_shift,
    curtailment_hours,
    curve_divergence,
    delete_comparison,
    food_comparison,
    get_comparisons,
    get_marginal_tips,
    lifetime_comparison,
    list_foods,
    list_materials,
    list_stacks,
    marginal_curve,
    material_comparison,
    rank_movement,
    ranking_changes,
    save_comparison,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()

apply_theme()

st.markdown(
    "<div class='section-header'>⚖️ Marginal Emissions</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "Every emission factor in this app is an **average**: total emissions "
    "divided by total activity. That is the right number for reporting a "
    "footprint and the wrong number for deciding what to do next. This page "
    "answers the second question."
)

with st.expander("Why one number cannot do both jobs"):
    st.markdown(
        """
**Attributional** — of the emissions that happened, how many are mine?
That is what your footprint is, and it has to use averages or the totals
stop adding up.

**Consequential** — if I do this differently, what changes? That is what
every recommendation is really claiming, and it needs the factor of whatever
responds at the margin.

For electricity the gap points in **both directions**. On a sunny grid at
midday the responding generation may be renewable output that would
otherwise have been curtailed, so the marginal factor collapses towards zero
while the average still reads 120 gCO₂/kWh. At 3am on a nuclear-heavy grid
the average looks clean but the marginal unit is usually still thermal.

One error flatters the middle of the day and the other flatters the middle
of the night, so they do not cancel — **they reorder the hours.**
        """
    )

stacks = list_stacks()
stack_col, demand_col = st.columns([2, 3])

with stack_col:
    stack_name = st.selectbox(
        "Grid mix",
        stacks,
        index=stacks.index(DEFAULT_STACK) if DEFAULT_STACK in stacks else 0,
        help=(
            "Both curves are derived from one dispatch model of this stack, "
            "so the divergence is a consequence rather than an assumption."
        ),
    )

with demand_col:
    st.caption(
        "The stack is dispatched hour by hour in merit order. The average is "
        "the emissions-weighted mean of everything running; the marginal is "
        "the rate of the last unit called. Same model, two questions."
    )

average = average_curve(stack_name)
marginal = marginal_curve(stack_name)
divergence = curve_divergence(stack_name)
curtailed = curtailment_hours(stack_name)

st.markdown("---")
st.markdown("### 📈 The Two Curves")

figure = go.Figure()
figure.add_trace(
    go.Scatter(
        x=HOUR_LABELS,
        y=average,
        name="Average (attributional)",
        mode="lines+markers",
        line=dict(width=3),
    )
)
figure.add_trace(
    go.Scatter(
        x=HOUR_LABELS,
        y=marginal,
        name="Marginal (consequential)",
        mode="lines+markers",
        line=dict(width=3, dash="dash"),
    )
)
figure.update_layout(
    xaxis_title="Hour",
    yaxis_title="gCO₂ per kWh",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
)
st.plotly_chart(figure, use_container_width=True)

if curtailed:
    st.info(
        "🌤️ **Curtailment at "
        + ", ".join(HOUR_LABELS[hour] for hour in curtailed)
        + ".** Must-run output exceeds demand in these hours, so an extra "
        "kilowatt-hour is served by generation that would otherwise have been "
        "thrown away. This is where the two curves diverge most, and it is "
        "precisely what an average-factor scheduler cannot see."
    )
else:
    st.caption(
        "No curtailment in this mix — every hour needs dispatchable "
        "generation, so the marginal unit is always thermal."
    )

st.markdown("### 🔀 Hours That Change Places")
st.caption(
    "The useful output is not the numbers. It is the hours that move when you "
    "rank by the honest curve — those are the hours where existing advice "
    "sends you to the wrong time of day."
)

changes = ranking_changes(average, marginal, top_n=8)
if changes:
    change_table = pd.DataFrame(
        [
            {
                "Hour": row["label"],
                "Rank by average": row["average_rank"],
                "Rank by marginal": row["marginal_rank"],
                "Moves": (
                    f"{'↑' if row['direction'] == 'better' else '↓'} "
                    f"{abs(row['movement'])} places"
                ),
            }
            for row in changes
        ]
    )
    st.dataframe(change_table, use_container_width=True, hide_index=True)

    biggest = changes[0]
    if biggest["direction"] == "better":
        st.success(
            f"**{biggest['label']} is {abs(biggest['movement'])} places better "
            f"than it looks.** Ranked by average intensity it comes "
            f"{biggest['average_rank']}; by what an extra kilowatt-hour "
            f"actually causes it comes {biggest['marginal_rank']}."
        )
    else:
        st.warning(
            f"**{biggest['label']} is {abs(biggest['movement'])} places worse "
            f"than it looks.** Ranked by average intensity it comes "
            f"{biggest['average_rank']}; by what an extra kilowatt-hour "
            f"actually causes it comes {biggest['marginal_rank']}."
        )
else:
    st.info(
        "The two rankings agree for this mix. Average-factor advice is safe "
        "here — which is worth knowing, and is not true of every grid."
    )

with st.expander("Hour-by-hour detail"):
    detail = pd.DataFrame(
        [
            {
                "Hour": row["label"],
                "Average": round(row["average"], 1),
                "Marginal": round(row["marginal"], 1),
                "Gap": round(row["gap"], 1),
                "Marginal unit": row["marginal_unit"],
                "Curtailing": "yes" if row["curtailed"] else "",
                "Material": "yes" if row["material"] else "",
            }
            for row in divergence
        ]
    )
    st.dataframe(detail, use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("### 🔌 Score a Load Shift")
st.caption(
    "A dishwasher, a wash cycle, an EV charge. Both accountings, side by side."
)

shift_kwh_col, from_col, to_col, duration_col = st.columns(4)
with shift_kwh_col:
    shift_kwh = st.number_input(
        "Energy (kWh)", min_value=0.0, max_value=200.0, value=1.5, step=0.5
    )
with from_col:
    from_hour = st.selectbox("Move from", range(24), index=19, format_func=lambda h: HOUR_LABELS[h])
with to_col:
    to_hour = st.selectbox("Move to", range(24), index=13, format_func=lambda h: HOUR_LABELS[h])
with duration_col:
    duration = st.number_input(
        "Run time (hours)", min_value=1, max_value=12, value=2, step=1
    )

shift = compare_shift(
    shift_kwh, from_hour, to_hour, duration_hours=duration, stack_name=stack_name
)

reported_col, actual_col, gap_col = st.columns(3)
with reported_col:
    st.metric(
        "Reported saving",
        f"{-shift['attributional_kg'] * 1000:.0f} g CO₂",
        help="What your footprint report would credit you with — average factors.",
    )
with actual_col:
    st.metric(
        "Actual saving",
        f"{-shift['consequential_kg'] * 1000:.0f} g CO₂",
        help="What the shift actually causes the grid to do — marginal factors.",
    )
with gap_col:
    st.metric(
        "Difference",
        f"{abs(shift['gap_kg']) * 1000:.0f} g CO₂",
        delta=f"{shift['relative_gap'] * 100:+.0f}%",
    )

if shift["sign_flip"]:
    st.error(f"⚠️ {shift['reading']}")
elif shift["material"]:
    st.warning(shift["reading"])
else:
    st.success(shift["reading"])

st.markdown("---")
st.markdown("### ♻️ Materials and Food")
st.caption(
    "The same average/marginal gap outside electricity, where it is larger "
    "than most people expect."
)

material_tab, food_tab = st.tabs(["Recycling", "Diet"])

actions = []

with material_tab:
    material_col, mass_col = st.columns(2)
    with material_col:
        material = st.selectbox("Material", list_materials())
    with mass_col:
        material_kg = st.number_input(
            "Mass recycled (kg)", min_value=0.0, max_value=500.0, value=5.0, step=1.0
        )

    material_result = material_comparison(material, material_kg)
    actions.append(material_result)

    reported, actual, ratio = st.columns(3)
    with reported:
        st.metric(
            "Credited", f"{-material_result['attributional_kg']:.1f} kg CO₂e"
        )
    with actual:
        st.metric("Actually avoided", f"{-material_result['consequential_kg']:.1f} kg CO₂e")
    with ratio:
        st.metric("Understated by", f"{material_result['ratio']:.1f}×")

    st.info(material_result["note"])
    st.caption(
        "Recycling one more can does not save the average factor, which "
        "blends primary and secondary metal. It avoids **primary** "
        "production."
    )

with food_tab:
    food_col, food_mass_col, horizon_col = st.columns(3)
    with food_col:
        food = st.selectbox("Food", list_foods(), index=list_foods().index("Beef"))
    with food_mass_col:
        food_kg = st.number_input(
            "Amount avoided (kg)", min_value=0.0, max_value=500.0, value=10.0, step=1.0
        )
    with horizon_col:
        horizon = st.radio(
            "Horizon",
            ["short_run", "long_run"],
            index=1,
            format_func=lambda value: value.replace("_", " ").title(),
            help=(
                "In the short run one person's demand change displaces almost "
                "nothing — herds and plantings adjust slowly. Over a decade "
                "the response approaches, and for land-intensive products can "
                "exceed, the average factor."
            ),
        )

    food_result = food_comparison(food, food_kg, horizon=horizon)
    actions.append(food_result)

    food_reported, food_actual = st.columns(2)
    with food_reported:
        st.metric("Credited", f"{-food_result['attributional_kg']:.1f} kg CO₂e")
    with food_actual:
        st.metric("Actually avoided", f"{-food_result['consequential_kg']:.1f} kg CO₂e")

    st.caption(food_result["reading"])

actions.append(shift)

movements = rank_movement(actions)
if movements:
    st.markdown("#### Ranking changes across these actions")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Action": row["label"],
                    "Rank by report": row["attributional_rank"],
                    "Rank by effect": row["consequential_rank"],
                    "Moves": f"{'↑' if row['direction'] == 'up' else '↓'} {abs(row['movement'])}",
                }
                for row in movements
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "Two numbers moving is unremarkable. Two options **swapping order** "
        "means the average-factor advice was pointing at the wrong one."
    )

st.markdown("---")
st.markdown("### 🔭 Long-Lived Assets")
st.caption(
    "A heat pump bought today spends most of its life on a grid that does not "
    "exist yet. Scoring it against today's intensity is the single largest "
    "error in most electrification comparisons."
)

kwh_col, life_col, intensity_col, trajectory_col = st.columns(4)
with kwh_col:
    annual_kwh = st.number_input(
        "Annual use (kWh)", min_value=0.0, max_value=50000.0, value=2600.0, step=100.0
    )
with life_col:
    lifetime_years = st.number_input(
        "Lifetime (years)", min_value=1, max_value=40, value=15, step=1
    )
with intensity_col:
    base_intensity = st.number_input(
        "Grid intensity today (gCO₂/kWh)",
        min_value=0.0,
        max_value=1200.0,
        value=250.0,
        step=10.0,
    )
with trajectory_col:
    trajectory = st.selectbox(
        "Decarbonisation",
        list(DECARBONISATION_RATES.keys()),
        index=list(DECARBONISATION_RATES.keys()).index(DEFAULT_DECARBONISATION),
    )

embodied_kg = st.number_input(
    "Embodied carbon of the asset (kg CO₂e)",
    min_value=0.0,
    max_value=20000.0,
    value=400.0,
    step=50.0,
)

lifetime = lifetime_comparison(
    annual_kwh,
    lifetime_years,
    base_intensity,
    trajectory=trajectory,
    embodied_kg=embodied_kg,
)

static_col, honest_col, overstated_col = st.columns(3)
with static_col:
    st.metric(
        "Scored against today's grid",
        f"{lifetime['static_lifetime_kg']:,.0f} kg CO₂e",
    )
with honest_col:
    st.metric(
        "Scored over its actual life",
        f"{lifetime['declining_lifetime_kg']:,.0f} kg CO₂e",
    )
with overstated_col:
    st.metric(
        "Overstated by",
        f"{lifetime['overstatement_kg']:,.0f} kg",
        delta=f"{lifetime['overstatement_pct']:.0f}%",
        delta_color="inverse",
    )

st.caption(
    f"Mean intensity across {lifetime['lifetime_years']} years under the "
    f"{trajectory.lower()} trajectory is "
    f"{lifetime['lifetime_mean_intensity']:.0f} gCO₂/kWh, against "
    f"{lifetime['static_intensity']:.0f} today."
)

st.markdown("---")
st.markdown("### 💡 What to Take From This")
for tip in get_marginal_tips(actions):
    st.markdown(f"- {tip}")

st.markdown("---")
st.markdown("### 💾 Saved Comparisons")

name_col, save_col = st.columns([3, 1])
with name_col:
    comparison_name = st.text_input(
        "Name", value=f"{stack_name} load shift", label_visibility="collapsed"
    )
with save_col:
    if st.button("Save", use_container_width=True):
        if save_comparison(user_id, comparison_name, shift, stack_name=stack_name):
            st.success("Saved.")
            st.rerun()
        else:
            st.error("Could not save this comparison.")

saved = get_comparisons(user_id)
if not saved:
    st.caption("Nothing saved yet.")
else:
    for entry in saved:
        with st.container(border=True):
            header_col, delete_col = st.columns([5, 1])
            with header_col:
                st.markdown(
                    f"**{entry['comparison_name']}** — {entry['stack_name']}"
                )
                st.caption(
                    f"Reported {-entry['attributional_kg'] * 1000:.0f} g · "
                    f"actual {-entry['consequential_kg'] * 1000:.0f} g · "
                    f"{entry['created_at']}"
                )
            with delete_col:
                if st.button("Delete", key=f"delete_comparison_{entry['id']}"):
                    delete_comparison(entry["id"])
                    st.rerun()

    st.download_button(
        "📥 Download as JSON",
        json.dumps(saved, indent=2),
        file_name="marginal_emissions_comparisons.json",
        mime="application/json",
    )
