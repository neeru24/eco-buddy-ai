"""Water scarcity footprint.

The existing water page reports litres. This one reports impact, which needs
three things the litre total does not have: a blue/green/grey split, a
location, and the distinction between water withdrawn and water consumed.
"""

import datetime
import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from styles.theme import apply_theme
from water_scarcity import (
    DEFAULT_REGION,
    MONTHS,
    WaterScarcityError,
    assess,
    delete_saved_assessment,
    diet_water,
    food_water,
    get_region,
    get_saved_assessments,
    get_water_insights,
    household_activity,
    household_profile,
    list_foods,
    list_household_activities,
    list_regions,
    rank_interventions,
    save_assessment,
    seasonal_factor,
)

DEFAULT_HOUSEHOLD = {
    "shower": 8.0,
    "laundry": 0.6,
    "dishwasher": 0.5,
    "toilet": 5.0,
    "garden": 3.0,
    "drinking_cooking": 1.0,
}

DEFAULT_DIET_KG_PER_YEAR = {
    "Beef": 20.0,
    "Rice": 40.0,
    "Vegetables": 120.0,
    "Milk": 90.0,
    "Coffee": 4.0,
}

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()

apply_theme()

st.markdown(
    "<div class='section-header'>💧 Water Scarcity Footprint</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "A litre is not a unit of impact. A litre drawn from an aquifer in a "
    "drought and a litre of rain that fell on a field are the same number and "
    "completely different things — and the app's water total adds them "
    "together."
)

with st.expander("The three separations this page makes"):
    st.markdown(
        """
**Blue water** is surface and groundwater withdrawn from a basin. This is the
water that competes with other users and with ecosystems, and it is the only
part that scarcity weighting applies to.

**Green water** is rainfall held in soil and used by plants. It does not
compete in the same way — it was going to fall on that field regardless.
Agricultural virtual water is overwhelmingly green, which is why the diet
term in a litre total is so misleading.

**Grey water** is not consumed at all. It is a *dilution volume*: the water
needed to assimilate a pollutant load. It is reported here alongside, never
inside, the consumptive total — adding it in counts water that is still in
the river.

And separately: **withdrawal is not consumption.** Most household use returns
to the basin, treated, a short time later. A shower withdraws ten litres a
minute and consumes almost none of them. Weighting withdrawal rather than
consumption is why domestic water advice is usually aimed at the wrong place.
        """
    )

st.markdown("---")
st.markdown("### 1. Where You Are")
st.caption(
    "There is deliberately no default. A scarcity footprint without a "
    "location is not a scarcity footprint, and quietly assuming the world "
    "average would flatter every stressed basin."
)

regions = list_regions()
region_col, month_col = st.columns([2, 1])
with region_col:
    region = st.selectbox(
        "Region",
        regions,
        index=regions.index(DEFAULT_REGION) if DEFAULT_REGION in regions else 0,
    )
with month_col:
    use_season = st.checkbox("Seasonal", value=False)
    month = None
    if use_season:
        month = st.selectbox(
            "Month",
            MONTHS,
            index=datetime.date.today().month - 1,
            label_visibility="collapsed",
        )

region_detail = get_region(region)
applied_factor = seasonal_factor(region, month)

factor_col, note_col = st.columns([1, 3])
with factor_col:
    st.metric(
        "Scarcity factor",
        f"{applied_factor:.1f}×",
        delta=(
            f"{applied_factor / region_detail['factor']:.2f}× seasonal"
            if month
            else None
        ),
        delta_color="off",
    )
with note_col:
    st.info(region_detail["note"])
    if month:
        st.caption(
            "Scarcity is not an annual property. Irrigation demand peaks when "
            "availability troughs, so the same litre in August and February "
            "are not the same event."
        )

st.markdown("---")
st.markdown("### 2. Household Use")

usage = {}
household_columns = st.columns(3)
for index, activity in enumerate(list_household_activities()):
    entry = household_activity(activity)
    default = DEFAULT_HOUSEHOLD.get(activity, 0.0)
    with household_columns[index % 3]:
        usage[activity] = st.number_input(
            f"{activity.replace('_', ' ').title()} ({entry['unit']}s/day)",
            min_value=0.0,
            max_value=500.0,
            value=float(default),
            step=0.5,
            help=entry["note"],
        )

