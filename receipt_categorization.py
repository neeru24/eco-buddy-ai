"""
AI Receipt Categorization Module (#349).

Provides receipt item detection, AI product classification into emission categories,
carbon emission estimation, and manual correction utilities for shopping receipt analysis.
"""

import re
from typing import List, Dict, Any, Tuple
import pandas as pd
import streamlit as st


EMISSION_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "Plant-based & Produce": {"factor": 0.25, "icon": "🥦", "tip": "Great choice! Plant-based items have a minimal carbon footprint."},
    "Food & Groceries": {"factor": 0.45, "icon": "🛒", "tip": "Standard grocery items. Consider buying locally sourced produce."},
    "Dairy & Meat": {"factor": 1.20, "icon": "🥩", "tip": "High impact item. Replacing meat/dairy days reduces emissions significantly."},
    "Apparel & Clothing": {"factor": 0.85, "icon": "👕", "tip": "Fast fashion impacts. Look for sustainable or thrift alternatives."},
    "Electronics & Gadgets": {"factor": 1.50, "icon": "📱", "tip": "High embodied carbon. Consider refurbished devices when possible."},
    "Transport & Fuel": {"factor": 2.30, "icon": "⛽", "tip": "Fuel usage creates direct emissions. Try carpooling or public transport."},
    "Home & Utilities": {"factor": 0.60, "icon": "🏡", "tip": "Home goods. Opt for energy-efficient or durable products."},
    "Services & Others": {"factor": 0.15, "icon": "🏷️", "tip": "Low carbon intensity service item."},
}


CATEGORY_KEYWORD_MAP = [
    (r"milk|cheese|yogurt|beef|chicken|pork|meat|steak|bacon|butter", "Dairy & Meat"),
    (r"apple|banana|berry|salad|vegetable|fruit|bread|rice|oats|tofu|tomato|spinach", "Plant-based & Produce"),
    (r"gas|fuel|petrol|diesel|oil|ev charge|parking", "Transport & Fuel"),
    (r"shirt|pants|jacket|shoes|dress|socks|jeans|sweater|apparel", "Apparel & Clothing"),
    (r"phone|laptop|charger|cable|tv|usb|headphone|battery|tech", "Electronics & Gadgets"),
    (r"detergent|soap|towel|cleaner|paper|bulb|lamp|furniture", "Home & Utilities"),
]


def classify_product_name(product_name: str) -> str:
    """
    Classify a product name into an emission category using rule-based AI pattern matching.
    """
    clean_name = product_name.lower().strip()
    for pattern, category in CATEGORY_KEYWORD_MAP:
        if re.search(pattern, clean_name):
            return category
    return "Food & Groceries"


def parse_receipt_text(receipt_text: str) -> List[Dict[str, Any]]:
    """
    Detect purchased items and prices from raw receipt text.
    
    Args:
        receipt_text: Raw string content of receipt.
        
    Returns:
        List[Dict[str, Any]]: Detected items with name, price, quantity, and predicted category.
    """
    items = []
    lines = receipt_text.strip().split("\n")
    
    price_pattern = re.compile(r"([A-Za-z0-9\s\-\.\'\&]+?)\s+\$?(\d+\.\d{2})")
    
    for line in lines:
        line = line.strip()
        if not line or any(k in line.lower() for k in ["total", "subtotal", "tax", "change", "cash", "visa", "mastercard"]):
            continue
            
        match = price_pattern.search(line)
        if match:
            item_name = match.group(1).strip()
            price = float(match.group(2))
            if price > 0 and len(item_name) > 1:
                category = classify_product_name(item_name)
                items.append({
                    "name": item_name,
                    "price": price,
                    "quantity": 1,
                    "category": category,
                })
                
    if not items and receipt_text.strip():
        # Fallback parsing for single item or comma separated line
        for line in lines[:5]:
            category = classify_product_name(line)
            items.append({
                "name": line[:30],
                "price": 10.0,
                "quantity": 1,
                "category": category,
            })
            
    return items


def estimate_item_emissions(item: Dict[str, Any]) -> float:
    """
    Estimate emissions (kg CO2) for a single receipt item.
    """
    category = item.get("category", "Food & Groceries")
    price = item.get("price", 0.0)
    qty = item.get("quantity", 1)
    
    factor = EMISSION_CATEGORIES.get(category, {}).get("factor", 0.45)
    return round(price * qty * factor, 2)


