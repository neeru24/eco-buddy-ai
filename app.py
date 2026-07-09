import html
import time
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import tempfile
import uuid
import os

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from database import init_db, save_assessment, get_assessments, init_gamification_db
import gamification as gf
from emissions import calculate_footprint, calculate_eco_score
from recommendations import generate_recommendations

# Added for Route Planning & Offsets
from database import (
    init_marketplace_db, save_journey_profile, get_journey_profiles, delete_journey_profile,
    save_offset_transaction, get_offset_transactions, delete_offset_transaction,
    get_total_offsets, get_total_spend
)
from marketplace import (
    calculate_trip_emissions, calculate_recurring_trip_emissions, compare_transit_modes,
    calculate_offset_cost, validate_offset_transaction, get_offset_projects,
    calculate_net_emissions, calculate_net_zero_progress, get_project_by_id, EMISSION_FACTORS
)

def h(text):
    return html.escape(str(text))

# -------------------------
# INIT
# -------------------------

init_db()
init_gamification_db()
init_marketplace_db()

# -------------------------
# DEFAULT FORM VALUES
# -------------------------
DEFAULT_VALUES = {
    "transport": "Car",
    "distance": 10.0,
    "electricity": 200.0,
    "diet": "Vegetarian",
    "flights": 0,
}

