"""Household marginal abatement cost curve.

Ranking actions by carbon saved is the right ranking for a household with
unlimited money. This page ranks them by cost per tonne and then answers the
question that actually gets asked: what should I do with this much money?
"""

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from abatement_curve import (
    ADOPTION_GAP_NOTE,
    DEFAULT_BUDGET,
    DEFAULT_DISCOUNT_RATE,
    DISCOUNT_RANGE,
    AbatementError,
    budget_ladder,
    build_curve,
    compose_package,
    delete_plan,
    get_abatement_insights,
    get_measure,
    get_plans,
    list_measures,
    save_plan,
    select_under_budget,
    sensitivity,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()

apply_theme()

st.markdown(
    "<div class='section-header'>📉 Abatement Cost Curve</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "Ranking actions by how much carbon they save is the right ranking for a "
    "household with unlimited money. A heat pump and a draught-proofing kit "
    "are not comparable on carbon alone: one saves more and costs sixty times "
    "as much."
)

with st.expander("Why cost per tonne alone is also wrong"):
    st.markdown(
        """
**Capital is lumpy.** A measure at 180 per tonne costing 9,000 and one at 220
per tonne costing 400 are not ordered by cost-effectiveness when you have 1,000
to spend. Reading down a cost curve until the money runs out is a known failure
on this problem, and it fails hardest where the budget is tightest.

**Measures interact.** Insulate the house and the heat pump you fit afterwards
saves less, because there is less heat to supply. Evaluating each measure
against the untouched baseline overstates any package of them, and the
overstatement grows with the number you pick. Here each measure is applied
against what the previous one left.

**Lifetime and timing.** Saving 200 kg a year for 25 years is not the same as
saving it for 5. Annualising capital needs a discount rate, and the rate
reorders the curve — so it is a control, not a constant.

**Free measures are not free of everything.** Draught-proofing, thermostat
setback and tyre pressure pay for themselves and sit left of the axis. They are
also the ones that famously do not get done. The curve shows what is economic,
not what will happen.

**The selection is exact.** Measures are grouped by the activity they act on,
every valid combination within each group is priced with its interactions and
exclusivity resolved, and a knapsack over those picks the optimum. Interactions
never cross activities, so nothing is missed.
        """
    )

st.markdown("---")
st.markdown("### 1. Your Assumptions")

budget_col, rate_col, price_col = st.columns(3)
with budget_col:
    budget = st.number_input(
        "Budget available",
        min_value=0.0,
        max_value=100000.0,
        value=DEFAULT_BUDGET,
        step=100.0,
    )
with rate_col:
    rate = st.select_slider(
        "Discount rate",
        options=list(DISCOUNT_RANGE),
        value=DEFAULT_DISCOUNT_RATE,
        format_func=lambda value: f"{value * 100:.0f}%",
        help="A household rate and a social rate give visibly different "
             "advice. That disagreement is real, so it is a control.",
    )
with price_col:
    energy_price = st.slider(
        "Energy price, relative to today",
        min_value=0.5,
        max_value=2.0,
        value=1.0,
        step=0.1,
    )

st.markdown("---")
st.markdown("### 2. The Curve")

try:
    curve = build_curve(None, rate, energy_price)
except AbatementError as error:
    st.error(str(error))
    st.stop()

figure = go.Figure()
for row in curve:
    figure.add_trace(
        go.Bar(
            x=[(row["cumulative_start"] + row["cumulative_end"]) / 2],
            y=[row["cost_per_tonne"]],
            width=[row["width_tonnes"]],
            name=row["label"],
            marker_color="#2e7d4f" if row["negative_cost"] else "#b6553b",
            hovertemplate=(
                f"<b>{row['label']}</b><br>"
                f"{row['cost_per_tonne']:,.0f} per tonne<br>"
                f"{row['saving_kg']:,.0f} kg/yr<br>"
                f"capital {row['capital']:,.0f}<extra></extra>"
            ),
            showlegend=False,
        )
    )
figure.add_hline(y=0, line_width=1)
figure.update_layout(
    title="Cost per tonne against annual abatement",
    xaxis_title="Cumulative abatement (tonnes CO₂e per year)",
    yaxis_title="Cost per tonne",
    bargap=0,
    height=440,
)
st.plotly_chart(figure, use_container_width=True)

negative = [row for row in curve if row["negative_cost"]]
if negative:
    st.info(
        f"**{len(negative)} measures pay for themselves** at this energy price "
        f"and discount rate. " + ADOPTION_GAP_NOTE
    )

st.dataframe(
    pd.DataFrame(
        [
            {
                "Measure": row["label"],
                "Per tonne": round(row["cost_per_tonne"]),
                "Capital": round(row["capital"]),
                "Saves (kg/yr)": round(row["saving_kg"]),
                "Life (yr)": round(row["lifetime"]),
                "Annual cost": round(row["annual_cost"]),
            }
            for row in curve
        ]
    ),
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")
st.markdown("### 3. What Your Budget Buys")

selection = select_under_budget(budget, rate, energy_price)

saving_col, spend_col, gap_col, cost_col = st.columns(4)
with saving_col:
    st.metric("Abatement", f"{selection['saving_kg']:,.0f} kg/yr")
with spend_col:
    st.metric(
        "Spent",
        f"{selection['capital']:,.0f}",
        delta=f"{selection['unspent']:,.0f} left",
        delta_color="off",
    )
with gap_col:
    st.metric(
        "Beats reading down the curve by",
        f"{selection['beats_greedy_kg']:,.0f} kg",
        help="Greedy selection is optimal when capital is smooth and wrong "
             "when it is lumpy.",
    )
with cost_col:
    st.metric(
        "Package cost per tonne",
        f"{selection['cost_per_tonne']:,.0f}" if selection["cost_per_tonne"] else "—",
    )

if selection["selected"]:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Measure": row["label"],
                    "Capital": round(row["capital"]),
                    "On its own (kg)": round(row["standalone_kg"]),
                    "After interaction (kg)": round(row["saving_kg"]),
                    "Per tonne": round(row["cost_per_tonne"]) if row["cost_per_tonne"] else "—",
                }
                for row in selection["package"]["measures"]
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.caption("Nothing is affordable at this budget.")

if selection["interaction_loss_kg"] > 1.0:
    st.warning(
        f"Adding these measures' individual savings would give "
        f"{selection['naive_saving_kg']:,.0f} kg. They act on the same heat "
        f"and the same miles, so each applies to what the previous one left: "
        f"**{selection['saving_kg']:,.0f} kg**. The "
        f"{selection['interaction_loss_kg']:,.0f} kg difference is "
        f"interaction, not an error in either number."
    )

if selection["beats_greedy_kg"] > 1.0:
    greedy_labels = ", ".join(
        get_measure(key)["label"].lower() for key in selection["greedy_selected"]
    )
    st.success(
        f"**Reading down the curve would have picked differently** "
        f"({greedy_labels}) and saved {selection['beats_greedy_kg']:,.0f} kg "
        f"less for the same money. This is the lumpiness of capital, not a "
        f"rounding difference."
    )

st.markdown("---")
st.markdown("### 4. What Each Budget Buys")

ladder = budget_ladder(rate=rate, energy_price_factor=energy_price)
ladder_figure = go.Figure()
ladder_figure.add_trace(
    go.Scatter(
        x=[row["budget"] for row in ladder],
        y=[row["saving_kg"] for row in ladder],
        mode="lines+markers",
        name="Exact selection",
        line={"width": 3},
    )
)
ladder_figure.add_trace(
    go.Scatter(
        x=[row["budget"] for row in ladder],
        y=[row["greedy_saving_kg"] for row in ladder],
        mode="lines+markers",
        name="Reading down the curve",
        line={"width": 2, "dash": "dot"},
    )
)
ladder_figure.update_layout(
    title="Abatement against budget, both ways of choosing",
    xaxis_title="Budget",
    yaxis_title="kg CO₂e per year",
    height=380,
    legend={"orientation": "h", "y": -0.2},
)
st.plotly_chart(ladder_figure, use_container_width=True)

st.dataframe(
    pd.DataFrame(
        [
            {
                "Budget": round(row["budget"]),
                "Spent": round(row["capital"]),
                "Abatement (kg/yr)": round(row["saving_kg"]),
                "Greedy would give": round(row["greedy_saving_kg"]),
                "Difference": round(row["beats_greedy_kg"]),
                "Measures": len(row["selected"]),
            }
            for row in ladder
        ]
    ),
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")
st.markdown("### 5. Build Your Own Package")

chosen = st.multiselect(
    "Measures",
    list_measures(),
    default=selection["selected"],
    format_func=lambda key: get_measure(key)["label"],
)

package = compose_package(chosen, rate, energy_price)
package_cols = st.columns(4)
with package_cols[0]:
    st.metric("Capital", f"{package['capital']:,.0f}")
with package_cols[1]:
    st.metric("Added up", f"{package['naive_saving_kg']:,.0f} kg")
with package_cols[2]:
    st.metric("After interaction", f"{package['saving_kg']:,.0f} kg")
with package_cols[3]:
    st.metric(
        "Per tonne",
        f"{package['cost_per_tonne']:,.0f}" if package["cost_per_tonne"] else "—",
    )

if package["measures"]:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Measure": row["label"],
                    "Acts on": row["activity"],
                    "On its own (kg)": round(row["standalone_kg"]),
                    "In this package (kg)": round(row["saving_kg"]),
                    "Given back (kg)": round(row["interaction_kg"]),
                }
                for row in package["measures"]
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "A measure's contribution depends on what else is in the package. "
        "The order changes what each is credited with, though not the total."
    )

