"""Rebound effect.

Every saving the app projects is a gross saving. This page reports what is
left after take-back, and — more usefully — which recommendations change
order once it is counted.
"""

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from rebound_effect import (
    DEFAULT_RESPENDING,
    DEFAULT_SATIATION,
    ReboundError,
    corrected_payback_years,
    delete_scenario,
    get_action_type,
    get_rebound_insights,
    get_respending,
    get_satiation,
    get_scenarios,
    list_action_types,
    list_respending_profiles,
    list_satiation_levels,
    net_saving,
    rank_actions,
    save_scenario,
    sensitivity,
)
from styles.theme import apply_theme

DEFAULT_ACTIONS = [
    {
        "label": "Insulate the loft",
        "action_type": "insulation",
        "gross_saving_kg": 800.0,
        "money_saved": 400.0,
    },
    {
        "label": "Switch to an EV",
        "action_type": "ev_switch",
        "gross_saving_kg": 900.0,
        "money_saved": 600.0,
    },
    {
        "label": "Skip one flight",
        "action_type": "avoided_flight",
        "gross_saving_kg": 750.0,
        "money_saved": 250.0,
    },
]

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()

apply_theme()

st.markdown(
    "<div class='section-header'>↩️ Rebound Effect</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "Every saving this app projects is a **gross** saving. It assumes you do "
    "exactly as much of the activity afterwards as before, and that the money "
    "you save evaporates. Neither is true."
)

with st.expander("The two ways a saving leaks"):
    st.markdown(
        """
**Direct rebound.** When an energy service gets cheaper to deliver, people
consume more of it. Insulate a cold house and the occupants do not bank the
whole saving — a good part goes into a warmer house. It is largest exactly
where this app's advice is strongest, and it is *not* a flat percentage: how
much you take back depends on how far you were from comfortable to begin with.

**Indirect rebound.** Money not spent on gas does not disappear. It gets spent
on something else, and that something else has a carbon intensity. Save £400
on heating and spend it on a flight and the net effect can be **negative** —
the efficiency measure increased your footprint. That is backfire, it is rare,
and a tool that cannot detect it is not a reduction tool.

**And one thing that is not a loss.** If you were under-heating your home on
cost grounds, the warmth you take back is the improvement the measure was
supposed to deliver. It is a real benefit. It is just not a carbon benefit,
and this page labels it as such rather than reporting it as a shortfall.
        """
    )

st.markdown("---")
st.markdown("### 1. Your Situation")

satiation_col, respending_col, fraction_col = st.columns(3)
with satiation_col:
    satiation = st.selectbox(
        "Starting comfort level",
        list_satiation_levels(),
        index=list_satiation_levels().index(DEFAULT_SATIATION),
        format_func=lambda level: get_satiation(level)["label"],
    )
with respending_col:
    respending = st.selectbox(
        "Where the money goes",
        list_respending_profiles(),
        index=list_respending_profiles().index(DEFAULT_RESPENDING),
        format_func=lambda profile: get_respending(profile)["label"],
    )
with fraction_col:
    respent_fraction = st.slider(
        "Share of the money re-spent", min_value=0.0, max_value=1.0, value=1.0,
        step=0.05,
    )

st.caption(get_satiation(satiation)["note"])
st.caption(get_respending(respending)["note"])

st.markdown("---")
st.markdown("### 2. A Single Measure")

action_col, gross_col, money_col = st.columns(3)
with action_col:
    action_type = st.selectbox(
        "Action",
        list_action_types(),
        index=list_action_types().index("insulation"),
        format_func=lambda name: get_action_type(name)["label"],
    )
with gross_col:
    gross_saving = st.number_input(
        "Projected saving (kg CO₂e/year)",
        min_value=0.0,
        max_value=50000.0,
        value=800.0,
        step=50.0,
        help="The gross figure — what the rest of the app would show.",
    )
with money_col:
    money_saved = st.number_input(
        "Money saved per year",
        min_value=0.0,
        max_value=50000.0,
        value=400.0,
        step=50.0,
    )

try:
    result = net_saving(
        gross_saving,
        action_type,
        money_saved=money_saved,
        satiation=satiation,
        respending=respending,
        respent_fraction=respent_fraction,
    )
except ReboundError as error:
    st.error(str(error))
    st.stop()

