import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ghg_inventory import (
    CONSOLIDATION_APPROACHES,
    DEFAULT_CONSOLIDATION,
    DEFAULT_GRID_INTENSITY,
    DEFAULT_TARIFF,
    SCOPE_1,
    SCOPE_2,
    SCOPE_3,
    SCOPE_DESCRIPTIONS,
    SCOPE_LABELS,
    InventoryError,
    build_inventory,
    compare_to_base_year,
    delete_inventory,
    explain,
    export_inventory,
    get_inventories,
    get_scope_insights,
    list_activities,
    list_tariffs,
    recalculate_base_year,
    save_inventory,
    scope_2_dual,
    total_under_method,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()

apply_theme()

st.markdown(
    "<div class='section-header'>📒 GHG Protocol Inventory</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "The rest of the app adds everything into one number. That hides the "
    "distinction that matters most: **some of your emissions change when you "
    "change equipment, and some change when you change your electricity "
    "contract**. This page splits your footprint the way every published "
    "inventory does — Scope 1, 2 and 3, with Scope 2 reported both ways."
)

with st.expander("What the three scopes actually mean"):
    for scope in (SCOPE_1, SCOPE_2, SCOPE_3):
        st.markdown(f"**{SCOPE_LABELS[scope]}**")
        st.markdown(SCOPE_DESCRIPTIONS[scope])

st.markdown("---")
st.markdown("### ⚡ Your Electricity, Counted Both Ways")
st.caption(
    "This is the part a single total cannot express. Both figures below are "
    "correct and they answer different questions."
)

tariffs = list_tariffs()
tariff_names = [tariff["name"] for tariff in tariffs]

kwh_col, intensity_col, tariff_col = st.columns(3)
with kwh_col:
    kwh = st.number_input(
        "Electricity used (kWh/year)", min_value=0.0, value=3000.0, step=100.0
    )
with intensity_col:
    grid_intensity = st.number_input(
        "Grid intensity (kg CO2e/kWh)",
        min_value=0.0,
        max_value=2.0,
        value=DEFAULT_GRID_INTENSITY,
        step=0.01,
    )
with tariff_col:
    tariff = st.selectbox(
        "Your electricity contract",
        tariff_names,
        index=tariff_names.index(DEFAULT_TARIFF),
    )

st.caption(next(item["description"] for item in tariffs if item["name"] == tariff))

scope_2 = scope_2_dual(kwh, grid_intensity, tariff)

location_col, market_col, difference_col = st.columns(3)
location_col.metric("Location-based", f"{scope_2['location_based']:,.0f} kg CO2e")
market_col.metric("Market-based", f"{scope_2['market_based']:,.0f} kg CO2e")
difference_col.metric("Difference", f"{scope_2['difference']:,.0f} kg CO2e")

if scope_2["market_based"] < scope_2["location_based"]:
    st.success(scope_2["explanation"])
elif scope_2["market_based"] > scope_2["location_based"]:
    st.warning(scope_2["explanation"])
else:
    st.info(scope_2["explanation"])

st.markdown(
    "- **Location-based** is what the wires actually did while your kettle "
    "was on. It is the number for understanding physical grid impact.\n"
    "- **Market-based** is what you contracted for. It is the number that "
    "drives demand for clean generation to be built."
)

st.markdown("---")
st.markdown("### 🧾 Your Activities")
st.caption(
    "Enter what you already know from your assessment. Each line is "
    "classified into a scope automatically, with the reasoning shown."
)

activity_catalogue = list_activities()
activity_labels = {item["label"]: item["key"] for item in activity_catalogue}

DEFAULT_ROWS = [
    {"Activity": "Gas heating", "kg CO2e per year": 2400.0},
    {"Activity": "Petrol vehicle fuel", "kg CO2e per year": 1800.0},
    {"Activity": "Food and diet", "kg CO2e per year": 2200.0},
    {"Activity": "Goods and services", "kg CO2e per year": 1500.0},
    {"Activity": "Flights", "kg CO2e per year": 900.0},
    {"Activity": "Waste and recycling", "kg CO2e per year": 180.0},
    {"Activity": "Upstream fuel and grid losses", "kg CO2e per year": 750.0},
]

edited = st.data_editor(
    pd.DataFrame(DEFAULT_ROWS),
    num_rows="dynamic",
    use_container_width=True,
    key="inventory_rows",
    column_config={
        "Activity": st.column_config.SelectboxColumn(
            options=sorted(activity_labels.keys())
        ),
        "kg CO2e per year": st.column_config.NumberColumn(min_value=0.0, format="%.0f"),
    },
)

line_items = []
for _, row in edited.iterrows():
    label = str(row.get("Activity", "")).strip()
    key = activity_labels.get(label)
    if not key:
        continue
    line_items.append({"activity": key, "emissions": row.get("kg CO2e per year", 0.0)})

# Electricity is added from the dual calculation above rather than typed in,
# so the headline total genuinely follows the declared method.
line_items.append(
    {
        "activity": "electricity",
        "emissions": scope_2["location_based"],
        "location_based": scope_2["location_based"],
        "market_based": scope_2["market_based"],
    }
)

period_col, consolidation_col, method_col = st.columns(3)
with period_col:
    reporting_period = st.text_input("Reporting period", value="2026")
with consolidation_col:
    consolidation = st.selectbox(
        "Consolidation approach",
        list(CONSOLIDATION_APPROACHES.keys()),
        index=list(CONSOLIDATION_APPROACHES.keys()).index(DEFAULT_CONSOLIDATION),
        format_func=lambda key: key.replace("_", " ").title(),
    )
with method_col:
    scope_2_method = st.radio(
        "Headline total uses",
        ["location_based", "market_based"],
        format_func=lambda value: value.replace("_", "-").title(),
    )

st.caption(CONSOLIDATION_APPROACHES[consolidation])

try:
    inventory = build_inventory(
        line_items,
        reporting_period=reporting_period,
        consolidation=consolidation,
        scope_2_method=scope_2_method,
    )
except InventoryError as error:
    st.error(str(error))
    st.stop()

st.markdown("---")
st.markdown("### 📊 Your Inventory")

scope_1_col, scope_2_col, scope_3_col, total_col = st.columns(4)
scope_1_col.metric("Scope 1", f"{inventory['scope_1']:,.0f} kg")
scope_2_col.metric("Scope 2", f"{inventory['scope_2']:,.0f} kg")
scope_3_col.metric("Scope 3", f"{inventory['scope_3']:,.0f} kg")
total_col.metric("Total", f"{inventory['total']:,.0f} kg")

other_method = (
    "market_based" if scope_2_method == "location_based" else "location_based"
)
st.caption(
    f"Under the {other_method.replace('_', '-')} method your total would be "
    f"{total_under_method(inventory, other_method):,.0f} kg. Both are correct; "
    f"a total that mixed them would not be."
)

scope_figure = go.Figure()
scope_figure.add_trace(
    go.Bar(
        x=["Scope 1", "Scope 2", "Scope 3"],
        y=[inventory["scope_1"], inventory["scope_2"], inventory["scope_3"]],
        marker_color=[
            "rgba(178, 58, 48, 0.85)",
            "rgba(70, 130, 180, 0.85)",
            "rgba(46, 139, 87, 0.85)",
        ],
        text=[
            f"{inventory['shares'][scope] * 100:.0f}%"
            for scope in (SCOPE_1, SCOPE_2, SCOPE_3)
        ],
        textposition="outside",
    )
)
scope_figure.update_layout(
    height=340,
    yaxis_title="kg CO2e per year",
    showlegend=False,
    margin=dict(l=10, r=10, t=40, b=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(scope_figure, use_container_width=True)

for insight in get_scope_insights(inventory):
    st.info(insight)

st.markdown("**Line by line, with the reasoning:**")
st.dataframe(
    pd.DataFrame(
        [
            {
                "Activity": line["label"],
                "Scope": line["scope"],
                "Scope 3 category": line["category_label"],
                "kg CO2e": round(line["emissions"]),
                "Why this scope": line["rationale"],
            }
            for line in inventory["lines"]
        ]
    ),
    use_container_width=True,
    hide_index=True,
)

if inventory["scope_3_by_category"]:
    st.markdown("**Scope 3 by category:**")
    category_figure = go.Figure()
    category_figure.add_trace(
        go.Bar(
            x=[value for value in inventory["scope_3_by_category"].values()],
            y=[
                key.replace("_", " ").title()
                for key in inventory["scope_3_by_category"]
            ],
            orientation="h",
            marker_color="rgba(46, 139, 87, 0.8)",
        )
    )
    category_figure.update_layout(
        height=320,
        xaxis_title="kg CO2e per year",
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(category_figure, use_container_width=True)

st.markdown("---")
st.markdown("### ✅ Is This Inventory Complete?")

completeness = inventory["completeness"]
score_col, rating_col = st.columns(2)
score_col.metric("Completeness", f"{completeness['score'] * 100:.0f}%")
rating_col.metric("Rating", completeness["rating"].title())

if completeness["warning"]:
    st.error(completeness["warning"])
else:
    st.success(
        "All the categories a personal inventory should cover are reported, "
        "across all three scopes."
    )

if completeness["missing"]:
    st.markdown("**Not yet reported:** " + ", ".join(completeness["missing"]))

st.markdown("---")
st.markdown("### 📐 Boundary")

boundary = inventory["boundary"]
st.markdown(f"> {boundary['statement']}")
st.markdown(f"- **Approach:** {boundary['consolidation_description']}")
st.markdown(f"- **Period:** {boundary['reporting_period']}")
st.markdown(f"- **Included:** {', '.join(boundary['included'])}")
if boundary["omitted"]:
    st.markdown(f"- **Omitted:** {', '.join(boundary['omitted'])}")

st.caption(
    "An inventory without a stated boundary is not an inventory — it is a "
    "number. This is what makes the total above comparable with anyone else's."
)

st.markdown("---")
st.markdown("### 📅 Base Year")
st.caption(
    "Change your method and your total moves without your behaviour moving at "
    "all. The recalculation rules exist so those two cannot be confused."
)

base_col, adjustment_col = st.columns(2)
with base_col:
    base_year_total = st.number_input(
        "Base year total (kg CO2e)", min_value=0.0, value=12000.0, step=100.0
    )
with adjustment_col:
    adjustment = st.number_input(
        "Methodology adjustment (kg CO2e)",
        value=0.0,
        step=100.0,
        help="How much a boundary or method change moves the base year.",
    )

comparison = compare_to_base_year(inventory, base_year_total, reporting_period)
change_col, percent_col = st.columns(2)
change_col.metric(
    "Change against base year",
    f"{comparison['change']:+,.0f} kg",
    delta=f"{comparison['percent_change']:+.1f}%",
    delta_color="inverse",
)
percent_col.metric(
    "Direction", "Reduced" if comparison["reduced"] else "Increased"
)
st.caption(f"⚖️ {comparison['caveat']}")

if adjustment != 0:
    restatement = recalculate_base_year(base_year_total, adjustment)
    if restatement["is_significant"]:
        st.warning(restatement["explanation"])
    else:
        st.info(restatement["explanation"])

st.markdown("---")
st.markdown("### 📤 Export")

export = export_inventory(inventory)
with st.expander("Structured inventory (JSON)"):
    st.code(json.dumps(export, indent=2), language="json")

st.download_button(
    "Download inventory as JSON",
    data=json.dumps(export, indent=2),
    file_name=f"ghg_inventory_{reporting_period or 'draft'}.json",
    mime="application/json",
)

st.markdown("**Method notes travelling with the numbers:**")
for note in export["method_notes"]:
    st.markdown(f"- {note}")

st.markdown("---")
st.markdown("### 💾 Saved Inventories")

name_col, save_col = st.columns([3, 1])
with name_col:
    inventory_name = st.text_input(
        "Inventory name",
        value=f"{reporting_period} inventory",
        label_visibility="collapsed",
    )
with save_col:
    if st.button("Save inventory", use_container_width=True):
        if save_inventory(user_id, inventory_name, inventory):
            st.success("Saved.")
        else:
            st.error("Could not save that inventory.")

saved = get_inventories(user_id)
if not saved:
    st.caption("No saved inventories yet.")
else:
    for item in saved:
        detail_col, delete_col = st.columns([5, 1])
        with detail_col:
            st.markdown(
                f"**{item['name']}** ({item['reporting_period']}) — "
                f"S1 {item['scope_1']:,.0f} · S2 {item['scope_2_location_based']:,.0f} "
                f"(market {item['scope_2_market_based']:,.0f}) · "
                f"S3 {item['scope_3']:,.0f} · total {item['total']:,.0f} kg "
                f"· {item['created_at']}"
            )
        with delete_col:
            if st.button("Delete", key=f"delete_inventory_{item['id']}"):
                delete_inventory(user_id, item["id"])
                st.rerun()

st.markdown("---")
st.caption(
    "Method: scope definitions follow the GHG Protocol Corporate Standard and "
    "the dual Scope 2 reporting follows the Scope 2 Guidance, both adapted to "
    "a household boundary. Scope 3 uses a household-relevant subset of the "
    "fifteen corporate categories. This page classifies and reports the "
    "figures the rest of the app produces; it does not recompute them."
)
