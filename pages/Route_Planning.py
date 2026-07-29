import streamlit as st
import pandas as pd
import time
from database import *
from emissions import *
from recommendations import *
from ocr_utils import *
import os
import tempfile
import uuid
import plotly.graph_objects as go
import plotly.express as px
from report import generate_pdf
import gamification as gf
from marketplace import *
import energy_audit as ea
import logging
from styles.theme import apply_theme

user_id = st.session_state.get('user_id', 1)
apply_theme()

logger = logging.getLogger(__name__)


def get_trip_frequency_multiplier(frequency):
    """
    Returns the trip multiplier and optional display message
    based on the selected trip frequency.
    """
    frequency_map = {
        "Weekly Commute (10 trips/week)": (
            10,
            "*Calculated for 10 trips per week*",
        ),
        "Daily (14 trips/week)": (
            14,
            "*Calculated for 14 trips per week*",
        ),
    }
    return frequency_map.get(frequency, (1, None))


st.markdown("<div class='section-header'>🗺️ Route Planning & Carbon Offsets</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Compare transit modes, track your footprint, and build a simulated offset portfolio. Note: This is a simulation and does not process real financial transactions.</div>", unsafe_allow_html=True)

route_col, offset_col = st.columns([1.2, 1])

with route_col:
    st.subheader("📍 Transit Mode Comparison")

    with st.form("route_form"):
        dist_val = st.number_input("Trip Distance (km)", min_value=0.1, value=15.0, step=1.0)
        pass_val = st.number_input("Number of Passengers", min_value=1, value=1, step=1)
        freq = st.selectbox(
            "Trip Frequency",
            [
                "One-time",
                "Weekly Commute (10 trips/week)",
                "Daily (14 trips/week)",
            ],
        )

        calc_btn = st.form_submit_button("Compare Emissions")

    if calc_btn:
        try:
            with st.spinner("Calculating transit emissions..."):
                comparisons = compare_transit_modes(dist_val, pass_val)

            st.write(f"**Estimated Emissions for a {dist_val}km trip:**")

            df_comp = pd.DataFrame(comparisons)
            multiplier, message = get_trip_frequency_multiplier(freq)

            if multiplier > 1:
                df_comp["emissions_kg"] *= multiplier

            if message:
                st.write(message)

            fig = px.bar(
                df_comp,
                x="mode",
                y="emissions_kg",
                title="CO2e by Transit Mode (Lower is Better)",
                color="emissions_kg",
                color_continuous_scale="Greens_r",
            )
            st.plotly_chart(fig, width="stretch")

            st.dataframe(df_comp.style.format({"emissions_kg": "{:.2f}"}))

        except Exception as e:
            st.error(f"Error calculating emissions: {e}")

with offset_col:
    st.subheader("🛒 Simulated Offset Marketplace")
    st.info("💡 Invest your simulated eco-points to offset carbon.")

    projects = get_offset_projects()
    project_lookup = {project["name"]: project for project in projects}
    proj_names = list(project_lookup.keys())

    selected_proj_name = st.selectbox("Select an Offset Project", proj_names)
    selected_proj = project_lookup[selected_proj_name]

    st.markdown(f"**{selected_proj['image']} {selected_proj['name']}**")
    st.write(f"*{selected_proj['description']}*")
    st.write(f"**Category:** {selected_proj['category']} | **Region:** {selected_proj['region']}")
    st.write(f"**Cost:** ${selected_proj['cost_per_tonne']:.2f} per tonne")

    with st.form("offset_form"):
        tonnes = st.number_input(
            "Tonnes of CO2e to Offset",
            min_value=0.1,
            value=1.0,
            step=0.1,
        )
        purchase_btn = st.form_submit_button("Purchase Simulated Offset")

        if purchase_btn:
            with st.spinner("Processing simulated offset purchase..."):
                is_valid, msg = validate_offset_transaction(
                    tonnes,
                    selected_proj["available_capacity"],
                )

                if is_valid:
                    cost = calculate_offset_cost(
                        tonnes,
                        selected_proj["cost_per_tonne"],
                    )

                    if save_offset_transaction(user_id, selected_proj["id"], selected_proj["name"], tonnes, selected_proj["cost_per_tonne"], cost):
                        st.success(f"Simulated purchase successful! Offset {tonnes}t for ${cost:.2f}.")
                    else:
                        st.error("Failed to save transaction.")
                else:
                    st.error(msg)

st.markdown("---")

st.markdown(
    "<div class='section-header'>📈 Your Offset Portfolio</div>",
    unsafe_allow_html=True,
)

port_col1, port_col2 = st.columns([1, 2])

with port_col1:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    try:
        total_offsets = get_total_offsets(user_id)
        total_spend = get_total_spend(user_id)

        st.metric("Total Tonnes Offset", f"{total_offsets:.2f}t")
        st.metric("Total Simulated Spend", f"${total_spend:.2f}")

        estimated_footprint = 50.0  # Placeholder lifetime footprint
        net_progress = calculate_net_zero_progress(estimated_footprint, total_offsets)

        st.metric("Net-Zero Progress (Estimated)", f"{net_progress:.1f}%")
        st.progress(net_progress / 100)
    except Exception:
        logger.exception("Failed to load portfolio metrics.")
        st.error("Unable to load your portfolio summary. Please try again later.")

    st.markdown("</div>", unsafe_allow_html=True)

with port_col2:
    st.subheader("Transaction History")
    try:
        transactions = get_offset_transactions(user_id)
        if transactions:
            df_trans = pd.DataFrame(transactions)
            st.dataframe(
                df_trans[["created_at", "project_name", "offset_tonnes", "total_cost", "transaction_status"]]
            )
            if st.button("Clear History"):
                try:
                    for transaction in transactions:
                        delete_offset_transaction(transaction["id"])
                    st.success("Transaction history cleared successfully.")
                    st.rerun()
                except Exception:
                    logger.exception("Failed to clear transaction history.")
                    st.error("Unable to clear transaction history. Please try again.")
        else:
            st.info("No transactions yet. Visit the marketplace to start your portfolio!")
    except Exception:
        logger.exception("Failed to load transaction history.")
        st.error("Unable to load your transaction history. Please try again later.")