for key, value in DEFAULT_VALUES.items():
    if key not in st.session_state:
        st.session_state[key] = value

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

    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }

    body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        color: var(--ink);
        background:
            linear-gradient(180deg, rgba(185, 215, 244, 0.74) 0%, rgba(244, 248, 240, 0.95) 48%, #f7faf3 100%),
            radial-gradient(circle at 14% 12%, rgba(255, 255, 255, 0.86), transparent 30%),
            linear-gradient(135deg, #d7ebff 0%, #f4f8e8 54%, #eaf5df 100%);
        min-height: 100vh;
    }

    [data-testid="stHeader"] { background: transparent; }

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
    [data-testid="stSidebar"] * { color: var(--ink); }

    .title {
        margin: 8px 0 12px;
        color: var(--ink);
        font-size: clamp(46px, 6vw, 82px);
        line-height: 1;
        font-weight: 800;
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

    .input-section, .card, .card-highlight, .metric-card {
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
    .input-section { padding: 34px; margin-bottom: 24px; }
    .card, .card-highlight, .metric-card { padding: 26px; margin-bottom: 16px; }

    .metric-card::before, .card-highlight::before {
        content: '';
        position: absolute;
        inset: 0 0 auto 0;
        height: 5px;
        background: linear-gradient(90deg, #030504, var(--leaf), #b6d274);
    }
    .metric-card:hover, .card:hover, .card-highlight:hover {
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
    }
    .badge-champion { background: linear-gradient(135deg, #f4c760, #d8831e); color: #2c1804; }
    .badge-guardian { background: linear-gradient(135deg, #acd66f, #5f8f36); color: #0d1c0f; }
    .badge-learner { background: linear-gradient(135deg, #b9d7f4, #6aa0cf); color: #071927; }
    .badge-high { background: linear-gradient(135deg, #ff8e70, #d84b35); color: #2e0904; }

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

    /* Fixed CSS Block */
    .stButton > button,
    .stDownloadButton > button,
    [data-testid="stFormSubmitButton"] > button {
        min-height: 52px;
        padding: 0 28px !important;
        border: none !important;
        border-radius: 12px !important;
        background: #030504 !important;
        color: #fff !important;
        box-shadow: 0 16px 34px rgba(0, 0, 0, 0.2) !important;
        font-size: 15px !important;
        font-weight: 800 !important;
        transition: transform 180ms ease, box-shadow 180ms ease, background 180ms ease !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        transform: translateY(-2px);
        background: #101713 !important;
        box-shadow: 0 22px 44px rgba(0, 0, 0, 0.26) !important;
    }

    .stInfo, .stWarning, .stSuccess, .stError {
        border-radius: 14px !important;
        border: 1px solid var(--line) !important;
        box-shadow: 0 12px 30px rgba(57, 86, 47, 0.08);
    }

    .stInfo { background: rgba(185, 215, 244, 0.42) !important; }
    .stWarning { background: rgba(244, 199, 96, 0.24) !important; }
    .stSuccess { background: rgba(172, 214, 111, 0.26) !important; }

    /* DARK PREMIUM THEME OVERRIDES */
    @media (prefers-color-scheme: dark) {
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
        }
        
        body, [data-testid="stAppViewContainer"] {
            color: var(--ink);
            background:
                radial-gradient(circle at 18% 8%, rgba(74, 222, 128, 0.22), transparent 28%),
                radial-gradient(circle at 84% 12%, rgba(96, 165, 250, 0.18), transparent 30%),
                linear-gradient(145deg, #030712 0%, #07130d 42%, #111827 100%) !important;
        }

        .input-section, .card, .card-highlight, .metric-card {
            background: linear-gradient(145deg, rgba(15, 23, 42, 0.94), rgba(17, 24, 39, 0.72));
        }

        .stTextInput > div > div > input,
        .stNumberInput input,
        .stSelectbox [data-baseweb="select"],
        .stTextArea textarea {
            background: #ffffff !important;
            color: #05070a !important;
        }
        
        .stButton > button,
        .stDownloadButton > button,
        [data-testid="stFormSubmitButton"] > button {
            background: linear-gradient(135deg, #0b0f18, #111827) !important;
            border: 1px solid rgba(134, 239, 172, 0.28) !important;
        }
        
        .stButton > button:hover,
        .stDownloadButton > button:hover,
        [data-testid="stFormSubmitButton"] > button:hover {
            background: linear-gradient(135deg, #111827, #0f2a1a) !important;
        }
    }

    .history-table-wrap {
        width: 100%; overflow-x: auto;
        border: 1px solid rgba(134, 239, 172, 0.24);
        border-radius: 16px; background: #0f172a;
    }
    .history-table { width: 100%; border-collapse: collapse; color: #ffffff; font-size: 15px; }
    .history-table thead th { padding: 16px 18px; background: #07130d; border-bottom: 1px solid rgba(134, 239, 172, 0.3); font-weight: 800; text-align: left; }
    .history-table tbody td { padding: 15px 18px; border-bottom: 1px solid rgba(148, 163, 184, 0.14); text-align: left; }
    .history-table tbody tr:nth-child(even) { background: #111827; }
    .history-table tbody tr:hover { background: rgba(34, 197, 94, 0.14); }

    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(18px); }
        to { opacity: 1; transform: translateY(0); }
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
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 16px;'>
        <span style='font-size: 24px;'>🚗</span>
        <span style='font-size: 18px; font-weight: 700; color: #e5e7eb;'>Transportation</span>
    </div>
    """, unsafe_allow_html=True)
    transport = st.selectbox("Primary Transport", ["Car", "Public Transport", "Bike", "Walking"], key="transport")
    distance = st.number_input("Daily Distance (km)", min_value=0.0, value=10.0, step=1.0, key="distance")

with col2:
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 16px;'>
        <span style='font-size: 24px;'>⚡</span>
        <span style='font-size: 18px; font-weight: 700; color: #e5e7eb;'>Energy & Diet</span>
    </div>
    """, unsafe_allow_html=True)
    electricity = st.number_input("Monthly Electricity (kWh)", min_value=0.0, value=200.0, step=10.0, key="electricity")
    diet = st.selectbox("Diet Type", ["Vegetarian", "Non-Vegetarian"], key="diet")

with col3:
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 16px;'>
        <span style='font-size: 24px;'>✈️</span>
        <span style='font-size: 18px; font-weight: 700; color: #e5e7eb;'>Travel</span>
    </div>
    """, unsafe_allow_html=True)
    flights = st.number_input("Annual Flights", min_value=0, value=0, step=1, key="flights")
    st.info("💡 How many long-distance flights per year?")

# -------------------------
# ACTION BUTTONS
# -------------------------
col_btn1, col_btn2, col_btn3 = st.columns([1, 1.5, 1])

with col_btn1:
    reset_btn = st.button("🔄 Reset Assessment", use_container_width=True)

with col_btn2:
    analyze_btn = st.button("🌿 Analyze My Impact", use_container_width=True)
    st.caption("✔ All input fields are validated before analysis.")

if reset_btn:
    for key in DEFAULT_VALUES:
        if key in st.session_state:
            del st.session_state[key]
    st.success("✅ Assessment form has been reset.")
    st.rerun()

# -------------------------
# PDF REPORT GENERATION
# -------------------------
def generate_pdf(total, eco_score, insight):
    try:
        file_name = os.path.join(tempfile.gettempdir(), f"eco_report_{uuid.uuid4().hex}.pdf")
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
    except Exception:
        st.error("Could not generate the PDF report. Please check disk space and permissions, then try again.")
        return None

# -------------------------
# TABS CONFIGURATION
# -------------------------
tab1, tab2, tab3, tab4 = st.tabs(["🌍 Carbon Footprint", "⚡ Home Energy Audit", "🎮 Gamification", "🗺️ Route Planning & Offsets"])

with tab1:
    st.markdown("<div class='section-header'>📝 Your Lifestyle Profile</div>", unsafe_allow_html=True)

    if analyze_btn:
        with st.spinner("🌍 Analyzing your carbon footprint..."):
            progress_text = st.empty()
            progress = st.progress(0)

            progress_text.info("🔍 Validating user inputs...")
            progress.progress(20)
            time.sleep(0.5)

            progress_text.info("🌍 Calculating carbon footprint...")
            progress.progress(40)

            total, contributors = calculate_footprint(transport, distance, electricity, diet, flights)

            progress_text.info("📊 Calculation completed...")
            progress.progress(100)
            
            progress.empty()
            progress_text.empty()

        eco_score = calculate_eco_score(total)
        insight, recommendations = generate_recommendations(transport, electricity, diet, flights, contributors)

        save_assessment(transport, distance, electricity, diet, flights, total, eco_score)
        st.success("✅ Analysis completed!")
        st.markdown("---")

        # -------------------------
        # RESULTS DASHBOARD
        # -------------------------
        st.markdown("<div class='section-header'>📊 Your Carbon Footprint Analysis</div>", unsafe_allow_html=True)

        met1, met2, met3, met4 = st.columns(4)
        with met1:
            st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size: 14px; color: #d1d5db; margin-bottom: 8px;'>🌍 Total Footprint</div>
                <div style='font-size: 36px; font-weight: 900; color: #4ade80;'>{total:.0f}</div>
                <div style='font-size: 12px; color: #9ca3af;'>kg CO₂/year</div>
            </div>
            """, unsafe_allow_html=True)

        with met2:
            st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size: 14px; color: #d1d5db; margin-bottom: 8px;'>🏆 Eco Score</div>
                <div style='font-size: 36px; font-weight: 900; color: #4ade80;'>{eco_score}</div>
                <div style='font-size: 12px; color: #9ca3af;'>out of 100</div>
            </div>
            """, unsafe_allow_html=True)

        with met3:
            st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size: 14px; color: #d1d5db; margin-bottom: 8px;'>📈 Biggest Impact</div>
                <div style='font-size: 24px; font-weight: 700; color: #4ade80;'>{max(contributors, key=contributors.get)}</div>
                <div style='font-size: 12px; color: #9ca3af;'>{max(contributors.values()):.0f} kg CO₂</div>
            </div>
            """, unsafe_allow_html=True)

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

            if eco_score >= 85: badge_text, badge_class = "🌟 Eco Champion", "badge badge-champion"
            elif eco_score >= 70: badge_text, badge_class = "🌿 Green Guardian", "badge badge-guardian"
            elif eco_score >= 50: badge_text, badge_class = "🍃 Eco Learner", "badge badge-learner"
            else: badge_text, badge_class = "🔥 High Impact User", "badge badge-high"

            st.markdown(f"<div class='{badge_class}'>{badge_text}</div>", unsafe_allow_html=True)

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

            if eco_score >= 85: st.info("🌟 Excellent! You're making exceptional environmental choices. Keep it up!")
            elif eco_score >= 70: st.info("🌿 Great work! Your footprint is below average. Focus on small improvements.")
            elif eco_score >= 50: st.info("🍃 Good start! There's room to improve. Check recommendations below.")
            else: st.warning("🔥 Your carbon footprint is above average. Let's work on reducing it!")

        with col_badge2:
            st.markdown("<div class='section-header' style='margin-top: 0;'>📊 Emission Sources</div>", unsafe_allow_html=True)
            fig = go.Figure(data=[go.Pie(
                labels=list(contributors.keys()),
                values=list(contributors.values()),
                hole=0.4,
                marker=dict(colors=['#4ade80', '#60a5fa', '#fbbf24', '#f87171'], line=dict(color='rgba(0,0,0,0.1)', width=2)),
                textposition='auto',
                hovertemplate='<b>%{label}</b><br>%{value:.0f} kg CO₂<br>%{percent}<extra></extra>'
            )])
            fig.update_layout(showlegend=True, height=280, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#d1d5db', size=12))
            st.plotly_chart(fig, width="stretch", config={'displayModeBar': False})

        st.markdown("---")

        # -------------------------
        # DETAILED BREAKDOWN & INSIGHTS
        # -------------------------
        st.markdown("<div class='section-header'>📋 Detailed Breakdown</div>", unsafe_allow_html=True)

        breakdown_fig = go.Figure(data=[go.Bar(
            x=list(contributors.keys()), y=list(contributors.values()),
            marker=dict(color=['#4ade80', '#60a5fa', '#fbbf24', '#f87171'], line=dict(color='rgba(255,255,255,0.2)', width=2)),
            text=[f'{v:.0f} kg' for v in contributors.values()], textposition='auto',
            hovertemplate='<b>%{x}</b><br>%{y:.0f} kg CO₂<extra></extra>'
        )])
        breakdown_fig.update_layout(height=350, margin=dict(l=40, r=20, t=20, b=40), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(55, 65, 81, 0.2)', font=dict(color='#d1d5db', size=12))
        st.plotly_chart(breakdown_fig, width="stretch", config={'displayModeBar': False})

        st.markdown("---")
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

        report = generate_pdf(total, eco_score, insight)
        if report:
            with open(report, "rb") as f:
                pdf_bytes = f.read()
            try: os.remove(report)
            except OSError: pass
            
            st.download_button("📄 Download Eco Report (PDF)", pdf_bytes, file_name="EcoBuddy_Report.pdf")

    # -------------------------
    # HISTORY TAB
    # -------------------------
    st.markdown("---")
    st.markdown("<div class='section-header'>📈 Your Eco Journey</div>", unsafe_allow_html=True)
    history = get_assessments()

    if history:
        df = pd.DataFrame(history, columns=["id", "date", "transport", "distance", "electricity", "diet", "flights", "footprint", "eco_score"])
        latest = history[0]

        stat1, stat2, stat3, stat4 = st.columns(4)
        with stat1:
            st.markdown(f"<div class='card'><div style='font-size: 12px; color: #9ca3af;'>Latest Footprint</div><div style='font-size: 28px; font-weight: 900; color: #4ade80;'>{latest[7]:.0f}</div><div style='font-size: 11px; color: #9ca3af;'>kg CO₂</div></div>", unsafe_allow_html=True)
        with stat2:
            st.markdown(f"<div class='card'><div style='font-size: 12px; color: #9ca3af;'>Latest Score</div><div style='font-size: 28px; font-weight: 900; color: #4ade80;'>{latest[8]}</div><div style='font-size: 11px; color: #9ca3af;'>out of 100</div></div>", unsafe_allow_html=True)
        with stat3:
            if len(history) >= 2:
                prev = history[1][7]
                change = ((prev - latest[7]) / prev) * 100 if prev else 0
                color, emoji, label = ("#4ade80", "📉", "Reduced") if change > 0 else ("#f87171", "📈", "Increased") if change < 0 else ("#60a5fa", "→", "No Change")
                st.markdown(f"<div class='card'><div style='font-size: 12px; color: #9ca3af;'>{emoji} {label}</div><div style='font-size: 28px; font-weight: 900; color: {color};'>{abs(change):.1f}%</div><div style='font-size: 11px; color: #9ca3af;'>vs previous</div></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='card'><div style='font-size: 12px; color: #9ca3af;'>Change</div><div style='font-size: 28px; font-weight: 900; color: #4ade80;'>N/A</div><div style='font-size: 11px; color: #9ca3af;'>need more data</div></div>", unsafe_allow_html=True)
        with stat4:
            st.markdown(f"<div class='card'><div style='font-size: 12px; color: #9ca3af;'>Total Records</div><div style='font-size: 28px; font-weight: 900; color: #4ade80;'>{len(history)}</div><div style='font-size: 11px; color: #9ca3af;'>assessments</div></div>", unsafe_allow_html=True)

        st.markdown("---")
        display_df = df[["date", "transport", "electricity", "footprint", "eco_score"]].copy()
        display_df.columns = ["📅 Date", "🚗 Transport", "⚡ Electricity (kWh)", "🌍 Footprint (kg CO₂)", "🏆 Score"]
        display_df = display_df.iloc[::-1].reset_index(drop=True)

        st.markdown("<div class='history-table-wrap'>" + display_df.to_html(index=False, classes="history-table", border=0) + "</div>", unsafe_allow_html=True)
    else:
        st.info("No assessment data available yet. Please run an analysis!")

with tab2:
    import database as db
    import energy_audit as ea

    st.markdown("<div class='section-header'>⚡ Home Energy Audit</div>", unsafe_allow_html=True)
    db.init_energy_db()

    st.markdown("### 🔌 Appliance Registry")
    with st.expander("➕ Add New Appliance", expanded=False):
        with st.form("appliance_form"):
            c1, c2, c3 = st.columns(3)
            app_name = c1.text_input("Appliance Name")
            app_cat = c2.selectbox("Category", ["AC", "EV Charger", "Heat Pump", "Refrigerator", "Lighting", "Other"])
            app_qty = c3.number_input("Quantity", min_value=1, value=1)

            c4, c5, c6 = st.columns(3)
            app_power = c4.number_input("Power Rating (Watts)", min_value=0.0, value=100.0)
            app_hours = c5.number_input("Hours Used/Day", min_value=0.0, max_value=24.0, value=1.0)
            app_standby = c6.number_input("Standby Draw (Watts)", min_value=0.0, value=0.0)

            if st.form_submit_button("Add Appliance") and app_name:
                db.add_appliance(app_name, app_cat, app_qty, app_power, app_hours, app_standby)
                st.success(f"Added {app_name}")
                st.rerun()

    appliances = db.get_appliances()
    if appliances:
        category_icons = {"AC": "❄️", "EV Charger": "🔋", "Heat Pump": "🌡️", "Refrigerator": "🧊", "Lighting": "💡", "Other": "🔌"}
        table_rows = "".join([f"<tr><td>{category_icons.get(a['category'], '🔌')} {h(a['name'])}</td><td><span style='background:rgba(74,222,128,0.15); padding:4px 10px; border-radius:8px; font-size:13px;'>{h(a['category'])}</span></td><td style='text-align:center;'>{a['quantity']}</td><td style='text-align:right;'>{a['power_rating_watts']:.0f} W</td><td style='text-align:right;'>{a['hours_used_per_day']:.1f} h</td><td style='text-align:right;'>{a['standby_draw_watts']:.1f} W</td></tr>" for a in appliances])

        st.markdown(f"""
        <div style='border:1px solid rgba(134,239,172,0.24); border-radius:16px; overflow:hidden; background:#0f172a; box-shadow:0 24px 70px rgba(0,0,0,0.38);'>
            <table style='width:100%; border-collapse:collapse; color:#fff; font-size:15px;'>
                <thead><tr style='background:#07130d;'><th style='padding:14px 18px; text-align:left; color:#86efac;'>Appliance</th><th style='padding:14px 18px; text-align:left; color:#86efac;'>Category</th><th style='padding:14px 18px; text-align:center; color:#86efac;'>Qty</th><th style='padding:14px 18px; text-align:right; color:#86efac;'>Power</th><th style='padding:14px 18px; text-align:right; color:#86efac;'>Hours/Day</th><th style='padding:14px 18px; text-align:right; color:#86efac;'>Standby</th></tr></thead>
                <tbody>{table_rows}</tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        del_cols = st.columns([3, 1])
        with del_cols[0]:
            del_id = st.selectbox("Select appliance to remove", options=[(a['id'], a['name']) for a in appliances], format_func=lambda x: x[1], label_visibility="collapsed")
        with del_cols[1]:
            if st.button("🗑️ Remove", key="del_app"):
                db.delete_appliance(del_id[0])
                st.rerun()

        daily_kwh, monthly_kwh, yearly_kwh = ea.calculate_home_energy_summary(appliances)
        st.markdown("### 📊 Energy Patterns")
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Daily Consumption", f"{daily_kwh:.2f} kWh")
        sc2.metric("Monthly Consumption", f"{monthly_kwh:.2f} kWh")
        sc3.metric("Yearly Consumption", f"{yearly_kwh:.2f} kWh")

        profile = ea.generate_hourly_energy_profile(appliances)
        fig_hr = go.Figure(data=[go.Bar(x=list(range(24)), y=profile, marker_color='#fbbf24')])
        fig_hr.update_layout(title="Hourly Energy Demand (kWh)", xaxis_title="Hour of Day", yaxis_title="kWh", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_hr, width="stretch")
    else:
        st.info("No Appliances Yet. Click 'Add New Appliance' to register your first device.")

with tab3:
    st.markdown("<div class='section-header'>🎮 Your Eco Journey</div>", unsafe_allow_html=True)
    
    total_xp = gf.get_total_xp(1)
    level = gf.calculate_level(total_xp)
    progress = gf.calculate_level_progress(total_xp)
    streak = gf.calculate_streak(1, [])
    
    g_col1, g_col2, g_col3 = st.columns(3)
    g_col1.metric("Current Level", f"Lvl {level}")
    g_col2.metric("Total XP", f"{total_xp} XP")
    g_col3.metric("Current Streak", f"{streak} Days 🔥")
    
    st.progress(min(progress, 1.0), text=f"Progress to Level {level+1}")
    
    st.markdown("---")
    st.markdown("### 🏆 Weekly Challenges")
    
    user_challenges = gf.get_user_challenges(1)
    enrolled_ids = [c['challenge_id'] for c in user_challenges if c['status'] != 'expired']
    
    for ch_id, ch_data in gf.CHALLENGES.items():
        with st.expander(f"{ch_data['title']} ({ch_data['xp']} XP) - {ch_data['category']}"):
            st.write(f"Target: {ch_data['target']} {ch_data['unit']}")
            if ch_id in enrolled_ids:
                status = [c['status'] for c in user_challenges if c['challenge_id'] == ch_id][-1]
                if status == 'completed':
                    st.success("Challenge Completed! 🎉")
                else:
                    current_prog = [c['progress_value'] for c in user_challenges if c['challenge_id'] == ch_id][-1]
                    st.write(f"Progress: {current_prog} / {ch_data['target']}")
                    
                    prog_val = st.number_input(f"Update Progress", min_value=0.0, step=1.0, key=f"prog_{ch_id}")
                    if st.button("Update", key=f"btn_prog_{ch_id}"):
                        gf.update_challenge_progress(1, ch_id, progress_increment=prog_val)
                        gf.validate_challenge_progress(1, ch_id)
                        st.rerun()
            else:
                if st.button("Enroll", key=f"enroll_{ch_id}"):
                    gf.enroll_challenge(1, ch_id)
                    st.rerun()

with tab4:
    st.markdown("<div class='section-header'>🗺️ Route Planning & Carbon Offsets</div>", unsafe_allow_html=True)

    route_col, offset_col = st.columns([1.2, 1])

    with route_col:
        st.subheader("📍 Transit Mode Comparison")
        with st.form("route_form"):
            dist_val = st.number_input("Trip Distance (km)", min_value=0.1, value=15.0, step=1.0)
            pass_val = st.number_input("Number of Passengers", min_value=1, value=1, step=1)
            freq = st.selectbox("Trip Frequency", ["One-time", "Weekly Commute (10 trips/week)", "Daily (14 trips/week)"])
            calc_btn = st.form_submit_button("Compare Emissions")
            
        if calc_btn:
            comparisons = compare_transit_modes(dist_val, pass_val)
            df_comp = pd.DataFrame(comparisons)
            
            if "Weekly" in freq: df_comp['emissions_kg'] *= 10
            elif "Daily" in freq: df_comp['emissions_kg'] *= 14
                
            fig = px.bar(df_comp, x='mode', y='emissions_kg', title='CO2e by Transit Mode (Lower is Better)', color='emissions_kg', color_continuous_scale='Greens_r')
            st.plotly_chart(fig, width="stretch")

    with offset_col:
        st.subheader("🛒 Simulated Offset Marketplace")
        projects = get_offset_projects()
        selected_proj_name = st.selectbox("Select an Offset Project", [p["name"] for p in projects])
        selected_proj = next(p for p in projects if p["name"] == selected_proj_name)
        
        with st.form("offset_form"):
            tonnes = st.number_input("Tonnes of CO2e to Offset", min_value=0.1, value=1.0, step=0.1)
            if st.form_submit_button("Purchase Simulated Offset"):
                is_valid, msg = validate_offset_transaction(tonnes, selected_proj["available_capacity"])
                if is_valid:
                    cost = calculate_offset_cost(tonnes, selected_proj["cost_per_tonne"])
                    save_offset_transaction(1, selected_proj["id"], selected_proj["name"], tonnes, selected_proj["cost_per_tonne"], cost)
                    st.success(f"Simulated purchase successful! Offset {tonnes}t for ${cost:.2f}.")
                else:
                    st.error(msg)