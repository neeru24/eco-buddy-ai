"""Gas-resolved climate metrics.

"kg CO2e" is a conversion with a convention buried in it. This page states
the convention, shows the same footprint under the alternatives, and points
at the places where the choice changes the advice.
"""

import datetime
import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from climate_metrics import (
    GAS_LABELS,
    GAS_LIFETIMES,
    GAS_NOTES,
    ClimateMetricsError,
    biogenic_payback,
    compare_metrics,
    decompose_footprint,
    delete_assessment,
    get_assessments,
    get_methane_history,
    get_metric_insights,
    gwp_star_vs_gwp100,
    list_activities,
    metric_disagreement,
    record_methane_year,
    save_assessment,
    separate_carbon,
    split_note,
    warming_contribution,
)
from styles.theme import apply_theme

DEFAULT_FOOTPRINT = {
    "beef": 900.0,
    "dairy": 450.0,
    "electricity": 1100.0,
    "petrol_car": 1400.0,
    "flights": 1000.0,
    "landfill_waste": 320.0,
    "wood_heating": 0.0,
}

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()

apply_theme()

st.markdown(
    "<div class='section-header'>🌡️ Climate Metrics</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "The app reports everything in **kg CO₂e**. That is a conversion, and "
    "every conversion has a convention buried in it. The convention used "
    "everywhere else — GWP100 — treats a kilogram of methane as though it "
    "behaves like a kilogram of CO₂ spread over a century. It does not."
)

with st.expander("Why methane breaks the metric"):
    st.markdown(
        """
Methane lasts about **twelve years** in the atmosphere. CO₂ has no
meaningful lifetime at all — a fraction of it is still there in a thousand
years. GWP100 handles this by integrating over a century and dividing, which
produces one convenient number and one specific error:

- **A constant methane source causes constant warming, not rising warming.**
  After a couple of decades the methane destroyed each year matches the
  methane emitted, and the stock stops growing. GWP100 reports the same
  emission every year as though it were adding to a permanent stock — true
  for CO₂, false for methane.

- **The converse is what matters.** A *reduction* in a sustained methane
  source actively **cools**, faster and further than GWP100 credits. If you
  are cutting dairy, you are doing more in the near term than the app tells
  you.

**GWP\\*** exists for exactly this. It relates the *rate of change* of a
short-lived gas to a warming effect, so a steady flow maps to roughly no
additional warming and a change maps to a real one.

This page does not switch the app to GWP\\*. It cannot: GWP\\* is undefined
for a single year with no history, and inventory reporting requires GWP100.
Both are needed, so both are always shown.
        """
    )

st.markdown("---")
st.markdown("### 1. Your Footprint, By Gas")
st.caption(
    "Enter what you already know in kg CO₂e. Splitting it into gases leaves "
    "the GWP100 total **exactly** where it was — this is a decomposition, not "
    "a restatement, and your headline number does not move because you "
    "opened this page."
)

activities = {}
columns = st.columns(3)
for index, activity in enumerate(sorted(DEFAULT_FOOTPRINT)):
    with columns[index % 3]:
        activities[activity] = st.number_input(
            activity.replace("_", " ").title(),
            min_value=0.0,
            max_value=100000.0,
            value=float(DEFAULT_FOOTPRINT[activity]),
            step=50.0,
            help=split_note(activity),
        )

extra_activity = st.selectbox(
    "Add another activity",
    ["—"] + [a for a in list_activities() if a not in activities],
)
if extra_activity != "—":
    activities[extra_activity] = st.number_input(
        extra_activity.replace("_", " ").title(),
        min_value=0.0,
        max_value=100000.0,
        value=100.0,
        step=50.0,
        help=split_note(extra_activity),
    )

activities = {name: value for name, value in activities.items() if value > 0}

if not activities:
    st.info("Enter at least one activity to see the decomposition.")
    st.stop()

try:
    decomposed = decompose_footprint(activities)
except ClimateMetricsError as error:
    st.error(str(error))
    st.stop()

comparison = compare_metrics(decomposed["by_gas_mass"])
carbon = separate_carbon(decomposed["by_gas_co2e"])

gas_rows = [
    {
        "Gas": GAS_LABELS[gas],
        "kg CO₂e (GWP100)": round(value, 1),
        "Share": f"{value / decomposed['total_gwp100_kg'] * 100:.1f}%",
        "Atmospheric lifetime": (
            "no fixed lifetime"
            if GAS_LIFETIMES[gas] is None
            else f"{GAS_LIFETIMES[gas]:.0f} years"
        ),
    }
    for gas, value in sorted(
        decomposed["by_gas_co2e"].items(), key=lambda item: item[1], reverse=True
    )
    if value > 0
]

