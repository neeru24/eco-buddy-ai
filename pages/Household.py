import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from database import (
    delete_household,
    get_assessments,
    get_household,
    save_household,
)
from household import (
    ALLOCATION_METHODS,
    DEFAULT_BENCHMARK_REGION,
    HOME_TYPES,
    METHOD_ADULT_EQUIVALENT,
    METHOD_LABELS,
    PER_CAPITA_BENCHMARKS,
    HouseholdError,
    adult_equivalent,
    allocate_footprint,
    compare_to_benchmark,
    describe_allocation,
    household_adult_equivalents,
    household_from_dict,
    household_size,
    make_household,
    make_member,
    member_shares,
    per_capita_footprint,
    shared_fraction,
    sharing_efficiency,
    solo_household,
)
from styles.theme import apply_theme

user_id = st.session_state.get('user_id')
if not user_id:
    st.warning('Please log in from the main application page.')
    st.stop()
apply_theme()

st.markdown("<div class='section-header'>🏠 Household</div>", unsafe_allow_html=True)
st.markdown(
    "Electricity, water and appliances are shared by everyone in a home, but EcoBuddy "
    "currently charges all of them to you alone. Tell it who you live with and it will "
    "work out your genuine personal share."
)
st.markdown("---")

stored = get_household(user_id)

if stored:
    try:
        household = household_from_dict(stored)
    except HouseholdError as exc:
        st.error(f"Your saved household could not be read: {exc}")
        household = solo_household(user_id)
else:
    household = solo_household(user_id)
    st.info(
        "No household saved yet — you are currently treated as living alone, which "
        "is exactly how the app behaves today."
    )


def _contributors_from_session():
    analysis = st.session_state.get("analysis") or {}
    contributors = analysis.get("contributors")
    if isinstance(contributors, dict) and contributors:
        return contributors
    return None


# --- Composition editor -----------------------------------------------------

st.markdown("### 👨‍👩‍👧 Who lives here?")
st.caption(
    "The first person listed is you. Ages matter: a toddler does not consume like "
    "an adult, so an equal per-head split would overstate their share and understate yours."
)

if "household_draft" not in st.session_state:
    st.session_state.household_draft = [
        {"name": member["name"], "age": member["age"],
         "is_dependent": member["is_dependent"]}
        for member in household["members"]
    ]

draft = st.session_state.household_draft

edited = st.data_editor(
    pd.DataFrame(draft),
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "name": st.column_config.TextColumn("Name", required=True),
        "age": st.column_config.NumberColumn("Age", min_value=0, max_value=120, step=1),
        "is_dependent": st.column_config.CheckboxColumn("Dependent"),
    },
    key="household_editor",
)

col_left, col_right = st.columns(2)
with col_left:
    home_type = st.selectbox(
        "Home type",
        HOME_TYPES,
        index=HOME_TYPES.index(household["home_type"])
        if household["home_type"] in HOME_TYPES else 0,
    )
with col_right:
    home_size = st.number_input(
        "Home size (m², optional)",
        min_value=0.0, max_value=2000.0,
        value=float(household["home_size_sqm"] or 0.0),
        step=5.0,
    )

if st.button("💾 Save household", use_container_width=True):
    rows = edited.to_dict("records")
    try:
        members = [
            make_member(row.get("name"), row.get("age"),
                        is_dependent=bool(row.get("is_dependent")))
            for row in rows
            if row.get("name") and row.get("age") is not None
        ]
        candidate = make_household(
            members, home_type=home_type,
            home_size_sqm=home_size or None, user_id=user_id,
        )
    except HouseholdError as exc:
        st.error(str(exc))
    else:
        if save_household(user_id, candidate["members"], home_type, home_size or None):
            st.session_state.household_draft = [
                {"name": m["name"], "age": m["age"], "is_dependent": m["is_dependent"]}
                for m in candidate["members"]
            ]
            st.success(f"Household saved — {household_size(candidate)} member(s).")
            st.rerun()
        else:
            st.error("Could not save your household. Please try again.")

# --- Allocation -------------------------------------------------------------

st.markdown("---")
st.markdown("### ⚖️ Your share")

method = st.radio(
    "Allocation method",
    ALLOCATION_METHODS[:2],
    format_func=lambda key: METHOD_LABELS[key],
    index=ALLOCATION_METHODS.index(METHOD_ADULT_EQUIVALENT),
    horizontal=True,
)

col1, col2, col3 = st.columns(3)
col1.metric("People", household_size(household))
col2.metric("Adult-equivalents", f"{household_adult_equivalents(household):.2f}")
col3.metric(
    "Your share of shared costs",
    f"{list(member_shares(household, method).values())[0] * 100:.0f}%",
)

