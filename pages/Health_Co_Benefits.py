import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from health_cobenefits import (
    DEFAULT_DENSITY,
    OUTCOME_LABELS,
    POLLUTANT_LABELS,
    POLLUTANTS,
    CoBenefitError,
    assess_activity,
    assess_switch,
    delete_assessment,
    describe_outcomes,
    get_assessments,
    get_method_caveats,
    list_activities,
    list_categories,
    list_density_options,
    rank_actions,
    save_assessment,
    scale_to_population,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()

apply_theme()

st.markdown(
    "<div class='section-header'>🫁 Health & Air Quality Co-Benefits</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "Burning things releases more than CO2. Carbon benefits are global and "
    "arrive over decades; **air quality benefits land on your street this "
    "year**. This page counts both — and flags the actions that look good on "
    "carbon while making the air worse."
)

density_options = [option["name"] for option in list_density_options()]

st.markdown("---")
st.markdown("### 📍 Where You Are")
st.caption(
    "The same tailpipe does very different amounts of harm depending on how "
    "many people are nearby to breathe it. This is not a detail — it changes "
    "the answer by close to an order of magnitude."
)

density = st.select_slider(
    "Where you live",
    options=list(reversed(density_options)),
    value=DEFAULT_DENSITY,
)
st.caption(
    next(
        option["description"]
        for option in list_density_options()
        if option["name"] == density
    )
)

st.markdown("---")
st.markdown("### 🔄 Compare Two Options")

category = st.selectbox("What are you deciding about?", list_categories())
activities = list_activities(category=category)
options = [activity["name"] for activity in activities]

from_col, to_col = st.columns(2)
with from_col:
    from_activity = st.selectbox("What you do now", options, index=len(options) - 1)
with to_col:
    to_activity = st.selectbox("What you are considering", options, index=0)

# Taken from what the user actually picked rather than from the first entry in
# the category: within transport, some options are per km and some are per
# passenger-km, and labelling them wrongly would invite a bad comparison.
unit = next(item["unit"] for item in activities if item["name"] == from_activity)

amount = st.number_input(
    f"How much per year ({unit})",
    min_value=0.0,
    value=12000.0 if category == "transport" else 10000.0,
    step=500.0,
)

try:
    switch = assess_switch(from_activity, to_activity, amount, density)
except CoBenefitError as error:
    st.error(str(error))
    st.stop()

carbon_col, health_col, total_col = st.columns(3)
carbon_col.metric("Carbon avoided", f"{switch['carbon_saving_kg']:,.0f} kg CO2e")
health_col.metric("Health damage avoided", f"{switch['air_quality_value']:,.0f}")
total_col.metric("Combined value", f"{switch['total_value']:,.0f}")

verdict_style = {
    "win_win": st.success,
    "carbon_only": st.error,
    "health_only": st.warning,
    "worse_on_both": st.error,
}
verdict_style[switch["verdict"]](switch["explanation"])

if switch["is_conflict"]:
    st.markdown(
        "⚠️ **The two measures disagree here.** This is exactly the case a "
        "carbon-only recommender gets wrong, and it is the reason this page "
        "exists."
    )

pollutant_frame = pd.DataFrame(
    [
        {
            "Pollutant": POLLUTANT_LABELS[pollutant],
            "Avoided (grams/year, exposure-weighted)": round(
                switch["avoided_pollutants"][pollutant], 1
            ),
        }
        for pollutant in POLLUTANTS
        if abs(switch["avoided_pollutants"][pollutant]) > 0.001
    ]
)
if not pollutant_frame.empty:
    st.dataframe(pollutant_frame, use_container_width=True, hide_index=True)

value_figure = go.Figure()
value_figure.add_trace(
    go.Bar(
        name="Climate benefit",
        x=["This switch"],
        y=[switch["carbon_value"]],
        marker_color="rgba(46, 139, 87, 0.8)",
    )
)
value_figure.add_trace(
    go.Bar(
        name="Local air quality benefit",
        x=["This switch"],
        y=[switch["air_quality_value"]],
        marker_color="rgba(70, 130, 180, 0.8)",
    )
)
value_figure.update_layout(
    barmode="relative",
    height=320,
    yaxis_title="Avoided damage (currency per year)",
    margin=dict(l=10, r=10, t=30, b=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(value_figure, use_container_width=True)

if switch["total_value"] > 0 and switch["health_share"] > 0:
    st.info(
        f"**{switch['health_share'] * 100:.0f}% of the value of this switch is "
        f"the air, not the climate.** Judged on carbon alone you would be "
        f"seeing a fraction of the benefit."
    )

st.markdown("---")
st.markdown("### 🏥 What That Means in Health Terms")

st.markdown("**For your household alone:**")
for line in describe_outcomes(switch["avoided_outcomes"]):
    st.markdown(f"- {line}")

households = st.select_slider(
    "Now imagine this many households did the same",
    options=[1, 100, 1000, 10000, 100000, 1000000],
    value=100000,
)
scaled = scale_to_population(switch, households)

st.markdown(f"**Across {households:,} households:**")
for line in describe_outcomes(scaled["outcomes"], households):
    st.markdown(f"- {line}")

outcome_frame = pd.DataFrame(
    [
        {
            "Outcome": OUTCOME_LABELS[outcome].title(),
            "Your household": f"{switch['avoided_outcomes'][outcome]:.4f}",
            f"{households:,} households": f"{value:,.1f}",
        }
        for outcome, value in scaled["outcomes"].items()
    ]
)
st.dataframe(outcome_frame, use_container_width=True, hide_index=True)

st.caption(
    "Deaths are a population-level statistical expectation, not a prediction "
    "about anyone. One household's share of a population effect is genuinely "
    "tiny — which is the honest answer, and the reason the scaled view is "
    "shown beside it."
)

st.markdown("---")
st.markdown("### 🏆 Ranking Actions on Both Measures")
st.caption(
    "The same candidate actions, ranked by carbon alone and by carbon plus "
    "health. Where the two orders disagree, the carbon-only ranking is the "
    "one that would have misled you."
)

CANDIDATES = [
    {"from": "Petrol car", "to": "Cycling or walking", "amount": 3000},
    {"from": "Petrol car", "to": "Electric car", "amount": 12000},
    {"from": "Petrol car", "to": "Bus", "amount": 5000},
    {"from": "Gas boiler", "to": "Modern wood stove", "amount": 10000},
    {"from": "Gas boiler", "to": "Heat pump", "amount": 10000},
    {"from": "Open fire or old stove", "to": "Heat pump", "amount": 8000},
]

ranking = rank_actions(CANDIDATES, density)

ranking_frame = pd.DataFrame(
    [
        {
            "Action": f"{item['from']} → {item['to']}",
            "Rank (both measures)": item["combined_rank"],
            "Rank (carbon only)": item["carbon_rank"],
            "Carbon saved (kg)": round(item["carbon_saving_kg"]),
            "Health value": round(item["air_quality_value"]),
            "Combined value": round(item["total_value"]),
            "Disagrees": "⚠️" if item["ranking_disagrees"] else "",
        }
        for item in ranking["ranked"]
    ]
)
st.dataframe(ranking_frame, use_container_width=True, hide_index=True)

if ranking["rankings_agree"]:
    st.success(
        "For these actions the two measures agree on the top choice. Carbon "
        "alone would not have misled you here."
    )
else:
    st.error(
        f"**The two measures disagree.** Ranked on carbon alone the winner is "
        f"*{ranking['top_by_carbon']}*; counting the air people breathe, it is "
        f"*{ranking['top_by_combined']}*."
    )

for conflict in ranking["conflicts"]:
    if conflict["is_conflict"]:
        st.warning(f"**{conflict['from']} → {conflict['to']}** — {conflict['explanation']}")

st.markdown("---")
st.markdown("### 💾 Saved Assessments")

name_col, save_col = st.columns([3, 1])
with name_col:
    assessment_name = st.text_input(
        "Assessment name", value="My commute", label_visibility="collapsed"
    )
with save_col:
    if st.button("Save assessment", use_container_width=True):
        if save_assessment(user_id, assessment_name, switch):
            st.success("Saved.")
        else:
            st.error("Could not save that assessment.")

saved = get_assessments(user_id)
if not saved:
    st.caption("No saved assessments yet.")
else:
    for item in saved:
        detail_col, delete_col = st.columns([5, 1])
        with detail_col:
            st.markdown(
                f"**{item['name']}** — {item['from']} → {item['to']} "
                f"({item['amount']:,.0f} units, {item['density']}): "
                f"{item['carbon_saving_kg']:,.0f} kg CO2e and "
                f"{item['air_quality_value']:,.0f} of health damage avoided "
                f"· {item['created_at']}"
            )
        with delete_col:
            if st.button("Delete", key=f"delete_cobenefit_{item['id']}"):
                delete_assessment(user_id, item["id"])
                st.rerun()

st.markdown("---")
st.markdown("### ⚠️ What This Method Does And Does Not Show")
for caveat in get_method_caveats():
    st.markdown(f"- {caveat}")

st.caption(
    "Method: emission factor → intake fraction → concentration-response → "
    "outcome, the standard screening-level chain used in health impact "
    "assessment. Damage costs per tonne follow published national guidance. "
    "The ranking of actions is considerably more reliable than the absolute "
    "money figures."
)