st.markdown("---")
st.markdown("### 6. How Stable Is This Advice?")
st.caption(
    "The ordering in the middle of the curve is genuinely unstable across "
    "plausible discount rates and energy prices. Presenting one ordering as "
    "definitive would be false precision of exactly the kind this page exists "
    "to remove."
)

st.dataframe(
    pd.DataFrame(
        [
            {
                "Discount rate": f"{row['rate'] * 100:.0f}%",
                "Energy price": f"{row['energy_price_factor']:.1f}×",
                "Cheapest measure": get_measure(row["cheapest"])["label"] if row["cheapest"] else "—",
                "Paying for themselves": row["negative_cost_count"],
                "Abatement (kg/yr)": round(row["saving_kg"]),
                "Measures": len(row["selected"]),
            }
            for row in sensitivity(budget)
        ]
    ),
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")
st.markdown("### 💡 What To Take From This")
for insight in get_abatement_insights(selection):
    st.markdown(f"- {insight}")

st.markdown("---")
st.markdown("### 💾 Saved Plans")

name_col, save_col = st.columns([3, 1])
with name_col:
    plan_name = st.text_input(
        "Name", value=f"Plan at {budget:,.0f}", label_visibility="collapsed"
    )
with save_col:
    if st.button("Save", use_container_width=True):
        if save_plan(user_id, plan_name, selection, rate):
            st.success("Saved.")
            st.rerun()
        else:
            st.error("Could not save this plan.")

saved = get_plans(user_id)
if not saved:
    st.caption("Nothing saved yet.")
else:
    for entry in saved:
        with st.container(border=True):
            detail_col, delete_col = st.columns([5, 1])
            with detail_col:
                st.markdown(f"**{entry['name']}**")
                st.caption(
                    f"{entry['capital']:,.0f} spent of {entry['budget']:,.0f} · "
                    f"{entry['saving_kg']:,.0f} kg/yr across "
                    f"{entry['measure_count']} measure(s) at "
                    f"{entry['discount_rate'] * 100:.0f}% · {entry['created_at']}"
                )
            with delete_col:
                if st.button("Delete", key=f"delete_abatement_{entry['id']}"):
                    delete_plan(entry["id"])
                    st.rerun()

    st.download_button(
        "📥 Download as JSON",
        json.dumps(saved, indent=2, default=str),
        file_name="abatement_plans.json",
        mime="application/json",
    )
