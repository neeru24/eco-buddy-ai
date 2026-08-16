import streamlit as st
import pandas as pd
import plotly.express as px
from food_scanner import FOOD_EMISSION_FACTORS, CATEGORIES, calculate_food_footprint, get_comparison_context
from database import save_food_scan, get_food_scans
from styles.theme import apply_theme

apply_theme()

st.markdown("<div class='section-header'>🔬 Food Carbon Scanner</div>", unsafe_allow_html=True)
st.markdown("Build a meal and see its carbon footprint — item by item.")

st.markdown("---")

if "food_items" not in st.session_state:
    st.session_state.food_items = {}

meal_name = st.text_input("Meal name (optional)", placeholder="e.g., Breakfast, Lunch, Dinner")

st.markdown("### 🥘 Select Food Items")

tab_map = {c: c for c in CATEGORIES}
tabs = st.tabs([f"{c.split()[0]}" for c in CATEGORIES])
for tab_idx, cat in enumerate(CATEGORIES):
    with tabs[tab_idx]:
        items_in_cat = {k: v for k, v in FOOD_EMISSION_FACTORS.items() if v["category"] == cat}
        cols = st.columns(2)
        for i, (item_name, info) in enumerate(sorted(items_in_cat.items())):
            with cols[i % 2]:
                st.caption(f"**{item_name}** — {info['co2_kg']} kg CO₂/100g, serving ≈ {info['serving_g']}g")
                servings = st.number_input(
                    f"Servings of {item_name}",
                    min_value=0, max_value=20, value=0, step=1,
                    key=f"food_{hash(item_name) % 2**31}"
                )
                if servings > 0:
                    st.session_state.food_items[item_name] = servings
                elif item_name in st.session_state.food_items:
                    del st.session_state.food_items[item_name]

st.markdown("---")

col_scan, col_clear = st.columns([3, 1])
with col_scan:
    scan_btn = st.button("🔬 Scan Meal Carbon Footprint", type="primary", use_container_width=True, disabled=len(st.session_state.food_items) == 0)
with col_clear:
    if st.button("Clear All", use_container_width=True):
        st.session_state.food_items = {}
        st.rerun()

if scan_btn and st.session_state.food_items:
    with st.spinner("Scanning meal carbon footprint..."):
        result = calculate_food_footprint(st.session_state.food_items)
        save_food_scan(1, meal_name or "Untitled Meal", st.session_state.food_items, result["total_co2"])
        st.session_state.food_scan_result = result

if "food_scan_result" in st.session_state:
    r = st.session_state.food_scan_result
    st.success(f"✅ Scan complete! This meal has a carbon footprint of **{r['total_co2']:.2f} kg CO₂**.")

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Total CO₂", f"{r['total_co2']:.2f} kg")
    m2.metric("Items Scanned", f"{len(r['breakdown'])}")
    m3.metric("Comparison", f"≈ {get_comparison_context(r['total_co2'])[0]['equivalent']} km driven")

    st.markdown("### 📊 Breakdown by Item")
    if r["breakdown"]:
        df_bd = pd.DataFrame(r["breakdown"])
        fig = px.bar(df_bd, x="item", y="co2_kg", color="category", title="CO₂ per Item (kg)", text_auto=".2f", color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### ♻️ Comparison Context")
    comparisons = get_comparison_context(r["total_co2"])
    for cmp in comparisons:
        st.markdown(f"- This meal's CO₂ is equivalent to **{cmp['equivalent']}x** {cmp['label']}")

    st.markdown("---")
    st.markdown("### 📋 Scan History")
    scans = get_food_scans(1)
    if scans:
        df_scans = pd.DataFrame(scans)
        df_scans["created_at"] = pd.to_datetime(df_scans["created_at"])
        df_scans["date"] = df_scans["created_at"].dt.date
        st.dataframe(
            df_scans[["date", "meal_name", "total_co2_kg"]].rename(columns={
                "date": "Date", "meal_name": "Meal", "total_co2_kg": "CO₂ (kg)"
            }),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("No scan history yet.")

st.markdown("---")
st.markdown("### 💡 Tips to Reduce Meal Carbon Footprint")
st.markdown("""
- **Choose plant-based proteins** — tofu, lentils, and beans have 10–50x lower emissions than beef
- **Go local & seasonal** — reduce transport emissions from imported produce
- **Reduce food waste** — only cook what you'll eat
- **Opt for whole grains** — brown rice and oats have lower footprints than processed alternatives
""")
