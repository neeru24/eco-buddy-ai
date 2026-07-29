import html
import time
import streamlit as st

st.set_page_config(
    page_title="EcoBuddy",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import tempfile
import uuid
import os
from dotenv import load_dotenv

load_dotenv()
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from database import init_db, save_assessment, get_assessments, init_gamification_db, verify_user, create_user
import gamification as gf
from emissions import calculate_footprint, calculate_eco_score
from llm_parser import parse_quick_log

from recommendations import generate_recommendations
from ocr_utils import extract_text_from_file, parse_energy_consumption

# Added for Route Planning & Offsets
from database import (
    init_marketplace_db, save_journey_profile, get_journey_profiles, delete_journey_profile,
    save_offset_transaction, get_offset_transactions, delete_offset_transaction, clear_offset_transactions,
    get_total_offsets, get_total_spend
)
from marketplace import (
    calculate_trip_emissions, calculate_recurring_trip_emissions, compare_transit_modes,
    calculate_offset_cost, validate_offset_transaction, get_offset_projects,
    calculate_net_emissions, calculate_net_zero_progress, get_project_by_id, EMISSION_FACTORS
)
from styles.theme import apply_theme, render_theme_selector



DEFAULT_VALUES = {
    "region": "Global",
    "transport": "Car",
    "distance": 10.0,
    "electricity": 200.0,
    "diet": "Vegetarian",
    "flights": 0,
}

def h(text):
    return html.escape(str(text))


def render_sidebar_auth():
    st.sidebar.title("Authentication")
    if 'user_id' not in st.session_state:
        st.session_state['user_id'] = None
        st.session_state['username'] = None

    if st.session_state['user_id'] is None:
        auth_mode = st.sidebar.radio("Choose Mode", ["Login", "Register", "Guest"])
        if auth_mode == "Login":
            with st.sidebar.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    user = verify_user(username, password)
                    if user:
                        st.session_state['user_id'] = user['id']
                        st.session_state['username'] = user['username']
                        st.sidebar.success("Logged in successfully!")
                        st.rerun()
                    else:
                        st.sidebar.error("Invalid username or password")
        elif auth_mode == "Register":
            with st.sidebar.form("register_form"):
                username = st.text_input("Username")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Register"):
                    if create_user(username, email, password):
                        st.sidebar.success("Registration successful! Please login.")
                    else:
                        st.sidebar.error("Username or email already exists")
        elif auth_mode == "Guest":
            if st.sidebar.button("Continue as Guest"):
                st.session_state['user_id'] = 1
                st.session_state['username'] = "Guest"
                st.rerun()
        
        st.sidebar.warning("Please log in or continue as Guest to use the app.")
        st.stop()
    else:
        st.sidebar.write(f"Logged in as **{st.session_state['username']}**")
        if st.sidebar.button("Logout"):
            st.session_state['user_id'] = None
            st.session_state['username'] = None
            st.session_state.pop('draft_status', None)
            for key, val in DEFAULT_VALUES.items():
                st.session_state[key] = val
            st.rerun()

    return st.session_state['user_id']

# -------------------------
# INIT
# -------------------------

@st.cache_resource
def run_db_initializations():
    # Run migrations first to ensure database schema is up to date
    from database import migrate
    success, message = migrate()
    if not success:
        print(f"Warning: Migration failed: {message}")
    else:
        print(f"Database: {message}")
    
    init_db()
    init_gamification_db()
    init_marketplace_db()

run_db_initializations()
user_id = render_sidebar_auth()
render_theme_selector()

if 'extracted_kwh' not in st.session_state:
    st.session_state.extracted_kwh = 200.0


# -------------------------
# DRAFT RECOVERY & DEFAULT FORM VALUES
# -------------------------
from database import save_assessment_draft, get_assessment_draft, delete_assessment_draft

if 'draft_status' not in st.session_state:
    st.session_state.draft_status = None

# Check for draft
draft = None
if user_id and st.session_state.draft_status is None:
    draft = get_assessment_draft(user_id)

for key, value in DEFAULT_VALUES.items():
    if key not in st.session_state:
        st.session_state[key] = value

# page config moved to top


# -------------------------
# THEME APPLICATION
# -------------------------
apply_theme()


# -------------------------
# HEADER
# -------------------------
st.markdown("<div class='title'>🌱 EcoBuddy AI+</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Your Personal AI-Powered Carbon Footprint Tracker & Eco Assistant</div>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; margin-bottom: 32px;'>
    <div style='display: inline-flex; gap: 16px; padding: 12px 24px; background: rgba(34, 197, 94, 0.08); border-radius: 50px; border: 1px solid rgba(74, 222, 128, 0.2);'>
        <span style='color: #000; font-size: 15px; font-weight: 700;'>✨ Track • 📊 Analyze • 💡 Improve</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")


# -------------------------
# INPUTS SECTION
# ------------------------


# -------------------------

tab1, tab2, tab3, tab4 = st.tabs(["🌍 Carbon Footprint", "⚡ Home Energy Audit", "🎮 Gamification", "🗺️ Route Planning & Offsets"])

with tab1:
    st.markdown("<div class='section-header'>📝 Your Lifestyle Profile</div>", unsafe_allow_html=True)

    # Draft recovery prompt
    if user_id and draft:
        st.info("📝 We found an unfinished assessment from your previous session. Would you like to restore it?")
        col_rest, col_disc, _ = st.columns([1, 1, 4])
        with col_rest:
            if st.button("✅ Restore Session", key="restore_session_btn"):
                st.session_state.draft_status = 'restored'
                for key, val in draft.items():
                    st.session_state[key] = val
                st.success("Session restored successfully!")
                st.rerun()
        with col_disc:
            if st.button("🗑️ Discard Draft", key="discard_draft_btn"):
                delete_assessment_draft(user_id)
                st.session_state.draft_status = 'discarded'
                st.success("Draft discarded.")
                st.rerun()
    
    st.markdown("### Region Setting")
    region = st.selectbox("Select Your Region for API Emissions Factor", ["Global", "US", "UK", "EU"], key="region")

    # -------------------------
    # QUICK LOG (AI)
    # -------------------------
    st.markdown("### 🤖 AI Quick Log")
    col_ai_input, col_ai_btn = st.columns([4, 1])
    with col_ai_input:
        quick_log_text = st.text_area("Let AI auto-fill your profile! Describe your day naturally.", placeholder="e.g., 'I drove 15 miles in my SUV and had a beef steak'", key="quick_log_input", height=68)
    with col_ai_btn:
        st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)
        parse_btn = st.button("✨ Parse with AI", use_container_width=True)
        
    if parse_btn:
        if quick_log_text.strip():
            with st.spinner("Analyzing text..."):
                parsed_data = parse_quick_log(quick_log_text)
                if parsed_data:
                    st.session_state.temp_parsed = parsed_data
                else:
                    st.error("Could not parse the text. Please try again.")
        else:
            st.warning("Please enter some text first.")

    if "temp_parsed" in st.session_state:
        tp = st.session_state.temp_parsed
        st.info(f"**We found:** {tp.get('distance', 10.0)} km by {tp.get('transport', 'Car')}, and {tp.get('diet', 'Vegetarian')} diet. Is this correct?")
        c_yes, c_no = st.columns(2)
        with c_yes:
            if st.button("✅ Yes, use this", key="confirm_yes"):
                st.session_state.transport = tp.get('transport', 'Car')
                st.session_state.distance = float(tp.get('distance', 10.0))
                st.session_state.diet = tp.get('diet', 'Vegetarian')
                del st.session_state.temp_parsed
                if user_id:
                    save_assessment_draft(user_id, st.session_state.transport, st.session_state.distance, st.session_state.get("electricity", 200.0), st.session_state.diet, st.session_state.get("flights", 0), st.session_state.get("region", "Global"))
                st.rerun()
        with c_no:
            if st.button("❌ No, cancel", key="confirm_no"):
                del st.session_state.temp_parsed
                st.rerun()

    col1, col2, col3 = st.columns(3)
 
 
    with col1:
        st.markdown("""
        <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 16px;'>
            <span style='font-size: 24px;'>🚗</span>
            <span style='font-size: 18px; font-weight: 700; color: #000;'>Transportation</span>
        </div>
        """, unsafe_allow_html=True)
        transport = st.selectbox("Primary Transport", ["Car", "Public Transport", "Bike", "Walking"], key="transport")
        distance = st.number_input("Daily Distance (km)", min_value=0.0, key="distance", step=1.0)

    with col2:
        st.markdown("""
            <style>
            div[data-testid="stFileUploader"] button {
                width: 110px !important;
                min-width: 110px !important;
                padding: 6px 12px !important;
                margin-left: 16px !important;
                border-radius: 8px !important;
            }

            div[data-testid="stFileUploader"] section {
                display: flex !important;
                align-items: center !important;
                gap: 16px !important;
            }
            </style>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 16px;'>
            <span style='font-size: 24px;'>⚡</span>
            <span style='font-size: 18px; font-weight: 700; color: #000;'>Energy & Diet</span>
        </div>
        """, unsafe_allow_html=True)
        uploaded_bill = st.file_uploader("Upload Utility Bill (PDF/Image)", type=["pdf", "png", "jpg", "jpeg"])
        if uploaded_bill is not None:
            # We use a button to trigger extraction so it doesn't re-run infinitely on every interaction
            if st.button("Extract Energy Usage"):
                with st.spinner("Extracting data from bill..."):
                    extracted_text = extract_text_from_file(uploaded_bill)
                    parsed_val = parse_energy_consumption(extracted_text)
                    if parsed_val is not None:
                        st.session_state.extracted_kwh = float(parsed_val)
                        st.session_state.electricity = float(parsed_val)
                        st.success(f"Extracted {parsed_val} kWh from bill!")
                    else:
                        st.warning("Could not extract energy consumption. Please enter manually.")

        electricity = st.number_input("Monthly Electricity (kWh)", min_value=0.0, key="electricity", step=10.0)
        diet = st.selectbox("Diet Type", ["Vegetarian", "Non-Vegetarian"], key="diet")
    
        col1, col2 = st.columns(2)
    with col3:
        st.markdown("""
        <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 16px;'>
            <span style='font-size: 24px;'>✈️</span>
            <span style='font-size: 18px; font-weight: 700; color: #000;'>Travel</span>
        </div>
        """, unsafe_allow_html=True)
        flights = st.number_input("Annual Flights", min_value=0, key="flights", step=1)
        st.info("💡 How many long-distance flights per year?")
        



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
    # CALCULATE & ANALYZE
    # -------------------------
    

 


    # col_btn1, col_btn2, col_btn3 = st.columns([1, 1.5, 1])
    # with col_btn2:
    #     analyze_btn = st.button("🌿 Analyze My Impact")
    # Auto-save draft inputs on change
    if user_id and (st.session_state.draft_status in ['restored', 'discarded'] or not get_assessment_draft(user_id)):
        is_modified = (
            st.session_state.get("region") != "Global" or
            st.session_state.get("transport") != "Car" or
            st.session_state.get("distance") != 10.0 or
            st.session_state.get("electricity") != 200.0 or
            st.session_state.get("diet") != "Vegetarian" or
            st.session_state.get("flights") != 0
        )
        if is_modified:
            save_assessment_draft(
                user_id,
                st.session_state.get("transport", "Car"),
                st.session_state.get("distance", 10.0),
                st.session_state.get("electricity", 200.0),
                st.session_state.get("diet", "Vegetarian"),
                st.session_state.get("flights", 0),
                st.session_state.get("region", "Global")
            )

    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    with col_btn1:
        reset_btn = st.button("🔄 Reset Assessment")
        if reset_btn:
            st.session_state.show_reset_confirm = True
            st.rerun()

    if st.session_state.get("show_reset_confirm", False):
        st.warning("⚠️ Are you sure you want to reset the assessment? All entered data will be lost.")
        confirm_col, cancel_col, _ = st.columns([1, 1, 3])
        with confirm_col:
            if st.button("✅ Confirm Reset", key="confirm_reset_clear"):
                for key in DEFAULT_VALUES:
                    st.session_state[key] = DEFAULT_VALUES[key]
                st.session_state.pop("extracted_kwh", None)
                st.session_state.show_reset_confirm = False
                if user_id:
                    delete_assessment_draft(user_id)
                st.success("✅ Assessment form has been reset.")
                st.rerun()
        with cancel_col:
            if st.button("❌ Cancel", key="cancel_reset_clear"):
                st.session_state.show_reset_confirm = False
                st.rerun()

    with col_btn2:
        analyze_btn = st.button("🌿 Analyze My Impact")


    if analyze_btn:

        with st.spinner("🌍 Analyzing your carbon footprint..."):
            total, contributors = calculate_footprint(
                transport, distance, electricity, diet, flights, region
            )

        eco_score = calculate_eco_score(total)

        insight, recommendations = generate_recommendations(
            transport, electricity, diet, flights, contributors
        )

        save_assessment(user_id, 
            transport, distance, electricity, diet, flights, total, eco_score
        )
        if user_id:
            delete_assessment_draft(user_id)

        st.success("✅ Analysis completed!")

        st.markdown("---")


        # Top metrics row
        met1, met2, met3, met4 = st.columns(4)

        with met1:
            st.markdown("""
            <div class='metric-card'>
                <div style='font-size: 14px; color: #374151; margin-bottom: 8px;'>🌍 Total Footprint</div>
                <div style='font-size: 36px; font-weight: 900; color: #4ade80;'>{:.0f}</div>
                <div style='font-size: 12px; color: #4b5563;'>kg CO₂/year</div>
            </div>
            """.format(total), unsafe_allow_html=True)

        with met2:
            st.markdown("""
            <div class='metric-card'>
                <div style='font-size: 14px; color: #374151; margin-bottom: 8px;'>🏆 Eco Score</div>
                <div style='font-size: 36px; font-weight: 900; color: #4ade80;'>{}</div>
                <div style='font-size: 12px; color: #4b5563;'>out of 100</div>
            </div>
            """.format(eco_score), unsafe_allow_html=True)

        with met3:
            st.markdown("""
            <div class='metric-card'>
                <div style='font-size: 14px; color: #374151; margin-bottom: 8px;'>📈 Biggest Impact</div>
                <div style='font-size: 24px; font-weight: 700; color: #4ade80;'>{}</div>
                <div style='font-size: 12px; color: #4b5563;'>{:.0f} kg CO₂</div>
            </div>
            """.format(max(contributors, key=contributors.get), max(contributors.values())), unsafe_allow_html=True)

        with met4:
            st.markdown("""
            <div class='metric-card'>
                <div style='font-size: 14px; color: #374151; margin-bottom: 8px;'>🎯 Status</div>
                <div style='font-size: 18px; font-weight: 700; color: #4ade80;'>Active</div>
                <div style='font-size: 12px; color: #4b5563;'>Tracking enabled</div>
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
                    <span style='color: #374151; font-size: 14px;'>Score Progress</span>
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
                font=dict(color='#374151', size=12),
                legend=dict(
                    x=-0.15,
                    y=1,
                    bgcolor='rgba(0,0,0,0.3)',
                    bordercolor='rgba(74, 222, 128, 0.3)',
                    borderwidth=1
                )
            )
        # -------------------------
        # DETAILED BREAKDOWN
        # -------------------------
        st.markdown("<div class='section-header'>📋 Detailed Breakdown</div>", unsafe_allow_html=True)

        # Bar chart creation
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
            font=dict(color='#374151', size=12),
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                color='#4b5563'
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(74, 222, 128, 0.1)',
                zeroline=False,
                color='#4b5563'
            ),
            showlegend=False
        )

        # Render Chart
        st.plotly_chart(breakdown_fig, use_container_width=True, config={'displayModeBar': False})

        # -------------------------
        # CHART EXPORT BUTTONS (#277)
        # -------------------------
        try:
            col_exp1, col_exp2 = st.columns(2)

            # Export PNG (High Quality Scale = 3)
            png_bytes = breakdown_fig.to_image(format="png", width=1200, height=700, scale=3)
            col_exp1.download_button(
                label="📥 Export Chart as PNG",
                data=png_bytes,
                file_name="breakdown_chart.png",
                mime="image/png",
                use_container_width=True
            )

            # Export SVG (Vector Quality)
            svg_bytes = breakdown_fig.to_image(format="svg", width=1200, height=700)
            col_exp2.download_button(
                label="📥 Export Chart as SVG",
                data=svg_bytes,
                file_name="breakdown_chart.svg",
                mime="image/svg+xml",
                use_container_width=True
            )
        except Exception:
            # Fallback if kaleido or required engine is not available
            pass

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
                        <div style='font-size: 15px; color: #374151; line-height: 1.8;'>{h(insight)}</div>
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
                        <ul style='color: #374151; font-size: 14px; line-height: 2.2; padding-left: 20px; margin: 0;'>
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
                            <div style='font-size: 15px; line-height: 1.8; color: #374151;'>{h(r)}</div>
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
                        <div style='color: #374151;'>Your lifestyle is already very eco-friendly. Keep maintaining these amazing habits!</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # -------------------------
        # PDF DOWNLOAD
        # -------------------------
        report = generate_pdf(total, eco_score, insight)

        if report:
            with open(report, "rb") as f:
                pdf_bytes = f.read()
                
            try:
                os.remove(report)
            except OSError:
                pass
                
            st.download_button(
                "📄 Download Eco Report (PDF)",
                pdf_bytes,
                file_name="EcoBuddy_Report.pdf"
            )


    # -------------------------
    # HISTORY & TRACKING
    # -------------------------
    st.markdown("---")
    with st.expander("🕒 Assessment Timeline", expanded=False):
        st.markdown("<div class='section-header'>📈 Your Eco Journey</div>", unsafe_allow_html=True)

        history = get_assessments(user_id)
        st.write("History length:", len(history))

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
                    <div style='font-size: 12px; color: #4b5563;'>Latest Footprint</div>
                    <div style='font-size: 28px; font-weight: 900; color: #4ade80;'>{latest[7]:.0f}</div>
                    <div style='font-size: 11px; color: #4b5563;'>kg CO₂</div>
                </div>
                """, unsafe_allow_html=True)

            with stat2:
                st.markdown(f"""
                <div class='card'>
                    <div style='font-size: 12px; color: #4b5563;'>Latest Score</div>
                    <div style='font-size: 28px; font-weight: 900; color: #4ade80;'>{latest[8]}</div>
                    <div style='font-size: 11px; color: #4b5563;'>out of 100</div>
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
                        <div style='font-size: 12px; color: #4b5563;'>{emoji} {label}</div>
                        <div style='font-size: 28px; font-weight: 900; color: {color};'>{abs(change):.1f}%</div>
                        <div style='font-size: 11px; color: #4b5563;'>vs previous</div>
                    </div>
                    """, unsafe_allow_html=True)

            with stat4:
                st.markdown(f"""
                <div class='card'>
                    <div style='font-size: 12px; color: #4b5563;'>Total Records</div>
                    <div style='font-size: 28px; font-weight: 900; color: #4ade80;'>{len(history)}</div>
                    <div style='font-size: 11px; color: #4b5563;'>assessments</div>
                </div>
                """, unsafe_allow_html=True)



            st.markdown("---")
            st.markdown("<br>", unsafe_allow_html=True)

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
                title="Carbon Footprint Over Time",
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


            st.plotly_chart(
                trend_fig,
                width="stretch",
                config={
                    "displayModeBar": False,
                    "scrollZoom": False,
                    "responsive": True
                }
            )

            st.markdown("---")

        # -------------------------
        # HISTORY TABLE
        # -------------------------
            st.markdown("<div style='font-size: 22px; font-weight: 800; background: linear-gradient(135deg, #4ade80, #86efac); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 16px;'>📋 Assessment History</div>", unsafe_allow_html=True)
            with st.expander("📂 View Assessment History", expanded=True):
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

            stats_col1, stats_col2, stats_col3 = st.columns([1.2, 1.2, 1])

            avg_footprint = df['footprint'].mean()
            avg_score = df['eco_score'].mean()
            max_footprint = df['footprint'].max()
            min_footprint = df['footprint'].min()

            with stats_col1:
                st.markdown(f"""
                <div class='card'>
                    <div style='font-size: 13px; color: #4b5563; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700;'>📊 Average Footprint</div>
                    <div style='font-size: 36px; font-weight: 900; color: #4ade80;'>{avg_footprint:.0f}</div>
                    <div style='font-size: 12px; color: #4b5563; margin-top: 8px;'>kg CO₂ across {len(history)} records</div>
                </div>
                """, unsafe_allow_html=True)

            with stats_col2:
                st.markdown(f"""
                <div class='card'>
                    <div style='font-size: 13px; color: #4b5563; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700;'>🎯 Average Score</div>
                    <div style='font-size: 36px; font-weight: 900; color: #4ade80;'>{avg_score:.0f}</div>
                    <div style='font-size: 12px; color: #4b5563; margin-top: 8px;'>out of 100 points</div>
                </div>
                """, unsafe_allow_html=True)

            with stats_col3:
                range_val = max_footprint - min_footprint
                st.markdown(f"""
                <div class='card'>
                    <div style='font-size: 13px; color: #4b5563; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700;'>📈 Range Variation</div>
                    <div style='font-size: 28px; font-weight: 700; color: #4ade80;'>{min_footprint:.0f}</div>
                    <div style='font-size: 14px; color: #4b5563;'>to</div>
                    <div style='font-size: 28px; font-weight: 700; color: #4ade80;'>{max_footprint:.0f}</div>
                </div>
                """, unsafe_allow_html=True)



        else:
            st.markdown("""
            <div class='card-highlight'>
                <div style='text-align: center; padding: 48px 32px;'>
                    <div style='font-size: 72px; margin-bottom: 20px; animation: bounce 2s infinite;'>🌱</div>
                    <div style='font-size: 26px; font-weight: 800; background: linear-gradient(135deg, #22c55e, #4ade80); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 12px;'>No Data Yet</div>
                    <div style='color: #374151; font-size: 16px; line-height: 1.6; max-width: 400px; margin: 0 auto;'>
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

with tab2:
    import database as db
    import energy_audit as ea
    import plotly.graph_objects as go

    st.markdown("<div class='section-header'>⚡ Home Energy Audit</div>", unsafe_allow_html=True)

    # Init energy db
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

            submit_app = st.form_submit_button("Add Appliance")
            if submit_app and app_name:
                db.add_appliance(user_id, app_name, app_cat, app_qty, app_power, app_hours, app_standby)
                st.success(f"Added {app_name}")
                st.rerun()

    appliances = db.get_appliances(user_id)
    if appliances:
        # Build a styled HTML table instead of st.dataframe
        category_icons = {"AC": "❄️", "EV Charger": "🔋", "Heat Pump": "🌡️", "Refrigerator": "🧊", "Lighting": "💡", "Other": "🔌"}
        table_rows = "".join([
            f"""
            <tr>
                <td>{category_icons.get(a['category'], '🔌')} {h(a['name'])}</td>
                <td><span style='background:rgba(74,222,128,0.15); padding:4px 10px; border-radius:8px; font-size:13px;'>{h(a['category'])}</span></td>
                <td style='text-align:center;'>{a['quantity']}</td>
                <td style='text-align:right;'>{a['power_rating_watts']:.0f} W</td>
                <td style='text-align:right;'>{a['hours_used_per_day']:.1f} h</td>
                <td style='text-align:right;'>{a['standby_draw_watts']:.1f} W</td>
            </tr>""" for a in appliances
        ])

        st.markdown(f"""
        <div style='border:1px solid rgba(134,239,172,0.24); border-radius:16px; overflow:hidden; background:#0f172a; box-shadow:0 24px 70px rgba(0,0,0,0.38);'>
            <table style='width:100%; border-collapse:collapse; color:#fff; font-size:15px;'>
                <thead>
                    <tr style='background:#07130d;'>
                        <th style='padding:14px 18px; text-align:left; font-weight:700; color:#86efac;'>Appliance</th>
                        <th style='padding:14px 18px; text-align:left; font-weight:700; color:#86efac;'>Category</th>
                        <th style='padding:14px 18px; text-align:center; font-weight:700; color:#86efac;'>Qty</th>
                        <th style='padding:14px 18px; text-align:right; font-weight:700; color:#86efac;'>Power</th>
                        <th style='padding:14px 18px; text-align:right; font-weight:700; color:#86efac;'>Hours/Day</th>
                        <th style='padding:14px 18px; text-align:right; font-weight:700; color:#86efac;'>Standby</th>
                    </tr>
                </thead>
                <tbody>{table_rows}</tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

        # Delete appliance controls
        st.markdown("")
        del_cols = st.columns([3, 1])
        with del_cols[0]:
            del_id = st.selectbox("Select appliance to remove", options=[(a['id'], a['name']) for a in appliances], format_func=lambda x: x[1], label_visibility="collapsed")
        with del_cols[1]:
            if st.button("🗑️ Remove", key="del_app"):
                db.delete_appliance(del_id[0])
                st.rerun()

        # Calculate summaries
        daily_kwh, monthly_kwh, yearly_kwh = ea.calculate_home_energy_summary(appliances)

        st.markdown("### 📊 Energy Patterns")
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Daily Consumption", f"{daily_kwh:.2f} kWh")
        sc2.metric("Monthly Consumption", f"{monthly_kwh:.2f} kWh")
        sc3.metric("Yearly Consumption", f"{yearly_kwh:.2f} kWh")

        # Hourly profile chart
        profile = ea.generate_hourly_energy_profile(appliances)
        fig_hr = go.Figure(data=[go.Bar(x=list(range(24)), y=profile, marker_color='#fbbf24')])
        fig_hr.update_layout(title="Hourly Energy Demand (kWh)", xaxis_title="Hour of Day", yaxis_title="kWh", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_hr, width="stretch")

    else:
        st.markdown("""
        <div style='text-align:center; padding:48px 24px; border:1px dashed rgba(134,239,172,0.3); border-radius:16px; background:rgba(15,23,42,0.5);'>
            <div style='font-size:48px; margin-bottom:12px;'>🔌</div>
            <div style='font-size:18px; font-weight:600; color:#e5e7eb; margin-bottom:8px;'>No Appliances Yet</div>
            <div style='font-size:14px; color:#94a3b8;'>Click <b>"➕ Add New Appliance"</b> above to register your first household appliance and start tracking energy consumption.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ☀️ Solar ROI Calculator")

    sc_form1, sc_form2 = st.columns(2)
    with sc_form1:
        roof_space = st.number_input("Available Roof Space (m²)", min_value=0.0, value=30.0)
        panel_eff = st.number_input("Panel Efficiency (%)", min_value=0.0, max_value=100.0, value=20.0)
        sun_hours = st.number_input("Peak Sun Hours/Day", min_value=0.0, value=4.5)
        install_cost = st.number_input("Installation Cost per kW ($)", min_value=0.0, value=2500.0)
    with sc_form2:
        util_rate = st.number_input("Utility Rate ($/kWh)", min_value=0.0, value=0.15)
        maint_cost = st.number_input("Annual Maintenance Cost ($)", min_value=0.0, value=100.0)
        rate_inc = st.number_input("Annual Rate Increase (%)", min_value=0.0, value=3.0)

    sys_size = ea.calculate_solar_system_size(roof_space, panel_eff)
    ann_gen = ea.calculate_annual_solar_generation(sys_size, sun_hours)
    inst_cost = ea.calculate_solar_installation_cost(sys_size, install_cost)
    ann_savings = ann_gen * util_rate
    payback = ea.calculate_solar_payback_period(inst_cost, ann_savings)
    savings_20y = ea.calculate_long_term_solar_savings(ann_gen, util_rate, 20, rate_inc, maint_cost) - inst_cost
    carbon_offset = ea.calculate_solar_carbon_offset(ann_gen)

    st.markdown("#### 📈 Solar Simulation Results")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("System Size", f"{sys_size:.1f} kW")
    r2.metric("Annual Generation", f"{ann_gen:.0f} kWh")
    r3.metric("Est. Installation", f"${inst_cost:,.0f}")
    r4.metric("Payback Period", f"{payback:.1f} years" if payback != float('inf') else "N/A")

    st.markdown(f"""
    <div style='padding:18px 24px; border-radius:14px; background:linear-gradient(135deg, rgba(34,197,94,0.15), rgba(74,222,128,0.08)); border:1px solid rgba(74,222,128,0.3); margin-top:8px;'>
        <span style='font-size:18px;'>💡</span>
        <span style='color:#e5e7eb; font-size:15px;'>Over 20 years, you could save <b style="color:#4ade80;">${savings_20y:,.0f}</b> and offset <b style="color:#4ade80;">{carbon_offset:,.0f} kg CO₂</b> annually.</span>
    </div>
    """, unsafe_allow_html=True)

with tab3:
    st.markdown("<div class='section-header'>🎮 Your Eco Journey</div>", unsafe_allow_html=True)
    
    # Header: Level, XP, Streak
    total_xp = gf.get_total_xp(user_id)
    level = gf.calculate_level(total_xp)
    progress = gf.calculate_level_progress(total_xp)
    history = get_assessments(user_id)
    activities_dates = [row[1] for row in history] if history else []
    streak = gf.calculate_streak(1, activities_dates)
    
    g_col1, g_col2, g_col3 = st.columns(3)
    g_col1.metric("Current Level", f"Lvl {level}")
    g_col2.metric("Total XP", f"{total_xp} XP")
    g_col3.metric("Current Streak", f"{streak} Days 🔥")
    
    st.progress(progress, text=f"Progress to Level {level+1}")
    
    st.markdown("---")
    st.markdown("### 🏆 Weekly Challenges")
    
    user_challenges = gf.get_user_challenges(user_id)
    # Optimize primary evaluation loop by pre-computing challenge states
    challenge_states = {}
    for c in user_challenges:
        if c['status'] != 'expired':
            challenge_states[c['challenge_id']] = c
            
    for ch_id, ch_data in gf.CHALLENGES.items():
        with st.expander(f"{ch_data['title']} ({ch_data['xp']} XP) - {ch_data['category']}"):
            st.write(f"Target: {ch_data['target']} {ch_data['unit']}")
            if ch_id in challenge_states:
                state = challenge_states[ch_id]
                status = state['status']
                if status == 'completed':
                    st.success("Challenge Completed! 🎉")
                else:
                    current_prog = state['progress_value']
                    st.write(f"Progress: {current_prog} / {ch_data['target']}")
                    
                    prog_val = st.number_input(f"Update Progress for {ch_id}", min_value=0.0, step=1.0, key=f"prog_{ch_id}")
                    if st.button("Update", key=f"btn_prog_{ch_id}"):
                        gf.update_challenge_progress(user_id, ch_id, progress_increment=prog_val)
                        gf.validate_challenge_progress(1, ch_id)
                        st.rerun()
            else:
                if st.button("Enroll", key=f"enroll_{ch_id}"):
                    gf.enroll_challenge(user_id, ch_id)
                    st.rerun()

    st.markdown("---")
    st.markdown("### 🎖️ Achievement Badges")
    
    unlocked = gf.get_unlocked_badges(user_id)
    unlocked_ids = [b['badge_id'] for b in unlocked]
    
    cols = st.columns(len(gf.BADGES))
    for i, (b_id, b_data) in enumerate(gf.BADGES.items()):
        with cols[i % len(cols)]:
            if b_id in unlocked_ids:
                st.markdown(f"**✅ {b_data['name']}**")
                st.caption(b_data['desc'])
                if st.button("Share Card", key=f"share_{b_id}"):
                    file_path = gf.generate_achievement_card(1, b_id, f"badge_{b_id}.png")
                    if file_path:
                        with open(file_path, "rb") as f:
                            st.download_button("Download Card", f, file_name=f"badge_{b_id}.png", key=f"dl_{b_id}")
            else:
                st.markdown(f"**🔒 {b_data['name']}**")
                st.caption(b_data['desc'])


with tab4:
    st.markdown("<div class='section-header'>🗺️ Route Planning & Carbon Offsets</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Compare transit modes, track your footprint, and build a simulated offset portfolio. Note: This is a simulation and does not process real financial transactions.</div>", unsafe_allow_html=True)

    route_col, offset_col = st.columns([1.2, 1])

    with route_col:
        st.subheader("📍 Transit Mode Comparison")
        
        with st.form("route_form"):
            dist_val = st.number_input("Trip Distance (km)", min_value=0.1, value=15.0, step=1.0)
            pass_val = st.number_input("Number of Passengers", min_value=1, value=1, step=1)
            freq = st.selectbox("Trip Frequency", ["One-time", "Weekly Commute (10 trips/week)", "Daily (14 trips/week)"])
            
            calc_btn = st.form_submit_button("Compare Emissions")
            
        if calc_btn:
            try:
                comparisons = compare_transit_modes(dist_val, pass_val)
                st.write(f"**Estimated Emissions for a {dist_val}km trip:**")
                
                # Chart
                df_comp = pd.DataFrame(comparisons)
                
                # Handle frequency
                if "Weekly" in freq:
                    df_comp['emissions_kg'] = df_comp['emissions_kg'] * 10
                    st.write("*Calculated for 10 trips per week*")
                elif "Daily" in freq:
                    df_comp['emissions_kg'] = df_comp['emissions_kg'] * 14
                    st.write("*Calculated for 14 trips per week*")
                    
                fig = px.bar(df_comp, x='mode', y='emissions_kg', 
                            title='CO2e by Transit Mode (Lower is Better)',
                            color='emissions_kg', color_continuous_scale='Greens_r')
                st.plotly_chart(fig, width="stretch")
                
                st.dataframe(df_comp.style.format({'emissions_kg': '{:.2f}'}))
                
            except Exception as e:
                st.error(f"Error calculating emissions: {e}")

    with offset_col:
        st.subheader("🛒 Simulated Offset Marketplace")
        st.info("💡 Invest your simulated eco-points to offset carbon.")
        
        projects = get_offset_projects()
        proj_names = [p["name"] for p in projects]
        selected_proj_name = st.selectbox("Select an Offset Project", proj_names)
        
        selected_proj = next(p for p in projects if p["name"] == selected_proj_name)
        
        st.markdown(f"**{selected_proj['image']} {selected_proj['name']}**")
        st.write(f"*{selected_proj['description']}*")
        st.write(f"**Category:** {selected_proj['category']} | **Region:** {selected_proj['region']}")
        st.write(f"**Cost:** ${selected_proj['cost_per_tonne']:.2f} per tonne")
        
        with st.form("offset_form"):
            tonnes = st.number_input("Tonnes of CO2e to Offset", min_value=0.1, value=1.0, step=0.1)
            purchase_btn = st.form_submit_button("Purchase Simulated Offset")
            
            if purchase_btn:
                is_valid, msg = validate_offset_transaction(tonnes, selected_proj["available_capacity"])
                if is_valid:
                    cost = calculate_offset_cost(tonnes, selected_proj["cost_per_tonne"])
                    # Defaulting to user_id=1 for now as per instructions
                    if save_offset_transaction(user_id, selected_proj["id"], selected_proj["name"], tonnes, selected_proj["cost_per_tonne"], cost):
                        st.success(f"Simulated purchase successful! Offset {tonnes}t for ${cost:.2f}.")
                    else:
                        st.error("Failed to save transaction.")
                else:
                    st.error(msg)

    st.markdown("---")
    
    st.markdown("<div class='section-header'>📈 Your Offset Portfolio</div>", unsafe_allow_html=True)
    port_col1, port_col2 = st.columns([1, 2])
    
    with port_col1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        total_offsets = get_total_offsets(user_id)
        total_spend = get_total_spend(user_id)
        st.metric("Total Tonnes Offset", f"{total_offsets:.2f}t")
        st.metric("Total Simulated Spend", f"${total_spend:.2f}")
        
        estimated_footprint = 50.0  # Just a placeholder lifetime footprint
        net_progress = calculate_net_zero_progress(estimated_footprint, total_offsets)
        st.metric("Net-Zero Progress (Estimated)", f"{net_progress:.1f}%")
        st.progress(net_progress / 100)
        st.markdown("</div>", unsafe_allow_html=True)

    with port_col2:
        st.subheader("Transaction History")
        transactions = get_offset_transactions(user_id)
        if transactions:
            df_trans = pd.DataFrame(transactions)
            st.dataframe(df_trans[['created_at', 'project_name', 'offset_tonnes', 'total_cost', 'transaction_status']])
            
            # Button to clear history for demo purposes
            if st.button("Clear History"):
                clear_offset_transactions(user_id)
                st.rerun()
        else:
            st.info("No transactions yet. Visit the marketplace to start your portfolio!")
    st.markdown("""
    <style>
    @keyframes bounce {
        0%,100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }

    .empty-card{
        background: linear-gradient(135deg,#132238,#0f172a);
        border:1px solid rgba(74,222,128,0.25);
        border-radius:20px;
        padding:45px 35px;
        text-align:center;
        box-shadow:0 12px 30px rgba(0,0,0,.25);
        margin-top:20px;
    }

    .empty-title{
        font-size:32px;
        font-weight:800;
        color:#4ade80;
        margin-bottom:12px;
    }

    .empty-subtitle{
        color:#cbd5e1;
        font-size:17px;
        line-height:1.8;
        max-width:650px;
        margin:auto;
    }

    .empty-checklist{
        margin-top:28px;
        text-align:left;
        display:inline-block;
        color:#e2e8f0;
        font-size:16px;
        line-height:2;
    }

    .empty-icon{
        font-size:72px;
        animation:bounce 2s infinite;
        margin-bottom:20px;
    }

    .tip-box{
        margin-top:28px;
        background:rgba(74,222,128,.08);
        border-left:5px solid #4ade80;
        padding:18px;
        border-radius:12px;
        color:#d1fae5;
        font-size:15px;
    }
    </style>

    <div class="empty-card">

        <div class="empty-icon">🌱</div>

        <div class="empty-title">
            Welcome to Your Eco Journey
        </div>

        <div class="empty-subtitle">
            Complete your lifestyle profile above and click
            <b>"Analyze My Impact"</b> to generate your first carbon footprint report.
        </div>

        <div class="empty-checklist">
            ✅ Personalized Eco Score<br>
            ✅ Carbon Footprint Dashboard<br>
            ✅ AI Insights & Recommendations<br>
            ✅ Emission Charts & Trends<br>
            ✅ Downloadable PDF Report
        </div>

        <div class="tip-box">
            💡 <b>Tip:</b> Even small lifestyle changes can make a meaningful impact over time.
            Start with your first assessment and track your progress.
        </div>

    </div>
    """, unsafe_allow_html=True)


st.markdown("---")

st.markdown("## 🌱 What You'll Unlock")

col1, col2, col3 = st.columns(3)

with col1:
    st.success("📊 Carbon Footprint Dashboard")
    st.caption("Track your yearly emissions.")

with col2:
    st.success("🤖 AI Insights")
    st.caption("Get AI-powered analysis.")

with col3:
    st.success("💡 Smart Recommendations")
    st.caption("Receive personalized eco tips.")


st.markdown("---")

st.markdown("## 🚀 How It Works")

st.info("1️⃣ Fill in your lifestyle details")
st.info("2️⃣ Click **Analyze My Impact**")
st.info("3️⃣ Review your carbon footprint")
st.info("4️⃣ Get personalized AI recommendations")
st.info("5️⃣ Download your PDF report")

st.markdown("---")
st.markdown("## ✨ Why Use EcoBuddy AI?")

feature1, feature2 = st.columns(2)

with feature1:
    st.success("📈 Track your carbon footprint over time")
    st.success("🤖 AI-powered personalized insights")
    st.success("📄 Export reports as PDF")

with feature2:
    st.success("🌍 Build sustainable habits")
    st.success("📊 Interactive charts and trends")
    st.success("🏆 Improve your Eco Score")


st.markdown("---")

st.markdown("## 💡 Eco Tips")

tip_col1, tip_col2 = st.columns(2)

with tip_col1:
    st.success("🚶 Walk or cycle for short trips")
    st.success("💧 Save water whenever possible")
    st.success("♻️ Recycle household waste")

with tip_col2:
    st.success("⚡ Turn off unused appliances")
    st.success("🚌 Use public transport")
    st.success("🌱 Plant more trees")

    
    st.markdown("---")

st.markdown(
    """
    ### 🌍 Every small action matters

    Your sustainability journey starts with a single assessment.
    Complete your profile today and discover simple ways to reduce
    your carbon footprint and make a positive environmental impact.
    """
)

st.markdown("---")

st.markdown("## 🚀 Ready to Begin?")

st.success(
    "Complete the lifestyle form above and click **Analyze My Impact** "
    "to generate your first carbon footprint assessment."
)
st.markdown("""
<style>
.footer{
    margin-top:60px;

    /* Stretch outside Streamlit container */
    width:100vw;
    margin-left:calc(50% - 50vw);
    margin-right:calc(50% - 50vw);
    margin-bottom:-60px;

    padding:50px 30px 25px;

    background:linear-gradient(135deg,#010b07 0%,#04140d 45%,#071c13 100%);
    color:white;
    text-align:center;

    box-shadow:0 -12px 35px rgba(0,0,0,.35);
}

.footer h2{
    color:white;
    font-size:38px;
    font-weight:800;
    margin-bottom:12px;
}

.footer p{
    margin:12px 0;
    color:#d1fae5;
    font-size:16px;
}

.footer hr{
    border:none;
    height:1px;
    background:rgba(255,255,255,.12);
    margin:28px auto 18px;
    width:90%;
}

.footer-bottom{
    color:#4b5563;
    font-size:14px;
}
</style>

<div class="footer">

<h2>🌱 EcoBuddy AI+</h2>

<p>
Your Personal AI-Powered Carbon Footprint Tracker &amp; Eco Assistant.
</p>

<p>
💚 <b>Track</b> &nbsp; • &nbsp;
📊 <b>Analyze</b> &nbsp; • &nbsp;
💡 <b>Improve</b>
</p>

<p>
Built with ❤️ using <b>Streamlit</b>,
<b>Google Gemini</b>,
<b>Python</b>,
and <b>Pandas</b>.
</p>

<hr>

<div class="footer-bottom">
© 2026 EcoBuddy AI+. Encouraging sustainable living, one step at a time.
</div>

</div>
""", unsafe_allow_html=True)