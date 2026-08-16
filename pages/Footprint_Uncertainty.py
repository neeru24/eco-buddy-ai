import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from footprint_uncertainty import (
    ACTIVITY_QUALITY,
    DEFAULT_ITERATIONS,
    DEFAULT_SEED,
    FACTOR_TIER,
    UncertaintyError,
    analytical_interval,
    build_component,
    compare_footprints,
    delete_profile,
    detectable_change,
    format_interval,
    get_profiles,
    get_uncertainty_notes,
    improvement_plan,
    list_activity_qualities,
    list_factor_tiers,
    point_estimate,
    propagate,
    save_profile,
    sensitivity_ranking,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()

apply_theme()

st.markdown(
    "<div class='section-header'>📊 Footprint Uncertainty & Confidence</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "Every other page in this app gives you a single number. None of them are "
    "that precise. This page puts an honest error bar around your footprint, "
    "tells you **which input to go and measure**, and answers the question "
    "that actually matters: is this year really lower than last year, or is "
    "it noise?"
)

# Default rows: a recognisable household footprint people can edit down to
# their own numbers rather than starting from an empty table.
DEFAULT_ROWS = [
    {
        "Source": "Car",
        "Amount": 12000.0,
        "Unit": "km",
        "Factor (kgCO2e/unit)": 0.170,
        "How you got the amount": "estimated",
        "Emission factor quality": "published",
    },
    {
        "Source": "Home heating",
        "Amount": 14000.0,
        "Unit": "kWh",
        "Factor (kgCO2e/unit)": 0.180,
        "How you got the amount": "recalled",
        "Emission factor quality": "published",
    },
    {
        "Source": "Electricity",
        "Amount": 3200.0,
        "Unit": "kWh",
        "Factor (kgCO2e/unit)": 0.210,
        "How you got the amount": "metered",
        "Emission factor quality": "verified",
    },
    {
        "Source": "Flights",
        "Amount": 2.0,
        "Unit": "return trips",
        "Factor (kgCO2e/unit)": 420.0,
        "How you got the amount": "logged",
        "Emission factor quality": "published",
    },
]

ACTIVITY_KEYS = [entry["key"] for entry in list_activity_qualities()]
FACTOR_KEYS = [entry["key"] for entry in list_factor_tiers()]


def rows_to_components(frame):
    """Turn the edited table into components, skipping unusable rows."""
    components = []
    problems = []
    for _, row in frame.iterrows():
        name = str(row.get("Source", "")).strip()
        if not name:
            continue
        try:
            components.append(
                build_component(
                    name,
                    row.get("Amount", 0.0),
                    row.get("Factor (kgCO2e/unit)", 0.0),
                    str(row.get("How you got the amount", "estimated")),
                    str(row.get("Emission factor quality", "published")),
                    unit=str(row.get("Unit", "")),
                )
            )
        except UncertaintyError as error:
            problems.append(str(error))
    return components, problems


st.markdown("---")
st.markdown("### 🧾 Your Footprint, Input by Input")
st.caption(
    "The two quality columns are the whole point. How you got a number "
    "determines how much it can be trusted, and a factor borrowed from a "
    "similar activity is far looser than one measured for yours."
)

with st.expander("What the quality levels mean"):
    quality_col, factor_col = st.columns(2)
    with quality_col:
        st.markdown("**How you got the amount**")
        for entry in list_activity_qualities():
            st.markdown(
                f"- `{entry['key']}` — {entry['description']} "
                f"*(±{(entry['gsd'] - 1) * 100:.0f}% ballpark)*"
            )
    with factor_col:
        st.markdown("**Emission factor quality**")
        for entry in list_factor_tiers():
            st.markdown(
                f"- `{entry['key']}` — {entry['description']} "
                f"*(±{(entry['gsd'] - 1) * 100:.0f}% ballpark)*"
            )

edited = st.data_editor(
    pd.DataFrame(DEFAULT_ROWS),
    num_rows="dynamic",
    use_container_width=True,
    key="uncertainty_rows",
    column_config={
        "Amount": st.column_config.NumberColumn(min_value=0.0, format="%.2f"),
        "Factor (kgCO2e/unit)": st.column_config.NumberColumn(
            min_value=0.0, format="%.4f"
        ),
        "How you got the amount": st.column_config.SelectboxColumn(options=ACTIVITY_KEYS),
        "Emission factor quality": st.column_config.SelectboxColumn(options=FACTOR_KEYS),
    },
)

components, problems = rows_to_components(edited)
for problem in problems:
    st.warning(problem)

if not components:
    st.info("Add at least one source above to see an interval.")
    st.stop()

settings_col, seed_col = st.columns(2)
with settings_col:
    iterations = st.select_slider(
        "Monte Carlo draws",
        options=[1000, 2500, 5000, 10000, 25000, 50000],
        value=DEFAULT_ITERATIONS,
        help="More draws means a smoother interval, not a more accurate one.",
    )
with seed_col:
    seed = st.number_input(
        "Random seed",
        min_value=0,
        max_value=10 ** 9,
        value=DEFAULT_SEED,
        help="Fixed so the same inputs always give the same interval.",
    )

with st.spinner("Running your uncertainty simulation..."):
    summary = propagate(components, iterations=iterations, seed=int(seed))
    rankings = sensitivity_ranking(components, iterations=iterations, seed=int(seed))

st.markdown("---")
st.markdown("### 📏 What Your Footprint Actually Is")

point_col, range_col, spread_col = st.columns(3)
point_col.metric("Point estimate", f"{summary['point_estimate']:,.0f} kg")
range_col.metric(
    "90% range", f"{summary['lower']:,.0f} – {summary['upper']:,.0f} kg"
)
spread_col.metric("Uncertainty", f"±{summary['relative_half_width'] * 100:.0f}%")

st.markdown(f"**Report it as:** {format_interval(summary)}")

for note in get_uncertainty_notes(summary, rankings):
    st.info(note)

# A simple horizontal range bar reads far better than a histogram here: the
# question is "how wide", not "what shape".
interval_figure = go.Figure()
interval_figure.add_trace(
    go.Bar(
        x=[summary["upper"] - summary["lower"]],
        base=[summary["lower"]],
        y=["Footprint"],
        orientation="h",
        marker_color="rgba(46, 139, 87, 0.45)",
        hovertemplate=(
            f"90% range: {summary['lower']:,.0f} – {summary['upper']:,.0f} kg"
            "<extra></extra>"
        ),
        showlegend=False,
    )
)
interval_figure.add_vline(
    x=summary["point_estimate"],
    line_dash="dash",
    line_color="#2e8b57",
    annotation_text="point estimate",
)
interval_figure.update_layout(
    height=180,
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis_title="kg CO2e per year",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(interval_figure, use_container_width=True)

with st.expander("Cross-check against the closed-form estimate"):
    quick = analytical_interval(components)
    st.markdown(
        f"Adding the component variances in quadrature gives "
        f"±{quick['relative_half_width'] * 100:.0f}%, against the sampled "
        f"±{summary['relative_half_width'] * 100:.0f}%. These use different "
        f"assumptions and will not match exactly — a large gap would mean one "
        f"input is dominating the tails."
    )

st.markdown("---")
st.markdown("### 🎯 Where the Uncertainty Comes From")
st.caption(
    "Not the same as where the emissions come from. A large, well-measured "
    "input can contribute almost nothing to the spread."
)

ranking_frame = pd.DataFrame(
    [
        {
            "Source": item["name"],
            "Emissions (kg)": round(item["emissions"], 1),
            "Share of total": f"{item['emissions_share'] * 100:.0f}%",
            "Share of uncertainty": f"{item['variance_share'] * 100:.0f}%",
            "Data": item["activity_quality"],
            "Factor": item["factor_tier"],
        }
        for item in rankings
    ]
)
st.dataframe(ranking_frame, use_container_width=True, hide_index=True)

contribution_figure = go.Figure()
contribution_figure.add_trace(
    go.Bar(
        name="Share of emissions",
        x=[item["name"] for item in rankings],
        y=[item["emissions_share"] * 100 for item in rankings],
        marker_color="rgba(46, 139, 87, 0.75)",
    )
)
contribution_figure.add_trace(
    go.Bar(
        name="Share of uncertainty",
        x=[item["name"] for item in rankings],
        y=[item["variance_share"] * 100 for item in rankings],
        marker_color="rgba(214, 137, 16, 0.75)",
    )
)
contribution_figure.update_layout(
    barmode="group",
    height=340,
    yaxis_title="%",
    margin=dict(l=10, r=10, t=30, b=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(contribution_figure, use_container_width=True)

st.markdown("---")
st.markdown("### 🔧 What To Go And Measure")

with st.spinner("Analyzing which input to measure..."):
    plan = improvement_plan(components, iterations=iterations, seed=int(seed))
best = plan["best_action"]
if best:
    st.success(
        f"**Measure your {best['name'].lower()} properly.** It would take your "
        f"uncertainty from ±{plan['baseline_relative_half_width'] * 100:.0f}% "
        f"to ±{best['improved_relative_half_width'] * 100:.0f}%, a "
        f"{best['reduction_points']:.0f} percentage point improvement. "
        f"Nothing else on your list comes close."
    )
else:
    st.success(
        "Every input is already metered. There is nothing left to measure — "
        "the remaining uncertainty is in the emission factors themselves."
    )

plan_frame = pd.DataFrame(
    [
        {
            "Source": action["name"],
            "Currently": action["current_quality"],
            "If metered": f"±{action['improved_relative_half_width'] * 100:.0f}%",
            "Improvement": (
                "already metered"
                if action["already_good"]
                else f"{action['reduction_points']:.1f} points"
            ),
        }
        for action in plan["actions"]
    ]
)
st.dataframe(plan_frame, use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("### 📉 Is Your Change Real?")
st.caption(
    "Enter last year's total the same way. The app will tell you whether the "
    "difference is bigger than the noise in both estimates."
)

with st.spinner("Estimating the smallest detectable change..."):
    threshold = detectable_change(components, iterations=iterations, seed=int(seed))
st.info(
    f"With data this good, the smallest change you could actually detect is "
    f"about **{threshold['min_detectable_percent']:.0f}%** "
    f"({threshold['min_detectable_absolute']:,.0f} kg). A target smaller than "
    f"that cannot be verified — you would be reading noise."
)

previous_scale = st.slider(
    "Last year's footprint, as a percentage of this year's",
    min_value=50,
    max_value=200,
    value=115,
    step=1,
    help="A quick way to test a change without re-entering every input.",
)

previous = []
for component in components:
    previous.append(
        build_component(
            component["name"],
            component["amount"] * previous_scale / 100.0,
            component["factor"],
            component["activity_quality"],
            component["factor_tier"],
            unit=component["unit"],
        )
    )

with st.spinner("Comparing this year against last year..."):
    verdict = compare_footprints(
        previous, components, iterations=iterations, seed=int(seed)
    )

before_col, after_col, probability_col = st.columns(3)
before_col.metric("Last year", f"{verdict['before_point']:,.0f} kg")
after_col.metric(
    "This year",
    f"{verdict['after_point']:,.0f} kg",
    delta=f"{verdict['percent_change']:.1f}%",
    delta_color="inverse",
)
probability_col.metric(
    "Confidence it fell", f"{verdict['probability_reduced'] * 100:.0f}%"
)

if verdict["verdict"] in ("reduced", "probably_reduced"):
    st.success(verdict["explanation"])
elif verdict["verdict"] == "inconclusive":
    st.warning(verdict["explanation"])
else:
    st.error(verdict["explanation"])

st.markdown("---")
st.markdown("### 💾 Saved Profiles")

name_col, save_col = st.columns([3, 1])
with name_col:
    profile_name = st.text_input("Name", value="Baseline", label_visibility="collapsed")
with save_col:
    if st.button("Save profile", use_container_width=True):
        if save_profile(user_id, profile_name, components, summary):
            st.success("Saved.")
        else:
            st.error("Could not save that profile.")

profiles = get_profiles(user_id)
if not profiles:
    st.caption("No saved profiles yet.")
else:
    for profile in profiles:
        detail_col, delete_col = st.columns([5, 1])
        with detail_col:
            st.markdown(
                f"**{profile['name']}** — {profile['median']:,.0f} kg "
                f"({profile['lower']:,.0f}–{profile['upper']:,.0f}, "
                f"±{profile['relative_half_width'] * 100:.0f}%) "
                f"· {profile['created_at']}"
            )
        with delete_col:
            if st.button("Delete", key=f"delete_profile_{profile['id']}"):
                delete_profile(user_id, profile["id"])
                st.rerun()

st.markdown("---")
st.caption(
    "Method: activity data and emission factors are modelled as lognormal "
    "distributions whose spread comes from how each was obtained, then "
    "propagated by Monte Carlo. This is the same approach used for "
    "uncertainty in national greenhouse gas inventories. The intervals "
    "describe estimation uncertainty only — they do not cover the chance that "
    "a category has been left out entirely."
)
