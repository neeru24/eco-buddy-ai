"""Permanence and ton-year accounting.

A tonne stored in a forest and a tonne never emitted are different assets. This
page prices the difference, by both accepted ton-year methods, and says what
the result is not for.
"""

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from permanence_accounting import (
    DEFAULT_EQUIVALENCE_TIME,
    DEFAULT_HORIZON_YEARS,
    HORIZON_RANGE,
    PermanenceError,
    atmospheric_fraction,
    compare_classes,
    delete_portfolio,
    get_class,
    get_permanence_insights,
    get_portfolios,
    like_for_like,
    list_classes,
    portfolio_value,
    save_portfolio,
    sensitivity,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()

apply_theme()

st.markdown(
    "<div class='section-header'>⏳ Permanence & Ton-Year Accounting</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "A tonne released from fossil fuel is a permanent addition to the active "
    "carbon cycle. A tonne stored in a young forest is stored for as long as "
    "the forest stands. This app has been treating them as the same thing."
)

with st.expander("How a temporary store is priced, and what this is not for"):
    st.markdown(
        """
**The unit is the ton-year**, not the tonne: a tonne held out of the atmosphere
for a year. A fossil tonne imposes a burden across the whole horizon; a
temporary store avoids the tail end of it. That makes the equivalence ratio
calculable instead of assumed to be one.

**Two accepted methods, and they disagree.**

- *Lashof* shifts the CO₂ decay curve forward by the storage duration and counts
  what gets pushed beyond the horizon.
- *Moura Costa* divides storage duration by an equivalence time.

For a 40-year forestry credit over a century they give roughly 33% and 83%. Both
are defensible, the gap is larger than most other uncertainties in this app, and
so both are shown. Presenting one as settled would be the real error.

**Buffers.** Registries hold a pool against reversal. Whether it is *adequate*
is an empirical question, and a buffer sized on historical rates is by
construction too small where the risk is rising.

**What this is not.** A discounted equivalence ratio can be read as a price list
for how many temporary credits substitute for a real reduction. It is not that.
It measures how much less a credit delivers — which is an argument for the
reduction, not a route to buying the difference.
        """
    )

st.markdown("---")
st.markdown("### 1. The Horizon")

horizon_col, equivalence_col = st.columns(2)
with horizon_col:
    horizon = st.select_slider(
        "Equivalence horizon (years)",
        options=list(HORIZON_RANGE),
        value=DEFAULT_HORIZON_YEARS,
        help="Over what period a store has to hold to count as permanent. "
             "There is no correct answer, which is why it is a control.",
    )
with equivalence_col:
    equivalence_time = st.slider(
        "Moura Costa equivalence time (years)",
        min_value=20.0,
        max_value=100.0,
        value=DEFAULT_EQUIVALENCE_TIME,
        step=1.0,
        help="The period over which regrowth absorbs an equivalent tonne. "
             "Scales the whole Moura Costa answer.",
    )

st.markdown("---")
st.markdown("### 2. Your Credits")

if "permanence_portfolio" not in st.session_state:
    st.session_state.permanence_portfolio = [
        {"class": "forestry_tropical", "tonnes": 5.0, "buffer_share": 0.15,
         "delivery_years": 0.0, "delivery_probability": 1.0},
        {"class": "soil_carbon", "tonnes": 3.0, "buffer_share": 0.10,
         "delivery_years": 0.0, "delivery_probability": 1.0},
        {"class": "geological_storage", "tonnes": 1.0, "buffer_share": 0.02,
         "delivery_years": 10.0, "delivery_probability": 0.8},
    ]

holdings = st.session_state.permanence_portfolio

add_col, clear_col, _ = st.columns([1, 1, 3])
with add_col:
    if st.button("➕ Add credit", use_container_width=True):
        holdings.append({
            "class": "forestry_temperate", "tonnes": 1.0, "buffer_share": 0.15,
            "delivery_years": 0.0, "delivery_probability": 1.0,
        })
with clear_col:
    if st.button("Clear all", use_container_width=True):
        st.session_state.permanence_portfolio = []
        st.rerun()

for index, holding in enumerate(list(holdings)):
    with st.container(border=True):
        row = st.columns([3, 2, 2, 1])
        with row[0]:
            holding["class"] = st.selectbox(
                "Type",
                list_classes(),
                index=list_classes().index(holding["class"]),
                format_func=lambda name: get_class(name)["label"],
                key=f"perm_class_{index}",
            )
        with row[1]:
            holding["tonnes"] = st.number_input(
                "Tonnes",
                min_value=0.0,
                max_value=100000.0,
                value=float(holding["tonnes"]),
                step=0.5,
                key=f"perm_tonnes_{index}",
            )
        with row[2]:
            holding["buffer_share"] = st.slider(
                "Buffer held",
                min_value=0.0,
                max_value=0.5,
                value=float(holding["buffer_share"]),
                step=0.01,
                key=f"perm_buffer_{index}",
            )
        with row[3]:
            st.write("")
            if st.button("Remove", key=f"perm_remove_{index}", use_container_width=True):
                holdings.pop(index)
                st.rerun()

        delivery = st.columns(2)
        with delivery[0]:
            holding["delivery_years"] = st.number_input(
                "Years until removal happens",
                min_value=0.0,
                max_value=100.0,
                value=float(holding["delivery_years"]),
                step=1.0,
                key=f"perm_delivery_{index}",
                help="Zero for carbon already removed.",
            )
        with delivery[1]:
            holding["delivery_probability"] = st.slider(
                "Chance it is delivered",
                min_value=0.0,
                max_value=1.0,
                value=float(holding["delivery_probability"]),
                step=0.05,
                key=f"perm_probability_{index}",
            )
        st.caption(get_class(holding["class"])["mechanism"])

try:
    portfolio = portfolio_value(holdings, horizon, equivalence_time)
except PermanenceError as error:
    st.error(str(error))
    st.stop()

st.markdown("---")
st.markdown("### 3. What It Delivers")

face_col, lashof_col, moura_col, discount_col = st.columns(4)
with face_col:
    st.metric("Face value", f"{portfolio['face_value_tonnes']:,.1f} t")
with lashof_col:
    st.metric(
        "Lashof",
        f"{portfolio['lashof_tonnes']:,.2f} t",
        delta=f"{portfolio['lashof_ratio'] * 100:.0f}% of face",
        delta_color="off",
    )
with moura_col:
    st.metric(
        "Moura Costa",
        f"{portfolio['moura_costa_tonnes']:,.2f} t",
        delta=f"{portfolio['moura_costa_ratio'] * 100:.0f}% of face",
        delta_color="off",
    )
with discount_col:
    st.metric(
        "Not delivered",
        f"{portfolio['discount_tonnes']:,.2f} t",
        delta=f"−{portfolio['discount_tonnes']:,.2f}",
        delta_color="inverse",
    )

st.caption(portfolio["caveat"])

if portfolio["credits"]:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Credit": credit["label"],
                    "Tonnes": round(credit["tonnes"], 2),
                    "Nominal years": round(credit["nominal_years"]),
                    "After reversal": round(credit["effective_years"]),
                    "Lashof": f"{credit['lashof_ratio'] * 100:.0f}%",
                    "Moura Costa": f"{credit['moura_costa_ratio'] * 100:.0f}%",
                    "Delivers (t)": round(credit["lashof_tonnes"], 2),
                    "Buffer": "adequate" if credit["buffer"]["adequate"] else "thin",
                }
                for credit in portfolio["credits"]
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            y=[credit["label"] for credit in portfolio["credits"]],
            x=[credit["lashof_tonnes"] for credit in portfolio["credits"]],
            name="Delivered (Lashof)",
            orientation="h",
            marker_color="#2e7d4f",
        )
    )
    figure.add_trace(
        go.Bar(
            y=[credit["label"] for credit in portfolio["credits"]],
            x=[credit["tonnes"] - credit["lashof_tonnes"] for credit in portfolio["credits"]],
            name="Not delivered over this horizon",
            orientation="h",
            marker_color="#b6553b",
        )
    )
    figure.update_layout(
        barmode="stack",
        title=f"Face value against delivery, over {horizon} years",
        xaxis_title="tonnes CO₂e",
        height=380,
        legend={"orientation": "h", "y": -0.2},
    )
    st.plotly_chart(figure, use_container_width=True)

