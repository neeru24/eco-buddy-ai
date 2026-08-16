"""The app header.

`app.py` has called `render_header()` since the header markup was pulled out
of it, but the module it imports from was never added to the repository, so
`app.py` failed on import and the app did not start. This is that module; the
markup is the header the app used inline before the extraction.
"""

import streamlit as st

TITLE = "🌱 EcoBuddy AI+"
SUBTITLE = "Your Personal AI-Powered Carbon Footprint Tracker & Eco Assistant"
TAGLINE = "✨ Track • 📊 Analyze • 💡 Improve"


def render_header():
    """Render the title, subtitle and tagline at the top of the app."""
    st.markdown(
        f"<div class='title'>{TITLE}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='subtitle'>{SUBTITLE}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
<div style='text-align: center; margin-bottom: 32px;'>
    <div style='display: inline-flex; gap: 16px; padding: 12px 24px;
                background: rgba(34, 197, 94, 0.08); border-radius: 50px;
                border: 1px solid rgba(74, 222, 128, 0.2);'>
        <span style='color: #000; font-size: 15px; font-weight: 700;'>{TAGLINE}</span>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("---")
