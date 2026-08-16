"""Streamlit page for Carbon Footprint Replay (#332)."""

import streamlit as st
from carbon_footprint_replay import render_carbon_footprint_replay

user_id = st.session_state.get("user_id") or 1
render_carbon_footprint_replay(user_id=user_id)
