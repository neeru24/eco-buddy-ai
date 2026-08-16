import pandas as pd
import streamlit as st

from database import get_assessments_with_factors
from emission_factors import (
    KIND_STATIC,
    compare_assessment_across_versions,
    describe_provenance,
    diff_factor_sets,
    explain_footprint_change,
    get_factor_set,
    group_assessments_by_version,
    is_history_comparable,
    list_factor_versions,
    normalize_version,
)
from styles.theme import apply_theme

user_id = st.session_state.get('user_id')
if not user_id:
    st.warning('Please log in from the main application page.')
    st.stop()
apply_theme()

st.markdown("<div class='section-header'>🔬 Emission Factor Provenance</div>", unsafe_allow_html=True)
st.markdown(
    "Every footprint depends on the emission factors used to compute it. This page "
    "records which factor set produced each of your results, so a change in your "
    "number can be traced to a change in your behaviour rather than a change in the data."
)
st.markdown("---")

assessments = get_assessments_with_factors(user_id)

# --- History comparability --------------------------------------------------

st.markdown("### 📊 Is your history comparable?")

if not assessments:
    st.info("No assessments recorded yet.")
else:
    groups = group_assessments_by_version(assessments)
    if is_history_comparable(assessments):
        only_version = next(iter(groups))
        st.success(
            f"All {len(assessments)} assessment(s) use factor set **{only_version}**, "
            "so your trend line compares like with like."
        )
    else:
        st.warning(
            f"Your history mixes **{len(groups)} different factor sets**. Part of any "
            "apparent change comes from the factors themselves, not from your habits. "
            "Use the comparison tool below to separate the two."
        )

    st.dataframe(
        pd.DataFrame([
            {
                "Factor set": version,
                "Assessments": len(rows),
                "Source": get_factor_set(version)["source"]["publisher"],
                "Effective": get_factor_set(version)["effective_date"],
            }
            for version, rows in groups.items()
        ]),
        use_container_width=True,
        hide_index=True,
    )

# --- Registry ---------------------------------------------------------------

st.markdown("---")
st.markdown("### 📚 Registered factor sets")

all_versions = list_factor_versions()
selected_version = st.selectbox("Factor set", all_versions, index=all_versions.index("static-v2")
                                if "static-v2" in all_versions else 0)

factor_set = get_factor_set(selected_version)
st.caption(describe_provenance(selected_version))
if factor_set["notes"]:
    st.info(factor_set["notes"])

meta_left, meta_right = st.columns(2)
with meta_left:
    st.markdown("**Metadata**")
    st.write(
        {
            "Version": factor_set["version"],
            "Kind": factor_set["kind"],
            "Effective": factor_set["effective_date"],
            "Region": factor_set["region"],
            "Fingerprint": factor_set["fingerprint"],
        }
    )
with meta_right:
    st.markdown("**Source**")
    st.write(factor_set["source"])

factor_rows = [
    {"Factor": "Electricity", "Value": factor_set["factors"]["electricity"], "Unit": "kg CO₂/kWh"},
    {"Factor": "Flight", "Value": factor_set["factors"]["flight"], "Unit": "kg CO₂/flight"},
]
factor_rows += [
    {"Factor": f"Transport — {mode}", "Value": value, "Unit": "kg CO₂/km"}
    for mode, value in factor_set["factors"]["transport"].items()
]
factor_rows += [
    {"Factor": f"Diet — {diet}", "Value": value, "Unit": "kg CO₂/year"}
    for diet, value in factor_set["factors"]["diet"].items()
]
st.dataframe(pd.DataFrame(factor_rows), use_container_width=True, hide_index=True)

# --- Diff -------------------------------------------------------------------

st.markdown("---")
st.markdown("### 🔀 Compare two factor sets")

diff_left, diff_right = st.columns(2)
with diff_left:
    version_a = st.selectbox("From", all_versions, index=0, key="diff_from")
