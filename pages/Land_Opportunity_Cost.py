"""Carbon opportunity cost of land.

Food footprints count the emissions released to produce the food. This page
counts the carbon the land would be holding if it were not being farmed, and
keeps the two as separate lines.
"""

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from land_opportunity_cost import (
    AMORTISATION_RANGE,
    DEFAULT_AMORTISATION_YEARS,
    DEFAULT_BIOME,
    LandCostError,
    biome_sensitivity,
    compare_foods,
    delete_analysis,
    diet_footprint,
    get_analyses,
    get_biome,
    get_food,
    get_land_insights,
    land_release_scenario,
    list_biomes,
    list_foods,
    ratio_and_gap,
    recoverable_stock,
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
    "<div class='section-header'>🌳 Carbon Opportunity Cost of Land</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "Every food footprint in this app counts the emissions released to "
    "**produce** the food. None of them count the carbon the land would be "
    "holding if it were not being farmed."
)

with st.expander("What this adds, and what it does not"):
    st.markdown(
        """
A kilogram of beef carries roughly 100 kg CO₂e of production emissions and
occupies a few hundred square metres of land for a year. Released, that land
regrows towards forest or grassland and accumulates carbon for decades.

**The correction does two opposite things at once.** Adding a term proportional
to land area *narrows* the ratio between beef and peas — the land difference
between them is large, but smaller than the emissions difference. It roughly
triples the *absolute gap* in kilograms, which is the scale the rest of the app
compares actions on. Both are shown below, because it would be easy to quote
whichever one suited the argument.

**Land is not interchangeable.** Rough upland grazing recovers about a tenth of
what tropical pasture does. The same kilogram of lamb has a completely different
opportunity cost depending on where it was reared, so the biome is a choice you
make rather than a constant hidden in the code.

**The amortisation period is the real argument.** Regrowth is not instant, and
the annual figure depends entirely on the period the recovered stock is spread
over. It is a slider, not a secret.

**Releasing land is a one-off gain that saturates.** It is not an annual saving
that continues forever, and it cannot be counted twice. The accumulation
schedule below shows the rate falling away decade by decade.
        """
    )

st.markdown("---")
st.markdown("### 1. The Two Assumptions That Decide The Answer")

years_col, biome_col = st.columns(2)
with years_col:
    years = st.slider(
        "Amortisation period (years)",
        min_value=10,
        max_value=100,
        value=DEFAULT_AMORTISATION_YEARS,
        step=5,
        help="The period the recovered carbon stock is spread over. There is "
             "no correct value; the shorter it is, the larger the annual "
             "figure.",
    )
with biome_col:
    biome = st.selectbox(
        "Default land type",
        list_biomes(),
        index=list_biomes().index(DEFAULT_BIOME),
        format_func=lambda name: get_biome(name)["label"],
        help="Individual foods keep their own typical biome unless you "
             "override it here.",
    )

st.caption(get_biome(biome)["note"])
st.caption(
    f"Cropland here recovers {recoverable_stock(biome, 'cropland'):.0f} tC/ha "
    f"and pasture {recoverable_stock(biome, 'pasture'):.0f} tC/ha if released."
)

st.markdown("---")
st.markdown("### 2. Your Weekly Basket")

if "land_basket" not in st.session_state:
    st.session_state.land_basket = [
        {"food": "beef_beef_herd", "kg": 0.5},
        {"food": "poultry", "kg": 1.0},
        {"food": "milk", "kg": 2.0},
        {"food": "peas", "kg": 0.5},
    ]

basket = st.session_state.land_basket

add_col, clear_col, _ = st.columns([1, 1, 3])
with add_col:
    if st.button("➕ Add food", use_container_width=True):
        basket.append({"food": "wheat_bread", "kg": 1.0})
with clear_col:
    if st.button("Clear basket", use_container_width=True):
        st.session_state.land_basket = []
        st.rerun()

for index, item in enumerate(list(basket)):
    row = st.columns([3, 2, 2, 1])
    with row[0]:
        item["food"] = st.selectbox(
            "Food",
            list_foods(),
            index=list_foods().index(item["food"]),
            format_func=lambda name: get_food(name)["label"],
            key=f"land_food_{index}",
        )
    with row[1]:
        item["kg"] = st.number_input(
            "kg per week",
            min_value=0.0,
            max_value=100.0,
            value=float(item["kg"]),
            step=0.1,
            key=f"land_kg_{index}",
        )
    with row[2]:
        override = st.selectbox(
            "Land",
            ["Typical"] + list_biomes(),
            index=0,
            format_func=lambda name: name if name == "Typical" else get_biome(name)["label"],
            key=f"land_biome_{index}",
        )
        item["biome"] = None if override == "Typical" else override
    with row[3]:
        st.write("")
        if st.button("Remove", key=f"land_remove_{index}", use_container_width=True):
            basket.pop(index)
            st.rerun()

