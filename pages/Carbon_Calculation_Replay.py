"""Streamlit page for Carbon Calculation Replay (#443)."""

import streamlit as st
from calculation_replay import render_calculation_replay

user_id = st.session_state.get("user_id") or 1
render_calculation_replay(user_id=user_id)
