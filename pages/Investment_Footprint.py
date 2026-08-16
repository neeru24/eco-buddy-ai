import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from financed_emissions import (
    DEFAULT_CURRENT_FUND,
    DEFAULT_DECARBONISATION_RATE,
    DEFAULT_GROWTH_RATE,
    DEFAULT_PROPOSED_FUND,
    DEFAULT_YEARS,
    SECTOR_INTENSITIES,
    PortfolioError,
    compare_funds,
    compare_to_operational,
    concentration,
    custom_portfolio,
    delete_portfolio,
    equivalent_actions,
    fund_intensity,
    get_caveats,
    get_portfolios,
    get_switch_advice,
    list_fund_archetypes,
    list_sectors,
    portfolio_emissions,
    project_switch,
    save_portfolio,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()

apply_theme()

st.markdown(
    "<div class='section-header'>💰 Investment & Pension Footprint</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "This app measures what you burn, drive and eat. It has never measured "
    "what your money does while you sleep. For most people with a few years "
    "of pension contributions, **that is the biggest line in their footprint** "
    "— and unlike everything else here, changing it takes one form, once."
)

funds = list_fund_archetypes()
fund_names = [fund["name"] for fund in funds]

st.markdown("---")
st.markdown("### 💼 What You Hold")

mode = st.radio(
    "How do you want to describe your investments?",
    ["Pick a fund type", "Enter sector weights"],
    horizontal=True,
    help="Pick a fund type if you do not know your fund's breakdown. Use "
    "sector weights if you have the factsheet in front of you.",
)

value_col, contribution_col = st.columns(2)
with value_col:
    holding_value = st.number_input(
        "Total invested (pension + ISA + other)",
        min_value=0.0,
        value=120000.0,
        step=5000.0,
        help="Include your workplace pension. It is usually the largest part.",
    )
with contribution_col:
    annual_contribution = st.number_input(
        "Added each year",
        min_value=0.0,
        value=6000.0,
        step=500.0,
        help="Your contributions plus your employer's.",
    )

if mode == "Pick a fund type":
    current_fund = st.selectbox(
        "What you are in now",
        fund_names,
        index=fund_names.index(DEFAULT_CURRENT_FUND),
        help="If you have never chosen, you are almost certainly in the "
        "default — usually a global equity tracker.",
    )
    current_intensity = fund_intensity(current_fund)
    breakdown = []
    st.caption(next(fund["description"] for fund in funds if fund["name"] == current_fund))
else:
    st.caption(
        "Enter your fund's sector weights as percentages. They do not need to "
        "add up to exactly 100 — they will be normalised."
    )
    # A rough global-index shape as a starting point. Keyed by sector rather
    # than positionally, so reordering the catalogue cannot silently attach
    # the wrong weight to the wrong sector.
    STARTING_WEIGHTS = {
        "Information technology": 24.0,
        "Financials": 16.0,
        "Healthcare": 12.0,
        "Consumer discretionary": 11.0,
        "Industrials": 10.0,
        "Communication services": 8.0,
        "Consumer staples": 7.0,
        "Energy (oil, gas, coal)": 5.0,
        "Materials (cement, steel, chemicals)": 4.0,
        "Utilities": 3.0,
        "Real estate": 2.0,
    }
    sector_frame = st.data_editor(
        pd.DataFrame(
            [
                {
                    "Sector": entry["name"],
                    "Weight (%)": STARTING_WEIGHTS.get(entry["name"], 0.0),
                }
                for entry in list_sectors()
            ]
        ),
        use_container_width=True,
        hide_index=True,
        key="sector_weights",
        column_config={
            "Sector": st.column_config.TextColumn(disabled=True),
            "Weight (%)": st.column_config.NumberColumn(min_value=0.0, format="%.1f"),
        },
    )
    weights = {
        str(row["Sector"]): row["Weight (%)"] for _, row in sector_frame.iterrows()
    }
    try:
        custom = custom_portfolio(weights)
    except PortfolioError as error:
        st.error(str(error))
        st.stop()

    current_fund = f"Custom ({custom['nearest_archetype']}-like)"
    current_intensity = custom["intensity"]
    breakdown = custom["breakdown"]

result = portfolio_emissions(
    [{"name": current_fund, "value": holding_value, "intensity": current_intensity}]
)

st.markdown("---")
st.markdown("### 🏭 What Your Money Finances")

intensity_col, financed_col, archetype_col = st.columns(3)
intensity_col.metric("Carbon intensity", f"{current_intensity:,.0f} t per £1m")
financed_col.metric(
    "Financed each year", f"{result['total_emissions']:,.2f} t CO2e"
)
archetype_col.metric("Closest to", result["nearest_archetype"])

if breakdown:
    top = concentration(breakdown, top_n=3)
    st.info(
        f"**{', '.join(top['top_sectors'])}** are "
        f"{top['share_of_value'] * 100:.0f}% of your money and "
        f"{top['share_of_carbon'] * 100:.0f}% of your financed carbon. That "
        f"concentration is why a screened fund can be so much lighter without "
        f"changing much of the portfolio."
    )

    sector_figure = go.Figure()
    sector_figure.add_trace(
        go.Bar(
            name="Share of your money",
            x=[entry["sector"] for entry in breakdown],
            y=[entry["weight"] * 100 for entry in breakdown],
            marker_color="rgba(46, 139, 87, 0.75)",
        )
    )
    sector_figure.add_trace(
        go.Bar(
            name="Share of your carbon",
            x=[entry["sector"] for entry in breakdown],
            y=[entry["share_of_carbon"] * 100 for entry in breakdown],
            marker_color="rgba(178, 58, 48, 0.75)",
        )
    )
    sector_figure.update_layout(
        barmode="group",
        height=380,
        yaxis_title="%",
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(sector_figure, use_container_width=True)

st.markdown("**How does that compare to the rest of your footprint?**")
operational = st.number_input(
    "Your footprint from everything else (tonnes CO2e per year)",
    min_value=0.0,
    value=5.0,
    step=0.5,
    help="Take this from your assessment. Driving, heating, flying, food.",
)

sizing = compare_to_operational(result["total_emissions"], operational)

comparison_figure = go.Figure()
comparison_figure.add_trace(
    go.Bar(
        x=["Everything you do", "What your money finances"],
        y=[sizing["operational"], sizing["financed"]],
        marker_color=["rgba(46, 139, 87, 0.8)", "rgba(178, 58, 48, 0.8)"],
    )
)
comparison_figure.update_layout(
    height=320,
    yaxis_title="tonnes CO2e per year",
    showlegend=False,
    margin=dict(l=10, r=10, t=30, b=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(comparison_figure, use_container_width=True)

if sizing["verdict"] in ("dominates", "larger"):
    st.error(sizing["explanation"])
elif sizing["verdict"] == "comparable":
    st.warning(sizing["explanation"])
else:
    st.info(sizing["explanation"])

st.caption(f"⚖️ {sizing['boundary_note']}")

st.markdown("---")
st.markdown("### 🔀 What a Switch Would Do")

proposed_fund = st.selectbox(
    "Fund you could switch to",
    fund_names,
    index=fund_names.index(DEFAULT_PROPOSED_FUND),
)
proposed_intensity = fund_intensity(proposed_fund)
st.caption(next(fund["description"] for fund in funds if fund["name"] == proposed_fund))

comparison = compare_funds(holding_value, current_intensity, proposed_intensity)

years_col, growth_col, decline_col = st.columns(3)
with years_col:
    years = st.slider("Years until you retire", 1, 45, DEFAULT_YEARS)
with growth_col:
    growth = st.slider(
        "Assumed annual growth", 0.0, 0.12, DEFAULT_GROWTH_RATE, step=0.005,
        format="%.3f",
    )
with decline_col:
    decline = st.slider(
        "Assumed market decarbonisation",
        0.0,
        0.10,
        DEFAULT_DECARBONISATION_RATE,
        step=0.005,
        format="%.3f",
        help="Listed companies have been getting cleaner anyway. Applied to "
        "both funds so the switch is not credited with it.",
    )

projection = project_switch(
    holding_value,
    annual_contribution,
    current_intensity,
    proposed_intensity,
    years=years,
    growth_rate=growth,
    decarbonisation_rate=decline,
)

now_col, lifetime_col, percent_col = st.columns(3)
now_col.metric("Avoided this year", f"{comparison['annual_avoided']:,.2f} t")
lifetime_col.metric(
    f"Avoided over {years} years", f"{projection['cumulative_avoided']:,.0f} t"
)
percent_col.metric("Intensity cut", f"{comparison['percent_avoided']:.0f}%")

timeline_figure = go.Figure()
timeline_figure.add_trace(
    go.Scatter(
        name=f"Staying in {current_fund}",
        x=[entry["year"] for entry in projection["timeline"]],
        y=[entry["current_emissions"] for entry in projection["timeline"]],
        mode="lines",
        line=dict(color="rgba(178, 58, 48, 0.9)"),
        fill="tozeroy",
    )
)
timeline_figure.add_trace(
    go.Scatter(
        name=f"Switching to {proposed_fund}",
        x=[entry["year"] for entry in projection["timeline"]],
        y=[entry["proposed_emissions"] for entry in projection["timeline"]],
        mode="lines",
        line=dict(color="rgba(46, 139, 87, 0.9)"),
        fill="tozeroy",
    )
)
timeline_figure.update_layout(
    height=360,
    xaxis_title="Years from now",
    yaxis_title="tonnes CO2e financed that year",
    margin=dict(l=10, r=10, t=30, b=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(timeline_figure, use_container_width=True)

if comparison["is_improvement"]:
    equivalents = equivalent_actions(projection["cumulative_avoided"])
    headline = equivalents[0]
    st.success(
        f"Over {years} years, switching avoids about "
        f"{projection['cumulative_avoided']:,.0f} tonnes — the same as "
        f"**{headline['equivalent_years']:.0f} years of {headline['action']}**. "
        f"It takes one form."
    )

    st.markdown("**That saving, in things you would otherwise have to do:**")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Instead of": item["action"],
                    "For this many years": f"{item['equivalent_years']:.1f}",
                }
                for item in equivalents
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

for line in get_switch_advice(comparison, projection):
    st.info(line)

st.markdown("---")
st.markdown("### ⚠️ What This Method Does And Does Not Show")
for caveat in get_caveats():
    st.markdown(f"- {caveat}")

st.markdown("---")
st.markdown("### 💾 Saved Portfolios")

name_col, save_col = st.columns([3, 1])
with name_col:
    portfolio_name = st.text_input(
        "Portfolio name", value="My pension", label_visibility="collapsed"
    )
with save_col:
    if st.button("Save portfolio", use_container_width=True):
        if save_portfolio(user_id, portfolio_name, result):
            st.success("Saved.")
        else:
            st.error("Could not save that portfolio.")

portfolios = get_portfolios(user_id)
if not portfolios:
    st.caption("No saved portfolios yet.")
else:
    for portfolio in portfolios:
        detail_col, delete_col = st.columns([5, 1])
        with detail_col:
            st.markdown(
                f"**{portfolio['name']}** — {portfolio['total_value']:,.0f} invested at "
                f"{portfolio['blended_intensity']:,.0f} t/£1m, financing "
                f"{portfolio['total_emissions']:,.2f} t CO2e a year "
                f"· {portfolio['created_at']}"
            )
        with delete_col:
            if st.button("Delete", key=f"delete_portfolio_{portfolio['id']}"):
                delete_portfolio(user_id, portfolio["id"])
                st.rerun()

st.markdown("---")
st.caption(
    "Method: financed emissions are attributed by ownership share, following "
    "the PCAF approach used for financial-sector carbon reporting. Fund "
    "intensities are documented archetypes showing the spread between fund "
    "types, not figures for any named product — use your own fund's published "
    "figure where you have it. Nothing on this page is investment advice."
)