household = household_profile(
    {name: value for name, value in usage.items() if value > 0}, days=365
)

withdrawal_col, consumption_col, grey_col = st.columns(3)
with withdrawal_col:
    st.metric("Withdrawn", f"{household['withdrawal_litres']:,.0f} L/year")
with consumption_col:
    st.metric(
        "Actually consumed",
        f"{household['consumption_litres']:,.0f} L/year",
        delta=(
            f"{household['consumption_litres'] / household['withdrawal_litres'] * 100:.0f}%"
            " of withdrawal"
            if household["withdrawal_litres"] > 0
            else None
        ),
        delta_color="off",
    )
with grey_col:
    st.metric(
        "Grey (dilution)",
        f"{household['grey_litres']:,.0f} L/year",
        help="Reported alongside, never inside, the consumptive total.",
    )

if household["lines"]:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Activity": line["activity"].replace("_", " ").title(),
                    "Withdrawn (L/yr)": round(line["withdrawal_litres"]),
                    "Consumed (L/yr)": round(line["consumption_litres"]),
                    "Returned (L/yr)": round(line["returned_litres"]),
                    "Grey (L/yr)": round(line["grey_litres"]),
                }
                for line in sorted(
                    household["lines"],
                    key=lambda item: item["consumption_litres"],
                    reverse=True,
                )
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

st.markdown("---")
st.markdown("### 3. Diet")
st.caption(
    "Blue is the column that matters. A food can have an enormous total and "
    "almost no effect on a stressed basin."
)

diet_input = {}
food_columns = st.columns(3)
for index, food in enumerate(list_foods()):
    default = DEFAULT_DIET_KG_PER_YEAR.get(food, 0.0)
    with food_columns[index % 3]:
        diet_input[food] = st.number_input(
            f"{food} (kg/year)",
            min_value=0.0,
            max_value=2000.0,
            value=float(default),
            step=1.0,
            help=food_water(food, 1)["note"],
        )

diet = diet_water({name: value for name, value in diet_input.items() if value > 0})

blue_col, green_col, diet_grey_col = st.columns(3)
with blue_col:
    st.metric("Blue", f"{diet['blue_litres']:,.0f} L/year")
with green_col:
    st.metric("Green", f"{diet['green_litres']:,.0f} L/year")
with diet_grey_col:
    st.metric("Grey", f"{diet['grey_litres']:,.0f} L/year")

if diet["lines"]:
    split_figure = go.Figure()
    ordered = sorted(diet["lines"], key=lambda line: line["blue_litres"], reverse=True)
    split_figure.add_trace(
        go.Bar(name="Blue", x=[line["food"] for line in ordered],
               y=[line["blue_litres"] for line in ordered])
    )
    split_figure.add_trace(
        go.Bar(name="Green", x=[line["food"] for line in ordered],
               y=[line["green_litres"] for line in ordered])
    )
    split_figure.add_trace(
        go.Bar(name="Grey", x=[line["food"] for line in ordered],
               y=[line["grey_litres"] for line in ordered])
    )
    split_figure.update_layout(
        barmode="stack",
        yaxis_title="litres/year",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=340,
    )
    st.plotly_chart(split_figure, use_container_width=True)
    st.caption(
        "Sorted by blue water. Note how different this order is from the "
        "order by total height."
    )

st.markdown("---")
st.markdown("### 4. Your Scarcity Footprint")

try:
    assessment = assess(household, diet, region, month)
except WaterScarcityError as error:
    st.error(str(error))
    st.stop()

litres_col, scarcity_col, share_col = st.columns(3)
with litres_col:
    st.metric(
        "Litre total",
        f"{assessment['total_litres']:,.0f} L/year",
        help="What the existing water page would show. Not comparable "
             "between people or places.",
    )
with scarcity_col:
    st.metric(
        "Scarcity footprint",
        f"{assessment['total_scarcity_m3']:,.1f} m³ world-eq",
        help="Blue water consumption, weighted by local scarcity. This one "
             "is comparable.",
    )
