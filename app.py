import io
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

from database import init_db, save_assessment, get_assessments
from emissions import calculate_footprint, calculate_eco_score
from recommendations import generate_recommendations


# -------------------------
# INIT
# -------------------------
init_db()

st.set_page_config(
    page_title="EcoBuddy 🌱",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)


# -------------------------
# HELPER: Dynamic Quick Tips based on contributor data
# -------------------------
def get_dynamic_tips(contributors: dict) -> list[str]:
    """Return top-3 actionable tips ranked by the user's actual biggest sources."""
    tip_map = {
        "Transport": "🚗 Try carpooling or switching to public transport 2x/week to cut transport emissions.",
        "Electricity": "💡 Unplug idle devices and switch to LED bulbs — small steps, big savings.",
        "Diet": "🥗 Adding 2 plant-based meals per week can cut diet emissions by up to 20%.",
        "Flights": "✈️ One less long-haul flight saves ~500 kg CO₂ — consider trains for shorter routes.",
    }
    sorted_sources = sorted(contributors, key=contributors.get, reverse=True)
    tips = [tip_map[s] for s in sorted_sources if s in tip_map]
    return tips[:3] if tips else ["🌱 Keep maintaining your sustainable habits!"]


# -------------------------
# HELPER: Render a metric card
# -------------------------
def metric_card(label: str, value: str, unit: str, color: str = "#4ade80") -> str:
    return f"""
    <div class='metric-card' role='region' aria-label='{label}: {value} {unit}'>
        <div style='font-size: 14px; color: #d1d5db; margin-bottom: 8px;'>{label}</div>
        <div style='font-size: 36px; font-weight: 900; color: {color};'>{value}</div>
        <div style='font-size: 12px; color: #9ca3af;'>{unit}</div>
    </div>
    """


# -------------------------
# HELPER: Render a stat card (smaller)
# -------------------------
def stat_card(label: str, value: str, unit: str) -> str:
    return f"""
    <div class='card'>
        <div style='font-size: 12px; color: #9ca3af;'>{label}</div>
        <div style='font-size: 28px; font-weight: 900; color: #4ade80;'>{value}</div>
        <div style='font-size: 11px; color: #9ca3af;'>{unit}</div>
    </div>
    """