try:
    weekly = diet_footprint(basket, None, years)
except LandCostError as error:
    st.error(str(error))
    st.stop()

annual_items = [dict(item, kg=item["kg"] * 52.0) for item in basket]
annual = diet_footprint(annual_items, None, years)

st.markdown("---")
st.markdown("### 3. The Two Lines")

production_col, land_col, total_col, share_col = st.columns(4)
with production_col:
    st.metric("Production (per year)", f"{annual['production_kg']:,.0f} kg")
with land_col:
    st.metric("Land opportunity cost", f"{annual['land_carbon_kg']:,.0f} kg")
with total_col:
    st.metric("Total", f"{annual['total_kg']:,.0f} kg")
with share_col:
    st.metric("From land", f"{annual['land_share'] * 100:.0f}%")

st.caption(
    "The two lines are never merged. Production emissions are measured; land "
    "opportunity cost is modelled against a counterfactual, and a single "
    "number would hide which is which."
)

if annual["items"]:
    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            y=[item["label"] for item in annual["items"]],
            x=[item["production_kg"] for item in annual["items"]],
            name="Production emissions",
            orientation="h",
            marker_color="#b6553b",
        )
    )
    figure.add_trace(
        go.Bar(
            y=[item["label"] for item in annual["items"]],
            x=[item["land_carbon_kg"] for item in annual["items"]],
            name="Land opportunity cost",
            orientation="h",
            marker_color="#2e7d4f",
        )
    )
    figure.update_layout(
        barmode="stack",
        title=f"Annual footprint by food, land amortised over {years} years",
        xaxis_title="kg CO₂e per year",
        height=420,
        legend={"orientation": "h", "y": -0.2},
    )
    st.plotly_chart(figure, use_container_width=True)

    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Food": item["label"],
                    "kg/year": round(item["kg"], 1),
                    "Production (kg)": round(item["production_kg"]),
                    "Land (kg)": round(item["land_carbon_kg"]),
                    "Total (kg)": round(item["total_kg"]),
                    "Land m²·yr": round(item["land"]["land_m2_year"]),
                    "Land": item["land"]["biome_label"],
                }
                for item in annual["items"]
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

st.markdown("---")
st.markdown("### 4. What The Correction Does To A Comparison")

comparison = ratio_and_gap("beef_beef_herd", "peas", None, years)
ratio_col, gap_col = st.columns(2)
with ratio_col:
    st.markdown("**The ratio narrows**")
    st.metric(
        f"{comparison['high_label']} ÷ {comparison['low_label']}",
        f"{comparison['total_ratio']:.0f}×",
        delta=f"was {comparison['production_ratio']:.0f}×",
        delta_color="off",
    )
    st.caption(
        "The land difference between the two is large, but smaller than the "
        "emissions difference, so a term proportional to land brings them "
        "closer together in relative terms."
    )
with gap_col:
    st.markdown("**The absolute gap widens**")
    st.metric(
        "Difference per kg",
        f"{comparison['total_gap_kg']:,.0f} kg",
        delta=f"was {comparison['production_gap_kg']:,.0f} kg",
        delta_color="off",
    )
    st.caption(
        "This is the number that matters, because the rest of the app ranks "
        "actions in kilograms. Dietary change has been competing against "
        "insulation and flights with a large part of its weight missing."
    )

st.markdown("---")
st.markdown("### 5. Foods Ranked")

basis = st.radio(
    "Compare per",
    ["mass", "protein"],
    horizontal=True,
    format_func=lambda value: "kilogram" if value == "mass" else "100 g of protein",
)
st.caption(
    "Foods that are not a meaningful protein source are dropped from the "
    "protein comparison rather than divided by something close to zero."
)

