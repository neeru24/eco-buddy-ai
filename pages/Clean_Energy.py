import streamlit as st

# -----------------------------------------------------------------------------
# Clean Energy Explorer
# -----------------------------------------------------------------------------
# Educational feature for introducing users to renewable and cleaner energy
# sources. Calculations/savings estimates are intentionally out of scope for
# this first version.
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Clean Energy Explorer | EcoBuddy",
    page_icon="🌱",
    layout="wide",
)

ENERGY_SOURCES = {
    "☀️ Solar Energy": {
        "tag": "Sun-powered electricity",
        "description": (
            "Solar energy uses sunlight to produce electricity, most commonly "
            "through photovoltaic (PV) panels."
        ),
        "why_it_matters": (
            "Solar is renewable and produces no direct greenhouse-gas "
            "emissions while generating electricity."
        ),
        "best_for": "Homes, campuses, businesses, and sunny regions",
        "highlights": [
            "Renewable energy source",
            "Low operating emissions",
            "Can be installed at different scales",
        ],
    },
    "🌬️ Wind Energy": {
        "tag": "Wind-powered electricity",
        "description": (
            "Wind turbines convert the movement of air into electricity "
            "using rotating blades and a generator."
        ),
        "why_it_matters": (
            "Wind power generates electricity without burning fuel during "
            "operation and can support large-scale clean-energy generation."
        ),
        "best_for": "Windy regions and utility-scale energy projects",
        "highlights": [
            "Renewable resource",
            "No fuel combustion during operation",
            "Suitable for large-scale generation",
        ],
    },
    "💧 Hydropower": {
        "tag": "Water-powered electricity",
        "description": (
            "Hydropower uses moving or falling water to turn turbines and "
            "generate electricity."
        ),
        "why_it_matters": (
            "Hydropower can provide renewable electricity and, depending on "
            "the system, can also help provide a steady power supply."
        ),
        "best_for": "Regions with suitable rivers, reservoirs, or elevation",
        "highlights": [
            "Renewable energy source",
            "Can provide steady generation",
            "Useful for grid-scale electricity",
        ],
    },
    "🌱 Biomass Energy": {
        "tag": "Energy from organic material",
        "description": (
            "Biomass energy uses organic material such as agricultural "
            "residues, wood, or other biological material to produce heat "
            "or electricity."
        ),
        "why_it_matters": (
            "When responsibly sourced, biomass can make productive use of "
            "organic materials that might otherwise become waste."
        ),
        "best_for": "Areas with sustainable organic-material resources",
        "highlights": [
            "Can use organic residues",
            "Can support waste-to-energy approaches",
            "Useful for heat and electricity",
        ],
    },
    "🌋 Geothermal Energy": {
        "tag": "Earth-heat energy",
        "description": (
            "Geothermal energy uses heat from beneath Earth's surface for "
            "heating or electricity generation."
        ),
        "why_it_matters": (
            "Geothermal systems can provide a consistent renewable energy "
            "source where suitable geothermal resources are available."
        ),
        "best_for": "Regions with accessible geothermal resources",
        "highlights": [
            "Renewable heat source",
            "Can provide consistent generation",
            "Useful for heating and electricity",
        ],
    },
}

