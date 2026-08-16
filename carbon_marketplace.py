import random
import math
from datetime import datetime
from typing import Any


PROJECTS = [
    {"id": "renewable-wind", "name": "Wind Farm – Gujarat", "category": "Renewable Energy", "region": "India", "cost_per_tonne": 18.0, "co_benefits": "Jobs, clean power"},
    {"id": "renewable-solar", "name": "Solar Array – Rajasthan", "category": "Renewable Energy", "region": "India", "cost_per_tonne": 22.0, "co_benefits": "Rural electrification"},
    {"id": "forestry", "name": "Reforestation – Western Ghats", "category": "Forestry", "region": "India", "cost_per_tonne": 12.0, "co_benefits": "Biodiversity, water"},
    {"id": "clean-cookstoves", "name": "Clean Cookstoves – Sub-Saharan Africa", "category": "Energy Efficiency", "region": "Africa", "cost_per_tonne": 8.0, "co_benefits": "Health, reduced deforestation"},
    {"id": "methane-capture", "name": "Methane Capture – Landfill Gas", "category": "Waste Management", "region": "Global", "cost_per_tonne": 15.0, "co_benefits": "Local air quality"},
    {"id": "blue-carbon", "name": "Blue Carbon – Mangrove Restoration", "category": "Ocean-Based", "region": "Southeast Asia", "cost_per_tonne": 25.0, "co_benefits": "Coastal protection, fisheries"},
    {"id": "carbon-removal", "name": "Direct Air Capture – DAC Facility", "category": "Technology", "region": "North America", "cost_per_tonne": 45.0, "co_benefits": "Permanent removal"},
]

CREDIT_PRICE_HISTORY = []


def simulate_market_tick(current_price: float, volatility: float = 0.05) -> dict[str, Any]:
    shock = random.gauss(0, volatility)
    new_price = current_price * (1 + shock)
    new_price = max(5.0, min(200.0, new_price))

    supply_response = random.uniform(-0.02, 0.03)
    demand_response = random.uniform(-0.03, 0.05)

    CREDIT_PRICE_HISTORY.append({
        "timestamp": datetime.now().isoformat(),
        "price": round(new_price, 2),
        "supply_shift": round(supply_response * 100, 1),
        "demand_shift": round(demand_response * 100, 1),
    })
    if len(CREDIT_PRICE_HISTORY) > 100:
        CREDIT_PRICE_HISTORY.pop(0)

    return {
        "price": round(new_price, 2),
        "supply_shift": round(supply_response * 100, 1),
        "demand_shift": round(demand_response * 100, 1),
    }


def get_price_history() -> list[dict[str, Any]]:
    return CREDIT_PRICE_HISTORY


def calculate_credit_value(price_per_tonne: float, quantity: float) -> float:
    return round(price_per_tonne * quantity, 2)


def get_learning_insights(
    portfolio_summary: dict[str, Any],
    market_state: dict[str, Any],
    trades_count: int,
) -> list[str]:
    insights = []
    total_credits = portfolio_summary.get("total_tonnes", 0)
    retired = portfolio_summary.get("retired", 0)

    if total_credits == 0:
        insights.append("You haven't earned any carbon credits yet. Complete assessments and challenges to earn your first credit!")
    else:
        insights.append(f"You hold {total_credits:.1f} tonnes of carbon credits across your portfolio.")
        if retired > 0:
            insights.append(f"You've retired {retired} credit(s) — permanently removing them from circulation to offset your footprint.")
        pct_traded = (portfolio_summary.get("traded", 0) / total_credits * 100) if total_credits > 0 else 0
        if pct_traded > 0:
            insights.append(f"{pct_traded:.0f}% of your credits have been traded on the marketplace, contributing to market liquidity.")

    if market_state:
        price = market_state.get("price_per_tonne", 25.0)
        insights.append(f"The current market price is ${price:.2f}/tonne. Prices fluctuate based on simulated supply and demand.")
        vol = market_state.get("volatility", 0.05)
        if vol > 0.08:
            insights.append("Market volatility is high — consider holding credits for long-term value rather than trading.")
        elif vol < 0.03:
            insights.append("Market is stable — good conditions for trading credits.")

    if trades_count > 0:
        insights.append(f"There have been {trades_count} trade(s) on the marketplace. Trading helps discover the fair price of carbon credits.")

    insights.append("Carbon credits represent 1 tonne of CO₂ reduced or removed. Retiring a credit means it can never be traded again.")
    return insights


def estimate_credit_price_trend(price_history: list[dict[str, Any]]) -> str:
    if len(price_history) < 5:
        return "stable"
    recent = price_history[-5:]
    prices = [p["price"] for p in recent]
    avg_first = sum(prices[:2]) / 2
    avg_last = sum(prices[-2:]) / 2
    change = ((avg_last - avg_first) / avg_first) * 100 if avg_first > 0 else 0
    if change > 5:
        return "rising"
    elif change < -5:
        return "falling"
    return "stable"
