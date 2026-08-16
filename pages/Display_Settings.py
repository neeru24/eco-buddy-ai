import pandas as pd
import streamlit as st

from database import get_assessments, get_unit_preference, save_unit_preference
from styles.theme import apply_theme, render_unit_selector
from units import (
    DIM_AREA,
    DIM_DISTANCE,
    DIM_ENERGY,
    DIM_MASS,
    DIM_TEMPERATURE,
    DIM_VOLUME,
    describe_preference,
    format_area,
    format_co2,
    format_currency,
    format_distance,
    format_energy,
    format_volume,
    label_with_unit,
    to_preferred,
    unit_symbol,
)

user_id = st.session_state.get('user_id')
if not user_id:
    st.warning('Please log in from the main application page.')
    st.stop()
apply_theme()

preference = render_unit_selector(user_id)

st.markdown("<div class='section-header'>⚙️ Display Settings</div>", unsafe_allow_html=True)
st.markdown(
    "Choose the units and currency EcoBuddy shows you. Your data is always stored "
    "in metric — this only changes how it is displayed, so switching back and forth "
    "never alters a single recorded value."
)
st.markdown("---")

st.info(f"**Currently showing:** {describe_preference(preference)}")

# --- Live preview -----------------------------------------------------------

st.markdown("### 👀 Preview")
st.caption("The same stored values, rendered with your current preference.")

preview_rows = [
    {
        "Quantity": "Annual carbon footprint",
        "Stored": "5,218.5 kg CO₂",
        "You see": format_co2(5218.5, preference),
    },
    {
        "Quantity": "Daily commute",
        "Stored": "10.0 km",
        "You see": format_distance(10.0, preference),
    },
    {
        "Quantity": "Monthly electricity",
        "Stored": "300.0 kWh",
        "You see": format_energy(300.0, preference, precision=0),
    },
    {
        "Quantity": "Daily water use",
        "Stored": "3,800.0 L",
        "You see": format_volume(3800.0, preference, precision=0),
    },
    {
        "Quantity": "Roof space",
        "Stored": "40.0 m²",
        "You see": format_area(40.0, preference, precision=0),
    },
    {
        "Quantity": "Annual energy cost",
        "Stored": "1,240.00 (bare number)",
        "You see": format_currency(1240.0, preference),
    },
]
st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)

# --- Form labels ------------------------------------------------------------

st.markdown("### 🏷️ Form labels")
st.caption(
    "Input labels are built from your preference rather than hardcoded, so a page "
    "never has to be edited to support a new unit."
)

label_rows = [
    {"Field": label_with_unit("Daily Distance", DIM_DISTANCE, preference, per="day")},
    {"Field": label_with_unit("Monthly Electricity", DIM_ENERGY, preference, per="month")},
    {"Field": label_with_unit("Shower Water", DIM_VOLUME, preference, per="day")},
    {"Field": label_with_unit("Roof Space", DIM_AREA, preference)},
    {"Field": label_with_unit("Thermostat Setting", DIM_TEMPERATURE, preference)},
]
st.dataframe(pd.DataFrame(label_rows), use_container_width=True, hide_index=True)

# --- Active symbols ---------------------------------------------------------

with st.expander("📐 Units in use"):
    st.dataframe(
        pd.DataFrame([
            {"Dimension": name, "Symbol": unit_symbol(dimension, preference)}
            for name, dimension in [
                ("Distance", DIM_DISTANCE),
                ("Mass / CO₂", DIM_MASS),
                ("Volume", DIM_VOLUME),
                ("Energy", DIM_ENERGY),
                ("Temperature", DIM_TEMPERATURE),
                ("Area", DIM_AREA),
            ]
        ]),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "Energy stays in kWh in both systems because that is the unit that appears "
        "on electricity bills everywhere."
    )

# --- Your own data ----------------------------------------------------------

assessments = get_assessments(user_id)
if assessments:
    st.markdown("---")
    st.markdown("### 📊 Your assessments in your units")

    distance_symbol = unit_symbol(DIM_DISTANCE, preference)
    st.dataframe(
        pd.DataFrame([
            {
                "Date": row[1],
                "Footprint": format_co2(row[7] or 0, preference),
                f"Distance ({distance_symbol})": round(
                    to_preferred(row[3] or 0, "km", preference)[0], 1
                ),
                "Electricity": format_energy(row[4] or 0, preference, precision=0),
                "Eco score": row[8],
            }
            for row in assessments[:20]
        ]),
        use_container_width=True,
        hide_index=True,
    )
    st.caption("Showing the 20 most recent assessments.")

# --- Reset ------------------------------------------------------------------

st.markdown("---")
if st.button("↩️ Reset to metric and USD", use_container_width=True):
    save_unit_preference(user_id, "metric", "USD")
    st.session_state.unit_preference = get_unit_preference(user_id)
    st.success("Display preference reset.")
    st.rerun()