st.dataframe(
    pd.DataFrame([
        {
            "Member": member["name"],
            "Age": member["age"],
            "Consumption weight": adult_equivalent(member),
            "Share of shared": f"{share * 100:.0f}%",
        }
        for member, share in zip(
            household["members"], member_shares(household, method).values()
        )
    ]),
    use_container_width=True,
    hide_index=True,
)

# --- Category classification ------------------------------------------------

with st.expander("📋 Which categories are shared?"):
    st.dataframe(
        pd.DataFrame([
            {
                "Category": category,
                "Shared": f"{shared_fraction(category) * 100:.0f}%",
                "Treated as": (
                    "Shared across the household"
                    if shared_fraction(category) >= 0.5 else "Personal to you"
                ),
            }
            for category in ["Electricity", "Water", "Heating", "Appliances",
                             "Waste", "Transport", "Diet", "Flights"]
        ]),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "Diet and flights are never divided — your own meals and your own flights "
        "are yours regardless of how many people you live with. Dividing them would "
        "understate your footprint just as badly as not dividing electricity "
        "overstates it."
    )

# --- Applied to your footprint ----------------------------------------------

contributors = _contributors_from_session()

if not contributors:
    st.markdown("---")
    st.info(
        "Run an assessment on the Carbon Footprint page to see your household "
        "allocation applied to your real numbers."
    )
else:
    st.markdown("---")
    st.markdown("### 🌍 Applied to your footprint")

    allocation = allocate_footprint(contributors, household, method)

    metric_left, metric_right = st.columns(2)
    metric_left.metric(
        "Household total", f"{allocation['household_total_kg']:,.0f} kg CO₂"
    )
    metric_right.metric(
        "Your footprint",
        f"{allocation['allocated_total_kg']:,.0f} kg CO₂",
        delta=f"-{allocation['reduction_kg']:,.0f} kg"
        if allocation["reduction_kg"] > 0 else None,
    )

    figure = go.Figure()
    categories = list(allocation["allocations"])
    figure.add_trace(go.Bar(
        name="Household total",
        x=categories,
        y=[allocation["allocations"][c]["household_total_kg"] for c in categories],
        marker_color="#9aa0a6",
    ))
    figure.add_trace(go.Bar(
        name="Your share",
        x=categories,
        y=[allocation["allocations"][c]["allocated_kg"] for c in categories],
        marker_color="#4caf50",
    ))
    figure.update_layout(
        barmode="group",
        height=380,
        margin=dict(l=10, r=10, t=30, b=10),
        yaxis_title="kg CO₂ / year",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    st.plotly_chart(figure, use_container_width=True)

    with st.expander("🧾 How this was worked out"):
        st.text(describe_allocation(allocation))

    # --- Benchmark ----------------------------------------------------------
    st.markdown("### 📊 Against the per-capita average")
    st.caption(
        "Published national averages are per person. Comparing an undivided "
        "household total against them is not a like-for-like comparison."
    )

    region = st.selectbox(
        "Benchmark region",
        list(PER_CAPITA_BENCHMARKS),
        index=list(PER_CAPITA_BENCHMARKS).index(DEFAULT_BENCHMARK_REGION),
    )

    raw_comparison = compare_to_benchmark(allocation["household_total_kg"], region)
    fair_comparison = compare_to_benchmark(allocation["allocated_total_kg"], region)

    st.dataframe(
        pd.DataFrame([
            {
                "Compared value": "Undivided household total (what the app shows today)",
                "kg CO₂": raw_comparison["per_capita_kg"],
                "vs benchmark": f"{raw_comparison['percent_of_benchmark']:.0f}%",
                "Verdict": raw_comparison["verdict"],
            },
            {
                "Compared value": "Your allocated share (like-for-like)",
                "kg CO₂": fair_comparison["per_capita_kg"],
                "vs benchmark": f"{fair_comparison['percent_of_benchmark']:.0f}%",
                "Verdict": fair_comparison["verdict"],
            },
        ]),
        use_container_width=True,
        hide_index=True,
    )

    if household_size(household) > 1:
        st.caption(
            f"Household average per person: "
            f"{per_capita_footprint(contributors, household):,.0f} kg CO₂."
        )

    # --- Sharing benefit ----------------------------------------------------
    efficiency = sharing_efficiency(household, contributors, method)
    if efficiency["is_shared"] and efficiency["avoided_kg"] > 0:
        st.success(
            f"🌱 Sharing a home avoids **{efficiency['avoided_kg']:,.0f} kg CO₂** "
            f"({efficiency['avoided_percent']:.0f}%) compared with everyone in your "
            "household living alone. Shared living is more efficient per person, "
            "not less."
        )

# --- Reset ------------------------------------------------------------------

if stored:
    st.markdown("---")
    if st.button("🗑️ Delete household (go back to solo)", use_container_width=True):
        delete_household(user_id)
        st.session_state.pop("household_draft", None)
        st.info("Household removed — you are treated as living alone again.")
        st.rerun()
