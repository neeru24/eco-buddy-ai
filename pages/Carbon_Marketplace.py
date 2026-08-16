import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from styles.theme import apply_theme
from database import (
    get_eco_balance, update_eco_balance,
    get_carbon_credits, get_all_listed_credits,
    issue_carbon_credit, retire_carbon_credit,
    list_credit_for_trade, execute_credit_trade,
    get_market_state, update_market_state,
    get_credit_trades, get_credit_portfolio_summary,
    get_assessments, get_offset_projects as db_get_offset_projects,
    save_offset_transaction,
)
from carbon_marketplace import (
    PROJECTS, simulate_market_tick, get_price_history,
    calculate_credit_value, get_learning_insights,
    estimate_credit_price_trend,
)

user_id = st.session_state.get("user_id", 1)
apply_theme()

st.markdown("<div class='section-header'>🌍 Carbon Marketplace Simulation</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Learn how carbon credit markets work — earn, trade, and retire virtual carbon credits in this interactive simulation.</div>", unsafe_allow_html=True)

market = get_market_state()
current_price = market.get("price_per_tonne", 25.0)
volatility = market.get("volatility", 0.05)

tab1, tab2, tab3, tab4 = st.tabs(["📊 Market Overview", "💼 My Portfolio", "🔄 Trade Credits", "🎓 Learning Insights"])