def process_receipt(receipt_text: str) -> Dict[str, Any]:
    """
    Process full receipt text: parse, categorize, estimate emissions, and build summary.
    """
    items = parse_receipt_text(receipt_text)
    
    total_price = 0.0
    total_emissions = 0.0
    category_breakdown: Dict[str, float] = {}
    
    for item in items:
        emissions = estimate_item_emissions(item)
        item["emissions"] = emissions
        total_price += item["price"] * item["quantity"]
        total_emissions += emissions
        
        cat = item["category"]
        category_breakdown[cat] = category_breakdown.get(cat, 0.0) + emissions
        
    return {
        "items": items,
        "total_price": round(total_price, 2),
        "total_emissions": round(total_emissions, 2),
        "category_breakdown": category_breakdown,
    }


def update_manual_corrections(
    items: List[Dict[str, Any]], index: int, new_category: str, new_price: float, new_qty: int = 1
) -> List[Dict[str, Any]]:
    """
    Apply user manual corrections to an item and recalculate its emissions.
    """
    updated = [dict(it) for it in items]
    if 0 <= index < len(updated):
        updated[index]["category"] = new_category
        updated[index]["price"] = new_price
        updated[index]["quantity"] = new_qty
        updated[index]["emissions"] = estimate_item_emissions(updated[index])
    return updated


def render_receipt_categorization() -> None:
    """
    Render the Streamlit UI component for AI Receipt Categorization.
    """
    st.title("🧾 AI Receipt Categorization")
    st.markdown(
        "Upload a shopping receipt or paste receipt text to automatically classify products "
        "into carbon emission categories and calculate environmental footprint."
    )
    
    sample_text = (
        "Organic Milk $4.99\n"
        "Fresh Spinach $2.99\n"
        "Beef Steak $14.50\n"
        "Cotton T-Shirt $18.00\n"
        "Gasoline Fuel $32.50\n"
        "AA Batteries $8.99"
    )
    
    input_mode = st.radio("Input Method", ["Paste Receipt Text", "Upload Receipt File"])
    receipt_input = ""
    
    if input_mode == "Paste Receipt Text":
        receipt_input = st.text_area("Receipt Raw Content", value=sample_text, height=180)
    else:
        uploaded_file = st.file_uploader("Upload Receipt Image/Text", type=["txt", "png", "jpg"])
        if uploaded_file:
            receipt_input = uploaded_file.getvalue().decode("utf-8", errors="ignore")
            
    if receipt_input:
        res = process_receipt(receipt_input)
        
        st.subheader("🛒 Detected Items & AI Categorization")
        st.info("You can make manual corrections to categories, prices, or quantities below:")
        
        items = res["items"]
        if "corrected_items" not in st.session_state or st.button("Reset Detections"):
            st.session_state.corrected_items = items
            
        current_items = st.session_state.corrected_items
        
        # Display editable items grid
        for i, item in enumerate(current_items):
            c1, c2, c3, c4 = st.columns([3, 3, 2, 2])
            with c1:
                st.text_input(f"Item #{i+1}", value=item["name"], key=f"name_{i}", disabled=True)
            with c2:
                new_cat = st.selectbox(
                    f"Category #{i+1}",
                    options=list(EMISSION_CATEGORIES.keys()),
                    index=list(EMISSION_CATEGORIES.keys()).index(item["category"]),
                    key=f"cat_{i}"
                )
            with c3:
                new_price = st.number_input(
                    f"Price (${i+1})",
                    value=float(item["price"]),
                    min_value=0.0,
                    step=0.5,
                    key=f"price_{i}"
                )
            with c4:
                em = estimate_item_emissions({"category": new_cat, "price": new_price, "quantity": item["quantity"]})
                st.metric(f"Emissions", f"{em:.2f} kg")
                
            current_items[i]["category"] = new_cat
            current_items[i]["price"] = new_price
            current_items[i]["emissions"] = em
            
        st.session_state.corrected_items = current_items
        
        # Summary & Breakdown
        tot_emissions = sum(it["emissions"] for it in current_items)
        tot_price = sum(it["price"] * it.get("quantity", 1) for it in current_items)
        
        st.divider()
        col1, col2 = st.columns(2)
        col1.metric("Total Receipt Amount", f"${tot_price:.2f}")
        col2.metric("Estimated Total Footprint", f"{tot_emissions:.2f} kg CO2")
        
        # Category breakdown chart
        st.subheader("📊 Emission Breakdown by Category")
        df_breakdown = pd.DataFrame([
            {"Category": cat, "Emissions (kg CO2)": sum(it["emissions"] for it in current_items if it["category"] == cat)}
            for cat in set(it["category"] for it in current_items)
        ])
        st.bar_chart(df_breakdown.set_index("Category"))