st.caption(get_action_type(action_type)["note"])

gross_col, direct_col, indirect_col, net_col = st.columns(4)
with gross_col:
    st.metric("Projected", f"{result['gross_saving_kg']:,.0f} kg")
with direct_col:
    st.metric(
        "Direct take-back",
        f"−{result['direct_rebound_kg']:,.0f} kg",
        help="More of the service that just got cheaper.",
    )
with indirect_col:
    st.metric(
        "Re-spending",
        f"−{result['indirect_rebound_kg']:,.0f} kg",
        help="The carbon in whatever the money buys instead.",
    )
with net_col:
    st.metric(
        "Actually saved",
        f"{result['net_saving_kg']:,.0f} kg",
        delta=f"−{result['rebound_share'] * 100:.0f}%",
        delta_color="inverse",
    )

waterfall = go.Figure(
    go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "total"],
        x=["Projected", "Direct take-back", "Re-spending", "Net saving"],
        y=[
            result["gross_saving_kg"],
            -result["direct_rebound_kg"],
            -result["indirect_rebound_kg"],
            0,
        ],
        connector={"line": {"width": 1}},
    )
)
waterfall.update_layout(yaxis_title="kg CO₂e/year", height=340, showlegend=False)
st.plotly_chart(waterfall, use_container_width=True)

if result["backfire"]:
    st.error(f"⚠️ **Backfire.** {result['reading']}")
elif result["is_welfare_gain"]:
    st.info(f"🏠 {result['reading']}")
elif result["rebound_share"] >= 0.4:
    st.warning(result["reading"])
else:
    st.success(result["reading"])

st.markdown("#### How confident is that?")
spread = sensitivity(
    gross_saving,
    action_type,
    money_saved=money_saved,
    satiation=satiation,
    respending=respending,
    respent_fraction=respent_fraction,
)

low_col, central_col, high_col = st.columns(3)
with low_col:
    st.metric("Pessimistic", f"{spread['low_kg']:,.0f} kg")
with central_col:
    st.metric("Central", f"{spread['central_kg']:,.0f} kg")
with high_col:
    st.metric("Optimistic", f"{spread['high_kg']:,.0f} kg")

st.caption(
    f"Elasticity range {spread['elasticity_range'][0]:.2f}–"
    f"{spread['elasticity_range'][1]:.2f} from the published literature. "
    "A range with a stated basis is more honest than a point estimate — this "
    "page should not reproduce the false precision it exists to correct."
)

if spread["could_backfire"] and not result["backfire"]:
    st.warning(
        "At the pessimistic end of the elasticity range this measure "
        "**backfires**, even though the central estimate is a saving. Worth "
        "knowing before it becomes a target."
    )

st.markdown("---")
st.markdown("### 3. Payback, Corrected")
st.caption(
    "Payback periods decide whether a purchase happens. Overstate the annual "
    "saving by a fifth and the payback period is understated by the same "
    "proportion."
)

embodied_kg = st.number_input(
    "Embodied carbon of the measure (kg CO₂e)",
    min_value=0.0,
    max_value=50000.0,
    value=2400.0,
    step=100.0,
)

payback = corrected_payback_years(
    embodied_kg,
    gross_saving,
    action_type,
    money_saved_per_year=money_saved,
    satiation=satiation,
    respending=respending,
)

if payback["never_pays_back"]:
    st.error(
        "**This never pays back.** The net annual saving is zero or negative, "
        "so there is no payback period to report — which is a more useful "
        "answer than a very large number."
    )
else:
    gross_years_col, net_years_col, difference_col = st.columns(3)
    with gross_years_col:
        st.metric(
            "Payback on gross saving",
            f"{payback['gross_payback_years']:.1f} years",
        )
    with net_years_col:
        st.metric(
            "Payback on net saving",
            f"{payback['net_payback_years']:.1f} years",
        )
    with difference_col:
        st.metric(
            "Understated by",
            f"{payback['understated_by_years']:.1f} years",
            delta_color="off",
        )

st.markdown("---")
st.markdown("### 4. Comparing Options")
st.caption(
    "Rebound differs by a factor of ten between action types, so correcting "
    "for it changes the **order** of the recommendations, not just their size."
)

