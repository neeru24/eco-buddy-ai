import streamlit as st
import pandas as pd
from lifestyle_analysis import (
    SPACE_TYPES, analyze_image, save_analysis, get_analysis_history,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()
apply_theme()

st.markdown("<div class='section-header'>📷 AI Image-Based Lifestyle Analysis</div>", unsafe_allow_html=True)
st.markdown(
    "Upload a photo of a room, kitchen, or workspace and get AI-powered "
    "sustainability suggestions — energy-hogging items detected, savings "
    "estimated, and recommendations generated."
)

st.markdown("---")

space_type = st.selectbox(
    "What kind of space is in the photo?",
    list(SPACE_TYPES.keys()),
    help=SPACE_TYPES[list(SPACE_TYPES.keys())[0]]["hint"],
)
hint = SPACE_TYPES[space_type]["hint"]
st.caption(f"💡 Analysis hint: {hint}")

uploaded_file = st.file_uploader(
    "Upload a photo (JPG/PNG)",
    type=["jpg", "jpeg", "png"],
)

if uploaded_file:
    st.image(uploaded_file, caption="Uploaded Photo", use_container_width=True)

    if st.button("🔍 Analyze Lifestyle", type="primary", use_container_width=True):
        with st.spinner("Analyzing your space..."):
            result = analyze_image(uploaded_file, space_type)
        save_analysis(
            user_id,
            space_type,
            result["items"],
            result["annual_co2_kg"],
            result["savings_co2_kg"],
        )
        st.session_state.lifestyle_result = result

st.markdown("---")

if "lifestyle_result" in st.session_state:
    r = st.session_state.lifestyle_result
    st.success("✅ Analysis complete!")

    st.markdown(f"### {r['icon']} Detected Energy-Consuming Items")
    if r["items"]:
        items_df = pd.DataFrame([
            {
                "Item": i["name"],
                "Power (W)": i.get("energy_w", 0),
                "Improvement": i.get("improvement", ""),
                "Recommendation": i.get("recommendation", ""),
            }
            for i in r["items"]
        ])
        st.dataframe(items_df, use_container_width=True, hide_index=True)

    if r["ocr_text"]:
        with st.expander("🔤 Text detected in image"):
            st.write(r["ocr_text"])

    st.markdown("### 📊 Estimated Impact")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Estimated Power", f"{r['total_watts']} W")
    m2.metric("Annual Energy", f"{r['annual_kwh']:,} kWh")
    m3.metric("Annual CO₂", f"{r['annual_co2_kg']:,} kg")
    m4.metric("Potential Savings", f"{r['savings_co2_kg']} kg CO₂/yr")

    st.markdown(f"**Potential improvement:** up to **{r['potential_savings_pct']}%** "
                f"energy savings ({r['savings_kwh']} kWh / {r['savings_co2_kg']} kg CO₂ per year) "
                "by applying the recommendations above.")

    st.markdown("### 💡 Recommendations")
    for i in r["items"]:
        st.markdown(f"- **{i['name']}:** {i.get('recommendation', '')}")

st.markdown("---")
st.markdown("### 📜 Analysis History")

history = get_analysis_history(user_id)
if history:
    rows = []
    for h in history:
        rows.append({
            "Date": (h["created_at"] or "")[:10],
            "Space": h["space_type"],
            "Annual CO₂ (kg)": h["annual_co2_kg"],
            "Potential Savings (kg CO₂/yr)": h["savings_co2_kg"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("No analyses yet — upload a photo above to get started.")
