import plotly.graph_objects as go

# Consistent color per category so it's easy to recognize at a glance
CATEGORY_COLORS = {
    "Transport": "#f97316",   # orange
    "Electricity": "#facc15", # yellow
    "Diet": "#22c55e",        # green
    "Flights": "#38bdf8",     # blue
}
TOTAL_NODE_COLOR = "#4ade80"


def create_emission_sankey(contributors: dict, total: float) -> go.Figure:
    """
    Build an interactive Sankey diagram showing how each lifestyle
    category (Transport, Electricity, Diet, Flights) flows into the
    user's total carbon footprint.

    Includes hover tooltips and category-wise percentage contribution.
    """
    categories = list(contributors.keys())
    values = list(contributors.values())

    # Nodes = each category + one "Total Emissions" node they all flow into
    labels = categories + ["Total Emissions"]
    node_colors = [CATEGORY_COLORS.get(cat, "#94a3b8") for cat in categories] + [TOTAL_NODE_COLOR]

    # Every category (source) flows into the single "Total Emissions" node (target)
    source = list(range(len(categories)))
    target = [len(categories)] * len(categories)

    percentages = [(v / total * 100) if total else 0 for v in values]
    link_labels = [
        f"{cat}: {val:.2f} kg CO₂ ({pct:.1f}% of total)"
        for cat, val, pct in zip(categories, values, percentages)
    ]

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color=node_colors,
        ),
        link=dict(
            source=source,
            target=target,
            value=values,
            label=link_labels,
            color=[node_colors[i] for i in source],
            hovertemplate="%{label}<extra></extra>",
        ),
    )])

    fig.update_layout(
        title_text="Emission Flow by Category",
        font_size=13,
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=50, b=10),
    )

    return fig