with diff_right:
    default_b = min(1, len(all_versions) - 1)
    version_b = st.selectbox("To", all_versions, index=default_b, key="diff_to")

difference = diff_factor_sets(version_a, version_b)
if difference["identical"]:
    st.success("These two factor sets contain identical numbers.")
else:
    st.write(f"**{difference['changed_count']} factor(s) changed.**")
    st.dataframe(
        pd.DataFrame([
            {
                "Factor": name,
                "Before": entry["before"],
                "After": entry["after"],
                "Change": entry["absolute_change"],
                "Change %": (
                    f"{entry['percent_change']:+.1f}%"
                    if entry["percent_change"] is not None else "—"
                ),
            }
            for name, entry in difference["changed"].items()
        ]),
        use_container_width=True,
        hide_index=True,
    )

# --- Behaviour vs factors ---------------------------------------------------

st.markdown("---")
st.markdown("### 🧭 Was it me, or was it the factors?")
st.caption(
    "Recompute one set of lifestyle inputs under several factor sets. Holding the "
    "inputs constant isolates the effect of the factors themselves."
)

with st.form("factor_comparison"):
    input_left, input_right = st.columns(2)
    with input_left:
        transport = st.selectbox("Transport", ["Car", "Bike", "Public Transport", "Walking"])
        distance = st.number_input("Daily distance (km)", min_value=0.0, max_value=500.0, value=10.0)
        flights = st.number_input("Flights per year", min_value=0, max_value=365, value=2)
    with input_right:
        electricity = st.number_input(
            "Monthly electricity (kWh)", min_value=0.0, max_value=10000.0, value=300.0
        )
        diet = st.selectbox("Diet", ["Vegetarian", "Non-Vegetarian"])
        compare_versions = st.multiselect(
            "Factor sets to compare",
            all_versions,
            default=[v for v in ("static-v1", "static-v2") if v in all_versions],
        )
    compare_submitted = st.form_submit_button("🔬 Compare", use_container_width=True)

if compare_submitted:
    if len(compare_versions) < 1:
        st.error("Select at least one factor set.")
    else:
        inputs = {
            "transport": transport,
            "distance": distance,
            "electricity": electricity,
            "diet": diet,
            "flights": flights,
        }
        comparison = compare_assessment_across_versions(inputs, compare_versions)

        st.dataframe(
            pd.DataFrame([
                {
                    "Factor set": result["version"],
                    "Total (kg CO₂)": result["total_kg"],
                    "Transport": result["contributors"]["Transport"],
                    "Electricity": result["contributors"]["Electricity"],
                    "Diet": result["contributors"]["Diet"],
                    "Flights": result["contributors"]["Flights"],
                }
                for result in comparison["results"]
            ]),
            use_container_width=True,
            hide_index=True,
        )

        if comparison["spread_kg"] > 0:
            st.warning(
                f"The same lifestyle produces a **{comparison['spread_kg']:,.0f} kg spread "
                f"({comparison['spread_percent']:.1f}%)** across these factor sets. "
                "That is how much of a footprint 'change' can come from the data alone."
            )

        if len(compare_versions) >= 2:
            attribution = explain_footprint_change(
                inputs, inputs, compare_versions[0], compare_versions[-1]
            )
            st.markdown(
                f"With identical habits, moving from **{compare_versions[0]}** to "
                f"**{compare_versions[-1]}** changes the reported footprint by "
                f"**{attribution['factor_change_kg']:+,.0f} kg** — none of which is a "
                "real reduction."
            )

# --- Per-assessment provenance ----------------------------------------------

if assessments:
    st.markdown("---")
    with st.expander("🗂️ Factor version per assessment"):
        st.dataframe(
            pd.DataFrame([
                {
                    "Date": row[1],
                    "Footprint (kg)": row[7],
                    "Eco score": row[8],
                    "Factor set": normalize_version(row[9]),
                }
                for row in assessments
            ]),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            "Assessments saved before factor versioning show as static-v1, which is "
            "exactly the factor set the app used at the time."
        )