# ─── TAB 1: Market Overview ──────────────────────────────────────────────────
with tab1:
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Current Price", f"${current_price:.2f}/t")
    with col_m2:
        st.metric("Volatility", f"{volatility*100:.1f}%")
    with col_m3:
        st.metric("Total Supply", f"{market.get('total_supply', 10000):.0f} t")
    with col_m4:
        st.metric("Trading Volume", f"{market.get('trading_volume', 0):.0f} t")

    if st.button("🔄 Simulate Market Tick", use_container_width=True):
        tick = simulate_market_tick(current_price, volatility)
        supply = market.get("total_supply", 10000) * (1 + tick["supply_shift"] / 100)
        demand = market.get("total_demand", 5000) * (1 + tick["demand_shift"] / 100)
        volume = market.get("trading_volume", 0) + random.uniform(10, 100)
        update_market_state(tick["price"], volatility, supply, demand, volume)
        if tick["price"] > current_price:
            st.success(f"Price increased to ${tick['price']:.2f}/t (+{((tick['price']/current_price)-1)*100:.1f}%)")
        elif tick["price"] < current_price:
            st.warning(f"Price dropped to ${tick['price']:.2f}/t ({((tick['price']/current_price)-1)*100:.1f}%)")
        else:
            st.info("Price held steady.")
        st.rerun()
    import random

    price_history = get_price_history()
    if len(price_history) >= 2:
        df_prices = pd.DataFrame(price_history)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(len(df_prices))),
            y=df_prices["price"],
            mode="lines+markers",
            name="Price",
            line=dict(color="#4ade80", width=2),
            fill="tozeroy",
            fillcolor="rgba(74, 222, 128, 0.15)",
        ))
        fig.update_layout(
            title="Price Simulation (Recent Ticks)",
            height=300,
            margin=dict(l=40, r=20, t=30, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(55, 65, 81, 0.1)",
            xaxis_title="Tick",
            yaxis_title="Price ($/tonne)",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Available Projects")
    for proj in PROJECTS:
        with st.expander(f"{proj['name']} — ${proj['cost_per_tonne']}/t ({proj['category']})"):
            st.markdown(f"**Region:** {proj['region']}")
            st.markdown(f"**Co-benefits:** {proj['co_benefits']}")
            st.markdown(f"**Category:** {proj['category']}")

# ─── TAB 2: My Portfolio ─────────────────────────────────────────────────────
with tab2:
    balance_data = get_eco_balance(user_id)
    st.markdown(f"### 🪙 Eco Balance: **${balance_data['balance']:.2f}**")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.metric("Lifetime Earned", f"${balance_data['lifetime_earned']:.2f}")
    with col_b2:
        st.metric("Lifetime Spent", f"${balance_data['lifetime_spent']:.2f}")

    if st.button("💰 Earn Eco Points (Daily Bonus)", use_container_width=True):
        bonus = random.randint(50, 200)
        if update_eco_balance(user_id, bonus):
            st.success(f"You earned ${bonus} eco points!")
            st.rerun()

    st.markdown("---")
    st.markdown("### My Carbon Credits")
    credits = get_carbon_credits(user_id)
    if credits:
        df_credits = pd.DataFrame(credits)
        st.dataframe(df_credits[["serial_no", "project_name", "vintage_year", "quantity", "status", "source", "issued_at"]])
    else:
        st.info("You don't have any carbon credits yet. Complete assessments or earn them through challenges!")

    summary = get_credit_portfolio_summary(user_id)
    if summary["total_tonnes"] > 0:
        st.markdown("### Portfolio Summary")
        cols = st.columns(5)
        labels = ["Issued", "Listed", "Traded", "Retired", "Total Tonnes"]
        keys = ["issued", "listed", "traded", "retired", "total_tonnes"]
        for i, (label, key) in enumerate(zip(labels, keys)):
            with cols[i]:
                val = summary[key]
                st.metric(label, f"{val:.1f}" if isinstance(val, float) else val)

    if credits:
        st.markdown("### Retire a Credit")
        retire_opts = [c for c in credits if c["status"] in ("issued", "traded")]
        if retire_opts:
            sel_credit = st.selectbox(
                "Select credit to retire",
                retire_opts,
                format_func=lambda c: f"{c['serial_no']} — {c['project_name']} ({c['quantity']}t, {c['status']})",
            )
            retire_reason = st.text_input("Reason for retiring (e.g., 'Offset my travel footprint')", placeholder="Offset my Q3 emissions")
            if st.button("♻️ Retire Credit", use_container_width=True):
                if retire_carbon_credit(sel_credit["id"], retire_reason):
                    st.success(f"Credit {sel_credit['serial_no']} retired permanently!")
                    st.rerun()
        else:
            st.info("No credits available to retire.")

# ─── TAB 3: Trade Credits ────────────────────────────────────────────────────
with tab3:
    st.markdown("### List Your Credits for Trade")
    my_issued = [c for c in get_carbon_credits(user_id) if c["status"] == "issued"]
    if my_issued:
        sel_list = st.selectbox(
            "Choose a credit to list",
            my_issued,
            format_func=lambda c: f"{c['serial_no']} — {c['project_name']} ({c['quantity']}t)",
            key="list_credit_sel",
        )
        if st.button("📋 List for Trade", use_container_width=True):
            if list_credit_for_trade(sel_list["id"]):
                st.success(f"Credit {sel_list['serial_no']} is now listed on the marketplace!")
                st.rerun()
    else:
        st.info("No issued credits available to list.")

    st.markdown("---")
    st.markdown("### Buy Credits from Marketplace")
    listed = get_all_listed_credits()
    available = [c for c in listed if c["user_id"] != user_id]
    if available:
        sel_buy = st.selectbox(
            "Available credits",
            available,
            format_func=lambda c: f"{c['serial_no']} — {c['project_name']} ({c['quantity']}t, ${current_price:.2f}/t)",
            key="buy_credit_sel",
        )
        buy_price = st.number_input("Offer price ($/tonne)", min_value=1.0, value=current_price, step=0.5)
        total_cost = sel_buy["quantity"] * buy_price
        st.write(f"Total cost: **${total_cost:.2f}**")
        bal = get_eco_balance(user_id)["balance"]
        if total_cost > bal:
            st.warning(f"Insufficient balance. You have ${bal:.2f} but need ${total_cost:.2f}.")
        if st.button("🛒 Buy Credit", use_container_width=True):
            if total_cost > bal:
                st.error("Not enough eco points.")
            else:
                if execute_credit_trade(sel_buy["id"], sel_buy["user_id"], user_id, sel_buy["quantity"], buy_price):
                    update_eco_balance(user_id, -total_cost)
                    update_eco_balance(sel_buy["user_id"], total_cost)
                    st.success(f"Purchased credit {sel_buy['serial_no']} for ${total_cost:.2f}!")
                    st.rerun()
    else:
        st.info("No credits listed for sale right now.")

    st.markdown("---")
    st.markdown("### Trade History")
    trades = get_credit_trades(user_id)
    if trades:
        df_trades = pd.DataFrame(trades)
        st.dataframe(df_trades[["created_at", "quantity", "price_per_tonne", "total_value", "status"]])
    else:
        st.info("No trades yet.")

# ─── TAB 4: Learning Insights ─────────────────────────────────────────────────
with tab4:
    st.markdown("### 📚 Carbon Market Education")

    with st.expander("What are Carbon Credits?"):
        st.markdown("""
        A carbon credit is a tradable certificate representing **1 tonne of CO₂** that has been
        reduced, avoided, or removed from the atmosphere. Credits are generated by projects like
        reforestation, renewable energy, or clean cookstoves.

        **Key concepts:**
        - **Issuance:** Credits are created when a verified project reduces emissions
        - **Trading:** Credits can be bought and sold on carbon markets
        - **Retirement:** When a credit is used to offset emissions, it is permanently retired
        """)

    with st.expander("How Does the Simulation Work?"):
        st.markdown("""
        This simulation models a simplified carbon market:

        1. **Market price** fluctuates based on random supply/demand shocks
        2. **Earning credits** — complete assessments and challenges to earn credits
        3. **Trading** — list your credits for sale or buy from other users
        4. **Retiring** — permanently remove credits from circulation to offset your footprint
        5. **Eco points** — simulated currency used to buy credits on the marketplace
        """)

    with st.expander("Why Do Carbon Prices Vary?"):
        st.markdown("""
        Carbon prices vary based on:
        - **Project type:** Technology-based removals (DAC) cost more than nature-based solutions
        - **Co-benefits:** Projects with additional benefits (biodiversity, jobs) may command premiums
        - **Market dynamics:** Supply and demand affect prices just like any commodity
        - **Quality:** High-quality credits with strong verification cost more
        """)

    st.markdown("---")
    st.markdown("### Your Personalized Insights")
    insights = get_learning_insights(summary, market, len(trades))
    for ins in insights:
        st.markdown(f"- {ins}")

    trend = estimate_credit_price_trend(get_price_history())
    trend_icons = {"rising": "📈", "falling": "📉", "stable": "➖"}
    st.metric("Market Trend", f"{trend_icons.get(trend, '➖')} {trend.title()}")

    total_credits_held = summary.get("total_tonnes", 0)
    if total_credits_held > 0:
        estimated_value = current_price * total_credits_held
        st.metric("Estimated Portfolio Value", f"${estimated_value:.2f}")

    st.markdown("---")
    st.markdown("#### 💡 Did You Know?")
    facts = [
        "The world's largest carbon market is the EU Emissions Trading System (EU ETS).",
        "A single tree can absorb about 20 kg of CO₂ per year.",
        "Voluntary carbon markets could be worth $50 billion by 2030.",
        "Mangroves store 3-5x more carbon per hectare than tropical forests.",
        "Carbon credits fund projects that wouldn't happen without carbon finance.",
    ]
    st.info(random.choice(facts))

    eco_bal = get_eco_balance(user_id)["balance"]
    if eco_bal >= 500:
        st.markdown("#### 🎯 Suggested Next Steps")
        recs = []
        if summary.get("total_tonnes", 0) == 0:
            recs.append("Browse the available projects and purchase your first carbon credit.")
        if summary.get("retired", 0) == 0 and summary.get("total_tonnes", 0) > 0:
            recs.append("Try retiring a credit to see how permanent offsetting works.")
        if summary.get("listed", 0) == 0 and summary.get("issued", 0) > 0:
            recs.append("List one of your credits for trade to experience the marketplace.")
        if eco_bal < 100:
            recs.append("Earn more eco points through the daily bonus or by completing assessments.")
        for r in recs:
            st.markdown(f"- {r}")