table_col, chart_col = st.columns([3, 2])
with table_col:
    st.dataframe(pd.DataFrame(gas_rows), use_container_width=True, hide_index=True)
    st.caption(
        f"Total: **{decomposed['total_gwp100_kg']:,.0f} kg CO₂e** — the same "
        "number the rest of the app shows."
    )
with chart_col:
    pie = go.Figure(
        data=[
            go.Pie(
                labels=[row["Gas"] for row in gas_rows],
                values=[row["kg CO₂e (GWP100)"] for row in gas_rows],
                hole=0.45,
            )
        ]
    )
    pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=280)
    st.plotly_chart(pie, use_container_width=True)

with st.expander("What each gas is, and why it behaves differently"):
    for gas in sorted(decomposed["by_gas_co2e"]):
        if decomposed["by_gas_co2e"][gas] <= 0:
            continue
        st.markdown(f"**{GAS_LABELS[gas]}** — {GAS_NOTES[gas]}")

st.markdown("---")
st.markdown("### 2. The Same Emissions Over 20 Years")

hundred_col, twenty_col, ratio_col = st.columns(3)
with hundred_col:
    st.metric("GWP100", f"{comparison['gwp100_kg']:,.0f} kg CO₂e")
with twenty_col:
    st.metric("GWP20", f"{comparison['gwp20_kg']:,.0f} kg CO₂e")
with ratio_col:
    st.metric(
        "Ratio",
        f"{comparison['ratio']:.2f}×",
        help="How much larger your footprint looks on a twenty-year horizon.",
    )

st.info(comparison["reading"])

horizon_figure = go.Figure()
horizon_figure.add_trace(
    go.Bar(
        name="GWP100",
        x=[GAS_LABELS[gas] for gas in comparison["by_gas_gwp100"]],
        y=list(comparison["by_gas_gwp100"].values()),
    )
)
horizon_figure.add_trace(
    go.Bar(
        name="GWP20",
        x=[GAS_LABELS[gas] for gas in comparison["by_gas_gwp20"]],
        y=list(comparison["by_gas_gwp20"].values()),
    )
)
horizon_figure.update_layout(
    barmode="group",
    yaxis_title="kg CO₂e",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    height=340,
)
st.plotly_chart(horizon_figure, use_container_width=True)

st.markdown("#### Where the horizon changes the advice")
changes = metric_disagreement(activities)
if changes:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Activity": row["activity"].replace("_", " ").title(),
                    "Rank under GWP100": row["gwp100_rank"],
                    "Rank under GWP20": row["gwp20_rank"],
                    "Moves": (
                        f"{'↑' if row['direction'] == 'up' else '↓'} "
                        f"{abs(row['movement'])}"
                    ),
                }
                for row in changes
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.warning(
        "These activities **swap places** depending on the horizon. Which one "
        "the app tells you to tackle first therefore depends on a convention "
        "it has never stated."
    )
else:
    st.success(
        "Your activities keep the same order on both horizons, so the metric "
        "convention does not change what you should do first."
    )

st.markdown("---")
st.markdown("### 3. Methane Over Time (GWP\\*)")
st.caption(
    "This is the part that needs history. One year cannot show a trend, and "
    "the module says so rather than inventing one."
)

history = get_methane_history(user_id)
this_year = datetime.date.today().year

year_col, amount_col, record_col = st.columns([1, 2, 1])
with year_col:
    entry_year = st.number_input(
        "Year", min_value=1990, max_value=this_year + 1, value=this_year, step=1
    )
with amount_col:
    methane_mass = sum(
        decomposed["by_gas_mass"].get(gas, 0.0)
        for gas in ("ch4_biogenic", "ch4_fossil")
    )
    entry_kg = st.number_input(
        "Methane this year (kg CH₄)",
        min_value=0.0,
        max_value=10000.0,
        value=round(methane_mass, 1),
        step=1.0,
        help="Pre-filled from the decomposition above.",
    )
with record_col:
    st.write("")
    if st.button("Record year", use_container_width=True):
        record_methane_year(user_id, entry_year, entry_kg)
        st.rerun()

if not history:
    st.info(
        "No methane history recorded yet. Record at least two years to see "
        "GWP\\* — with one year it falls back to ordinary pulse accounting, "
        "because there is no rate of change to measure."
    )