# -------------------------
# PDF REPORT GENERATION
# -------------------------
def generate_pdf(total: float, eco_score: int, insight: str, recommendations: list) -> io.BytesIO:
    """Generate a styled PDF report in memory and return the bytes buffer."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, rightMargin=inch, leftMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    content = [
        Paragraph("🌱 EcoBuddy AI — Eco Report", styles["Title"]),
        Spacer(1, 0.2 * inch),
        Paragraph(f"Carbon Footprint: {total:.2f} kg CO₂/year", styles["Normal"]),
        Paragraph(f"Eco Score: {eco_score} / 100", styles["Normal"]),
        Spacer(1, 0.15 * inch),
        Paragraph("Key Insight:", styles["Heading2"]),
        Paragraph(insight, styles["Normal"]),
        Spacer(1, 0.15 * inch),
        Paragraph("Personalized Recommendations:", styles["Heading2"]),
    ]
    for r in recommendations:
        # Strip emoji for PDF compatibility
        clean = r.encode("ascii", "ignore").decode()
        content.append(Paragraph(f"• {clean}", styles["Normal"]))
    doc.build(content)
    buffer.seek(0)
    return buffer


# -------------------------
# ADVANCED STYLING
# -------------------------
st.markdown("""
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
        background: linear-gradient(-45deg, #0a2818, #0f3d1f, #1a5c2a, #0d4a27);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        min-height: 100vh;
        font-family: 'Inter', sans-serif;
    }

    @keyframes gradientBG {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* ── TITLE ── */
    .title {
        font-size: 64px; font-weight: 900;
        background: linear-gradient(135deg, #22c55e 0%, #4ade80 50%, #86efac 100%);
        background-size: 200% 200%;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 12px; text-align: center; letter-spacing: -1px;
        animation: slideDown 0.8s cubic-bezier(0.23,1,.32,1), shimmer 3s ease-in-out infinite;
    }

    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-30px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes shimmer {
        0%,100% { background-position: 0% 50%; }
        50%     { background-position: 100% 50%; }
    }

    .subtitle {
        color: #e5e7eb; margin-bottom: 28px; text-align: center;
        font-size: 18px; font-weight: 400; letter-spacing: 0.5px;
        animation: fadeInUp 0.8s 0.2s cubic-bezier(0.23,1,.32,1) both;
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ── METRIC CARD ── */
    .metric-card {
        background: linear-gradient(135deg,rgba(34,197,94,.12),rgba(74,222,128,.08));
        padding: 28px; border-radius: 20px;
        border: 1.5px solid rgba(74,222,128,.35);
        margin-bottom: 14px;
        box-shadow: 0 12px 32px rgba(0,0,0,.25),inset 0 1px 2px rgba(255,255,255,.05);
        transition: all 0.4s cubic-bezier(0.23,1,.32,1);
        position: relative; overflow: hidden; backdrop-filter: blur(10px);
    }
    .metric-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 24px 48px rgba(34,197,94,.35),inset 0 1px 2px rgba(255,255,255,.1);
        border-color: rgba(74,222,128,.7);
    }

    /* ── CARD ── */
    .card {
        background: linear-gradient(135deg,rgba(31,41,55,.5),rgba(55,65,81,.3));
        padding: 24px; border-radius: 18px;
        border: 1.5px solid rgba(74,222,128,.25);
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(0,0,0,.2),inset 0 1px 2px rgba(255,255,255,.03);
        backdrop-filter: blur(12px);
        transition: all 0.3s cubic-bezier(0.23,1,.32,1);
    }
    .card:hover {
        border-color: rgba(74,222,128,.5);
        transform: translateY(-4px);
        box-shadow: 0 16px 40px rgba(74,222,128,.2);
    }

    /* ── HIGHLIGHT CARD ── */
    .card-highlight {
        background: linear-gradient(135deg,rgba(34,197,94,.15),rgba(74,222,128,.08));
        padding: 28px; border-radius: 20px;
        border: 2px solid rgba(74,222,128,.45);
        margin-bottom: 16px;
        box-shadow: 0 12px 40px rgba(34,197,94,.2),inset 0 1px 3px rgba(255,255,255,.1);
        position: relative; backdrop-filter: blur(12px);
    }
    .card-highlight::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg,transparent,rgba(34,197,94,.6),transparent);
        animation: shimmerLine 2s ease-in-out infinite;
    }
    @keyframes shimmerLine {
        0%,100% { opacity: .3; } 50% { opacity: 1; }
    }

    /* ── BADGES ── */
    .badge {
        display: inline-block; padding: 14px 32px; border-radius: 50px;
        font-weight: 800; font-size: 17px;
        box-shadow: 0 8px 24px rgba(34,197,94,.35),inset 0 1px 2px rgba(255,255,255,.2);
        border: 1px solid rgba(255,255,255,.15); letter-spacing: 0.5px;
    }
    .badge-champion { background: linear-gradient(135deg,#f59e0b,#fbbf24); color:#78350f; }
    .badge-guardian  { background: linear-gradient(135deg,#22c55e,#4ade80); color:#0a2818; }
    .badge-learner   { background: linear-gradient(135deg,#3b82f6,#60a5fa); color:#082f49; }
    .badge-high      { background: linear-gradient(135deg,#ef4444,#f87171); color:#7c2d12; }

    /* ── INPUT SECTION ── */
    .input-section {
        background: linear-gradient(135deg,rgba(31,41,55,.4),rgba(55,65,81,.2));
        padding: 36px; border-radius: 22px;
        border: 1.5px solid rgba(74,222,128,.25); margin-bottom: 24px;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 24px rgba(0,0,0,.15),inset 0 1px 2px rgba(255,255,255,.03);
    }

    /* ── SECTION HEADERS ── */
    .section-header {
        font-size: 28px; font-weight: 900;
        background: linear-gradient(135deg,#22c55e,#4ade80);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-top: 28px; margin-bottom: 20px; letter-spacing: -0.5px;
    }
    .section-header::after {
        content: ''; display: block; width: 48px; height: 3px;
        background: linear-gradient(90deg,#22c55e,#4ade80);
        margin-top: 10px; border-radius: 2px;
    }

    /* ── PROGRESS BAR ── */
    .progress-bar {
        width: 100%; height: 14px;
        background: rgba(74,222,128,.08); border-radius: 12px; overflow: hidden;
        margin-top: 10px; border: 1px solid rgba(74,222,128,.2);
        box-shadow: inset 0 2px 4px rgba(0,0,0,.1);
    }
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg,#22c55e,#4ade80,#86efac);
        border-radius: 12px;
        box-shadow: 0 0 12px rgba(34,197,94,.5);
        animation: fillPulse 2s ease-in-out infinite;
    }
    @keyframes fillPulse {
        0%,100% { box-shadow: 0 0 12px rgba(34,197,94,.5); }
        50%     { box-shadow: 0 0 20px rgba(34,197,94,.8); }
    }

    /* ── SEPARATORS ── */
    hr {
        border: none; height: 1px;
        background: linear-gradient(90deg,transparent,rgba(74,222,128,.2),transparent);
        margin: 24px 0;
    }

    /* ── INPUTS ── */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background-color: rgba(31,41,55,.6) !important;
        border: 1.5px solid rgba(74,222,128,.3) !important;
        border-radius: 12px !important; color: #e5e7eb !important;
        padding: 12px 16px !important; font-weight: 500;
        transition: all 0.3s ease !important;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: rgba(74,222,128,.8) !important;
        box-shadow: 0 0 12px rgba(34,197,94,.3) !important;
    }

    /* ── ALERTS ── */
    .stInfo, .stWarning, .stSuccess, .stError {
        border-radius: 14px !important; border-left: 4px solid !important;
        padding: 16px !important;
    }
    .stInfo    { background-color: rgba(59,130,246,.1) !important; border-left-color: #3b82f6 !important; }
    .stWarning { background-color: rgba(245,158,11,.1)  !important; border-left-color: #f59e0b !important; }
    .stSuccess { background-color: rgba(34,197,94,.1)   !important; border-left-color: #22c55e !important; }
    .stError   { background-color: rgba(239,68,68,.1)   !important; border-left-color: #ef4444 !important; }

    /* ── PRIMARY BUTTON ── */
    .stButton > button {
        background: linear-gradient(135deg,#22c55e,#4ade80) !important;
        color: #0a2818 !important; font-weight: 800 !important; font-size: 16px !important;
        padding: 14px 32px !important; border: none !important; border-radius: 12px !important;
        box-shadow: 0 8px 24px rgba(34,197,94,.3) !important;
        transition: all 0.3s cubic-bezier(0.23,1,.32,1) !important;
        letter-spacing: 0.5px !important;
    }
    .stButton > button:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 16px 40px rgba(34,197,94,.5) !important;
    }
    .stButton > button:active { transform: translateY(-2px) !important; }

    /* ── DOWNLOAD BUTTON (distinct blue so user knows it's a different action) ── */
    .stDownloadButton > button {
        background: linear-gradient(135deg,#1d4ed8,#3b82f6) !important;
        color: #ffffff !important; font-weight: 700 !important; font-size: 15px !important;
        padding: 12px 28px !important; border: none !important; border-radius: 12px !important;
        box-shadow: 0 8px 24px rgba(59,130,246,.3) !important;
        transition: all 0.3s cubic-bezier(0.23,1,.32,1) !important;
        letter-spacing: 0.3px !important;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 14px 32px rgba(59,130,246,.45) !important;
    }

    /* ── SIDEBAR ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg,rgba(10,40,24,.97),rgba(15,61,31,.97)) !important;
        border-right: 1px solid rgba(74,222,128,.2) !important;
    }
    .sidebar-stat {
        background: rgba(34,197,94,.08);
        border: 1px solid rgba(74,222,128,.25);
        border-radius: 14px; padding: 16px; margin-bottom: 12px;
    }

    /* ── TABS ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(31,41,55,.4) !important;
        border-radius: 14px; padding: 6px;
        border: 1px solid rgba(74,222,128,.2);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important; font-weight: 600 !important;
        color: #9ca3af !important; padding: 10px 20px !important;
        transition: all 0.2s ease !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg,#22c55e,#4ade80) !important;
        color: #0a2818 !important; font-weight: 800 !important;
    }

    /* ── DATAFRAME ── */
    [data-testid="stDataFrame"] { border-radius: 14px !important; overflow: hidden; }

    /* ── BOUNCE ANIMATION (empty state) ── */
    @keyframes bounce {
        0%,100% { transform: translateY(0); }
        50%     { transform: translateY(-12px); }
    }
</style>
""", unsafe_allow_html=True)


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 20px 0 8px;'>
        <div style='font-size:52px;'>🌱</div>
        <div style='font-size:22px; font-weight:900; color:#4ade80; margin-top:8px;'>EcoBuddy AI+</div>
        <div style='font-size:12px; color:#9ca3af; margin-top:4px;'>Carbon Footprint Tracker</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Live summary from session state
    if st.session_state.get("analyzed", False):
        eco_score_sb = st.session_state.eco_score
        total_sb     = st.session_state.total

        if eco_score_sb >= 85:
            status_color, status_text = "#fbbf24", "🌟 Eco Champion"
        elif eco_score_sb >= 70:
            status_color, status_text = "#4ade80", "🌿 Green Guardian"
        elif eco_score_sb >= 50:
            status_color, status_text = "#60a5fa", "🍃 Eco Learner"
        else:
            status_color, status_text = "#f87171", "🔥 High Impact"

        st.markdown(f"""
        <div class='sidebar-stat'>
            <div style='font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;'>Current Session</div>
            <div style='font-size:24px;font-weight:900;color:#4ade80;margin:6px 0;'>{total_sb:.0f} <span style='font-size:12px;color:#9ca3af;'>kg CO₂</span></div>
            <div style='font-size:13px;color:{status_color};font-weight:700;'>{status_text}</div>
        </div>
        <div class='sidebar-stat'>
            <div style='font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;'>Eco Score</div>
            <div style='font-size:28px;font-weight:900;color:#4ade80;'>{eco_score_sb}<span style='font-size:12px;color:#9ca3af;'>/100</span></div>
            <div style='height:8px;background:rgba(74,222,128,.1);border-radius:8px;margin-top:8px;overflow:hidden;'>
                <div style='width:{eco_score_sb}%;height:100%;background:linear-gradient(90deg,#22c55e,#4ade80);border-radius:8px;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='sidebar-stat' style='text-align:center;'>
            <div style='font-size:28px;margin-bottom:8px;'>📊</div>
            <div style='color:#9ca3af;font-size:13px;'>Fill in your profile and click<br><b style='color:#4ade80;'>Analyze My Impact</b><br>to see your stats here.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # History quick stats
    history_sb = get_assessments()
    if history_sb:
        df_sb = pd.DataFrame(history_sb, columns=[
            "id","date","transport","distance","electricity","diet","flights","footprint","eco_score"
        ])
        st.markdown(f"""
        <div style='font-size:13px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;'>All-Time Stats</div>
        <div class='sidebar-stat'>
            <div style='color:#9ca3af;font-size:11px;'>Assessments</div>
            <div style='color:#4ade80;font-size:22px;font-weight:900;'>{len(history_sb)}</div>
        </div>
        <div class='sidebar-stat'>
            <div style='color:#9ca3af;font-size:11px;'>Avg Footprint</div>
            <div style='color:#4ade80;font-size:22px;font-weight:900;'>{df_sb['footprint'].mean():.0f} <span style='font-size:11px;color:#9ca3af;'>kg CO₂</span></div>
        </div>
        <div class='sidebar-stat'>
            <div style='color:#9ca3af;font-size:11px;'>Best Score</div>
            <div style='color:#4ade80;font-size:22px;font-weight:900;'>{df_sb['eco_score'].max()}<span style='font-size:11px;color:#9ca3af;'>/100</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style='font-size:11px;color:#6b7280;text-align:center;padding-bottom:12px;'>
        🌍 Every small action counts.<br>Track · Improve · Inspire.
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# MAIN HEADER
# =========================================================
st.markdown("<div class='title'>🌱 EcoBuddy AI+</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Your Personal AI-Powered Carbon Footprint Tracker & Eco Assistant</div>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align:center;margin-bottom:28px;'>
    <div style='display:inline-flex;gap:16px;padding:12px 24px;
                background:rgba(34,197,94,.08);border-radius:50px;
                border:1px solid rgba(74,222,128,.2);'>
        <span style='color:#d1d5db;font-size:13px;font-weight:600;'>✨ Track &nbsp;•&nbsp; 📊 Analyze &nbsp;•&nbsp; 💡 Improve</span>
    </div>
</div>
""", unsafe_allow_html=True)


# =========================================================
# TABS  — keeps the page clean instead of one giant scroll
# =========================================================
tab_input, tab_results, tab_history = st.tabs([
    "📝  Lifestyle Profile",
    "📊  My Analysis",
    "📈  Eco Journey"
])


# =========================================================
# TAB 1 — INPUT FORM
# =========================================================
with tab_input:
    st.markdown("<div class='section-header'>📝 Your Lifestyle Profile</div>", unsafe_allow_html=True)
    st.markdown("<div class='input-section'>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style='display:flex;align-items:center;gap:8px;margin-bottom:16px;'>
            <span style='font-size:24px;'>🚗</span>
            <span style='font-size:18px;font-weight:700;color:#e5e7eb;'>Transportation</span>
        </div>
        """, unsafe_allow_html=True)
        transport = st.selectbox(
            "Primary Transport",
            ["Car", "Public Transport", "Bike", "Walking"],
            help="Select how you travel most days. Car = personal petrol/diesel vehicle."
        )
        distance = st.number_input(
            "Daily Distance (km)",
            min_value=0.0, value=10.0, step=1.0,
            help="Estimate the total km you travel daily for work, errands, or school."
        )

    with col2:
        st.markdown("""
        <div style='display:flex;align-items:center;gap:8px;margin-bottom:16px;'>
            <span style='font-size:24px;'>⚡</span>
            <span style='font-size:18px;font-weight:700;color:#e5e7eb;'>Energy & Diet</span>
        </div>
        """, unsafe_allow_html=True)
        electricity = st.number_input(
            "Monthly Electricity (kWh)",
            min_value=0.0, value=200.0, step=10.0,
            help="Check your electricity bill. A typical household uses 200–400 kWh/month."
        )
        diet = st.selectbox(
            "Diet Type",
            ["Vegetarian", "Non-Vegetarian"],
            help="Vegetarian diets produce roughly 45% less food-related CO₂ than meat-heavy diets."
        )

    with col3:
        st.markdown("""
        <div style='display:flex;align-items:center;gap:8px;margin-bottom:16px;'>
            <span style='font-size:24px;'>✈️</span>
            <span style='font-size:18px;font-weight:700;color:#e5e7eb;'>Air Travel</span>
        </div>
        """, unsafe_allow_html=True)
        flights = st.number_input(
            "Annual Flights",
            min_value=0, value=0, step=1,
            help="Count each one-way trip as 1 flight. A round trip = 2 flights."
        )
        st.info("💡 Long-haul flights are among the highest per-trip emission sources.")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── ANALYZE BUTTON ──
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1.5, 1])
    with col_btn2:
        analyze_btn = st.button("🌿 Analyze My Impact", use_container_width=True)

    if analyze_btn:
        with st.spinner("🌍 Calculating your carbon footprint..."):
            total, contributors = calculate_footprint(
                transport, distance, electricity, diet, flights
            )

        eco_score = calculate_eco_score(total)
        insight, recommendations = generate_recommendations(
            transport, electricity, diet, flights, contributors
        )
        save_assessment(transport, distance, electricity, diet, flights, total, eco_score)

        # Persist in session state
        st.session_state.total           = total
        st.session_state.contributors    = contributors
        st.session_state.eco_score       = eco_score
        st.session_state.insight         = insight
        st.session_state.recommendations = recommendations
        st.session_state.analyzed        = True

        st.toast("✅ Analysis complete! Check the 'My Analysis' tab.", icon="🌱")
        st.success("✅ Analysis completed! Switch to the **📊 My Analysis** tab to see your results.")


# =========================================================
# TAB 2 — RESULTS DASHBOARD
# =========================================================
with tab_results:
    if not st.session_state.get("analyzed", False):
        st.markdown("""
        <div class='card-highlight' style='text-align:center;padding:60px 32px;'>
            <div style='font-size:72px;margin-bottom:20px;animation:bounce 2s infinite;'>🌿</div>
            <div style='font-size:24px;font-weight:800;color:#4ade80;margin-bottom:12px;'>No Analysis Yet</div>
            <div style='color:#d1d5db;font-size:16px;line-height:1.8;max-width:400px;margin:0 auto;'>
                Head over to the <b style='color:#4ade80;'>📝 Lifestyle Profile</b> tab,
                fill in your details, and click <b style='color:#4ade80;'>Analyze My Impact</b>.
            </div>
        </div>
        <style>@keyframes bounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}</style>
        """, unsafe_allow_html=True)
    else:
        total        = st.session_state.total
        contributors = st.session_state.contributors
        eco_score    = st.session_state.eco_score
        insight      = st.session_state.insight
        recommendations = st.session_state.recommendations

        # ── TOP METRIC CARDS ──
        st.markdown("<div class='section-header'>📊 Carbon Footprint Analysis</div>", unsafe_allow_html=True)

        met1, met2, met3, met4 = st.columns(4)
        biggest_key = max(contributors, key=contributors.get)
        biggest_val = contributors[biggest_key]

        # Color-code footprint card based on severity
        footprint_color = "#4ade80" if total <= 3000 else ("#fbbf24" if total <= 5000 else "#f87171")

        with met1:
            st.markdown(metric_card("🌍 Total Footprint", f"{total:.0f}", "kg CO₂/year", footprint_color), unsafe_allow_html=True)
        with met2:
            score_color = "#4ade80" if eco_score >= 70 else ("#fbbf24" if eco_score >= 50 else "#f87171")
            st.markdown(metric_card("🏆 Eco Score", str(eco_score), "out of 100", score_color), unsafe_allow_html=True)
        with met3:
            st.markdown(metric_card("📈 Biggest Source", biggest_key, f"{biggest_val:.0f} kg CO₂"), unsafe_allow_html=True)
        with met4:
            global_avg = 4800
            diff = global_avg - total
            diff_label = f"{abs(diff):.0f} kg below avg" if diff > 0 else f"{abs(diff):.0f} kg above avg"
            diff_color = "#4ade80" if diff > 0 else "#f87171"
            st.markdown(metric_card("🌐 vs Global Avg", diff_label, "4,800 kg/yr avg", diff_color), unsafe_allow_html=True)

        st.markdown("---")

        # ── BADGE + PIE CHART ──
        col_badge1, col_badge2 = st.columns([1, 1])

        with col_badge1:
            st.markdown("<div class='section-header' style='margin-top:0;'>🏅 Eco Achievement</div>", unsafe_allow_html=True)

            if eco_score >= 85:
                badge_text, badge_class = "🌟 Eco Champion",    "badge badge-champion"
                desc = "🌟 Excellent! You're making exceptional environmental choices."
                desc_fn = st.info
            elif eco_score >= 70:
                badge_text, badge_class = "🌿 Green Guardian",  "badge badge-guardian"
                desc = "🌿 Great work! Your footprint is below average."
                desc_fn = st.info
            elif eco_score >= 50:
                badge_text, badge_class = "🍃 Eco Learner",     "badge badge-learner"
                desc = "🍃 Good start! There's meaningful room to improve."
                desc_fn = st.info
            else:
                badge_text, badge_class = "🔥 High Impact",     "badge badge-high"
                desc = "🔥 Your footprint is above average. Let's work on reducing it!"
                desc_fn = st.warning

            st.markdown(f"<div class='{badge_class}' role='status' aria-label='Achievement badge: {badge_text}'>{badge_text}</div>", unsafe_allow_html=True)

            st.markdown(f"""
            <div style='margin-top:16px;'>
                <div style='display:flex;justify-content:space-between;margin-bottom:6px;'>
                    <span style='color:#d1d5db;font-size:14px;'>Score Progress</span>
                    <span style='color:#4ade80;font-weight:700;'>{eco_score}%</span>
                </div>
                <div class='progress-bar' role='progressbar' aria-valuenow='{eco_score}' aria-valuemin='0' aria-valuemax='100'>
                    <div class='progress-fill' style='width:{eco_score}%;'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            desc_fn(desc)

        with col_badge2:
            st.markdown("<div class='section-header' style='margin-top:0;'>📊 Emission Sources</div>", unsafe_allow_html=True)
            fig = go.Figure(data=[go.Pie(
                labels=list(contributors.keys()),
                values=list(contributors.values()),
                hole=0.42,
                marker=dict(colors=['#4ade80','#60a5fa','#fbbf24','#f87171'],
                            line=dict(color='rgba(0,0,0,0.1)',width=2)),
                textposition='auto',
                hovertemplate='<b>%{label}</b><br>%{value:.0f} kg CO₂<br>%{percent}<extra></extra>'
            )])
            fig.update_layout(
                showlegend=True, height=280,
                margin=dict(l=0,r=0,t=0,b=0),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#d1d5db',size=12),
                legend=dict(x=-0.15,y=1,bgcolor='rgba(0,0,0,0.3)',
                            bordercolor='rgba(74,222,128,0.3)',borderwidth=1)
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")

        # ── BAR CHART ──
        st.markdown("<div class='section-header'>📋 Detailed Breakdown</div>", unsafe_allow_html=True)
        bar_colors = ['#4ade80','#60a5fa','#fbbf24','#f87171']
        breakdown_fig = go.Figure(data=[go.Bar(
            x=list(contributors.keys()),
            y=list(contributors.values()),
            marker=dict(color=bar_colors[:len(contributors)],
                        line=dict(color='rgba(255,255,255,0.2)',width=2)),
            text=[f'{v:.0f} kg' for v in contributors.values()],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>%{y:.0f} kg CO₂<extra></extra>'
        )])
        breakdown_fig.update_layout(
            height=320, margin=dict(l=40,r=20,t=20,b=40),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(55,65,81,0.2)',
            font=dict(color='#d1d5db',size=12),
            xaxis=dict(showgrid=False,zeroline=False,color='#9ca3af'),
            yaxis=dict(showgrid=True,gridwidth=1,gridcolor='rgba(74,222,128,0.1)',
                       zeroline=False,color='#9ca3af'),
            showlegend=False
        )
        st.plotly_chart(breakdown_fig, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")


        # ── AI INSIGHT + DYNAMIC QUICK TIPS ──
        st.markdown("<div class='section-header'>🤖 AI Insights & Analysis</div>", unsafe_allow_html=True)

        col_insight1, col_insight2 = st.columns([1.2, 0.8])

        with col_insight1:
            st.markdown(f"""
            <div class='card-highlight'>
                <div style='display:flex;gap:12px;align-items:flex-start;'>
                    <div style='font-size:32px;' aria-hidden='true'>💡</div>
                    <div style='flex:1;'>
                        <div style='font-size:16px;font-weight:800;color:#4ade80;margin-bottom:12px;'>Key Finding</div>
                        <div style='font-size:15px;color:#d1d5db;line-height:1.8;'>{insight}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_insight2:
            # Dynamic tips based on the user's actual data
            dynamic_tips = get_dynamic_tips(contributors)
            tips_html = "".join([f"<li style='margin-bottom:10px;'>{t}</li>" for t in dynamic_tips])
            st.markdown(f"""
            <div class='card'>
                <div style='display:flex;gap:12px;align-items:flex-start;'>
                    <div style='font-size:32px;' aria-hidden='true'>🎯</div>
                    <div style='flex:1;'>
                        <div style='font-size:16px;font-weight:800;color:#4ade80;margin-bottom:12px;'>Your Top Tips</div>
                        <ul style='color:#d1d5db;font-size:14px;line-height:1.7;padding-left:18px;margin:0;'>
                            {tips_html}
                        </ul>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # ── RECOMMENDATIONS ──
        st.markdown("<div class='section-header'>💡 Personalized Recommendations</div>", unsafe_allow_html=True)

        if recommendations:
            for r in recommendations:
                st.markdown(f"""
                <div class='card' style='border-left:4px solid #22c55e;'>
                    <div style='display:flex;gap:12px;'>
                        <div style='font-size:24px;' aria-hidden='true'>💚</div>
                        <div style='flex:1;font-size:15px;line-height:1.8;color:#d1d5db;'>{r}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='card-highlight'>
                <div style='display:flex;gap:16px;align-items:center;'>
                    <div style='font-size:48px;'>🌟</div>
                    <div>
                        <div style='font-size:18px;font-weight:700;color:#4ade80;margin-bottom:4px;'>Excellent Work!</div>
                        <div style='color:#d1d5db;'>Your lifestyle is already very eco-friendly. Keep it up!</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # ── PDF DOWNLOAD ──
        pdf_buffer = generate_pdf(total, eco_score, insight, recommendations)
        col_d1, col_d2, col_d3 = st.columns([1, 1.4, 1])
        with col_d2:
            st.download_button(
                "📄 Download Eco Report (PDF)",
                pdf_buffer,
                file_name="EcoBuddy_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )


# =========================================================
# TAB 3 — HISTORY & TRACKING
# =========================================================
with tab_history:
    history = get_assessments()

    if not history:
        st.markdown("""
        <div class='card-highlight' style='text-align:center;padding:60px 32px;'>
            <div style='font-size:72px;margin-bottom:20px;animation:bounce 2s infinite;'>🌱</div>
            <div style='font-size:24px;font-weight:800;color:#4ade80;margin-bottom:12px;'>No Data Yet</div>
            <div style='color:#d1d5db;font-size:16px;line-height:1.6;max-width:400px;margin:0 auto;'>
                Start your eco journey! Complete the Lifestyle Profile and click
                <b style='color:#4ade80;'>Analyze My Impact</b> to generate your first report.
            </div>
        </div>
        <style>@keyframes bounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}</style>
        """, unsafe_allow_html=True)
    else:
        df = pd.DataFrame(history, columns=[
            "id","date","transport","distance","electricity","diet","flights","footprint","eco_score"
        ])
        latest = df.iloc[0]

        # ── QUICK STATS ROW ──
        st.markdown("<div class='section-header'>📈 Your Eco Journey</div>", unsafe_allow_html=True)

        stat1, stat2, stat3, stat4 = st.columns(4)

        with stat1:
            st.markdown(stat_card("Latest Footprint", f"{latest['footprint']:.0f}", "kg CO₂"), unsafe_allow_html=True)
        with stat2:
            st.markdown(stat_card("Latest Score", str(int(latest['eco_score'])), "out of 100"), unsafe_allow_html=True)
        with stat4:
            st.markdown(stat_card("Total Records", str(len(history)), "assessments saved"), unsafe_allow_html=True)

        # Change column — only show when there are at least 2 records
        with stat3:
            if len(history) >= 2:
                prev_fp = df.iloc[1]['footprint']
                change  = ((prev_fp - latest['footprint']) / prev_fp * 100) if prev_fp else 0
                if change > 0:
                    c_color, c_emoji, c_label = "#4ade80", "📉", "Reduced"
                elif change < 0:
                    c_color, c_emoji, c_label = "#f87171", "📈", "Increased"
                else:
                    c_color, c_emoji, c_label = "#60a5fa",  "→",  "No Change"
                st.markdown(f"""
                <div class='card'>
                    <div style='font-size:12px;color:#9ca3af;'>{c_emoji} {c_label}</div>
                    <div style='font-size:28px;font-weight:900;color:{c_color};'>{abs(change):.1f}%</div>
                    <div style='font-size:11px;color:#9ca3af;'>vs previous</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class='card'>
                    <div style='font-size:12px;color:#9ca3af;'>📊 Trend</div>
                    <div style='font-size:15px;font-weight:600;color:#9ca3af;margin-top:8px;'>Need 2+ records</div>
                    <div style='font-size:11px;color:#6b7280;'>Submit another assessment</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # ── TREND LINE CHART ──
        st.markdown("<div class='section-header'>📉 Carbon Footprint Trend</div>", unsafe_allow_html=True)

        trend_df = df[["date","footprint"]].iloc[::-1].reset_index(drop=True)
        trend_df['date'] = pd.to_datetime(trend_df['date'])

        trend_fig = go.Figure()
        trend_fig.add_trace(go.Scatter(
            x=trend_df['date'], y=trend_df['footprint'],
            mode='lines+markers', name='Carbon Footprint',
            line=dict(color='#4ade80',width=3),
            marker=dict(size=8,color='#4ade80',line=dict(color='#86efac',width=2)),
            fill='tozeroy', fillcolor='rgba(74,222,128,0.15)',
            hovertemplate='<b>%{x|%b %d, %Y}</b><br>%{y:.0f} kg CO₂<extra></extra>'
        ))
        # Global average reference line
        trend_fig.add_hline(
            y=4800, line_dash="dash", line_color="rgba(248,113,113,0.5)",
            annotation_text="Global avg (4,800 kg)", annotation_position="bottom right",
            annotation_font_color="#f87171"
        )
        trend_fig.update_layout(
            height=320, margin=dict(l=40,r=20,t=20,b=40),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(55,65,81,0.2)',
            font=dict(color='#d1d5db',size=12),
            xaxis=dict(showgrid=False,zeroline=False,color='#9ca3af'),
            yaxis=dict(showgrid=True,gridwidth=1,gridcolor='rgba(74,222,128,0.1)',
                       zeroline=False,color='#9ca3af'),
            showlegend=False, hovermode='x unified'
        )
        st.plotly_chart(trend_fig, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")

        # ── HISTORY TABLE (styled with column_config) ──
        st.markdown("<div class='section-header'>📋 Assessment History</div>", unsafe_allow_html=True)

        display_df = df[["date","transport","electricity","footprint","eco_score"]].copy()
        display_df.columns = ["Date","Transport","Electricity (kWh)","Footprint (kg CO₂)","Score"]
        display_df = display_df.iloc[::-1].reset_index(drop=True)
        max_fp = int(display_df["Footprint (kg CO₂)"].max()) + 500

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Date": st.column_config.DatetimeColumn("📅 Date", format="MMM DD, YYYY · HH:mm"),
                "Transport": st.column_config.TextColumn("🚗 Transport"),
                "Electricity (kWh)": st.column_config.NumberColumn("⚡ Electricity", format="%.0f kWh"),
                "Footprint (kg CO₂)": st.column_config.ProgressColumn(
                    "🌍 Footprint (kg CO₂)", format="%.0f kg",
                    min_value=0, max_value=max_fp
                ),
                "Score": st.column_config.ProgressColumn(
                    "🏆 Score", format="%d / 100",
                    min_value=0, max_value=100
                ),
            }
        )

        st.markdown("---")

        # ── AGGREGATE STATS ──
        st.markdown("<div class='section-header'>📊 Your Statistics</div>", unsafe_allow_html=True)

        sc1, sc2, sc3 = st.columns(3)
        avg_fp  = df['footprint'].mean()
        avg_sc  = df['eco_score'].mean()
        min_fp  = df['footprint'].min()
        max_fp2 = df['footprint'].max()

        with sc1:
            st.markdown(f"""
            <div class='card'>
                <div style='font-size:13px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin-bottom:12px;'>📊 Average Footprint</div>
                <div style='font-size:36px;font-weight:900;color:#4ade80;'>{avg_fp:.0f}</div>
                <div style='font-size:12px;color:#9ca3af;margin-top:8px;'>kg CO₂ across {len(history)} records</div>
            </div>
            """, unsafe_allow_html=True)
        with sc2:
            st.markdown(f"""
            <div class='card'>
                <div style='font-size:13px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin-bottom:12px;'>🎯 Average Score</div>
                <div style='font-size:36px;font-weight:900;color:#4ade80;'>{avg_sc:.0f}</div>
                <div style='font-size:12px;color:#9ca3af;margin-top:8px;'>out of 100 points</div>
            </div>
            """, unsafe_allow_html=True)
        with sc3:
            st.markdown(f"""
            <div class='card'>
                <div style='font-size:13px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin-bottom:12px;'>📈 Best vs Worst</div>
                <div style='display:flex;align-items:center;gap:8px;margin-top:8px;'>
                    <div>
                        <div style='font-size:11px;color:#4ade80;'>Best</div>
                        <div style='font-size:24px;font-weight:700;color:#4ade80;'>{min_fp:.0f}</div>
                    </div>
                    <div style='color:#6b7280;font-size:20px;'>→</div>
                    <div>
                        <div style='font-size:11px;color:#f87171;'>Highest</div>
                        <div style='font-size:24px;font-weight:700;color:#f87171;'>{max_fp2:.0f}</div>
                    </div>
                </div>
                <div style='font-size:11px;color:#9ca3af;margin-top:8px;'>kg CO₂</div>
            </div>
            """, unsafe_allow_html=True)