if portfolio["inadequate_buffers"]:
    st.warning(
        "**Thin buffers:** "
        + ", ".join(get_class(name)["label"] for name in portfolio["inadequate_buffers"])
        + ". A buffer sized on historical reversal rates is by construction too "
        "small where the risk is rising with climate."
    )

st.markdown("---")
st.markdown("### 4. Against One Fossil Tonne")

class_for_check = st.selectbox(
    "If you emit one tonne and try to cover it with",
    list_classes(),
    index=list_classes().index("forestry_tropical"),
    format_func=lambda name: get_class(name)["label"],
)

check = like_for_like(1.0, class_for_check, horizon)
lashof_col, moura_col = st.columns(2)
with lashof_col:
    st.metric(
        "Credits needed (Lashof)",
        f"{check['credits_required']:.2f} t" if check["credits_required"] else "—",
    )
with moura_col:
    st.metric(
        "Credits needed (Moura Costa)",
        f"{check['credits_required_moura']:.2f} t" if check["credits_required_moura"] else "—",
    )

st.error(check["caveat"])

st.markdown("---")
st.markdown("### 5. Every Class At This Horizon")

st.dataframe(
    pd.DataFrame(
        [
            {
                "Class": row["label"],
                "Family": row["family"],
                "Nominal years": round(row["nominal_years"]),
                "After reversal": round(row["effective_years"]),
                "Lashof": f"{row['lashof_ratio'] * 100:.0f}%",
                "Moura Costa": f"{row['moura_costa_ratio'] * 100:.0f}%",
                "Buffer": "adequate" if row["buffer_adequate"] else "thin",
            }
            for row in compare_classes(horizon, equivalence_time)
        ]
    ),
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")
st.markdown("### 6. The Horizon Is Doing The Work")

rows = sensitivity(class_for_check)
horizon_figure = go.Figure()
horizon_figure.add_trace(
    go.Bar(
        x=[f"{row['horizon_years']} yr" for row in rows],
        y=[row["lashof_ratio"] * 100 for row in rows],
        name="Lashof",
        marker_color="#2e7d4f",
    )
)
horizon_figure.add_trace(
    go.Bar(
        x=[f"{row['horizon_years']} yr" for row in rows],
        y=[row["moura_costa_ratio"] * 100 for row in rows],
        name="Moura Costa",
        marker_color="#8aa6b8",
    )
)
horizon_figure.update_layout(
    barmode="group",
    title=f"{get_class(class_for_check)['label']}: share of a fossil tonne, by horizon",
    yaxis_title="% of a fossil tonne",
    height=340,
    legend={"orientation": "h", "y": -0.2},
)
st.plotly_chart(horizon_figure, use_container_width=True)

st.caption(
    "A short horizon makes temporary storage look permanent. That is an "
    "argument for stating the horizon, not for choosing twenty years."
)

decay = pd.DataFrame(
    {
        "year": list(range(0, 501, 10)),
        "airborne": [atmospheric_fraction(year) * 100 for year in range(0, 501, 10)],
    }
)
decay_figure = go.Figure()
decay_figure.add_trace(
    go.Scatter(x=decay["year"], y=decay["airborne"], mode="lines", name="Still airborne",
               line={"width": 3})
)
decay_figure.update_layout(
    title="One tonne of fossil CO₂, and the fifth of it that never leaves",
    xaxis_title="Years after emission",
    yaxis_title="% still airborne",
    height=320,
)
st.plotly_chart(decay_figure, use_container_width=True)

st.markdown("---")
st.markdown("### 💡 What To Take From This")
for insight in get_permanence_insights(portfolio):
    st.markdown(f"- {insight}")

st.markdown("---")
st.markdown("### 💾 Saved Portfolios")

name_col, save_col = st.columns([3, 1])
with name_col:
    portfolio_name = st.text_input(
        "Name", value=f"Portfolio over {horizon} years", label_visibility="collapsed"
    )
with save_col:
    if st.button("Save", use_container_width=True):
        if save_portfolio(user_id, portfolio_name, portfolio):
            st.success("Saved.")
            st.rerun()
        else:
            st.error("Could not save this portfolio.")

saved = get_portfolios(user_id)
if not saved:
    st.caption("Nothing saved yet.")
else:
    for entry in saved:
        with st.container(border=True):
            detail_col, delete_col = st.columns([5, 1])
            with detail_col:
                st.markdown(f"**{entry['name']}**")
                st.caption(
                    f"{entry['face_value_tonnes']:,.1f} t bought → "
                    f"{entry['lashof_tonnes']:,.2f} t (Lashof) / "
                    f"{entry['moura_costa_tonnes']:,.2f} t (Moura Costa) over "
                    f"{entry['horizon_years']:.0f} years · {entry['created_at']}"
                )
            with delete_col:
                if st.button("Delete", key=f"delete_permanence_{entry['id']}"):
                    delete_portfolio(entry["id"])
                    st.rerun()

    st.download_button(
        "📥 Download as JSON",
        json.dumps(saved, indent=2, default=str),
        file_name="permanence_portfolios.json",
        mime="application/json",
    )
