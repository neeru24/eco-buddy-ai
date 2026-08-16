"""One-shot migration script from the single-file app to the pages/ layout.

This has already been run: `styles/theme.py` and the pages it generates are
in the repository. It is kept for the record, not for reuse — the line
indices below refer to a version of `app.py` that no longer exists.

The body is guarded because it is destructive. It rewrites `app.py`,
overwrites `styles/theme.py` and creates four page files, all as a side
effect of *importing* the module. Anything that imports every module in the
repository — a test sweep, a linter, an editor indexing the project — would
silently rewrite the source tree.
"""

import os


def main():

    with open("app.py", "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 1. Extract CSS
    css_start = -1
    css_end = -1
    for i, line in enumerate(lines):
        if line.strip() == "<style>":
            css_start = i
        if line.strip() == "</style>":
            css_end = i
            break

    if css_start != -1 and css_end != -1:
        css_content = "".join(lines[css_start:css_end+1])
        theme_py_content = f"""import streamlit as st\n\ndef apply_theme():\n    st.markdown(\"\"\"\n{css_content}\n\"\"\", unsafe_allow_html=True)\n"""
        os.makedirs("styles", exist_ok=True)
        with open("styles/theme.py", "w", encoding="utf-8") as f:
            f.write(theme_py_content)

    # 2. Extract tab contents
    tab1_idx = 939 # The LAST with tab1: is at index 939 (line 940)
    tab2_idx = 1531
    tab3_idx = 1665
    tab4_idx = 1730
    else_idx = 1835 # The else: at the end is at index 1835 (line 1836)

    def get_block(start, end):
        return "".join(line[4:] if line.startswith("    ") else line for line in lines[start+1:end])

    imports = """import streamlit as st
    import pandas as pd
    import time
    from database import *
    from emissions import *
    from recommendations import *
    from ocr_utils import *
    import os
    import tempfile
    import uuid
    import plotly.graph_objects as go
    import plotly.express as px
    from report import generate_pdf
    import gamification as gf
    from marketplace import *
    import energy_audit as ea

    from styles.theme import apply_theme
    apply_theme()

    """

    os.makedirs("pages", exist_ok=True)

    # Page 1: Rebuilt explicitly to avoid the bad merge conflicts
    page1_content = imports + """st.markdown("<div class='section-header'>📝 Your Lifestyle Profile</div>", unsafe_allow_html=True)
    st.markdown("### Region Setting")
    region = st.selectbox("Select Your Region for API Emissions Factor", ["Global", "US", "UK", "EU"])
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div style='display: flex; align-items: center; gap: 8px; margin-bottom: 16px;'><span style='font-size: 24px;'>🚗</span><span style='font-size: 18px; font-weight: 700; color: #000;'>Transportation</span></div>", unsafe_allow_html=True)
        transport = st.selectbox("Primary Transport", ["Car", "Public Transport", "Bike", "Walking"])
        distance = st.number_input("Daily Distance (km)", min_value=0.0, value=10.0, step=1.0)

    with col2:
        st.markdown("<div style='display: flex; align-items: center; gap: 8px; margin-bottom: 16px;'><span style='font-size: 24px;'>⚡</span><span style='font-size: 18px; font-weight: 700; color: #000;'>Energy & Diet</span></div>", unsafe_allow_html=True)
        uploaded_bill = st.file_uploader("Upload Utility Bill (PDF/Image)", type=["pdf", "png", "jpg", "jpeg"])
        if uploaded_bill is not None:
            # Same 10 MB cap as the Carbon Footprint page. Surfaces the
            # rejection in the UI immediately rather than letting the OCR
            # worker crash inside pdfplumber on a multi-hundred-MB dump.
            try:
                _bill_size = getattr(uploaded_bill, "size", None) or len(uploaded_bill.getvalue())
            except Exception:
                _bill_size = 0
            if _bill_size and _bill_size > 10 * 1024 * 1024:
                st.warning(
                    f"That bill is {_bill_size / (1024*1024):.1f} MB. "
                    "Please upload a PDF or image under 10 MB."
                )
            elif st.button("Extract Energy Usage"):
                progress_bar = st.progress(0.0, text="Starting…")
                with st.spinner("Extracting data from bill..."):
                    extracted_text = extract_text_from_file(
                        uploaded_bill,
                        on_progress=lambda done, total: progress_bar.progress(
                            (done / total) if total else 1.0,
                            text=f"Reading page {done}/{total}",
                        ),
                        notify=lambda message, level: (
                            st.warning(message) if level == "warning" else st.info(message)
                        ),
                    )
                    progress_bar.empty()
                    parsed_val = parse_energy_consumption(extracted_text)
                    if parsed_val is not None:
                        st.session_state.extracted_kwh = float(parsed_val)
                        st.success(f"Extracted {parsed_val} kWh from bill!")
                    else:
                        st.warning("Could not extract energy consumption. Please enter manually.")

        electricity = st.number_input("Monthly Electricity (kWh)", min_value=0.0, value=float(st.session_state.get('extracted_kwh', 0.0)), step=10.0)
        diet = st.selectbox("Diet Type", ["Vegetarian", "Non-Vegetarian"])

    with col3:
        st.markdown("<div style='display: flex; align-items: center; gap: 8px; margin-bottom: 16px;'><span style='font-size: 24px;'>✈️</span><span style='font-size: 18px; font-weight: 700; color: #000;'>Travel</span></div>", unsafe_allow_html=True)
        flights = st.number_input("Annual Flights", min_value=0, value=0, step=1)
        st.info("💡 How many long-distance flights per year?")

    col_btn1, col_btn2, col_btn3 = st.columns([1, 1.5, 1])
    with col_btn1:
        reset_btn = st.button("🔄 Reset Assessment", use_container_width=True)
        if reset_btn:
            st.session_state.pop("extracted_kwh", None)
            st.session_state.pop("analysis", None)
            st.success("✅ Assessment form has been reset.")
            st.rerun()

    with col_btn2:
        st.caption("✔ All input fields are validated before analysis.")
        analyze_btn = st.button("🌿 Analyze My Impact", use_container_width=True)

    if analyze_btn:
        with st.spinner("🌍 Analyzing your carbon footprint..."):
            total, contributors = calculate_footprint(transport, distance, electricity, diet, flights, region)
        eco_score = calculate_eco_score(total, contributors)
        insight, recommendations = generate_recommendations(transport, electricity, diet, flights, contributors)
        save_assessment(transport, distance, electricity, diet, flights, total, eco_score)
        st.session_state.analysis = {
            "transport": transport, "distance": distance, "electricity": electricity,
            "diet": diet, "flights": flights, "total": total, "eco_score": eco_score,
            "contributors": contributors, "insight": insight, "recommendations": recommendations,
        }

    if "analysis" in st.session_state:
        data = st.session_state.analysis
        st.success("✅ Analysis completed!")
        st.markdown("---")
        st.markdown("### 👤 Your Inputs")
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**🚗 Transport:** {data['transport']}")
            st.write(f"**📍 Daily Distance:** {data['distance']} km")
            st.write(f"**⚡ Electricity:** {data['electricity']} kWh")
        with c2:
            st.write(f"**🥗 Diet:** {data['diet']}")
            st.write(f"**✈️ Annual Flights:** {data['flights']}")
        st.markdown("---")
        st.markdown("<div class='section-header'>📊 Your Carbon Footprint Analysis</div>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🌍 Total Footprint", f"{data['total']:.2f} kg CO₂")
        with col2:
            st.metric("🌱 Eco Score", f"{data['eco_score']}/100")

        st.markdown("### 💡 AI Insight")
        st.info(data["insight"])
        st.markdown("### 🌱 Recommendations")
        for rec in data["recommendations"]:
            st.success(rec)
    else:
    """ + "".join(line for line in lines[else_idx+1:])

    with open("pages/1_🌍_Carbon_Footprint.py", "w", encoding="utf-8") as f:
        f.write(page1_content)

    with open("pages/2_⚡_Home_Energy_Audit.py", "w", encoding="utf-8") as f:
        f.write(imports + get_block(tab2_idx, tab3_idx))

    with open("pages/3_🎮_Gamification.py", "w", encoding="utf-8") as f:
        f.write(imports + get_block(tab3_idx, tab4_idx))

    with open("pages/4_🗺️_Route_Planning.py", "w", encoding="utf-8") as f:
        f.write(imports + get_block(tab4_idx, else_idx))

    # 3. New app.py
    app_head = lines[:78] # up to the start of CSS block

    app_new = "".join(app_head) + """
    from styles.theme import apply_theme
    apply_theme()

    st.markdown("<div class='title'>🌱 EcoBuddy AI+</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Your Personal AI-Powered Carbon Footprint Tracker & Eco Assistant</div>", unsafe_allow_html=True)

    st.info("👈 Please select a module from the sidebar to get started!")
    """

    with open("app.py", "w", encoding="utf-8") as f:
        f.write(app_new)



if __name__ == "__main__":
    main()
