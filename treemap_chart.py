import plotly.graph_objects as go

# Consistent color per category so it's easy to recognize at a glance
CATEGORY_COLORS = {
    "Transport": "#f97316",   # orange
    "Electricity": "#facc15", # yellow
    "Diet": "#22c55e",        # green
    "Flights": "#38bdf8",     # blue
}


def create_emission_treemap(contributors: dict, total: float) -> go.Figure:
    """
    Build an interactive treemap showing how each lifestyle category
    (Transport, Electricity, Diet, Flights) contributes to the user's
    total carbon footprint, sized by emissions.

    Includes hover details and category-wise percentage contribution.
    """
    categories = list(contributors.keys())
    values = list(contributors.values())

    percentages = [(v / total * 100) if total else 0 for v in values]
    colors = [CATEGORY_COLORS.get(cat, "#94a3b8") for cat in categories]

    hover_text = [
        f"{cat}<br>{val:.2f} kg CO₂<br>{pct:.1f}% of total"
        for cat, val, pct in zip(categories, values, percentages)
    ]

    fig = go.Figure(go.Treemap(
        labels=categories,
        parents=["Total Emissions"] * len(categories),
        values=values,
        marker=dict(colors=colors),
        text=hover_text,
        hovertemplate="%{text}<extra></extra>",
        textinfo="label+percent parent",
        root_color="rgba(0,0,0,0)",
    ))

    fig.update_layout(
        title_text="Emission Breakdown by Category",
        margin=dict(l=10, r=10, t=50, b=10),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return fig