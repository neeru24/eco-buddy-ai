import html
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from database import init_db, save_assessment, get_assessments
from emissions import calculate_footprint, calculate_eco_score
from recommendations import generate_recommendations


def h(text):
    return html.escape(str(text))


# -------------------------
# INIT
# -------------------------

init_db()

st.set_page_config(
    page_title="EcoBuddy",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -------------------------
# REFERENCE-INSPIRED ADVANCED STYLING
# -------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --sky: #b9d7f4;
        --sky-soft: #d9eafa;
        --field: #5f8f36;
        --leaf: #78a945;
        --moss: #2f5e32;
        --ink: #080b0a;
        --muted: #66736a;
        --paper: rgba(255, 255, 255, 0.76);
        --paper-strong: rgba(255, 255, 255, 0.92);
        --line: rgba(38, 64, 41, 0.12);
        --shadow: 0 24px 70px rgba(38, 67, 44, 0.18);
        --radius: 18px;
    }

    * {
        box-sizing: border-box;
    }

    html {
        scroll-behavior: smooth;
    }

    body,
    [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        color: var(--ink);
        background:
            linear-gradient(180deg, rgba(185, 215, 244, 0.74) 0%, rgba(244, 248, 240, 0.95) 48%, #f7faf3 100%),
            radial-gradient(circle at 14% 12%, rgba(255, 255, 255, 0.86), transparent 30%),
            linear-gradient(135deg, #d7ebff 0%, #f4f8e8 54%, #eaf5df 100%);
        min-height: 100vh;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    .block-container {
        max-width: 1280px;
        padding: 24px 32px 56px;
    }

    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.74);
        border-right: 1px solid var(--line);
        box-shadow: 18px 0 48px rgba(44, 72, 47, 0.08);
        backdrop-filter: blur(18px);
    }

    [data-testid="stSidebar"] * {
        color: var(--ink);
    }

    .title {
        margin: 8px 0 12px;
        color: var(--ink);
        font-size: clamp(46px, 6vw, 82px);
        line-height: 1;
        font-weight: 800;
        letter-spacing: 0;
        text-align: center;
        animation: fadeUp 700ms ease both;
    }

    .subtitle {
        max-width: 720px;
        margin: 0 auto 30px;
        color: var(--muted);
        font-size: 19px;
        line-height: 1.6;
        font-weight: 500;
        text-align: center;
        animation: fadeUp 800ms 80ms ease both;
    }

    .section-header {
        margin: 38px 0 18px;
        color: var(--ink);
        font-size: clamp(28px, 3vw, 42px);
        line-height: 1.08;
        font-weight: 800;
        letter-spacing: 0;
        animation: fadeUp 650ms ease both;
    }

    .section-header::after {
        content: '';
        display: block;
        width: 88px;
        height: 4px;
        margin-top: 14px;
        border-radius: 999px;
        background: linear-gradient(90deg, #030504, var(--leaf), rgba(120, 169, 69, 0));
    }

    .input-section,
    .card,
    .card-highlight,
    .metric-card {
        border: 1px solid var(--line);
        border-radius: var(--radius);
        background: linear-gradient(145deg, var(--paper-strong), rgba(255, 255, 255, 0.64));
        box-shadow: 0 18px 50px rgba(57, 86, 47, 0.12);
        backdrop-filter: blur(18px);
        position: relative;
        overflow: hidden;
        animation: fadeUp 700ms ease both;
        transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
    }

    .input-section {
        padding: 34px;
        margin-bottom: 24px;
    }

    .card,
    .card-highlight,
    .metric-card {
        padding: 26px;
        margin-bottom: 16px;
    }

    .metric-card::before,
    .card-highlight::before {
        content: '';
        position: absolute;
        inset: 0 0 auto 0;
        height: 5px;
        background: linear-gradient(90deg, #030504, var(--leaf), #b6d274);
    }

    .metric-card:hover,
    .card:hover,
    .card-highlight:hover {
        transform: translateY(-6px);
        border-color: rgba(95, 143, 54, 0.28);
        box-shadow: 0 26px 64px rgba(57, 86, 47, 0.17);
    }

    .card-highlight {
        background:
            linear-gradient(145deg, rgba(255, 255, 255, 0.94), rgba(232, 244, 216, 0.82)),
            linear-gradient(135deg, rgba(120, 169, 69, 0.12), transparent);
    }

    .badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 42px;
        padding: 0 20px;
        border-radius: 999px;
        border: 1px solid rgba(8, 11, 10, 0.08);
        background: #030504;
        color: #fff;
        box-shadow: 0 14px 30px rgba(0, 0, 0, 0.14);
        font-size: 14px;
        font-weight: 800;
        letter-spacing: 0;
    }

    .badge-champion {
        background: linear-gradient(135deg, #f4c760, #d8831e);
        color: #2c1804;
    }

    .badge-guardian {
        background: linear-gradient(135deg, #acd66f, #5f8f36);
        color: #0d1c0f;
    }

    .badge-learner {
        background: linear-gradient(135deg, #b9d7f4, #6aa0cf);
        color: #071927;
    }

    .badge-high {
        background: linear-gradient(135deg, #ff8e70, #d84b35);
        color: #2e0904;
    }

    .progress-bar {
        width: 100%;
        height: 12px;
        margin-top: 12px;
        border-radius: 999px;
        background: rgba(8, 11, 10, 0.08);
        overflow: hidden;
    }

    .progress-fill {
        height: 100%;
        border-radius: inherit;
        background: linear-gradient(90deg, #030504, var(--moss), var(--leaf));
        box-shadow: 0 0 20px rgba(95, 143, 54, 0.34);
        transition: width 600ms ease;
    }

    hr {
        height: 1px;
        margin: 32px 0;
        border: none;
        background: linear-gradient(90deg, transparent, rgba(8, 11, 10, 0.16), transparent);
    }

    .stTextInput > div > div > input,
    .stNumberInput input,
    .stSelectbox [data-baseweb="select"],
    .stTextArea textarea {
        min-height: 48px;
        border: 1px solid rgba(8, 11, 10, 0.12) !important;
        border-radius: 12px !important;
        background: rgba(255, 255, 255, 0.88) !important;
        color: var(--ink) !important;
        box-shadow: 0 12px 30px rgba(57, 86, 47, 0.08);
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput input:focus,
    .stTextArea textarea:focus {
        border-color: rgba(95, 143, 54, 0.55) !important;
        box-shadow: 0 0 0 4px rgba(120, 169, 69, 0.14) !important;
    }

    .stButton > button {
        min-height: 52px;
        padding: 0 28px !important;
        border: none !important;
        border-radius: 12px !important;
        background: #030504 !important;
        color: #fff !important;
        box-shadow: 0 16px 34px rgba(0, 0, 0, 0.2) !important;
        font-size: 15px !important;
        font-weight: 800 !important;
        letter-spacing: 0 !important;
        transition: transform 180ms ease, box-shadow 180ms ease, background 180ms ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        background: #101713 !important;
        box-shadow: 0 22px 44px rgba(0, 0, 0, 0.26) !important;
    }

    .stInfo,
    .stWarning,
    .stSuccess,
    .stError {
        border-radius: 14px !important;
        border: 1px solid var(--line) !important;
        box-shadow: 0 12px 30px rgba(57, 86, 47, 0.08);
    }

    .stInfo {
        background: rgba(185, 215, 244, 0.42) !important;
    }

    .stWarning {
        background: rgba(244, 199, 96, 0.24) !important;
    }

    .stSuccess {
        background: rgba(172, 214, 111, 0.26) !important;
    }

    /* DARK PREMIUM THEME OVERRIDES */
    :root {
        --sky: #8ec5ff;
        --sky-soft: #18273a;
        --field: #4ade80;
        --leaf: #58d27b;
        --moss: #86efac;
        --ink: #f8fafc;
        --muted: #a7b3c6;
        --paper: rgba(15, 23, 42, 0.76);
        --paper-strong: rgba(12, 18, 32, 0.92);
        --line: rgba(148, 163, 184, 0.18);
        --shadow: 0 24px 70px rgba(0, 0, 0, 0.38);
        --radius: 18px;
    }

    body,
    [data-testid="stAppViewContainer"] {
        color: var(--ink);
        background:
            radial-gradient(circle at 18% 8%, rgba(74, 222, 128, 0.22), transparent 28%),
            radial-gradient(circle at 84% 12%, rgba(96, 165, 250, 0.18), transparent 30%),
            linear-gradient(145deg, #030712 0%, #07130d 42%, #111827 100%) !important;
    }

    .block-container {
        padding-top: 28px;
    }

    [data-testid="stSidebar"] {
        background: rgba(3, 7, 18, 0.84);
        border-right: 1px solid var(--line);
        box-shadow: 18px 0 48px rgba(0, 0, 0, 0.26);
    }

    [data-testid="stSidebar"] * {
        color: var(--ink);
    }

    .title {
        color: var(--ink);
        text-shadow: 0 18px 48px rgba(74, 222, 128, 0.18);
    }

    .subtitle,
    .section-header {
        color: var(--ink);
    }

    .subtitle {
        color: var(--muted);
    }

    .input-section,
    .card,
    .card-highlight,
    .metric-card {
        background:
            linear-gradient(145deg, rgba(15, 23, 42, 0.94), rgba(17, 24, 39, 0.72)),
            linear-gradient(135deg, rgba(74, 222, 128, 0.08), transparent);
        border-color: var(--line);
        box-shadow: var(--shadow);
    }

    .card-highlight {
        background:
            linear-gradient(145deg, rgba(13, 36, 25, 0.92), rgba(12, 18, 32, 0.84)),
            linear-gradient(135deg, rgba(74, 222, 128, 0.14), transparent);
    }

    .metric-card::before,
    .card-highlight::before,
    .section-header::after {
        background: linear-gradient(90deg, #4ade80, #86efac, rgba(96, 165, 250, 0));
    }

    .progress-bar {
        background: rgba(148, 163, 184, 0.14);
    }

    .progress-fill {
        background: linear-gradient(90deg, #16a34a, #4ade80, #86efac);
    }

    .stTextInput > div > div > input,
    .stNumberInput input,
    .stSelectbox [data-baseweb="select"],
    .stTextArea textarea {
        background: #ffffff !important;
        border-color: rgba(148, 163, 184, 0.2) !important;
        color: #05070a !important;
        box-shadow: 0 14px 36px rgba(0, 0, 0, 0.18);
    }

    .stTextInput label,
    .stNumberInput label,
    .stSelectbox label,
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }

    .stSelectbox [data-baseweb="select"] *,
    .stNumberInput input,
    .stTextInput input,
    .stTextArea textarea {
        color: #05070a !important;
        -webkit-text-fill-color: #05070a !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #0b0f18, #111827) !important;
        border: 1px solid rgba(134, 239, 172, 0.28) !important;
        box-shadow: 0 18px 40px rgba(0, 0, 0, 0.32) !important;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #111827, #0f2a1a) !important;
        border-color: rgba(134, 239, 172, 0.55) !important;
    }

    .stInfo,
    .stWarning,
    .stSuccess,
    .stError {
        color: var(--ink) !important;
        background: rgba(15, 23, 42, 0.78) !important;
        border-color: var(--line) !important;
    }

    [style*="#d1d5db"],
    [style*="#9ca3af"],
    [style*="rgb(209, 213, 219)"],
    [style*="rgb(156, 163, 175)"] {
        color: var(--muted) !important;
    }

    [style*="#4ade80"],
    [style*="rgb(74, 222, 128)"] {
        color: var(--moss) !important;
    }

    [data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid var(--line);
        box-shadow: var(--shadow);
        background: #0f172a !important;
    }

    [data-testid="stDataFrame"] > div,
    [data-testid="stDataFrame"] iframe,
    [data-testid="stDataFrame"] [class*="stDataFrame"],
    [data-testid="stDataFrame"] [class*="dataframe"],
    [data-testid="stDataFrame"] [class*="glide"],
    [data-testid="stDataFrame"] [class*="table"] {
        background: #0f172a !important;
        color: #ffffff !important;
    }

    [data-testid="stDataFrame"] canvas {
        background: #0f172a !important;
    }

    [data-testid="stDataFrame"] button,
    [data-testid="stDataFrame"] [role="button"] {
        background: #111827 !important;
        color: #ffffff !important;
        border-color: rgba(134, 239, 172, 0.22) !important;
    }

    [data-testid="stDataFrame"] svg {
        color: #ffffff !important;
        fill: #ffffff !important;
    }

    [data-testid="stDataFrame"] [role="grid"],
    [data-testid="stDataFrame"] [role="row"],
    [data-testid="stDataFrame"] [role="columnheader"],
    [data-testid="stDataFrame"] [role="gridcell"] {
        background-color: #0f172a !important;
        color: #ffffff !important;
        border-color: rgba(148, 163, 184, 0.16) !important;
    }

    [data-testid="stDataFrame"] [role="columnheader"] {
        background-color: #07130d !important;
        color: #ffffff !important;
        font-weight: 800 !important;
    }

    .history-table-wrap {
        width: 100%;
        overflow-x: auto;
        border: 1px solid rgba(134, 239, 172, 0.24);
        border-radius: 16px;
        background: #0f172a;
        box-shadow: var(--shadow);
    }

    .history-table {
        width: 100%;
        border-collapse: collapse;
        background: #0f172a;
        color: #ffffff;
        font-size: 15px;
    }

    .history-table thead th {
        padding: 16px 18px;
        background: #07130d;
        color: #ffffff !important;
        border-bottom: 1px solid rgba(134, 239, 172, 0.3);
        font-weight: 800;
        text-align: left;
        white-space: nowrap;
    }

    .history-table tbody td {
        padding: 15px 18px;
        color: #ffffff !important;
        border-bottom: 1px solid rgba(148, 163, 184, 0.14);
        text-align: left;
    }

    .history-table tbody tr:nth-child(odd) {
        background: #0f172a;
    }

    .history-table tbody tr:nth-child(even) {
        background: #111827;
    }

    .history-table tbody tr:hover {
        background: rgba(34, 197, 94, 0.14);
    }

    @keyframes fadeUp {
        from {
            opacity: 0;
            transform: translateY(18px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @media (max-width: 760px) {
        .block-container {
            padding: 16px 14px 42px;
        }

        .input-section,
        .card,
        .card-highlight,
        .metric-card {
            padding: 22px;
        }
    }
</style>
""", unsafe_allow_html=True)


# -------------------------
# HEADER
# -------------------------
st.markdown("<div class='title'>🌱 EcoBuddy AI+</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Your Personal AI-Powered Carbon Footprint Tracker & Eco Assistant</div>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; margin-bottom: 32px;'>
    <div style='display: inline-flex; gap: 16px; padding: 12px 24px; background: rgba(34, 197, 94, 0.08); border-radius: 50px; border: 1px solid rgba(74, 222, 128, 0.2);'>
        <span style='color: #d1d5db; font-size: 13px; font-weight: 600;'>✨ Track • 📊 Analyze • 💡 Improve</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")


# -------------------------
# INPUTS SECTION
# -------------------------
st.markdown("<div class='section-header'>📝 Your Lifestyle Profile</div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 16px;'>
        <span style='font-size: 24px;'>🚗</span>
        <span style='font-size: 18px; font-weight: 700; color: #e5e7eb;'>Transportation</span>
    </div>
    """, unsafe_allow_html=True)
    transport = st.selectbox("Primary Transport", ["Car", "Public Transport", "Bike", "Walking"])
    distance = st.number_input("Daily Distance (km)", min_value=0.0, value=10.0, step=1.0)

with col2:
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 16px;'>
        <span style='font-size: 24px;'>⚡</span>
        <span style='font-size: 18px; font-weight: 700; color: #e5e7eb;'>Energy & Diet</span>
    </div>
    """, unsafe_allow_html=True)
    electricity = st.number_input("Monthly Electricity (kWh)", min_value=0.0, value=200.0, step=10.0)
    diet = st.selectbox("Diet Type", ["Vegetarian", "Non-Vegetarian"])

with col3:
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 16px;'>
        <span style='font-size: 24px;'>✈️</span>
        <span style='font-size: 18px; font-weight: 700; color: #e5e7eb;'>Travel</span>
    </div>
    """, unsafe_allow_html=True)
    flights = st.number_input("Annual Flights", min_value=0, value=0, step=1)
    st.info("💡 How many long-distance flights per year?")


# -------------------------
# PDF REPORT GENERATION
# -------------------------
def generate_pdf(total, eco_score, insight):
    file_name = "eco_report.pdf"
    doc = SimpleDocTemplate(file_name)
    styles = getSampleStyleSheet()

    content = [
        Paragraph("EcoBuddy AI Report", styles["Title"]),
        Paragraph(f"Carbon Footprint: {total:.2f} kg CO₂", styles["Normal"]),
        Paragraph(f"Eco Score: {eco_score}/100", styles["Normal"]),
        Paragraph("Key Insight:", styles["Heading2"]),
        Paragraph(insight, styles["Normal"])
    ]

    doc.build(content)
    return file_name


# -------------------------
# CALCULATE & ANALYZE
# -------------------------
col_btn1, col_btn2, col_btn3 = st.columns([1, 1.5, 1])
with col_btn2:
    analyze_btn = st.button("🌿 Analyze My Impact", use_container_width=True)

if analyze_btn:

    with st.spinner("🌍 Analyzing your carbon footprint..."):
        total, contributors = calculate_footprint(
            transport, distance, electricity, diet, flights
        )

    eco_score = calculate_eco_score(total)

    insight, recommendations = generate_recommendations(
        transport, electricity, diet, flights, contributors
    )

    save_assessment(
        transport, distance, electricity, diet, flights, total, eco_score
    )

    st.success("✅ Analysis completed!")

    st.markdown("---")

    # -------------------------
    # RESULTS DASHBOARD
    # -------------------------
    st.markdown("<div class='section-header'>📊 Your Carbon Footprint Analysis</div>", unsafe_allow_html=True)

    # Top metrics row
    met1, met2, met3, met4 = st.columns(4)
    
    with met1:
        st.markdown("""
        <div class='metric-card'>
            <div style='font-size: 14px; color: #d1d5db; margin-bottom: 8px;'>🌍 Total Footprint</div>
            <div style='font-size: 36px; font-weight: 900; color: #4ade80;'>{:.0f}</div>
            <div style='font-size: 12px; color: #9ca3af;'>kg CO₂/year</div>
        </div>
        """.format(total), unsafe_allow_html=True)
    
    with met2:
        st.markdown("""
        <div class='metric-card'>
            <div style='font-size: 14px; color: #d1d5db; margin-bottom: 8px;'>🏆 Eco Score</div>
            <div style='font-size: 36px; font-weight: 900; color: #4ade80;'>{}</div>
            <div style='font-size: 12px; color: #9ca3af;'>out of 100</div>
        </div>
        """.format(eco_score), unsafe_allow_html=True)
    
    with met3:
        st.markdown("""
        <div class='metric-card'>
            <div style='font-size: 14px; color: #d1d5db; margin-bottom: 8px;'>📈 Biggest Impact</div>
            <div style='font-size: 24px; font-weight: 700; color: #4ade80;'>{}</div>
            <div style='font-size: 12px; color: #9ca3af;'>{:.0f} kg CO₂</div>
        </div>
        """.format(max(contributors, key=contributors.get), max(contributors.values())), unsafe_allow_html=True)
    
    with met4:
        st.markdown("""
        <div class='metric-card'>
            <div style='font-size: 14px; color: #d1d5db; margin-bottom: 8px;'>🎯 Status</div>
            <div style='font-size: 18px; font-weight: 700; color: #4ade80;'>Active</div>
            <div style='font-size: 12px; color: #9ca3af;'>Tracking enabled</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # -------------------------
    # ECO SCORE PROGRESS & BADGE
    # -------------------------
    col_badge1, col_badge2 = st.columns([1, 1])
    
    with col_badge1:
        st.markdown("<div class='section-header' style='margin-top: 0;'>🏅 Eco Achievement</div>", unsafe_allow_html=True)
        
        if eco_score >= 85:
            badge_text = "🌟 Eco Champion"
            badge_class = "badge badge-champion"
        elif eco_score >= 70:
            badge_text = "🌿 Green Guardian"
            badge_class = "badge badge-guardian"
        elif eco_score >= 50:
            badge_text = "🍃 Eco Learner"
            badge_class = "badge badge-learner"
        else:
            badge_text = "🔥 High Impact User"
            badge_class = "badge badge-high"
        
        st.markdown(f"<div class='{badge_class}'>{badge_text}</div>", unsafe_allow_html=True)
        
        # Progress bar
        st.markdown(f"""
        <div style='margin-top: 16px;'>
            <div style='display: flex; justify-content: space-between; margin-bottom: 6px;'>
                <span style='color: #d1d5db; font-size: 14px;'>Score Progress</span>
                <span style='color: #4ade80; font-weight: 700;'>{eco_score}%</span>
            </div>
            <div class='progress-bar'>
                <div class='progress-fill' style='width: {eco_score}%;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Description
        if eco_score >= 85:
            st.info("🌟 Excellent! You're making exceptional environmental choices. Keep it up!")
        elif eco_score >= 70:
            st.info("🌿 Great work! Your footprint is below average. Focus on small improvements.")
        elif eco_score >= 50:
            st.info("🍃 Good start! There's room to improve. Check recommendations below.")
        else:
            st.warning("🔥 Your carbon footprint is above average. Let's work on reducing it!")
    
    with col_badge2:
        st.markdown("<div class='section-header' style='margin-top: 0;'>📊 Emission Sources</div>", unsafe_allow_html=True)
        
        # Pie chart with Plotly
        fig = go.Figure(data=[go.Pie(
            labels=list(contributors.keys()),
            values=list(contributors.values()),
            hole=0.4,
            marker=dict(
                colors=['#4ade80', '#60a5fa', '#fbbf24', '#f87171'],
                line=dict(color='rgba(0,0,0,0.1)', width=2)
            ),
            textposition='auto',
            hovertemplate='<b>%{label}</b><br>%{value:.0f} kg CO₂<br>%{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            showlegend=True,
            height=280,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#d1d5db', size=12),
            legend=dict(
                x=-0.15,
                y=1,
                bgcolor='rgba(0,0,0,0.3)',
                bordercolor='rgba(74, 222, 128, 0.3)',
                borderwidth=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown("---")

    # -------------------------
    # DETAILED BREAKDOWN
    # -------------------------
    st.markdown("<div class='section-header'>📋 Detailed Breakdown</div>", unsafe_allow_html=True)
    
    # Bar chart
    breakdown_fig = go.Figure(data=[
        go.Bar(
            x=list(contributors.keys()),
            y=list(contributors.values()),
            marker=dict(
                color=['#4ade80', '#60a5fa', '#fbbf24', '#f87171'],
                line=dict(color='rgba(255,255,255,0.2)', width=2)
            ),
            text=[f'{v:.0f} kg' for v in contributors.values()],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>%{y:.0f} kg CO₂<extra></extra>'
        )
    ])
    
    breakdown_fig.update_layout(
        height=350,
        margin=dict(l=40, r=20, t=20, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(55, 65, 81, 0.2)',
        font=dict(color='#d1d5db', size=12),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            color='#9ca3af'
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(74, 222, 128, 0.1)',
            zeroline=False,
            color='#9ca3af'
        ),
        showlegend=False
    )
    
    st.plotly_chart(breakdown_fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown("---")

    # -------------------------
    # AI INSIGHT
    # -------------------------
    st.markdown("<div class='section-header'>🤖 AI Insights & Analysis</div>", unsafe_allow_html=True)
    
    col_insight1, col_insight2 = st.columns([1.2, 0.8])
    
    with col_insight1:
        st.markdown(f"""
        <div class='card-highlight'>
            <div style='display: flex; gap: 12px; align-items: flex-start;'>
                <div style='font-size: 32px;'>💡</div>
                <div style='flex: 1;'>
                    <div style='font-size: 16px; font-weight: 800; color: #4ade80; margin-bottom: 12px;'>Key Finding</div>
                    <div style='font-size: 15px; color: #d1d5db; line-height: 1.8;'>{h(insight)}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_insight2:
        st.markdown("""
        <div class='card'>
            <div style='display: flex; gap: 12px; align-items: flex-start;'>
                <div style='font-size: 32px;'>🎯</div>
                <div style='flex: 1;'>
                    <div style='font-size: 16px; font-weight: 800; color: #4ade80; margin-bottom: 12px;'>Quick Tips</div>
                    <ul style='color: #d1d5db; font-size: 14px; line-height: 2.2; padding-left: 20px; margin: 0;'>
                        <li>Start with small daily changes</li>
                        <li>Track progress regularly</li>
                        <li>Share with friends & family</li>
                        <li>Focus on your biggest source</li>
                    </ul>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # -------------------------
    # RECOMMENDATIONS
    # -------------------------
    st.markdown("<div class='section-header'>💡 Personalized Recommendations</div>", unsafe_allow_html=True)
    
    if len(recommendations) > 0:
        for idx, r in enumerate(recommendations):
            st.markdown(f"""
            <div class='card' style='border-left: 4px solid #22c55e;'>
                <div style='display: flex; gap: 12px;'>
                    <div style='font-size: 24px;'>💚</div>
                    <div style='flex: 1;'>
                        <div style='font-size: 15px; line-height: 1.8; color: #d1d5db;'>{h(r)}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='card-highlight'>
            <div style='display: flex; gap: 16px; align-items: center;'>
                <div style='font-size: 48px;'>🌟</div>
                <div>
                    <div style='font-size: 18px; font-weight: 700; color: #4ade80; margin-bottom: 4px;'>Excellent Work!</div>
                    <div style='color: #d1d5db;'>Your lifestyle is already very eco-friendly. Keep maintaining these amazing habits!</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # -------------------------
    # PDF DOWNLOAD
    # -------------------------
    report = generate_pdf(total, eco_score, insight)

    with open(report, "rb") as f:
        st.download_button(
            "📄 Download Eco Report (PDF)",
            f,
            file_name="EcoBuddy_Report.pdf"
        )


# -------------------------
# HISTORY & TRACKING
# -------------------------
st.markdown("---")

st.markdown("<div class='section-header'>📈 Your Eco Journey</div>", unsafe_allow_html=True)

history = get_assessments()

if history:

    df = pd.DataFrame(history, columns=[
        "id", "date", "transport", "distance",
        "electricity", "diet", "flights",
        "footprint", "eco_score"
    ])

    latest = history[0]

    # Latest stats
    stat1, stat2, stat3, stat4 = st.columns(4)
    
    with stat1:
        st.markdown(f"""
        <div class='card'>
            <div style='font-size: 12px; color: #9ca3af;'>Latest Footprint</div>
            <div style='font-size: 28px; font-weight: 900; color: #4ade80;'>{latest[7]:.0f}</div>
            <div style='font-size: 11px; color: #9ca3af;'>kg CO₂</div>
        </div>
        """, unsafe_allow_html=True)
    
    with stat2:
        st.markdown(f"""
        <div class='card'>
            <div style='font-size: 12px; color: #9ca3af;'>Latest Score</div>
            <div style='font-size: 28px; font-weight: 900; color: #4ade80;'>{latest[8]}</div>
            <div style='font-size: 11px; color: #9ca3af;'>out of 100</div>
        </div>
        """, unsafe_allow_html=True)

    if len(history) >= 2:
        prev = history[1][7]
        change = ((prev - latest[7]) / prev) * 100 if prev else 0

        with stat3:
            if change > 0:
                color = "#4ade80"
                emoji = "📉"
                label = "Reduced"
            elif change < 0:
                color = "#f87171"
                emoji = "📈"
                label = "Increased"
            else:
                color = "#60a5fa"
                emoji = "→"
                label = "No Change"
            
            st.markdown(f"""
            <div class='card'>
                <div style='font-size: 12px; color: #9ca3af;'>{emoji} {label}</div>
                <div style='font-size: 28px; font-weight: 900; color: {color};'>{abs(change):.1f}%</div>
                <div style='font-size: 11px; color: #9ca3af;'>vs previous</div>
            </div>
            """, unsafe_allow_html=True)

    with stat4:
        st.markdown(f"""
        <div class='card'>
            <div style='font-size: 12px; color: #9ca3af;'>Total Records</div>
            <div style='font-size: 28px; font-weight: 900; color: #4ade80;'>{len(history)}</div>
            <div style='font-size: 11px; color: #9ca3af;'>assessments</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # -------------------------
    # TREND VISUALIZATION
    # -------------------------
    st.markdown("<div style='font-size: 22px; font-weight: 800; background: linear-gradient(135deg, #4ade80, #86efac); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 16px;'>📉 Carbon Footprint Trend</div>", unsafe_allow_html=True)

    trend_df = df[["date", "footprint"]].iloc[::-1].reset_index(drop=True)
    trend_df['date'] = pd.to_datetime(trend_df['date'])
    
    trend_fig = go.Figure()
    trend_fig.add_trace(go.Scatter(
        x=trend_df['date'],
        y=trend_df['footprint'],
        mode='lines+markers',
        name='Carbon Footprint',
        line=dict(color='#4ade80', width=3),
        marker=dict(size=8, color='#4ade80', line=dict(color='#86efac', width=2)),
        fill='tozeroy',
        fillcolor='rgba(74, 222, 128, 0.2)',
        hovertemplate='<b>%{x|%b %d}</b><br>%{y:.0f} kg CO₂<extra></extra>'
    ))
    
    trend_fig.update_layout(
        height=320,
        margin=dict(l=40, r=20, t=20, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(55, 65, 81, 0.2)',
        font=dict(color='#d1d5db', size=12),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            color='#9ca3af'
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(74, 222, 128, 0.1)',
            zeroline=False,
            color='#9ca3af'
        ),
        showlegend=False,
        hovermode='x unified'
    )
    
    st.plotly_chart(trend_fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown("---")

    # -------------------------
    # HISTORY TABLE
    # -------------------------
    st.markdown("<div style='font-size: 22px; font-weight: 800; background: linear-gradient(135deg, #4ade80, #86efac); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 16px;'>📋 Assessment History</div>", unsafe_allow_html=True)

    # Create a nice table display
    display_df = df[["date", "transport", "electricity", "footprint", "eco_score"]].copy()
    display_df.columns = ["📅 Date", "🚗 Transport", "⚡ Electricity (kWh)", "🌍 Footprint (kg CO₂)", "🏆 Score"]
    display_df = display_df.iloc[::-1].reset_index(drop=True)

    st.markdown(
        "<div class='history-table-wrap'>"
        + display_df.to_html(index=False, classes="history-table", border=0)
        + "</div>",
        unsafe_allow_html=True
    )

    st.markdown("---")

    # -------------------------
    # STATS & INSIGHTS
    # -------------------------
    st.markdown("<div style='font-size: 22px; font-weight: 800; background: linear-gradient(135deg, #4ade80, #86efac); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 16px;'>📊 Your Statistics</div>", unsafe_allow_html=True)

    stats_col1, stats_col2, stats_col3 = st.columns(3)
    
    avg_footprint = df['footprint'].mean()
    avg_score = df['eco_score'].mean()
    max_footprint = df['footprint'].max()
    min_footprint = df['footprint'].min()
    
    with stats_col1:
        st.markdown(f"""
        <div class='card'>
            <div style='font-size: 13px; color: #9ca3af; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700;'>📊 Average Footprint</div>
            <div style='font-size: 36px; font-weight: 900; color: #4ade80;'>{avg_footprint:.0f}</div>
            <div style='font-size: 12px; color: #9ca3af; margin-top: 8px;'>kg CO₂ across {len(history)} records</div>
        </div>
        """, unsafe_allow_html=True)
    
    with stats_col2:
        st.markdown(f"""
        <div class='card'>
            <div style='font-size: 13px; color: #9ca3af; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700;'>🎯 Average Score</div>
            <div style='font-size: 36px; font-weight: 900; color: #4ade80;'>{avg_score:.0f}</div>
            <div style='font-size: 12px; color: #9ca3af; margin-top: 8px;'>out of 100 points</div>
        </div>
        """, unsafe_allow_html=True)
    
    with stats_col3:
        range_val = max_footprint - min_footprint
        st.markdown(f"""
        <div class='card'>
            <div style='font-size: 13px; color: #9ca3af; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700;'>📈 Range Variation</div>
            <div style='font-size: 28px; font-weight: 700; color: #4ade80;'>{min_footprint:.0f}</div>
            <div style='font-size: 14px; color: #9ca3af;'>to</div>
            <div style='font-size: 28px; font-weight: 700; color: #4ade80;'>{max_footprint:.0f}</div>
        </div>
        """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div class='card-highlight'>
        <div style='text-align: center; padding: 48px 32px;'>
            <div style='font-size: 72px; margin-bottom: 20px; animation: bounce 2s infinite;'>🌱</div>
            <div style='font-size: 26px; font-weight: 800; background: linear-gradient(135deg, #22c55e, #4ade80); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 12px;'>No Data Yet</div>
            <div style='color: #d1d5db; font-size: 16px; line-height: 1.6; max-width: 400px; margin: 0 auto;'>
                Start your eco journey! Complete the lifestyle profile above and click "Analyze My Impact" to generate your personalized carbon footprint report.
            </div>
        </div>
    </div>
    <style>
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
    </style>
    """, unsafe_allow_html=True)
