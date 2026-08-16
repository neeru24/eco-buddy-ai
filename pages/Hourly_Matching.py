"""Hourly carbon-free energy matching.

A "100% renewable" tariff is an annual claim. This page scores it hour by hour
against the household's actual consumption, and reports the difference between
what the claim says and what the matching supports.
"""

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from hourly_matching import (
    DEFAULT_GRID_PROFILE,
    DEFAULT_LOAD_PROFILE,
    MatchingError,
    certificate_gap,
    compare_supply_options,
    delete_analysis,
    get_grid_profile,
    get_load_profile,
    get_matching_insights,
    get_supply_profile,
    get_analyses,
    list_grid_profiles,
    list_load_profiles,
    list_supply_profiles,
    match_year,
    save_analysis,
    sensitivity,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()

apply_theme()

st.markdown(
    "<div class='section-header'>🕐 Hourly Carbon-Free Matching</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "A green tariff is an **annual** claim: over a year, someone generated as "
    "many clean kilowatt-hours as you used. It says nothing about whether "
    "clean power was on the wire at the hours you actually drew from it."
)

with st.expander("Why the two numbers differ"):
    st.markdown(
        """
**Annual matching** compares totals. Generate or contract 3,000 kWh of clean
power, use 3,500 kWh, and you are 86% matched. The comparison is made once, at
the end of the year.

**Hourly matching** compares each hour to itself. Rooftop solar exports at
midday and your largest load is at 7pm in January. The midday surplus cannot
travel forward in time to cover the evening, so it does not.

The gap between the two is not an accounting subtlety. It is the share of your
consumption that was met by the grid at the moment it happened — and on a still
winter evening, the grid means gas.

**Export is not simply banked either.** A kilowatt-hour exported into a midday
that is already saturated with solar displaces very little and may be curtailed
outright. Annual netting counts it at full value against your evening
consumption. This page does not.

**What actually moves the number:** shifting flexible load towards the matched
hours, or storage that carries midday generation into the evening. Buying more
certificates moves only the annual figure.
        """
    )

st.markdown("---")
st.markdown("### 1. Your Consumption")

consumption_col, load_col, grid_col = st.columns(3)
with consumption_col:
    consumption = st.number_input(
        "Annual electricity use (kWh)",
        min_value=100.0,
        max_value=100000.0,
        value=3500.0,
        step=100.0,
    )
with load_col:
    load_profile = st.selectbox(
        "When you use it",
        list_load_profiles(),
        index=list_load_profiles().index(DEFAULT_LOAD_PROFILE),
        format_func=lambda name: get_load_profile(name)["label"],
    )
with grid_col:
    grid_profile = st.selectbox(
        "Your grid",
        list_grid_profiles(),
        index=list_grid_profiles().index(DEFAULT_GRID_PROFILE),
        format_func=lambda name: get_grid_profile(name)["label"],
    )

st.caption(get_load_profile(load_profile)["note"])
st.caption(get_grid_profile(grid_profile)["note"])

st.markdown("---")
st.markdown("### 2. Your Clean Supply")
st.caption(
    "On-site generation reduces what you physically import. A contract moves "
    "certificates and changes nothing on the wire — an annual claim cannot "
    "tell the two apart, which is most of the problem."
)

if "matching_supplies" not in st.session_state:
    st.session_state.matching_supplies = [
        {"profile": "rooftop_solar", "annual_kwh": 3000.0},
    ]

supplies = st.session_state.matching_supplies

add_col, clear_col, _ = st.columns([1, 1, 3])
with add_col:
    if st.button("➕ Add supply", use_container_width=True):
        supplies.append({"profile": "unspecified_certificates", "annual_kwh": 1000.0})
with clear_col:
    if st.button("Clear all", use_container_width=True):
        st.session_state.matching_supplies = []
        st.rerun()

for index, supply in enumerate(list(supplies)):
    row = st.columns([3, 2, 1])
    with row[0]:
        supply["profile"] = st.selectbox(
            "Source",
            list_supply_profiles(),
            index=list_supply_profiles().index(supply["profile"]),
            format_func=lambda name: get_supply_profile(name)["label"],
            key=f"matching_profile_{index}",
        )
    with row[1]:
        supply["annual_kwh"] = st.number_input(
            "kWh/year",
            min_value=0.0,
            max_value=100000.0,
            value=float(supply["annual_kwh"]),
            step=100.0,
            key=f"matching_kwh_{index}",
        )
    with row[2]:
        st.write("")
        if st.button("Remove", key=f"matching_remove_{index}", use_container_width=True):
            supplies.pop(index)
            st.rerun()
    st.caption(get_supply_profile(supply["profile"])["note"])

try:
    result = match_year(consumption, load_profile, supplies, grid_profile)
except MatchingError as error:
    st.error(str(error))
    st.stop()

st.markdown("---")
st.markdown("### 3. What The Claim Delivers")

annual_col, hourly_col, gap_col, kg_col = st.columns(4)
with annual_col:
    st.metric(
        "Annual matching",
        f"{result['annual_match_pct']:.0f}%",
        help="The figure a tariff or a solar quote would report.",
    )
with hourly_col:
    st.metric(
        "Hourly matching",
        f"{result['hourly_cfe_pct']:.0f}%",
        help="The share met by clean supply in the hour you used it.",
    )
with gap_col:
    st.metric(
        "Gap",
        f"{result['matching_gap_pct']:.0f} pts",
        delta=f"−{result['matching_gap_pct']:.0f}",
        delta_color="inverse",
    )
with kg_col:
    st.metric(
        "Unmatched",
        f"{result['unmatched_kwh']:,.0f} kWh",
        help="Consumption with no clean supply behind it at the time.",
    )

hours = pd.DataFrame(result["hours"])
figure = go.Figure()
figure.add_trace(
    go.Bar(
        x=hours["hour"],
        y=hours["matched_kwh"],
        name="Matched by clean supply",
        marker_color="#2e9e5b",
    )
)
figure.add_trace(
    go.Bar(
        x=hours["hour"],
        y=hours["consumption_kwh"] - hours["matched_kwh"],
        name="Taken from the grid",
        marker_color="#b6553b",
    )
)
figure.add_trace(
    go.Scatter(
        x=hours["hour"],
        y=hours["mean_import_intensity"],
        name="Grid intensity of imports (g/kWh)",
        yaxis="y2",
        mode="lines",
        line={"width": 2, "dash": "dot"},
    )
)
figure.update_layout(
    barmode="stack",
    title="Consumption by hour of day, across the year",
    xaxis_title="Hour",
    yaxis_title="kWh",
    yaxis2={"title": "gCO₂e/kWh", "overlaying": "y", "side": "right"},
    height=420,
    legend={"orientation": "h", "y": -0.2},
)
st.plotly_chart(figure, use_container_width=True)

st.caption(
    "The unmatched block is concentrated in the evening, which is also where "
    "the dotted line is highest. That coincidence is the whole subject."
)

st.markdown("---")
st.markdown("### 4. Both Accounting Frames")

location_col, market_col = st.columns(2)
with location_col:
    st.markdown("**Location-based** — what the grid emitted for your imports")
    st.metric("Hour by hour", f"{result['location_based_kg']:,.0f} kg")
    st.caption(
        f"Using the grid's annual average instead gives "
        f"{result['location_based_flat_kg']:,.0f} kg. The "
        f"{result['timing_premium_kg']:,.0f} kg difference is there because "
        f"your imports land on dirtier hours than the average — true whatever "
        f"tariff you are on."
    )
with market_col:
    st.markdown("**Market-based** — after your supply contract is counted")
    st.metric("Hour by hour", f"{result['market_based_hourly_kg']:,.0f} kg")
    st.caption(
        f"Netting certificates annually, as suppliers do, gives "
        f"{result['market_based_annual_kg']:,.0f} kg."
    )

gap = certificate_gap(result)
if gap["gap_kg"] > 1.0:
    st.warning(
        f"**The certificate gap is {gap['gap_kg']:,.0f} kg.** That is the "
        f"difference between netting certificates over the year and requiring "
        f"them to arrive in the hour you consumed — an overstatement of "
        f"{gap['overstatement_pct']:.0f}% in the reported footprint. The "
        f"tariff has not become worse; the reporting has become honest about "
        f"the hours it never covered."
    )

if result["export_kwh"] > 0:
    st.markdown("**Export**")
    export_col, curtailed_col, credit_col = st.columns(3)
    with export_col:
        st.metric("Exported", f"{result['export_kwh']:,.0f} kWh")
    with curtailed_col:
        st.metric(
            "Displaces nothing",
            f"{result['export_curtailed_kwh']:,.0f} kWh",
            help="Exported into hours where the grid is already clean.",
        )
    with credit_col:
        st.metric("Actually displaced", f"{result['export_credit_kg']:,.0f} kg")
    if result["export_curtailed_kwh"] > 1.0:
        st.info(
            "Some of your export lands in hours the grid does not need it. "
            "Annual netting counts those kilowatt-hours at full value against "
            "your evening consumption, which is where most of the flattery in "
            "an annual figure comes from."
        )

st.markdown("---")
st.markdown("### 5. By Season")
st.caption(
    "An annual figure averages the winter away. The winter is the season the "
    "household uses most electricity and the season the supply is weakest."
)

seasons = pd.DataFrame(
    [
        {
            "Season": row["label"],
            "Hourly matching": round(row["hourly_cfe_pct"], 1),
            "Annual matching": round(row["annual_match_pct"], 1),
            "Consumption (kWh)": round(row["consumption_kwh"]),
            "Unmatched (kWh)": round(row["unmatched_kwh"]),
            "Market-based (kg)": round(row["market_hourly_kg"]),
        }
        for row in result["seasons"]
    ]
)
st.dataframe(seasons, use_container_width=True, hide_index=True)

season_figure = go.Figure()
season_figure.add_trace(
    go.Bar(
        x=[row["label"] for row in result["seasons"]],
        y=[row["hourly_cfe_pct"] for row in result["seasons"]],
        name="Hourly matching",
        marker_color="#2e9e5b",
    )
)
season_figure.add_trace(
    go.Bar(
        x=[row["label"] for row in result["seasons"]],
        y=[row["annual_match_pct"] for row in result["seasons"]],
        name="Annual matching",
        marker_color="#8aa6b8",
    )
)
season_figure.update_layout(
    barmode="group",
    yaxis_title="%",
    height=340,
    legend={"orientation": "h", "y": -0.2},
)
st.plotly_chart(season_figure, use_container_width=True)

st.markdown("---")
st.markdown("### 6. The Same Household On Other Grids")
st.caption(
    "A matching score is a statement about a household *and* the system it "
    "sits in. The same array scores very differently against a solar-saturated "
    "grid than against a coal one."
)

st.dataframe(
    pd.DataFrame(
        [
            {
                "Grid": row["label"],
                "Hourly": f"{row['hourly_cfe_pct']:.0f}%",
                "Annual": f"{row['annual_match_pct']:.0f}%",
                "Market-based (kg)": round(row["market_based_hourly_kg"]),
                "Certificate gap (kg)": round(row["certificate_gap_kg"]),
                "Export displacing nothing (kWh)": round(row["export_curtailed_kwh"]),
            }
            for row in sensitivity(consumption, load_profile, supplies)
        ]
    ),
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")
st.markdown("### 7. What Would Score Better")

options = [
    {"label": "What you have now", "supplies": supplies},
    {
        "label": "Annual certificates only",
        "supplies": [{"profile": "unspecified_certificates", "annual_kwh": consumption}],
    },
    {
        "label": "Solar with a battery",
        "supplies": [{"profile": "solar_with_battery", "annual_kwh": consumption * 0.85}],
    },
    {
        "label": "A wind contract",
        "supplies": [{"profile": "contracted_wind", "annual_kwh": consumption}],
    },
]

comparison = compare_supply_options(consumption, options, load_profile, grid_profile)
st.dataframe(
    pd.DataFrame(
        [
            {
                "Arrangement": row["label"],
                "Hourly": f"{row['hourly_cfe_pct']:.0f}%",
                "Annual": f"{row['annual_match_pct']:.0f}%",
                "Gap (pts)": f"{row['matching_gap_pct']:.0f}",
                "Market-based (kg)": round(row["market_based_hourly_kg"]),
            }
            for row in comparison
        ]
    ),
    use_container_width=True,
    hide_index=True,
)

if comparison and comparison[0]["label"] != "What you have now":
    st.info(
        f"**{comparison[0]['label']}** scores highest against your load at "
        f"{comparison[0]['hourly_cfe_pct']:.0f}%. All four arrangements are "
        f"sized to roughly the same annual kilowatt-hours, so the difference "
        f"between them is entirely a matter of *when* the supply arrives."
    )

st.markdown("---")
st.markdown("### 💡 What To Take From This")
for insight in get_matching_insights(result):
    st.markdown(f"- {insight}")

st.markdown("---")
st.markdown("### 💾 Saved Analyses")

name_col, save_col = st.columns([3, 1])
with name_col:
    analysis_name = st.text_input(
        "Name",
        value=f"{get_load_profile(load_profile)['label']} on {get_grid_profile(grid_profile)['label']}",
        label_visibility="collapsed",
    )
with save_col:
    if st.button("Save", use_container_width=True):
        if save_analysis(user_id, analysis_name, result):
            st.success("Saved.")
            st.rerun()
        else:
            st.error("Could not save this analysis.")

saved = get_analyses(user_id)
if not saved:
    st.caption("Nothing saved yet.")
else:
    for entry in saved:
        with st.container(border=True):
            detail_col, delete_col = st.columns([5, 1])
            with detail_col:
                st.markdown(f"**{entry['name']}**")
                st.caption(
                    f"{entry['annual_match_pct']:.0f}% annual → "
                    f"{entry['hourly_cfe_pct']:.0f}% hourly · "
                    f"certificate gap {entry['certificate_gap_kg']:,.0f} kg · "
                    f"{entry['created_at']}"
                )
            with delete_col:
                if st.button("Delete", key=f"delete_matching_{entry['id']}"):
                    delete_analysis(entry["id"])
                    st.rerun()

    st.download_button(
        "📥 Download as JSON",
        json.dumps(saved, indent=2, default=str),
        file_name="hourly_matching_analyses.json",
        mime="application/json",
    )