rows = compare_foods(None, basis, None, years)
st.dataframe(
    pd.DataFrame(
        [
            {
                "Food": row["label"],
                "Production": round(row["production_kg"], 2),
                "Land": round(row["land_carbon_kg"], 2),
                "Total": round(row["total_kg"], 2),
                "Land m²·yr": round(row["land_m2_year"], 1),
                "Multiplier": f"{row['uplift_ratio']:.1f}×",
            }
            for row in rows
        ]
    ),
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")
st.markdown("### 6. Where It Was Grown")

food_for_biome = st.selectbox(
    "Food",
    list_foods(),
    index=list_foods().index("lamb"),
    format_func=lambda name: get_food(name)["label"],
    key="land_biome_check",
)
st.caption(get_food(food_for_biome)["note"] or "—")

biome_rows = biome_sensitivity(food_for_biome, 1.0, years)
st.dataframe(
    pd.DataFrame(
        [
            {
                "Land": row["label"],
                "Recoverable (tC/ha)": round(row["recoverable_tc_ha"]),
                "Land cost (kg/kg)": round(row["land_carbon_kg"], 1),
                "Total (kg/kg)": round(row["total_kg"], 1),
            }
            for row in biome_rows
        ]
    ),
    use_container_width=True,
    hide_index=True,
)

if biome_rows and biome_rows[-1]["land_carbon_kg"] > 0:
    st.info(
        f"Same food, same kilogram, **{biome_rows[0]['land_carbon_kg'] / biome_rows[-1]['land_carbon_kg']:.0f}× "
        f"difference** between the most and least carbon-dense land it could "
        f"have come from. This is why there is no single global figure here."
    )

st.markdown("---")
st.markdown("### 7. The Amortisation Period")

period_rows = sensitivity("beef_beef_herd", 1.0, None, AMORTISATION_RANGE)
period_figure = go.Figure()
period_figure.add_trace(
    go.Bar(
        x=[f"{row['amortisation_years']} yr" for row in period_rows],
        y=[row["production_kg"] for row in period_rows],
        name="Production emissions",
        marker_color="#b6553b",
    )
)
period_figure.add_trace(
    go.Bar(
        x=[f"{row['amortisation_years']} yr" for row in period_rows],
        y=[row["land_carbon_kg"] for row in period_rows],
        name="Land opportunity cost",
        marker_color="#2e7d4f",
    )
)
period_figure.update_layout(
    barmode="stack",
    title="One kilogram of beef, at four amortisation periods",
    yaxis_title="kg CO₂e",
    height=340,
    legend={"orientation": "h", "y": -0.2},
)
st.plotly_chart(period_figure, use_container_width=True)
st.caption(
    "Production emissions do not move. Everything that changes across these "
    "four bars is a methodological choice, which is the argument for showing "
    "it rather than picking one."
)

st.markdown("---")
st.markdown("### 8. If You Changed Something")

before_col, after_col = st.columns(2)
with before_col:
    swap_from = st.selectbox(
        "Replace",
        list_foods(),
        index=list_foods().index("beef_beef_herd"),
        format_func=lambda name: get_food(name)["label"],
        key="land_swap_from",
    )
with after_col:
    swap_to = st.selectbox(
        "With",
        list_foods(),
        index=list_foods().index("peas"),
        format_func=lambda name: get_food(name)["label"],
        key="land_swap_to",
    )

swap_kg = st.number_input(
    "Kilograms per year", min_value=0.0, max_value=500.0, value=26.0, step=1.0
)

scenario = land_release_scenario(
    [{"food": swap_from, "kg": swap_kg}],
    [{"food": swap_to, "kg": swap_kg}],
    biome,
    years,
)

saving_col, area_col, stock_col = st.columns(3)
with saving_col:
    st.metric("Annual saving", f"{scenario['annual_saving_kg']:,.0f} kg")
with area_col:
    st.metric("Land freed", f"{scenario['area_freed_m2']:,.0f} m²")
with stock_col:
    st.metric("Eventual stock recovered", f"{scenario['eventual_stock_kg']:,.0f} kg")

st.warning(scenario["caveat"])

schedule = pd.DataFrame(scenario["schedule"])
schedule_figure = go.Figure()
schedule_figure.add_trace(
    go.Scatter(
        x=schedule["year"],
        y=schedule["stock_kg"],
        mode="lines+markers",
        name="Carbon accumulated",
        line={"width": 3},
    )
)
schedule_figure.update_layout(
    title="Accumulation on the freed land, and where it flattens",
    xaxis_title="Years after release",
    yaxis_title="kg CO₂e held",
    height=340,
)
st.plotly_chart(schedule_figure, use_container_width=True)

st.markdown("---")
st.markdown("### 💡 What To Take From This")
for insight in get_land_insights(annual):
    st.markdown(f"- {insight}")

st.markdown("---")
st.markdown("### 💾 Saved Analyses")

name_col, save_col = st.columns([3, 1])
with name_col:
    analysis_name = st.text_input(
        "Name",
        value=f"Diet, land over {years} years",
        label_visibility="collapsed",
    )
with save_col:
    if st.button("Save", use_container_width=True):
        if save_analysis(user_id, analysis_name, annual):
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
                    f"{entry['production_kg']:,.0f} kg production + "
                    f"{entry['land_carbon_kg']:,.0f} kg land = "
                    f"{entry['total_kg']:,.0f} kg · "
                    f"{entry['land_m2_year']:,.0f} m²·yr · "
                    f"amortised over {entry['amortisation_years']:.0f} years · "
                    f"{entry['created_at']}"
                )
            with delete_col:
                if st.button("Delete", key=f"delete_land_{entry['id']}"):
                    delete_analysis(entry["id"])
                    st.rerun()

    st.download_button(
        "📥 Download as JSON",
        json.dumps(saved, indent=2, default=str),
        file_name="land_opportunity_analyses.json",
        mime="application/json",
    )
