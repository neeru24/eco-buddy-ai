import streamlit as st


def success(message):
    """Display a success notification."""
    st.success(message)


def error(message):
    """Display an error notification."""
    st.error(message)


def warning(message):
    """Display a warning notification."""
    st.warning(message)


def info(message):
    """Display an informational notification."""
    st.info(message)