st.markdown(
    """
    <style>
    .energy-hero {
        padding: 2rem 2.2rem;
        border: 1px solid #dcefe5;
        border-radius: 22px;
        background: linear-gradient(135deg, #f5fff9 0%, #ffffff 65%);
        margin-bottom: 1.5rem;
    }

    .energy-eyebrow {
        color: #159447;
        font-weight: 700;
        letter-spacing: .04em;
        text-transform: uppercase;
        font-size: .82rem;
        margin-bottom: .35rem;
    }

    .energy-hero h1 {
        margin: 0;
        color: #14213d;
        font-size: 2.1rem;
    }

    .energy-hero p {
        color: #53627a;
        font-size: 1rem;
        max-width: 760px;
        margin-top: .65rem;
    }

    .source-card {
        border: 1px solid #dcefe5;
        border-radius: 18px;
        padding: 1.1rem;
        background: #ffffff;
        min-height: 145px;
        margin-bottom: 1rem;
    }

    .source-title {
        color: #14213d;
        font-size: 1.05rem;
        font-weight: 750;
        margin-bottom: .35rem;
    }

    .source-tag {
        color: #159447;
        font-size: .82rem;
        font-weight: 650;
        margin-bottom: .55rem;
    }

    .source-description {
        color: #5b6980;
        font-size: .9rem;
        line-height: 1.5;
    }

    .detail-card {
        border: 1px solid #dcefe5;
        border-radius: 20px;
        padding: 1.5rem;
        background: #ffffff;
        margin-top: .5rem;
    }

    .detail-card h2 {
        color: #14213d;
        margin-top: 0;
    }

    .detail-label {
        color: #159447;
        font-weight: 750;
        margin-bottom: .25rem;
    }

    .detail-text {
        color: #53627a;
        line-height: 1.6;
    }

    .highlight {
        padding: .7rem .85rem;
        border-radius: 12px;
        background: #f3fbf6;
        border: 1px solid #e0f2e7;
        margin-bottom: .55rem;
        color: #33435c;
    }

    .scope-note {
        padding: 1rem 1.1rem;
        border-radius: 14px;
        background: #f8fbfa;
        border: 1px solid #e4eee9;
        color: #667389;
        font-size: .86rem;
        margin-top: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="energy-hero">
        <div class="energy-eyebrow">EcoBuddy • Clean Energy</div>
        <h1>🌱 Clean Energy Explorer</h1>
        <p>
            Explore renewable and cleaner energy sources, understand how they
            work, and discover where each option can be useful.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Explore energy sources")
st.caption("Select a source below to learn more about how it works and why it matters.")

source_names = list(ENERGY_SOURCES.keys())
selected_source = st.session_state.get("selected_energy_source", source_names[0])

# Five interactive source cards. The buttons make the section genuinely
# interactive without introducing calculations that are outside this issue.
columns = st.columns(len(source_names))

for column, source_name in zip(columns, source_names):
    data = ENERGY_SOURCES[source_name]
    with column:
        st.markdown(
            f"""
            <div class="source-card">
                <div class="source-title">{source_name}</div>
                <div class="source-tag">{data["tag"]}</div>
                <div class="source-description">{data["description"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(
            "Explore",
            key=f"explore_{source_name}",
            use_container_width=True,
            type="secondary",
        ):
            st.session_state["selected_energy_source"] = source_name
            selected_source = source_name

# Re-read the session state after a button click.
selected_source = st.session_state.get("selected_energy_source", source_names[0])
data = ENERGY_SOURCES[selected_source]

st.markdown(
    f"""
    <div class="detail-card">
        <h2>{selected_source}</h2>
        <div class="detail-label">How it works</div>
        <div class="detail-text">{data["description"]}</div>
        <br>
        <div class="detail-label">Why it matters</div>
        <div class="detail-text">{data["why_it_matters"]}</div>
        <br>
        <div class="detail-label">Best suited for</div>
        <div class="detail-text">{data["best_for"]}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("### Key takeaways")
takeaway_columns = st.columns(3)
for column, highlight in zip(takeaway_columns, data["highlights"]):
    with column:
        st.markdown(
            f'<div class="highlight">✓ {highlight}</div>',
            unsafe_allow_html=True,
        )

st.markdown(
    """
    <div class="scope-note">
        <strong>About this explorer:</strong>
        This version is designed for education and exploration. Energy savings,
        local electricity rates, renewable-energy potential, and CO₂ calculations
        are intentionally not included yet and can be added as future enhancements.
    </div>
    """,
    unsafe_allow_html=True,
)