else:
    series = [value for _, value in history]
    star = gwp_star_vs_gwp100(series)

    history_figure = go.Figure()
    history_figure.add_trace(
        go.Scatter(
            x=[year for year, _ in history],
            y=series,
            mode="lines+markers",
            name="Methane (kg CH₄/year)",
        )
    )
    history_figure.update_layout(
        xaxis_title="Year", yaxis_title="kg CH₄", height=300
    )
    st.plotly_chart(history_figure, use_container_width=True)

    pulse_col, star_col, trend_col = st.columns(3)
    with pulse_col:
        st.metric("Under GWP100", f"{star['gwp100_kg']:,.0f} kg CO₂e")
    with star_col:
        st.metric("Under GWP\\*", f"{star['gwp_star_kg']:,.0f} kg CO₂we")
    with trend_col:
        st.metric("Trend", star["trend"].title())

    if star["sign_flip"]:
        st.success(
            "**GWP100 reports an emission; GWP\\* reports cooling.** Your "
            "methane flow is falling, and a sustained short-lived source that "
            "shrinks removes warming rather than adding it. "
            + star["reading"]
        )
    else:
        st.info(star["reading"])

    if star["basis"] == "pulse":
        st.caption(
            "Only one year on record, so this is GWP100 pulse accounting "
            "rather than GWP\\*."
        )

st.markdown("---")
st.markdown("### 4. Fossil and Biogenic Carbon")

fossil_col, biogenic_col, other_col = st.columns(3)
with fossil_col:
    st.metric(
        "Fossil carbon",
        f"{carbon['fossil_kg']:,.0f} kg",
        delta=f"{carbon['fossil_share'] * 100:.0f}% of total",
        delta_color="off",
    )
with biogenic_col:
    st.metric(
        "Biogenic carbon",
        f"{carbon['biogenic_kg']:,.0f} kg",
        delta=f"{carbon['biogenic_share'] * 100:.0f}% of total",
        delta_color="off",
    )
with other_col:
    st.metric("Nitrous oxide", f"{carbon['other_kg']:,.0f} kg")

st.caption(
    "Burning wood releases carbon a tree recently took out of the air. "
    "Burning gas releases carbon that has been underground for 300 million "
    "years. Both currently land in the same total at the same weight. The "
    "honest answer is not that one is free — it is a payback period."
)

for line in decomposed["lines"]:
    biogenic_co2 = line["by_gas_co2e"].get("co2_biogenic", 0.0)
    if biogenic_co2 <= 0:
        continue
    payback = biogenic_payback(line["activity"], biogenic_co2)
    if payback["counted_as_neutral"]:
        st.success(
            f"**{line['activity'].replace('_', ' ').title()}** — "
            f"{payback['verdict']}"
        )
    else:
        st.warning(
            f"**{line['activity'].replace('_', ' ').title()}** — "
            f"{payback['verdict']}"
        )

st.markdown("---")
st.markdown("### 5. What This Is All A Proxy For")

population = st.slider(
    "If this many people emitted the same",
    min_value=1_000_000,
    max_value=8_200_000_000,
    value=100_000_000,
    step=1_000_000,
    format="%d",
)

warming_100 = warming_contribution(comparison["gwp100_kg"], population)
warming_20 = warming_contribution(comparison["gwp20_kg"], population)

warm_col_a, warm_col_b = st.columns(2)
with warm_col_a:
    st.metric("Warming, GWP100 basis", f"{warming_100['millikelvin']:.2f} mK")
with warm_col_b:
    st.metric("Warming, GWP20 basis", f"{warming_20['millikelvin']:.2f} mK")

st.caption(warming_100["caveat"])

st.markdown("---")
st.markdown("### 💡 What To Take From This")
for insight in get_metric_insights(decomposed, comparison):
    st.markdown(f"- {insight}")

st.markdown("---")
st.markdown("### 💾 Saved Assessments")

name_col, save_col = st.columns([3, 1])
with name_col:
    assessment_name = st.text_input(
        "Name", value=f"Footprint {this_year}", label_visibility="collapsed"
    )
with save_col:
    if st.button("Save", use_container_width=True):
        if save_assessment(user_id, assessment_name, decomposed, comparison):
            st.success("Saved.")
            st.rerun()
        else:
            st.error("Could not save this assessment.")

saved = get_assessments(user_id)
if not saved:
    st.caption("Nothing saved yet.")
else:
    for entry in saved:
        with st.container(border=True):
            detail_col, delete_col = st.columns([5, 1])
            with detail_col:
                st.markdown(f"**{entry['name']}**")
                st.caption(
                    f"GWP100 {entry['gwp100_kg']:,.0f} kg · "
                    f"GWP20 {entry['gwp20_kg']:,.0f} kg · "
                    f"methane {entry['methane_share'] * 100:.0f}% · "
                    f"{entry['created_at']}"
                )
            with delete_col:
                if st.button("Delete", key=f"delete_metric_{entry['id']}"):
                    delete_assessment(entry["id"])
                    st.rerun()

    st.download_button(
        "📥 Download as JSON",
        json.dumps(saved, indent=2, default=str),
        file_name="climate_metrics.json",
        mime="application/json",
    )