if "rebound_actions" not in st.session_state:
    st.session_state.rebound_actions = list(DEFAULT_ACTIONS)

actions = st.session_state.rebound_actions

with st.expander("Edit the options"):
    for index, action in enumerate(actions):
        row = st.columns([3, 2, 2, 2])
        with row[0]:
            action["label"] = st.text_input(
                "Label", value=action["label"], key=f"rebound_label_{index}"
            )
        with row[1]:
            action["action_type"] = st.selectbox(
                "Type",
                list_action_types(),
                index=list_action_types().index(action["action_type"]),
                format_func=lambda name: get_action_type(name)["label"],
                key=f"rebound_type_{index}",
            )
        with row[2]:
            action["gross_saving_kg"] = st.number_input(
                "kg CO₂e/yr",
                min_value=0.0,
                max_value=50000.0,
                value=float(action["gross_saving_kg"]),
                step=50.0,
                key=f"rebound_gross_{index}",
            )
        with row[3]:
            action["money_saved"] = st.number_input(
                "Money/yr",
                min_value=0.0,
                max_value=50000.0,
                value=float(action["money_saved"]),
                step=50.0,
                key=f"rebound_money_{index}",
            )

ranked = rank_actions(actions, satiation=satiation, respending=respending)

gross_order_col, net_order_col = st.columns(2)
with gross_order_col:
    st.markdown("**Ranked by projected saving** — today's advice")
    st.dataframe(
        pd.DataFrame(
            [
                {"Action": row["label"], "kg CO₂e": round(row["gross_saving_kg"])}
                for row in ranked["by_gross"]
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
with net_order_col:
    st.markdown("**Ranked by what survives** — after take-back")
    st.dataframe(
        pd.DataFrame(
            [
                {"Action": row["label"], "kg CO₂e": round(row["net_saving_kg"])}
                for row in ranked["by_net"]
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

if ranked["top_changed"]:
    st.warning(
        f"**The top recommendation changes.** By projected saving you should "
        f"do *{ranked['by_gross'][0]['label'].lower()}*; by what actually "
        f"survives it is *{ranked['by_net'][0]['label'].lower()}*. Correcting "
        "for rebound systematically promotes avoided consumption over "
        "efficiency measures, because efficiency measures give part of the "
        "saving back and not consuming something gives back almost none."
    )
elif ranked["ranking_changes"]:
    st.info(
        "The order changes below the top, though the first recommendation "
        "holds."
    )
else:
    st.success("The two rankings agree, which is not the usual case.")

if ranked["backfiring"]:
    st.error(
        "**These options increase your footprint:** "
        + ", ".join(ranked["backfiring"])
    )

st.markdown("---")
st.markdown("### 💡 What To Take From This")
for insight in get_rebound_insights(ranked["by_net"] + [result]):
    st.markdown(f"- {insight}")

st.markdown("---")
st.markdown("### 💾 Saved Scenarios")

name_col, save_col = st.columns([3, 1])
with name_col:
    scenario_name = st.text_input(
        "Name",
        value=f"{get_action_type(action_type)['label']} scenario",
        label_visibility="collapsed",
    )
with save_col:
    if st.button("Save", use_container_width=True):
        if save_scenario(user_id, scenario_name, result):
            st.success("Saved.")
            st.rerun()
        else:
            st.error("Could not save this scenario.")

saved = get_scenarios(user_id)
if not saved:
    st.caption("Nothing saved yet.")
else:
    for entry in saved:
        with st.container(border=True):
            detail_col, delete_col = st.columns([5, 1])
            with detail_col:
                flag = " ⚠️ backfires" if entry["backfire"] else ""
                st.markdown(f"**{entry['name']}**{flag}")
                st.caption(
                    f"{entry['gross_saving_kg']:,.0f} kg projected → "
                    f"{entry['net_saving_kg']:,.0f} kg net "
                    f"({entry['rebound_share'] * 100:.0f}% taken back) · "
                    f"{entry['created_at']}"
                )
            with delete_col:
                if st.button("Delete", key=f"delete_rebound_{entry['id']}"):
                    delete_scenario(entry["id"])
                    st.rerun()

    st.download_button(
        "📥 Download as JSON",
        json.dumps(saved, indent=2, default=str),
        file_name="rebound_scenarios.json",
        mime="application/json",
    )