with share_col:
    st.metric("Food's share", f"{assessment['diet_share'] * 100:.0f}%")

comparison_figure = go.Figure(
    data=[
        go.Bar(
            x=["Household", "Diet"],
            y=[
                assessment["household"]["scarcity_m3"],
                assessment["diet"]["scarcity_m3"],
            ],
        )
    ]
)
comparison_figure.update_layout(
    yaxis_title="m³ world-equivalent", height=300, showlegend=False
)
st.plotly_chart(comparison_figure, use_container_width=True)

st.markdown("---")
st.markdown("### 5. What Actually Helps")
st.caption(
    "Ranked by scarcity saved rather than litres saved. For most users this "
    "inverts the usual advice."
)

interventions = []
if usage.get("shower", 0) > 0:
    entry = household_activity("shower")
    interventions.append({
        "label": "Two minutes less in the shower",
        "litres_saved": entry["withdrawal"] * 2 * 365,
        "blue_fraction": entry["consumptive_fraction"],
    })
if usage.get("garden", 0) > 0:
    entry = household_activity("garden")
    interventions.append({
        "label": "Halve the garden watering",
        "litres_saved": entry["withdrawal"] * usage["garden"] * 0.5 * 365,
        "blue_fraction": entry["consumptive_fraction"],
    })
for line in diet["lines"]:
    if line["total_litres"] <= 0:
        continue
    interventions.append({
        "label": f"Halve your {line['food'].lower()}",
        "litres_saved": line["total_litres"] * 0.5,
        "blue_fraction": line["blue_share"],
    })

if interventions:
    ranked = rank_interventions(interventions, region, month)

    litre_order, scarcity_order = st.columns(2)
    with litre_order:
        st.markdown("**Ranked by litres saved** — today's advice")
        st.dataframe(
            pd.DataFrame(
                [
                    {"Action": row["label"], "Litres": round(row["litres_saved"])}
                    for row in ranked["by_litres"][:6]
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    with scarcity_order:
        st.markdown("**Ranked by scarcity saved** — what helps the basin")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Action": row["label"],
                        "m³ world-eq": round(row["scarcity_m3_saved"], 2),
                    }
                    for row in ranked["by_scarcity"][:6]
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

    if ranked["inverted"]:
        st.warning(
            f"**The two rankings disagree at the top.** By litres you should "
            f"tackle *{ranked['by_litres'][0]['label'].lower()}*; by scarcity "
            f"it is *{ranked['by_scarcity'][0]['label'].lower()}*. The second "
            "is the one that reaches the basin."
        )
    else:
        st.success(
            "Both rankings agree on the top action here, which is not the "
            "usual case and is worth knowing."
        )

st.markdown("---")
st.markdown("### 💡 What To Take From This")
for insight in get_water_insights(assessment, diet):
    st.markdown(f"- {insight}")

st.markdown("---")
st.markdown("### 💾 Saved Assessments")

name_col, save_col = st.columns([3, 1])
with name_col:
    assessment_name = st.text_input(
        "Name", value=f"{region} assessment", label_visibility="collapsed"
    )
with save_col:
    if st.button("Save", use_container_width=True):
        if save_assessment(user_id, assessment_name, assessment):
            st.success("Saved.")
            st.rerun()
        else:
            st.error("Could not save this assessment.")

saved = get_saved_assessments(user_id)
if not saved:
    st.caption("Nothing saved yet.")
else:
    for entry in saved:
        with st.container(border=True):
            detail_col, delete_col = st.columns([5, 1])
            with detail_col:
                st.markdown(f"**{entry['name']}** — {entry['region']}")
                st.caption(
                    f"{entry['scarcity_m3']:,.1f} m³ world-eq · "
                    f"{entry['total_litres']:,.0f} L · "
                    f"food {entry['diet_share'] * 100:.0f}% · "
                    f"{entry['created_at']}"
                )
            with delete_col:
                if st.button("Delete", key=f"delete_water_{entry['id']}"):
                    delete_saved_assessment(entry["id"])
                    st.rerun()

    st.download_button(
        "📥 Download as JSON",
        json.dumps(saved, indent=2, default=str),
        file_name="water_scarcity_assessments.json",
        mime="application/json",
    )
