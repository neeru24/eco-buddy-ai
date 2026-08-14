import html
import time
import logging
import streamlit as st
from logging_config import setup_logging
from styles.skeleton import show_card_skeleton, show_chart_skeleton

setup_logging()
logger = logging.getLogger(__name__)


def _apply_page_config(**kwargs):
    """Apply page config defensively.

    Validates theme/page_config settings before passing them to Streamlit and
    falls back to safe defaults if anything is invalid or Streamlit rejects the
    call, so a bad config can never stop the app from loading.
    """
    defaults = {
        "page_title": "EcoBuddy",
        "page_icon": "🌱",
        "layout": "wide",
        "initial_sidebar_state": "expanded",
    }
    settings = {
        key: (kwargs.get(key) if kwargs.get(key) is not None else default)
        for key, default in defaults.items()
    }
    if settings["layout"] not in ("centered", "wide"):
        settings["layout"] = defaults["layout"]
    if settings["initial_sidebar_state"] not in ("auto", "expanded", "collapsed"):
        settings["initial_sidebar_state"] = defaults["initial_sidebar_state"]
    if not settings["page_title"]:
        settings["page_title"] = defaults["page_title"]
    try:
        st.set_page_config(**settings)
    except Exception:
        # Let Streamlit use its own defaults rather than crashing startup.
        logger.warning("set_page_config failed with %r; using Streamlit defaults", settings)


_apply_page_config()
from eco_school import render_eco_school_hub
import tempfile
import uuid
import os
from global_search import render_global_search
from dotenv import load_dotenv
from green_business import render_business_hub
from styles.theme import apply_theme
from achievement_showcase import render_achievement_showcase
from garden_Assistant import render_garden_hub
from habit_tracker import render_habit_hub
from event_calendar import render_event_hub
from voice_assistant import render_voice_assessment
from components.header import render_header
#from components.profile import render_profile
from community_marketplace import render_marketplace_hub
from sustainability_hub import (
    render_sustainability_hub  
)
from community_resilience import render_resilience_hub
from eco_heritage import render_heritage_hub
from eco_parenting import render_parenting_hub
from mindset_coach import render_coach_hub
from smart_home import render_smart_home_hub
from fashion_guide import render_fashion_hub
from certification_system import render_certification_hub
from eco_news import render_news_hub
from pet_care import render_pet_hub
from community_dashboard import render_community_analytics
from home_guide import render_home_hub
from wellness_center import render_wellness_hub
from learning_center import render_learning_hub
from travel_planner import render_travel_hub
from weather_alerts import render_weather_hub
from eco_social import render_eco_social, render_eco_tip
from volunteer_platform import render_volunteer_hub
load_dotenv()
from shopping_assistant import render_shopping_hub
from impact_dashboard import render_impact_dashboard
from database import init_db, save_assessment, get_assessments, init_gamification_db, init_freeze_tokens_db, save_assessment_draft, verify_user, create_user, get_leaderboard, update_user_leaderboard_preference
import gamification as gf
from emissions import calculate_footprint, calculate_eco_score

from recommendations import generate_recommendations
from what_changed import generate_what_changed_analysis, render_what_changed_ui

from datetime import datetime

# ----------------------------
# Welcome Section
# ----------------------------
st.title("🌱 Welcome to EcoBuddy AI")

st.markdown(
    """
    Welcome to **EcoBuddy AI**, an intelligent sustainability platform designed
    to help users understand their environmental impact through AI-powered
    insights, carbon footprint analysis, and eco-friendly recommendations.
    """
)

# ----------------------------
# Application Information
# ----------------------------
welcome_info = {
    "message": "Welcome to EcoBuddy AI API",
    "version": "1.0.0",
    "status": "Running",
    "framework": "Streamlit",
    "environment": "Development",
}

st.subheader("Application Information")
st.json(welcome_info)

# ----------------------------
# Feature Highlights
# ----------------------------
st.subheader("Key Features")

features = [
    "🌍 Carbon Footprint Calculator",
    "⚡ Energy Consumption Analysis",
    "🚗 Sustainable Commute Planner",
    "♻️ Waste Management Assistant",
    "📊 Environmental Dashboard",
    "🤖 AI-powered Recommendations",
    "🎬 Carbon Footprint Replay",
    "🧾 AI Receipt Categorization",
]

for feature in features:
    st.markdown(f"- {feature}")

# ----------------------------
# Quick Statistics
# ----------------------------
st.subheader("Application Status")

form = st.form(key='assessment_form')
with form:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Version", "1.0.0")

    with col2:
        st.metric("Status", "Online")

    with col3:
        st.metric("Environment", "Development")

    # ----------------------------
    # Additional Information
    # ----------------------------
    with st.expander("About EcoBuddy AI"):
        st.write(
            """
            EcoBuddy AI empowers users to make environmentally conscious decisions
            by providing personalized sustainability insights, educational resources,
            and practical recommendations for reducing their ecological footprint.
            """
        )

    st.success("EcoBuddy AI is running successfully.")

    # Added for Route Planning & Offsets
    from database import (
        init_marketplace_db, save_journey_profile, get_journey_profiles, delete_journey_profile,
        save_offset_transaction, get_offset_transactions, delete_offset_transaction, clear_offset_transactions,
        get_total_offsets, get_total_spend,
        get_total_freeze_tokens_earned
    )
    from marketplace import (
        calculate_trip_emissions, calculate_recurring_trip_emissions, compare_transit_modes,
        calculate_offset_cost, validate_offset_transaction, get_offset_projects,
        calculate_net_emissions, calculate_net_zero_progress, get_project_by_id, EMISSION_FACTORS
    )
    from styles.theme import apply_theme, render_theme_selector
    from dashboard_widgets import render_customizable_dashboard, render_widget_customizer
    from environmental_timeline import render_environmental_timeline
    from report_validation import validate_report_data
    from future_self import generate_future_self_report, build_projection_timeline
    from session_recovery import (
        autosave_session_draft,
        discard_current_draft,
        render_draft_recovery_prompt,
    )
    from session_state_utils import (
        ensure_session_state,
        set_session_state_if_changed,
        check_session_timeout,
        update_last_activity,
        clear_auth_session,
    )



    DEFAULT_VALUES = {
        "region": "Global",
        "transport": "Car",
        "distance": 10.0,
        "electricity": 200.0,
        "diet": "Vegetarian",
        "flights": 0,
    }

    def render_breadcrumbs(current_page, parent_page="Dashboard"):
        st.markdown(
            f"""
            <div class="breadcrumb-container">
                <span class="breadcrumb-home">🏠</span>
                <span class="breadcrumb-link">{parent_page}</span>
                <span class="breadcrumb-separator">›</span>
                <span class="breadcrumb-current">{current_page}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    def h(text):
        return html.escape(str(text))
    def format_timestamp(ts):
        if ts:
            return datetime.strptime(
                ts,
                "%Y-%m-%d %H:%M:%S"
            ).strftime("%d %b %Y %I:%M %p")
        return "-"

    def render_sidebar_auth():
        st.sidebar.title("Authentication")
        if 'user_id' not in st.session_state:
            st.session_state['user_id'] = None
            st.session_state['username'] = None

        if st.session_state.get('user_id'):
            if check_session_timeout():
                clear_auth_session()
                st.sidebar.warning("Your session has expired. Please sign in again.")
                st.rerun()
            else:
                update_last_activity()

        if st.session_state['user_id'] is None:
            auth_mode = st.sidebar.radio("Choose Mode", ["Login", "Register", "Guest"])
            if auth_mode == "Login":
                with st.sidebar.form("login_form"):
                    MAX_USERNAME = 30

                    username = st.text_input(
                        "Username",
                        key="username",
                        max_chars=MAX_USERNAME,
                        help="Enter your registered username."
                    )

                    st.caption(f"👤 {len(username or '')}/{MAX_USERNAME} characters")

                    password = st.text_input("Password", type="password",
                    help="Enter your account password. Characters will be hidden for security.")
                    if st.form_submit_button("Login"):
                        user = verify_user(username, password)
                        if user:
                            st.session_state['user_id'] = user['id']
                            st.session_state['username'] = user['username']
                            st.session_state['anonymous_leaderboard'] = user.get('anonymous_leaderboard', False)
                            st.sidebar.success("Logged in successfully!")
                            st.rerun()
                        else:
                            st.sidebar.error("Invalid username or password")
            elif auth_mode == "Register":
                with st.sidebar.form("register_form"):
                    MAX_USERNAME = 30

                    username = st.text_input(
                        "Username",
                        max_chars=MAX_USERNAME,
                        help="Choose a unique username."
                    )

                    st.caption(f"👤 {len(username or '')}/{MAX_USERNAME} characters")
                    MAX_EMAIL = 100

                    email = st.text_input(
                        "Email",
                        max_chars=MAX_EMAIL,
                        help="Enter a valid email address."
                    )

                    st.caption(f"📧 {len(email or '')}/{MAX_EMAIL} characters")
                    password = st.text_input("Password", type="password",help="Use a strong password with letters, numbers, and special characters.")
                    anonymous = st.checkbox("Appear anonymously on leaderboard")
                    if st.form_submit_button("Register"):
                        if create_user(username, email, password, anonymous_leaderboard=anonymous):
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
            anon_pref = st.sidebar.checkbox(
                "Appear anonymously on leaderboard",
                value=st.session_state.get("anonymous_leaderboard", False)
            )
            if anon_pref != st.session_state.get("anonymous_leaderboard", False):
                update_user_leaderboard_preference(st.session_state['user_id'], anon_pref)
                set_session_state_if_changed('anonymous_leaderboard', anon_pref)
                st.sidebar.success("Leaderboard preference saved.")
                st.experimental_rerun()

            if st.sidebar.button("Logout"):
                clear_auth_session()
                for key, val in DEFAULT_VALUES.items():
                    st.session_state[key] = val
                st.rerun()

            st.sidebar.markdown("---")
            st.sidebar.subheader("🧭 Navigation")

            st.markdown("""
            <style>

            /* Sidebar navigation expanders */
            [data-testid="stSidebar"] [data-testid="stExpander"] {
                border: 1px solid rgba(34, 197, 94, 0.18);
                border-radius: 12px;
                margin-bottom: 10px;
                background: rgba(255, 255, 255, 0.03);
                transition: all 0.25s ease;
            }


run_db_initializations()
user_id = render_sidebar_auth()
render_theme_selector()
selected_dashboard_widgets = render_widget_customizer(user_id)
render_customizable_dashboard(user_id, selected_dashboard_widgets)
run_db_initializations()
user_id = render_sidebar_auth()
render_theme_selector()

render_global_search(user_id)

selected_dashboard_widgets = render_widget_customizer(user_id)
render_customizable_dashboard(user_id, selected_dashboard_widgets)
with st.expander("🌍 Environmental Impact Timeline", expanded=False):
    render_environmental_timeline(user_id)

            /* Expander header */
            [data-testid="stSidebar"] [data-testid="stExpander"] summary {
                font-weight: 700;
                transition: all 0.25s ease;
            }

            /* Hover effect */
            [data-testid="stSidebar"] [data-testid="stExpander"]:hover {
                border-color: rgba(34, 197, 94, 0.45);
                transform: translateX(2px);
            }


            /* Navigation content */
            [data-testid="stSidebar"] [data-testid="stExpander"] div[role="group"] {
                padding: 4px 8px 8px 8px;
            }

            </style>
            """, unsafe_allow_html=True)

            with st.sidebar.expander("🌱 Sustainability", expanded=True):
                st.write("🌍 Carbon Footprint")
                st.write("⚡ Home Energy Audit")
                st.write("🎮 Gamification")

            with st.sidebar.expander("🗺️ Travel & Community", expanded=False):
                st.write("🗺️ Route Planning & Offsets")
                st.write("🏆 Community Leaderboard")

            with st.sidebar.expander("🔮 Insights", expanded=False):
                st.write("🔮 Future Self")
                st.write("📊 Environmental Timeline")

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
        init_freeze_tokens_db()
        init_marketplace_db()

    run_db_initializations()
    user_id = render_sidebar_auth()
    render_theme_selector()
    selected_dashboard_widgets = render_widget_customizer(user_id)
    render_customizable_dashboard(user_id, selected_dashboard_widgets)

    with st.expander("🌍 Environmental Impact Timeline", expanded=False):
        render_environmental_timeline(user_id)


    # -------------------------
    # DRAFT RECOVERY & DEFAULT FORM VALUES
    # -------------------------
    ensure_session_state(DEFAULT_VALUES)

    # page config moved to top


    # -------------------------
    # THEME APPLICATION
    # -------------------------

    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {
            --ink: #111827;
            --muted: #6b7280;
            --paper: rgba(255,255,255,0.75);
            --paper-strong: rgba(255,255,255,0.95);
            --line: rgba(0,0,0,0.08);
            --shadow: 0 10px 30px rgba(0,0,0,0.08);
        }

        * {
            box-sizing: border-box;
        }

        html {
            scroll-behavior: smooth;
        }

        body,
        [data-testid="stAppViewContainer"] {
            color: #1f2937;
            background:
                radial-gradient(circle at top left, #dcfce7 0%, transparent 30%),
                radial-gradient(circle at top right, #dbeafe 0%, transparent 30%),
                #f8fafc !important;
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

        /* =========================
        COLLAPSIBLE SIDEBAR NAV
        ========================= */

        [data-testid="stSidebar"] [data-testid="stExpander"] {
            border: 1px solid rgba(74, 222, 128, 0.18) !important;
            border-radius: 12px !important;
            margin-bottom: 10px !important;
            background: rgba(255, 255, 255, 0.08) !important;
            transition: all 0.2s ease !important;
        }

        [data-testid="stSidebar"] [data-testid="stExpander"]:hover {
            border-color: rgba(74, 222, 128, 0.40) !important;
            background: rgba(74, 222, 128, 0.08) !important;
        }

        /* Expander header */
        [data-testid="stSidebar"] [data-testid="stExpander"] summary {
            padding: 12px 14px !important;
            font-weight: 700 !important;
            cursor: pointer !important;
        }

        /* Navigation text */
        [data-testid="stSidebar"] [data-testid="stExpander"] p {
            font-size: 14px !important;
            font-weight: 600 !important;
        }

        /* Navigation section heading */
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            font-weight: 800 !important;
        }

        /* Sidebar divider */
        [data-testid="stSidebar"] hr {
            margin: 14px 0 !important;
            border-color: rgba(74, 222, 128, 0.18) !important;
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
            background: rgba(255,255,255,0.9);
            border: 1px solid #e5e7eb;
            box-shadow: 0 8px 24px rgba(0,0,0,0.06);
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
            letter-spacing: 0 !important;
            transition: transform 180ms ease, box-shadow 180ms ease, background 180ms ease !important;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        [data-testid="stFormSubmitButton"] > button:hover {
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

        @media (prefers-color-scheme: dark) {
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
            background: #e6f5e9 !important;
            border-color: rgba(74, 222, 128, 0.4) !important;
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

        .stButton > button,
        .stDownloadButton > button,
        [data-testid="stFormSubmitButton"] > button {
            background: linear-gradient(135deg, #0b0f18, #111827) !important;
            color: #ffffff !important;
            border: 1px solid rgba(134, 239, 172, 0.28) !important;
            box-shadow: 0 18px 40px rgba(0, 0, 0, 0.32) !important;
        }
        .stButton > button:hover,
        .stDownloadButton > button:hover,
        [data-testid="stFormSubmitButton"] > button:hover {
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
        [style*="#6b7280"],
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
            background: var(--paper-strong) !important;
        }

        [data-testid="stDataFrame"] > div,
        [data-testid="stDataFrame"] iframe,
        [data-testid="stDataFrame"] [class*="stDataFrame"],
        [data-testid="stDataFrame"] [class*="dataframe"],
        [data-testid="stDataFrame"] [class*="glide"],
        [data-testid="stDataFrame"] [class*="table"] {
            background: transparent !important;
        }

        [data-testid="stDataFrame"] canvas {
            background: transparent !important;
        }

        [data-testid="stDataFrame"] button,
        [data-testid="stDataFrame"] [role="button"] {
            background: rgba(255, 255, 255, 0.8) !important;
            color: var(--ink) !important;
            border-color: var(--line) !important;
        }

        [data-testid="stDataFrame"] svg {
            color: var(--ink) !important;
            fill: var(--ink) !important;
        }

        [data-testid="stDataFrame"] [role="grid"],
        [data-testid="stDataFrame"] [role="row"],
        [data-testid="stDataFrame"] [role="columnheader"],
        [data-testid="stDataFrame"] [role="gridcell"] {
            background-color: transparent !important;
            border-color: var(--line) !important;
        }

        [data-testid="stDataFrame"] [role="columnheader"] {
            background-color: var(--sky-soft) !important;
            color: var(--moss) !important;
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

        button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
            color: #d1d5db !important;
            font-weight: 600 !important;
        }
    
        button[data-baseweb="tab"][aria-selected="true"] > div[data-testid="stMarkdownContainer"] > p {
            color: #4ade80 !important;
            font-weight: 800 !important;
        }
    
        [data-testid="stExpander"] {
            background: #0f172a !important;
            border: 1px solid rgba(134, 239, 172, 0.28) !important;
            border-radius: 8px !important;
            overflow: hidden;
        }
    
        [data-testid="stExpander"] details {
            background: #0f172a !important;
        }

        [data-testid="stExpander"] summary {
            background-color: #0f172a !important;
        }
    
        [data-testid="stExpander"] summary:hover {
            background-color: #1e293b !important;
        }

        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] summary p,
        [data-testid="stExpander"] summary span,
        [data-testid="stExpander"] summary svg {
            color: #ffffff !important;
            font-weight: 600 !important;
            fill: #ffffff !important;
        }
    
        [data-testid="stExpanderDetails"] {
            background-color: #0f172a !important;
            color: #d1d5db !important;
        }
        } /* end @media (prefers-color-scheme: dark) */
    </style>
    """, unsafe_allow_html=True)

    apply_theme()



    # -------------------------
    # HEADER
    # -------------------------
    render_header()


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
        transport = st.selectbox(
        "Primary Transport",
        ["Car", "Public Transport", "Bike", "Walking"],
        key="transport_quick",
        help="Select the mode of transportation you use most frequently for your daily commute."
        )
        diet = st.selectbox(
        "Diet Type",
        ["Vegetarian", "Non-Vegetarian"],
        key="diet_quick",
        help="Choose the option that best represents your regular dietary habits."
    )

    with col2:
        st.markdown("""
        <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 16px;'>
            <span style='font-size: 24px;'>⚡</span>
            <span style='font-size: 18px; font-weight: 700; color: #e5e7eb;'>Energy & Diet</span>
        </div>
        """, unsafe_allow_html=True)
        electricity = st.number_input(
            "Monthly Electricity (kWh)",
            min_value=0.0,
            value=200.0,
            step=10.0,
            key="electricity_quick",
            help="Enter your average monthly electricity consumption in kWh."
        )

        diet = st.selectbox(
        "Diet Type",
        ["Vegetarian", "Non-Vegetarian"],
        key="diet_quick2",
        help="Choose the option that best represents your regular dietary habits."
    )
    with col3:
        st.markdown("""
        <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 16px;'>
            <span style='font-size: 24px;'>✈️</span>
            <span style='font-size: 18px; font-weight: 700; color: #e5e7eb;'>Travel</span>
        </div>
        """, unsafe_allow_html=True)
        flights = st.number_input(
            "Annual Flights",
            min_value=0,
            value=0,
            step=1,
            key="flights",
            help="Enter the number of long-distance flights you take each year."
        )
        st.info("💡 How many long-distance flights per year?")

 

    # -------------------------
    # PDF REPORT GENERATION
    # -------------------------

    # -------------------------
    # TABS CONFIGURATION
    # -------------------------
col_btn1, col_btn2, col_btn3 = st.columns([1, 1.5, 1])

# Initialize session state
if "show_reset_confirm" not in st.session_state:
    st.session_state.show_reset_confirm = False

if "last_reset_time" not in st.session_state:
    st.session_state.last_reset_time = None

with col_btn1:
    if st.button(
        "🔄 Reset Assessment",
        use_container_width=True,
        key="reset_btn"
    ):
        st.session_state.show_reset_confirm = True
        st.rerun()

with col_btn2:

    st.caption("✔ All input fields are validated before analysis.")

    analyze_btn = form.form_submit_button(
        "🌿 Analyze My Impact",
        use_container_width=True,
        key="analyze_btn"
    )

# -----------------------------
# Reset Confirmation Dialog
# -----------------------------
if st.session_state.show_reset_confirm:

    st.warning("⚠️ Reset Assessment")

    st.markdown("""
This action will:

- 🚗 Clear transportation details
- ⚡ Reset electricity usage
- 🥗 Reset diet selection
- ✈️ Clear annual flight information
- 🌍 Restore default region
- 🤖 Remove AI Quick Log input
- 📄 Clear uploaded utility bill
- 📊 Remove temporary analysis results
- 💾 Discard unsaved draft

**This action cannot be undone.**
""")

    confirm_col, cancel_col = st.columns(2)

    with confirm_col:
        if st.button(
            "✅ Confirm Reset",
            key="confirm_reset"
        ):

            # Restore default values
            for key, value in DEFAULT_VALUES.items():
                st.session_state[key] = value

            # Clear temporary session values
            temp_keys = [
                "quick_log_input",
                "temp_parsed",
                "uploaded_bill",
                "extracted_kwh",
                "analysis_complete",
                "generated_report",
                "contributors",
                "recommendations",
                "footprint",
                "eco_score",
                "assessment_history_search",
                "assessment_history_score_range",
            ]

            for key in temp_keys:
                st.session_state.pop(key, None)

            st.session_state.show_reset_confirm = False
            st.session_state.last_reset_time = time.strftime("%H:%M:%S")

            st.success("✅ Assessment has been reset successfully!")

            st.info(
                "All values have been restored to their defaults. "
                "You can now start a fresh sustainability assessment."
            )

            st.balloons()

            time.sleep(1)

            st.rerun()

    with cancel_col:
        if st.button(
            "❌ Cancel",
            key="cancel_reset"
        ):
            st.session_state.show_reset_confirm = False
            st.info("Reset cancelled.")
            st.rerun()

if st.session_state.last_reset_time:
    st.caption(
        f"🕒 Last reset performed at {st.session_state.last_reset_time}"
    )

 

tab1, tab2, tab3, tab4 = st.tabs(["🌍 Carbon Footprint", "⚡ Home Energy Audit", "🎮 Gamification", "🗺️ Route Planning & Offsets"])


st.caption("✔ All input fields are validated before analysis.")
    
 

tab1, tab2, tab3, tab4 = st.tabs(["🌍 Carbon Footprint", "⚡ Home Energy Audit", "🎮 Gamification", "🗺️ Route Planning & Offsets"])
 
 
# ------------------------


# -------------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11,tab36, tab12, tab13, tab14, tab15, tab16, tab17, tab18, tab19, tab20, tab21, tab22, tab23, tab24,tab34,tab35, tab25,tab26,tab27,tab28,tab29,tab30,tab31,tab32,tab33 = st.tabs([
    "🌍 Carbon Footprint",
    "⚡ Home Energy Audit",
    "🎮 Gamification",
    "🗺️ Route Planning & Offsets",
    "🏆 Community Leaderboard",
    "🔮 Future Self",
    "🌿 Sustainability Hub",
    "🌍 Eco-Social",
    "📖 Eco-Stories",
    "♻️ Waste Manager",
    "💰 Eco-Finance",
    "🎤 Voice Assessment",
    "🌤️ Eco-Weather",
    "🌍 Eco-Travel",
    "🌱 Eco-Garden",
    "📚 Learning Center",
    "🧘 Eco-Wellness",
    "🏠 Eco-Home",
    "🐾 Pet Care",
    "📊 Community Analytics",
    "📰 Eco-News",
    "🤝 Volunteer",
    "👗 Fashion",
    "🏅 Certification",
    "🛒 Shopping" ,
    "Eco-Impact",
    "Habit-Tracker",
    "Event-Planner",
    "Minset_planner",
    "Smart-home",
    "Market Place",
    "Eco-school",
    "Eco-Heritage",
    "Eco-Parenting",
    "Eco-Resillence",
    "green_business.py"
])
with tab36:
    render_business_hub()
with tab35:
    render_resilience_hub()
with tab34:
    render_parenting_hub()
with tab33:
    render_heritage_hub()
with tab32:
    render_eco_school_hub()
with tab31:
    render_marketplace_hub()
with tab30:
    render_smart_home_hub()
with tab29:
    render_coach_hub()
with tab28:
    render_event_hub()
with tab27:
    render_habit_hub()
with tab26:
    render_impact_dashboard()
with tab25:
    render_shopping_hub()

with tab24:
    render_certification_hub()

with tab23:
    render_fashion_hub()

with tab22:
    render_volunteer_hub()

with tab21:
    render_news_hub()

with tab20:
    render_community_analytics()


with tab1:
    st.markdown("<div class='section-header'>📝 Your Lifestyle Profile</div>", unsafe_allow_html=True)

with tab7:
    render_voice_assessment()
 

    placeholder = st.empty()
with tab8:
    render_weather_hub()
with tab9:
    render_travel_hub()
with tab10:
    render_garden_hub()

with tab11:
    render_learning_hub()
with tab12:
    render_wellness_hub()
with tab13:
    render_home_hub()
with tab14:
    render_pet_hub()
with placeholder.container():
    show_card_skeleton()
    show_chart_skeleton()

# Existing analysis code here

placeholder.empty()

progress_text = st.empty()
progress = st.progress(0)

progress_text.info("🔍 Validating user inputs...")
progress.progress(20)
time.sleep(0.5)  # Simulate validation delay

# TABS CONFIGURATION
# -------------------------
col_btn1, col_btn2 = st.columns([1, 3])


with col_btn1:
    reset_btn = st.button(
        "🔄 Reset Assessment",
        use_container_width=True
    )

if reset_btn:
    for key in DEFAULT_VALUES:
        if key in st.session_state:
            del st.session_state[key]
    st.success("✅ Assessment form has been reset.")
    st.rerun()

tab1, tab2, tab3, tab4 = st.tabs(["🌍 Carbon Footprint", "⚡ Home Energy Audit", "🎮 Gamification", "🗺️ Route Planning & Offsets"])

with tab1:
    st.markdown("<div class='section-header'>📝 Your Lifestyle Profile</div>", unsafe_allow_html=True)

    # Draft recovery prompt
    render_draft_recovery_prompt(user_id, DEFAULT_VALUES)

    st.markdown("### Region Setting")
    region = st.selectbox(
    "Select Your Region for API Emissions Factor",
    ["Global", "US", "UK", "EU"],
    key="region",
    help="Choose your region to apply the appropriate emission factors for more accurate carbon footprint calculations."
)

    # -------------------------
    # QUICK LOG (AI)
    # -------------------------
    st.markdown("### 🤖 AI Quick Log")
    col_ai_input, col_ai_btn = st.columns([4, 1])
    with col_ai_input:
        MAX_CHARS = 500
        quick_log_text = st.text_area(
    "Let AI auto-fill your profile! Describe your day naturally.",
    placeholder="e.g., 'I drove 15 miles in my SUV and had a beef steak'",
    key="quick_log_input",
    height=68,
    max_chars=MAX_CHARS,
    help="Describe your daily activities in natural language. The AI will analyze your routine and automatically populate relevant sustainability and carbon footprint fields."
)
        st.caption(f"📝 {len(quick_log_text)}/{MAX_CHARS} characters")
    with col_ai_btn:
        st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)
        parse_btn = st.button("✨ Parse with AI", use_container_width=True)
        
    if parse_btn:
        if quick_log_text.strip():
            with st.spinner("Analyzing text..."):
                from llm_parser import parse_quick_log
                from errors import AppError
                try:
                    parsed_data = parse_quick_log(quick_log_text)
                    st.session_state.temp_parsed = parsed_data
                except AppError as exc:
                    st.error(f"❌ {exc.message}")
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
        transport = st.selectbox(
    "Primary Transport",
    ["Car", "Public Transport", "Bike", "Walking"],
    key="transport",
    help="Select the mode of transportation you use most frequently for your daily commute."
)
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
        uploaded_bill = st.file_uploader(
            "Upload Utility Bill (PDF/Image)",
            type=["pdf", "png", "jpg", "jpeg"],
            help="Upload your latest electricity bill to automatically extract usage information."
        )
        if uploaded_bill is not None:
            # We use a button to trigger extraction so it doesn't re-run infinitely on every interaction
            if st.button("Extract Energy Usage"):
                try:
                    with st.spinner("Extracting data from bill..."):
                        from ocr_utils import extract_text_from_file, parse_energy_consumption
                    extracted_text = extract_text_from_file(uploaded_bill)
                    parsed_val = parse_energy_consumption(extracted_text)
                    if parsed_val is not None:
                        st.session_state.extracted_kwh = float(parsed_val)
                        st.session_state.electricity = float(parsed_val)
                        st.success(f"Extracted {parsed_val} kWh from bill!")
                    else:
                        st.warning("Could not extract energy consumption. Please enter manually.")
                except Exception:
                    st.error(
                    "⚠️ Unable to process the uploaded bill. "
                    "Please check the file and try again."
            )

        electricity = st.number_input("Monthly Electricity (kWh)", min_value=0.0, key="electricity", step=10.0)
        diet = st.selectbox(
    "Diet Type",
    ["Vegetarian", "Non-Vegetarian"],
    key="diet",
    help="Choose the option that best represents your regular dietary habits."
)
    
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
    # CALCULATE & ANALYZE
    # -------------------------


 


    # col_btn1, col_btn2, col_btn3 = st.columns([1, 1.5, 1])
    # with col_btn2:
    #     analyze_btn = st.button("🌿 Analyze My Impact")
    # Auto-save after every Streamlit rerun caused by form changes.
    autosave_session_draft(user_id, DEFAULT_VALUES)

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
                discard_current_draft(
                    user_id,
                    st.session_state,
                )
                st.success("✅ Assessment form has been reset.")
                st.rerun()
        with cancel_col:
            if st.button("❌ Cancel", key="cancel_reset_clear"):
                st.session_state.show_reset_confirm = False
                st.rerun()

    with col_btn2:
        analyze_btn = st.button("🌿 Analyze My Impact")


    if analyze_btn:

        placeholder = st.empty()

        with placeholder.container():
            show_card_skeleton()
            show_chart_skeleton()

# Existing analysis code here

        placeholder.empty()  
        total, contributors = calculate_footprint(
            transport, distance, electricity, diet, flights, region
        )

        eco_score = calculate_eco_score(total)


        # Circular Economy Score
        circular_score = 100

        if transport.lower() in ["car", "taxi"]:
            circular_score -= 20

        if electricity > 500:
            circular_score -= 20

        if diet.lower() == "non-vegetarian":
            circular_score -= 20

        if flights > 2:
            circular_score -= 20

        circular_score = max(0, circular_score)

        trees_required = max(1, round(total / 22))

        transport_emission = contributors.get("Transportation", 0)
        electricity_emission = contributors.get("Electricity", 0)
        diet_emission = contributors.get("Diet", 0)
        flight_emission = contributors.get("Flights", 0)

        insight, recommendations = generate_recommendations(
            transport, electricity, diet, flights, contributors
        )

        # --------------------------
        # Hidden Carbon Source Detector
        # --------------------------

        hidden_sources = []

        if transport > 20:
            hidden_sources.append(
                {
                    "source": "🚚 Food Delivery Packaging",
                    "impact": round(total * 0.05, 2),
                    "tip": "Cook at home occasionally or order multiple meals together."
                }
            )

        if flights > 0:
            hidden_sources.append(
                {
                    "source": "🧳 Airport & Travel Waste",
                    "impact": round(total * 0.08, 2),
                    "tip": "Pack light and avoid unnecessary short flights."
                }
            )

        if electricity > 8:
            hidden_sources.append(
                {
                    "source": "🔌 Idle Electronics",
                    "impact": round(total * 0.04, 2),
                    "tip": "Switch off chargers and unused devices."
                }
            )

        if diet > 6:
            hidden_sources.append(
                {
                    "source": "🥡 Food Packaging Waste",
                    "impact": round(total * 0.03, 2),
                    "tip": "Prefer reusable containers and local produce."
                }
            )

        # -------------------------
        # Cross-Module Smart Suggestions
        # -------------------------

        cross_module_suggestions = []

        if transport_emission > max(electricity_emission, diet_emission, flight_emission):
            cross_module_suggestions.append(
                "🛣️ Explore the Route Planning module to discover lower-emission travel options."
            )

        if electricity_emission > 5:
            cross_module_suggestions.append(
                "⚡ Open the Home Energy Audit section for personalized electricity-saving recommendations."
            )

        if flight_emission > 2:
            cross_module_suggestions.append(
                "✈️ Visit Carbon Offsets to balance emissions from frequent air travel."
            )

        if eco_score < 60:
            cross_module_suggestions.append(
                "🏆 Complete weekly sustainability challenges to improve your Eco Score faster."
            )

        if eco_score >= 80:
            cross_module_suggestions.append(
                "🌍 Compare your progress on the Community Leaderboard and inspire other users."
            )

        cross_module_suggestions.append(
            "📊 Review your Assessment History to monitor long-term sustainability progress."
        )

        save_assessment(user_id, 
            transport, distance, electricity, diet, flights, total, eco_score
        )
        gf.award_freeze_tokens_for_streak_milestones(user_id)
        gf.check_badge_eligibility(user_id)
        discard_current_draft(
            user_id,
            st.session_state,
        )

        st.success("✅ Analysis completed! Your sustainability score has been generated.")
        st.balloons()
        st.toast("🎉 Congratulations! Analysis completed successfully!")
        st.info("💡 Visit the Recommendations section to reduce your carbon footprint.")



        # -------------------------
        # INPUT CONFIDENCE SCORE
        # -------------------------

        confidence_score = 100
        missing_items = []

        if distance == 0:
            confidence_score -= 15
            missing_items.append("Transportation distance")

        if electricity == 0:
            confidence_score -= 20
            missing_items.append("Electricity usage")

        if flights == 0:
            confidence_score -= 10
            missing_items.append("Flight activity")

        if diet.lower() in ["unknown", "", "select"]:
            confidence_score -= 15
            missing_items.append("Diet information")

        confidence_score = max(confidence_score, 0)

        st.markdown("""
        <div class='card-highlight' style='margin-bottom:18px;'>
            <h3>🎯 Assessment Confidence</h3>
            <p>
                EcoBuddy evaluates the completeness and consistency of your inputs to
                estimate how reliable your carbon footprint assessment is. Providing
                detailed and accurate information improves recommendation quality and
                overall assessment accuracy.""")

        st.markdown("""
        <div class='card-highlight' style='margin-bottom:18px;'>
            <h3>🔗 Cross-Module Smart Suggestions</h3>
            <p>
                Based on your assessment results, EcoBuddy recommends additional
                modules that can help you further reduce your environmental impact.
                These suggestions connect different features across the application
                to provide a more personalized sustainability experience.""")


        st.caption(
            "These personalized feature recommendations are automatically generated "
            "after every assessment to help users discover useful EcoBuddy modules "
            "that match their environmental profile and encourage continued engagement."
        )

        # -------------------------
        # SMART FEATURE DISCOVERY
        # -------------------------

        st.markdown("""
        <div class='card-highlight' style='margin-bottom:18px;'>
            <h3 style='margin-bottom:12px;'>💡 Smart Feature Discovery</h3>
            <p style='color:#6b7280;'>
                Based on your assessment results, EcoBuddy has identified additional
                tools that can help you better understand, monitor, and reduce your
                environmental impact. Explore the suggestions below to continue your
                sustainability journey with personalized insights.

            </p>
        </div>
        """, unsafe_allow_html=True)



        st.markdown("### 🎯 Input Confidence Score")

        st.progress(confidence_score / 100)

        st.metric("Confidence", f"{confidence_score}%")

        if confidence_score >= 90:
            st.success("🟢 High confidence assessment. Your inputs appear complete and reliable.")

        elif confidence_score >= 70:
            st.warning("🟡 Medium confidence assessment. Some additional information could improve accuracy.")

        else:
            st.error("🔴 Low confidence assessment. Consider completing more fields for better estimates.")

        if missing_items:

            st.markdown("#### Missing or Incomplete Information")

            for item in missing_items:
                st.write(f"• {item}")

            st.info(
                "Providing more complete information will improve the accuracy "
                "of your carbon footprint calculations and recommendations."
            )

        st.markdown("#### 💡 Improvement Suggestions")

        if confidence_score < 100:

            st.write("✅ Provide accurate transportation distance.")
            st.write("✅ Enter realistic electricity consumption.")
            st.write("✅ Include annual flight information.")
            st.write("✅ Select the most appropriate diet type.")

        else:

            st.success(
                "Excellent! Your assessment contains sufficient information "
                "to generate highly reliable sustainability insights."
            )

        st.markdown("### 🔗 Cross-Module Smart Suggestions")

        st.caption(
            "EcoBuddy analyzed your assessment and identified additional modules "
            "that can provide relevant guidance based on your current environmental profile."
        )

        for item in cross_module_suggestions:
            st.info(item)


        feature_suggestions = []

        if contributors.get("transport", 0) > 0:
            feature_suggestions.append(
                "🚗 Try the Route Planning & Offsets tab to compare greener travel options and reduce transport emissions."
            )

        if electricity > 150:
            feature_suggestions.append(
                "⚡ Visit the Home Energy Audit section for recommendations that can reduce electricity consumption."
            )

        if eco_score < 70:
            feature_suggestions.append(
                "🏆 Improve your Eco Score by completing more assessments and earning sustainability badges."
            )

        feature_suggestions.append(
            "📈 Track your future environmental progress using the Future Self dashboard."
        )

        feature_suggestions.append(
            "🌍 Check the Community Leaderboard to compare your sustainability progress with other users."
        )

        st.info(
            "🌱 Personalized Feature Suggestions\n\n"
            "These recommendations are generated from your latest assessment "
            "to help you discover useful EcoBuddy features."
        )

        for suggestion in feature_suggestions:
            st.write(f"✅ {suggestion}")

        if st.button("❌ Dismiss Suggestions", key="dismiss_feature_suggestions"):
            st.success("Feature suggestions dismissed. They will appear again after your next assessment.")


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

            st.markdown(
                f"""
            <div class="metric-card">
                <div style="font-size:14px;color:#6b7280;">♻️ Circular Economy Score</div>
                <div style="font-size:34px;font-weight:700;color:#22c55e;">
                    {circular_score}/100
                </div>
            </div>
            """,
            unsafe_allow_html=True
            )

        with met4:
            st.markdown("""
            <div class='metric-card'>
                <div style='font-size: 14px; color: #374151; margin-bottom: 8px;'>🎯 Status</div>
                <div style='font-size: 18px; font-weight: 700; color: #4ade80;'>Active</div>
                <div style='font-size: 12px; color: #4b5563;'>Tracking enabled</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("<div class='section-header'>🌳 Carbon Offset Estimate</div>", unsafe_allow_html=True)

        st.markdown(f"""
        <div class='card-highlight'>
            <h3>🌱 Trees Needed</h3>
            <p style="font-size:18px;">
                Based on your estimated annual carbon footprint,
                you would need approximately
                <b style="font-size:32px; color:#22c55e;">
                    {trees_required}
                </b>
                mature trees to absorb the same amount of CO₂ in one year.
            </p>
            <p style="color:#6b7280;">
                This estimate assumes one mature tree absorbs around
                <b>22 kg CO₂/year</b>.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if trees_required <= 20:
         st.success("🌿 Great! Your footprint is relatively low.")
        elif trees_required <= 80:
            st.warning("🌳 Consider reducing emissions and supporting tree-planting initiatives.")
        else:
            st.error("🔥 Your footprint is high. Reducing transport and electricity usage can make a big difference.")

        # ============================================================
# 🌿 Eco Health Report
# ============================================================

        st.markdown("<div class='section-header'>🌿 Eco Health Report</div>", unsafe_allow_html=True)

        health_score = eco_score

        if health_score >= 90:
            grade = "A+"
            color = "#16a34a"
            status = "Outstanding Sustainability"
        elif health_score >= 80:
            grade = "A"
            color = "#22c55e"
            status = "Very Eco Friendly"
        elif health_score >= 70:
            grade = "B"
            color = "#84cc16"
            status = "Good Environmental Performance"
        elif health_score >= 60:
            grade = "C"
            color = "#eab308"
            status = "Needs Improvement"
        elif health_score >= 40:
            grade = "D"
            color = "#f97316"
            status = "High Environmental Impact"
        else:
            grade = "F"
            color = "#ef4444"
            status = "Critical Environmental Impact"


        st.info("♻️ Circular Economy Score evaluates how well your lifestyle follows sustainable and circular economy principles.")

        if circular_score < 60:
            st.warning(
                "Suggestions: Reduce unnecessary flights, lower electricity usage, prefer public transport, and adopt more sustainable food choices."
            )
        elif circular_score < 80:
            st.success(
                "Good progress! Small improvements in transport and energy consumption can further increase your Circular Economy Score."
            )
        else:
            st.success(
                "Excellent! Your current lifestyle strongly aligns with circular economy principles."
            )

        st.markdown("---")


        st.markdown(f"""
        <div style="
        padding:25px;
        border-radius:15px;
        background:#ffffff;
        border-left:8px solid {color};
        box-shadow:0 6px 18px rgba(0,0,0,0.08);
        margin-bottom:20px;
        ">
        <h2 style="color:{color};margin-bottom:5px;">
        Overall Grade : {grade}
        </h2>

        <h4 style="margin-top:0;">
        {status}
        </h4>

        <p>
        Your Eco Health Grade summarizes your sustainability habits based on
        transportation, electricity consumption, diet and air travel.
        </p>
        </div>
        """, unsafe_allow_html=True)

        strengths = []
        improvements = []

        if transport in ["Bike", "Walking"]:
            strengths.append("🚲 Excellent choice of transportation.")
        else:
            improvements.append("🚗 Reduce private vehicle usage.")

        if electricity <= 150:
            strengths.append("⚡ Efficient electricity consumption.")
        else:
            improvements.append("⚡ Try lowering monthly electricity usage.")

        if diet == "Vegetarian":
            strengths.append("🥗 Plant-based diet reduces emissions.")
        else:
            improvements.append("🥩 Consider reducing meat consumption.")

        if flights == 0:
            strengths.append("✈ Minimal flight emissions.")
        else:
            improvements.append("✈ Reduce unnecessary air travel.")

        col1, col2 = st.columns(2)

        with col1:
        
            st.success("### 🌱 Your Strengths")

            if strengths:
                for item in strengths:
                    st.write(item)
            else:
                st.write("No major strengths identified yet.")

        with col2:
        
            st.warning("### 📌 Improvement Areas")

            if improvements:
                for item in improvements:
                    st.write(item)
            else:
                st.write("Excellent! No major improvements needed.")

        st.markdown("### 📈 Sustainability Summary")

        st.info(
            f"""
        • Eco Score : **{eco_score}/100**

        • Annual Carbon Footprint : **{total:.2f} kg CO₂**

        • Biggest Contributor : **{max(contributors, key=contributors.get)}**

        • Estimated Trees Needed : **{max(1, round(total/22))}**

        Continue making sustainable choices to improve your grade in future assessments.
        """
        )

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

            selected_categories = st.multiselect(
                "Filter categories",
                options=list(contributors.keys()),
                default=list(contributors.keys()),
                key="emission_category_filter"
            )
            filtered_contributors = {
                k: v for k, v in contributors.items() if k in selected_categories
            } or contributors

            # Pie chart with Plotly
            import plotly.graph_objects as go
            fig = go.Figure(data=[go.Pie(
    labels=list(filtered_contributors.keys()),
    values=list(filtered_contributors.values()),
    hole=0.55,
    pull=[0.03] * len(filtered_contributors),
    textinfo="label+percent",
    textfont=dict(size=13),
    marker=dict(
        colors=['#22c55e', '#3b82f6', '#facc15', '#ef4444'],
        line=dict(color="white", width=2)
    ),
    hovertemplate="""
    <b>%{label}</b><br>
    Emissions: %{value:.1f} kg CO₂<br>
    Share: %{percent}<extra></extra>
    """
)])

            fig.update_layout(
    height=340,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=20, b=20),
    font=dict(size=13),
    hoverlabel=dict(
        bgcolor="white",
        font_size=13,
        font_family="Arial"
    ),
    legend=dict(
        orientation="h",
        y=-0.2,
        x=0.5,
        xanchor="center",
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#22c55e",
        borderwidth=1
    )
)

            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})        # -------------------------
        # DETAILED BREAKDOWN
        # -------------------------
       # -------------------------
# DETAILED BREAKDOWN
# -------------------------

st.markdown(
    "<div class='section-header'>📋 Detailed Breakdown</div>",
    unsafe_allow_html=True,
)

total_filtered = sum(filtered_contributors.values()) or 1

category_icons = {
    "Transport": "🚗",
    "Electricity": "⚡",
    "Food": "🍽️",
    "Waste": "🗑️",
}

for category, emission in filtered_contributors.items():
    percentage = (emission / total_filtered) * 100

    with st.expander(
        f"{category_icons.get(category, '🌿')} {category} • {emission:.1f} kg CO₂",
        expanded=False,
    ):

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Emission",
                f"{emission:.1f} kg CO₂",
            )

        with col2:
            st.metric(
                "Contribution",
                f"{percentage:.1f}%",
            )

        st.progress(min(percentage / 100, 1.0))

        if percentage >= 40:
            st.warning(
                "This category contributes significantly to your carbon footprint."
            )

        elif percentage >= 20:
            st.info(
                "There is room for improvement in this category."
            )

        else:
            st.success(
                "Great! This category has a relatively low carbon impact."
            )

        st.markdown("#### Tips")

        if category == "Transport":
            st.markdown(
                """
- 🚶 Walk or cycle for short trips
- 🚌 Use public transport
- 🚗 Carpool whenever possible
"""
            )

        elif category == "Electricity":
            st.markdown(
                """
- 💡 Switch to LED bulbs
- 🔌 Turn off unused appliances
- 🌞 Consider renewable energy
"""
            )

        elif category == "Food":
            st.markdown(
                """
- 🥗 Eat more plant-based meals
- 🛒 Buy local produce
- 🍽 Reduce food waste
"""
            )

        elif category == "Waste":
            st.markdown(
                """
- ♻ Recycle regularly
- 🚮 Compost organic waste
- 🛍 Use reusable bags
"""
            )

        else:
            st.markdown(
                """
- 🌱 Continue improving your sustainability habits.
"""
            )
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
        # WHAT CHANGED?
        # -------------------------
        history_after = get_assessments(user_id)
        if history_after and len(history_after) >= 2:
            prev = history_after[1]
            region_val = st.session_state.get("region", "Global")
            from emissions import calculate_footprint
            prev_total, prev_contributors = calculate_footprint(
                prev[2], prev[3], prev[4], prev[5], prev[6], region_val
            )
            current_data = {
                "transport": transport,
                "distance": distance,
                "electricity": electricity,
                "diet": diet,
                "flights": flights,
                "footprint": total,
                "eco_score": eco_score,
                "contributors": contributors,
            }
            prev_data = {
                "transport": prev[2],
                "distance": prev[3],
                "electricity": prev[4],
                "diet": prev[5],
                "flights": prev[6],
                "footprint": prev[7],
                "eco_score": prev[8],
                "contributors": prev_contributors,
            }
            diff_result = generate_what_changed_analysis(current_data, prev_data)
            if diff_result:
                render_what_changed_ui(diff_result)

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

        st.markdown("---")

        # =========================
        # 🌿 Green Decision Comparator
        # =========================

        st.markdown(
            "<div class='section-header'>🌿 Green Decision Comparator</div>",
            unsafe_allow_html=True,
        )

        st.write("Compare two everyday choices and see which is more eco-friendly.")

        options = {
            "Drive Car (10 km)": 2.3,
            "Public Transport (10 km)": 0.8,
            "Bike (10 km)": 0.0,
            "Walk (10 km)": 0.0,
            "Beef Meal": 5.0,
            "Vegetarian Meal": 1.5,
            "LED Bulb": 0.2,
            "Incandescent Bulb": 0.8,
        }

        col1, col2 = st.columns(2)

        with col1:
            choice1 = st.selectbox(
                "First Option",
                list(options.keys()),
                key="decision_1",
            )

        with col2:
            choice2 = st.selectbox(
                "Second Option",
                list(options.keys()),
                key="decision_2",
            )

        if st.button("Compare Choices"):

            emission1 = options[choice1]
            emission2 = options[choice2]

            st.metric(choice1, f"{emission1:.2f} kg CO₂")
            st.metric(choice2, f"{emission2:.2f} kg CO₂")

            if emission1 < emission2:
                st.success(f"✅ {choice1} is the greener option.")
                st.info(f"You save approximately {emission2-emission1:.2f} kg CO₂.")

            elif emission2 < emission1:
                st.success(f"✅ {choice2} is the greener option.")
                st.info(f"You save approximately {emission1-emission2:.2f} kg CO₂.")

            else:
                st.info("Both choices have similar environmental impact.")

        

        # ---------------------------------
        # Sustainability Learning Hub
        # ---------------------------------

        st.markdown("---")
        st.subheader("📚 Sustainability Learning Hub")

        learning_cards = []

        if transport_emission > max(electricity_emission, diet_emission, flight_emission):
            learning_cards.append(
                ("🚲 Green Transportation",
                "Walking, cycling, or public transport can significantly reduce your carbon footprint.")
            )

        if electricity_emission > 5:
            learning_cards.append(
                ("💡 Energy Saving",
                "Turning off unused appliances and using LED bulbs helps lower electricity emissions.")
            )

        if flight_emission > 0:
            learning_cards.append(
                ("✈️ Sustainable Travel",
                "Consider trains or virtual meetings whenever possible to reduce travel emissions.")
            )

        if diet_emission > 2:
            learning_cards.append(
                ("🥗 Sustainable Diet",
                "Eating more plant-based meals can reduce emissions from food production.")
            )

        if not learning_cards:
            learning_cards.append(
                ("🌍 Eco Fact",
                "Every small sustainable habit contributes to protecting our planet.")
            )

        search_topic = st.text_input(
            "🔍 Search sustainability topics",
            placeholder="transport, electricity, flights, diet..."
        )

        for title, content in learning_cards:
            if search_topic == "" or search_topic.lower() in title.lower() or search_topic.lower() in content.lower():
                with st.expander(title):
                    st.write(content)
                    
                    # ============================================================
                    # 🌍 Environmental Impact Comparison
                    # ============================================================

        # ============================================================
        # 🌎 Eco Performance Summary
        # ============================================================
        
        st.markdown(
            "<div class='section-header'>🌎 Eco Performance Summary</div>",
            unsafe_allow_html=True
        )
        
        transport_score = 100
        energy_score = 100
        diet_score = 100
        travel_score = 100
        
        if transport == "Car":
            transport_score = 50
        elif transport == "Public Transport":
            transport_score = 80
        elif transport == "Bike":
            transport_score = 100
        elif transport == "Walking":
            transport_score = 100
        
        if electricity > 300:
            energy_score = 40
        elif electricity > 200:
            energy_score = 60
        elif electricity > 100:
            energy_score = 80
        else:
            energy_score = 100
        
        if diet == "Non-Vegetarian":
            diet_score = 60
        
        if flights >= 8:
            travel_score = 20
        elif flights >= 5:
            travel_score = 40
        elif flights >= 3:
            travel_score = 60
        elif flights >= 1:
            travel_score = 80
        
        overall = round(
            (transport_score +
             energy_score +
             diet_score +
             travel_score) / 4
        )
        
        st.metric("Overall Sustainability Rating", f"{overall}/100")
        
        st.markdown("### Category Performance")
        
        categories = {
            "Transportation": transport_score,
            "Energy Usage": energy_score,
            "Diet": diet_score,
            "Air Travel": travel_score
        }
        
        for category, score in categories.items():
        
            st.write(f"**{category}**")
        
            st.progress(score / 100)
        
            if score >= 90:
                st.success("Excellent")
            elif score >= 70:
                st.info("Good")
            elif score >= 50:
                st.warning("Average")
            else:
                st.error("Needs Improvement")
        
        st.markdown("---")
        
        st.subheader("🌱 Positive Habits")
        
        good = []
        
        if transport in ["Bike", "Walking"]:
            good.append("🚴 Low-carbon transportation")
        
        if electricity <= 150:
            good.append("⚡ Efficient electricity usage")
        
        if diet == "Vegetarian":
            good.append("🥗 Environment-friendly diet")
        
        if flights == 0:
            good.append("✈ Low air travel emissions")
        
        if len(good) == 0:
            st.info("No significant eco-friendly habits identified yet.")
        else:
            for item in good:
                st.success(item)
        
        st.markdown("---")
        
        st.subheader("📌 Areas to Improve")
        
        bad = []
        
        if transport == "Car":
            bad.append("Use public transport or bike whenever possible.")
        
        if electricity > 200:
            bad.append("Reduce unnecessary electricity consumption.")
        
        if diet == "Non-Vegetarian":
            bad.append("Try including more plant-based meals.")
        
        if flights > 2:
            bad.append("Reduce air travel or offset flight emissions.")
        
        if len(bad) == 0:
            st.success("Excellent! No major improvement areas found.")
        else:
            for item in bad:
                st.warning(item)
        
        st.markdown("---")
        
        st.subheader("📊 Final Assessment")
        
        if overall >= 90:
            st.success("🌍 Outstanding sustainability performance!")
        elif overall >= 75:
            st.success("🌱 You're doing very well. Keep improving.")
        elif overall >= 60:
            st.info("🙂 Good progress. A few changes can make a big difference.")
        else:
            st.error("♻ Your environmental impact can be reduced with better daily habits.")
# ============================================================
# 🌍 Environmental Impact Comparison
# ============================================================


        st.markdown("<div class='section-header'>🌍 Environmental Impact Comparison</div>", unsafe_allow_html=True)
        
        benchmarks = {
            "Eco Lifestyle": 2000,
            "Average Citizen": 4500,
            "High Consumer": 8000
        }
        
        st.markdown(
            "Compare your estimated annual carbon footprint with common environmental benchmarks."
        )
        
        comparison_data = [
            ("🌱 Eco Lifestyle", benchmarks["Eco Lifestyle"]),
            ("🙂 Average Citizen", benchmarks["Average Citizen"]),
            ("🏭 High Consumer", benchmarks["High Consumer"]),
            ("👤 You", total),
        ]
        
        for name, value in comparison_data:
        
            if name == "👤 You":
                progress = min(value / benchmarks["High Consumer"], 1.0)
        
                st.markdown(f"""
                <div style="
                padding:18px;
                border-radius:12px;
                border:2px solid #22c55e;
                background:#f0fdf4;
                margin-bottom:12px;
                ">
                <h4>{name}</h4>
                <p><b>{value:.0f} kg CO₂/year</b></p>
                </div>
                """, unsafe_allow_html=True)
        
                st.progress(progress)
        
            else:
                st.markdown(f"""
                <div style="
                padding:15px;
                border-radius:10px;
                border:1px solid #d1d5db;
                margin-bottom:8px;
                ">
                <b>{name}</b><br>
                {value:.0f} kg CO₂/year
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("### 📊 Your Position")
        
        if total <= benchmarks["Eco Lifestyle"]:
            st.success("🌱 Excellent! Your footprint is even lower than a typical eco-friendly lifestyle.")
        elif total <= benchmarks["Average Citizen"]:
            st.info("😊 Great! Your emissions are below the average citizen.")
        elif total <= benchmarks["High Consumer"]:
            st.warning("⚠️ Your emissions are above average. Small lifestyle changes can significantly reduce them.")
        else:
            st.error("🚨 Your emissions exceed the high consumer benchmark. Consider reducing transport and electricity usage.")
        
        difference = benchmarks["Average Citizen"] - total
        
        if difference > 0:
            st.success(
                f"You emit approximately **{difference:.0f} kg CO₂ less** than the average citizen each year."
            )
        else:
            st.warning(
                f"You emit approximately **{abs(difference):.0f} kg CO₂ more** than the average citizen each year."
            )
        
        st.caption(
            "These benchmark values are illustrative and intended to help users better understand the relative scale of their carbon footprint."
        )
                    # ============================================================
        # 🌍 Carbon Footprint Comparison
        # ============================================================

        st.markdown(
            "<div class='section-header'>🌍 Carbon Footprint Comparison</div>",
            unsafe_allow_html=True,
        )

        st.caption(
            "See how your annual carbon footprint compares with common lifestyle benchmarks."
        )

        comparison_levels = [
            {
                "name": "🌱 Eco Lifestyle",
                "value": 2000,
                "description": "Highly sustainable transportation, renewable energy, and low-impact diet.",
            },
            {
                "name": "🙂 Average Citizen",
                "value": 4500,
                "description": "Represents a typical yearly carbon footprint.",
            },
            {
                "name": "🏭 High Consumer",
                "value": 8000,
                "description": "Frequent private transport, high electricity use, and regular air travel.",
            },
        ]

        comparison_levels.append(
            {
                "name": "👤 Your Footprint",
                "value": total,
                "description": "Calculated from your latest assessment.",
            }
        )

        highest_value = max(item["value"] for item in comparison_levels)

        st.markdown("### 📊 Comparison Overview")

        for item in comparison_levels:
        
            progress = item["value"] / highest_value

            if item["name"] == "👤 Your Footprint":
                border = "#22c55e"
                background = "#ecfdf5"
            else:
                border = "#d1d5db"
                background = "#ffffff"

            st.markdown(
                f"""
        <div style="
        padding:18px;
        margin-bottom:14px;
        border-radius:12px;
        border-left:6px solid {border};
        background:{background};
        box-shadow:0 4px 12px rgba(0,0,0,0.06);
        ">
        <h4>{item["name"]}</h4>

        <p style="margin-bottom:6px;">
        <b>{item["value"]:.0f} kg CO₂/year</b>
        </p>

        <p style="color:#6b7280;">
        {item["description"]}
        </p>
        </div>
        """,
                unsafe_allow_html=True,
            )

            st.progress(progress)

        st.markdown("---")

        st.markdown("### 🏅 Your Environmental Rating")

        if total <= 2000:
            rating = "Excellent"
            color = "green"
            message = (
                "Your carbon footprint is exceptionally low. "
                "You are following highly sustainable habits."
            )

        elif total <= 4500:
            rating = "Good"
            color = "blue"
            message = (
                "Your footprint is below the average citizen. "
                "Keep maintaining your sustainable lifestyle."
            )

        elif total <= 8000:
            rating = "Average"
            color = "orange"
            message = (
                "Your emissions are above average. "
                "There is significant room for improvement."
            )

        else:
            rating = "High Impact"
            color = "red"
            message = (
                "Your annual emissions are considerably higher than recommended."
            )

        if color == "green":
            st.success(f"🏆 Rating: {rating}\n\n{message}")

        elif color == "blue":
            st.info(f"🌿 Rating: {rating}\n\n{message}")

        elif color == "orange":
            st.warning(f"⚠ Rating: {rating}\n\n{message}")

        else:
            st.error(f"🚨 Rating: {rating}\n\n{message}")

        st.markdown("---")

        st.markdown("### 📈 Comparison Statistics")

        col1, col2, col3 = st.columns(3)

        average_value = 4500
        difference = average_value - total

        with col1:
            st.metric(
                "Your Footprint",
                f"{total:.0f} kg",
            )

        with col2:
        
            if difference >= 0:
                st.metric(
                    "Compared to Average",
                    f"{abs(difference):.0f} kg Less",
                )
            else:
                st.metric(
                    "Compared to Average",
                    f"{abs(difference):.0f} kg More",
                )

        with col3:
        
            percentage = (total / average_value) * 100

            st.metric(
                "Average Usage",
                f"{percentage:.1f}%"
            )

        st.markdown("---")

        st.markdown("### 💡 What This Means")

        if total <= 2000:
        
            st.success(
                """
        You are performing better than the eco-lifestyle benchmark.

        Continue using sustainable transport, renewable energy,
        and environmentally friendly habits.
        """
            )

        elif total <= 4500:
        
            st.info(
                """
        You are below the average citizen.

        Small improvements in transportation or electricity
        usage can further reduce your emissions.
        """
            )

        elif total <= 8000:
        
            st.warning(
                """
        Your footprint is higher than the average.

        Focus on reducing electricity consumption,
        private vehicle usage, and unnecessary flights.
        """
            )

        else:
        
            st.error(
                """
        Your emissions are significantly higher than recommended.

        Consider major improvements in transportation,
        energy consumption, and travel habits.
        """
            )

        st.caption(
            "Benchmark values are reference estimates used only for comparison and educational purposes."
        )
                

        
        st.markdown("---")
        # ============================================================
        # 🏆 Sustainability Milestones
        # ============================================================

        st.markdown(
            "<div class='section-header'>🏆 Sustainability Milestones</div>",
            unsafe_allow_html=True
        )

        milestones = [
            {
                "title": "Eco Beginner",
                "condition": eco_score >= 50,
                "description": "Achieve an Eco Score of at least 50."
            },
            {
                "title": "Green Commuter",
                "condition": transport in ["Bike", "Walking", "Public Transport"],
                "description": "Use sustainable transportation."
            },
            {
                "title": "Energy Saver",
                "condition": electricity <= 150,
                "description": "Keep monthly electricity usage below 150 kWh."
            },
            {
                "title": "Plant Friendly",
                "condition": diet == "Vegetarian",
                "description": "Follow a vegetarian diet."
            },
            {
                "title": "Flight Free",
                "condition": flights == 0,
                "description": "Avoid annual air travel."
            },
            {
                "title": "Eco Expert",
                "condition": eco_score >= 90,
                "description": "Achieve an Eco Score above 90."
            }
        ]

        completed = 0

        for milestone in milestones:
        
            if milestone["condition"]:
                completed += 1

        progress = completed / len(milestones)

        st.metric(
            "Milestones Completed",
            f"{completed}/{len(milestones)}"
        )

        st.progress(progress)

        st.markdown("---")

        for milestone in milestones:
        
            if milestone["condition"]:
            
                st.markdown(f"""
                <div style="
                padding:18px;
                border-radius:12px;
                background:#ecfdf5;
                border-left:6px solid #22c55e;
                margin-bottom:12px;
                ">
                <h4>✅ {milestone['title']}</h4>
                <p>{milestone['description']}</p>
                <b>Status:</b> Unlocked
                </div>
                """, unsafe_allow_html=True)

            else:
            
                st.markdown(f"""
                <div style="
                padding:18px;
                border-radius:12px;
                background:#f9fafb;
                border-left:6px solid #9ca3af;
                margin-bottom:12px;
                ">
                <h4>🔒 {milestone['title']}</h4>
                <p>{milestone['description']}</p>
                <b>Status:</b> Locked
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        remaining = len(milestones) - completed

        if remaining == 0:
        
            st.success(
                "🎉 Congratulations! You have unlocked every sustainability milestone."
            )

        else:
        
            st.info(
                f"You are only **{remaining} milestone(s)** away from completing the collection."
            )

        st.caption(
            "Complete more eco-friendly activities to unlock additional sustainability milestones and improve your overall environmental performance."
        )

        with st.expander("🧮 Interactive Calculation Breakdown", expanded=False):

            st.markdown("### Step-by-Step Carbon Footprint Calculation")

            st.markdown("#### 🚗 Transportation")
            st.write(f"Mode: **{transport}**")
            st.write(f"Distance: **{distance} km/day**")
            st.success(f"Contribution: **{transport_emission:.2f} kg CO₂**")

            st.markdown("#### ⚡ Electricity")
            st.write(f"Monthly Usage: **{electricity} kWh**")
            st.success(f"Contribution: **{electricity_emission:.2f} kg CO₂**")

            st.markdown("#### 🥗 Diet")
            st.write(f"Diet Type: **{diet}**")
            st.success(f"Contribution: **{diet_emission:.2f} kg CO₂**")

            st.markdown("#### ✈ Flights")
            st.write(f"Flights per year: **{flights}**")
            st.success(f"Contribution: **{flight_emission:.2f} kg CO₂**")

            st.markdown("---")

            st.metric("🌍 Total Carbon Footprint", f"{total:.2f} kg CO₂")

            st.info("""
        ### How the total is calculated

        The final carbon footprint is calculated by combining:

        • Transportation emissions

        • Electricity consumption

        • Diet impact

        • Flight emissions

        Each category contributes independently to the final result. Expanding this section allows users to inspect every intermediate value instead of only viewing the final score, making the assessment more transparent and easier to understand.
        """)

        # ============================================================
        # 🌍 Personalized Eco Action Plan
        # ============================================================

        st.markdown(
            "<div class='section-header'>🌍 Personalized Eco Action Plan</div>",
            unsafe_allow_html=True
        )

        actions = []

        if transport == "Car":
            actions.append({
                "title": "🚲 Choose Greener Transportation",
                "priority": "High",
                "benefit": "Reduce transportation emissions by using public transport, cycling, or walking whenever possible."
            })

        if electricity > 200:
            actions.append({
                "title": "⚡ Reduce Electricity Usage",
                "priority": "High",
                "benefit": "Switch off unused appliances and use energy-efficient devices."
            })

        if diet == "Non-Vegetarian":
            actions.append({
                "title": "🥗 Improve Dietary Choices",
                "priority": "Medium",
                "benefit": "Adding more plant-based meals can significantly reduce your carbon footprint."
            })

        if flights > 2:
            actions.append({
                "title": "✈ Reduce Air Travel",
                "priority": "High",
                "benefit": "Reduce unnecessary flights or offset emissions through verified programs."
            })

        if eco_score >= 85:
            actions.append({
                "title": "🌱 Inspire Others",
                "priority": "Low",
                "benefit": "Share your sustainable lifestyle and encourage friends and family."
            })

        if len(actions) == 0:
        
            st.success(
                "🎉 Excellent! Your current lifestyle already follows many sustainable practices."
            )

        else:
        
            st.metric("Recommended Actions", len(actions))

            priority_colors = {
                "High": "#ef4444",
                "Medium": "#f59e0b",
                "Low": "#22c55e"
            }

            for index, action in enumerate(actions, start=1):
            
                color = priority_colors[action["priority"]]

                st.markdown(f"""
                <div style="
                    border-left:6px solid {color};
                    background:#ffffff;
                    padding:18px;
                    margin-bottom:14px;
                    border-radius:10px;
                    box-shadow:0 4px 12px rgba(0,0,0,.06);
                ">
                    <h4>{index}. {action['title']}</h4>

                    <p><b>Priority:</b>
                    <span style="color:{color};">
                    {action['priority']}
                    </span></p>

                    <p>{action['benefit']}</p>

                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        completed = max(0, eco_score)

        st.subheader("📈 Sustainability Readiness")

        st.progress(completed / 100)

        if eco_score >= 90:
            st.success("Your sustainability readiness is outstanding.")
        elif eco_score >= 75:
            st.info("You are close to becoming an Eco Champion.")
        elif eco_score >= 60:
            st.warning("A few improvements will significantly reduce your emissions.")
        else:
            st.error("Your action plan should focus on high-priority improvements first.")

        st.caption(
            "The action plan is generated dynamically based on your latest assessment to help you prioritize sustainability improvements."
        )
        report = generate_pdf(total, eco_score, insight)

        report_validation = validate_report_data(
            total,
            eco_score,
            insight,
        )


        if not report_validation.is_valid:
            st.error(
                "The report could not be generated because the assessment "
                "contains invalid or incomplete data."
            )
            for validation_error in report_validation.errors:
                st.warning(f"• {validation_error}")
        else:
            from report import generate_pdf
            report = generate_pdf(
                report_validation.cleaned_data["total"],
                report_validation.cleaned_data["eco_score"],
                report_validation.cleaned_data["insight"],
            )

            if report:
                with open(report, "rb") as report_file:
                    pdf_bytes = report_file.read()

                try:
                    os.remove(report)
                except OSError:
                    pass

                st.download_button(
                    "📄 Download Eco Report (PDF)",
                    pdf_bytes,
                    file_name="EcoBuddy_Report.pdf",
                    mime="application/pdf",
                )
            else:
                st.error(
                    "The assessment data is valid, but the PDF could not be "
                    "created. Please try again."
                )
            # ============================================================
        # 🌍 Carbon Budget Manager
        # ============================================================

        st.markdown(
            "<div class='section-header'>💰 Carbon Budget Manager</div>",
            unsafe_allow_html=True
        )

        if "monthly_budget" not in st.session_state:
            st.session_state.monthly_budget = 500

        budget = st.slider(
            "Set Monthly Carbon Budget (kg CO₂)",
            min_value=100,
            max_value=2000,
            step=50,
            value=st.session_state.monthly_budget,
            help="Choose your personal monthly carbon emission target."
        )

        st.session_state.monthly_budget = budget

        monthly_emission = total / 12

        remaining_budget = budget - monthly_emission

        used_percent = (monthly_emission / budget) * 100

        used_percent = min(used_percent, 100)

        remaining_percent = max(0, 100 - used_percent)

        st.markdown("---")

        card1, card2, card3, card4 = st.columns(4)

        with card1:
        
            st.metric(
                "Monthly Budget",
                f"{budget:.0f} kg"
            )

        with card2:
        
            st.metric(
                "Estimated Usage",
                f"{monthly_emission:.1f} kg"
            )

        with card3:
        
            st.metric(
                "Remaining",
                f"{max(0, remaining_budget):.1f} kg"
            )

        with card4:
        
            st.metric(
                "Budget Used",
                f"{used_percent:.1f}%"
            )

        st.markdown("---")

        st.subheader("📊 Budget Progress")

        st.progress(used_percent / 100)

        if used_percent < 50:
        
            st.success(
                "✅ Excellent! You've used less than half of your monthly carbon budget."
            )

        elif used_percent < 75:
        
            st.info(
                "🌱 You're within your monthly carbon budget."
            )

        elif used_percent < 90:
        
            st.warning(
                "⚠ You're approaching your monthly carbon budget limit."
            )

        else:
        
            st.error(
                "🚨 Your estimated emissions are close to or above your monthly budget."
            )

        st.markdown("---")

        st.subheader("📋 Budget Breakdown")

        left, right = st.columns(2)

        with left:
        
            st.info(f"""
        ### Current Budget

        Monthly Budget

        **{budget:.0f} kg CO₂**

        Estimated Monthly Usage

        **{monthly_emission:.1f} kg CO₂**
        """)

        with right:
        
            st.info(f"""
        ### Remaining Allowance

        Remaining Budget

        **{max(0, remaining_budget):.1f} kg CO₂**

        Remaining Percentage

        **{remaining_percent:.1f}%**
        """)

        st.markdown("---")

        st.subheader("🎯 Budget Status")

        if remaining_budget > 250:
        
            st.success(
                "You still have plenty of room within your monthly carbon budget."
            )

        elif remaining_budget > 100:
        
            st.info(
                "Your budget is healthy, but continue making sustainable choices."
            )

        elif remaining_budget > 0:
        
            st.warning(
                "Your remaining budget is getting low."
            )

        else:
        
            st.error(
                "Your monthly carbon budget has been exceeded."
            )

        st.markdown("---")

        st.subheader("💡 Budget Suggestions")

        tips = []

        if transport == "Car":
            tips.append(
                "🚲 Switch to cycling or public transportation to save carbon budget."
            )

        if electricity > 200:
            tips.append(
                "⚡ Reduce electricity usage by switching off unused appliances."
            )

        if diet == "Non-Vegetarian":
            tips.append(
                "🥗 Add more plant-based meals during the week."
            )

        if flights > 2:
            tips.append(
                "✈ Reduce unnecessary air travel."
            )

        if eco_score >= 90:
        
            tips.append(
                "🌍 Great work! Maintain your current sustainable lifestyle."
            )

        if len(tips) == 0:
        
            st.success(
                "No immediate suggestions. Your carbon budget is well managed."
            )

        else:
        
            for tip in tips:
            
                st.write(f"✅ {tip}")

        st.markdown("---")

        st.subheader("📈 Budget Health")

        health = 100 - used_percent

        health = max(0, health)

        st.progress(health / 100)

        if health >= 80:
        
            health_text = "Excellent"

        elif health >= 60:
        
            health_text = "Good"

        elif health >= 40:
        
            health_text = "Average"

        elif health >= 20:
        
            health_text = "Poor"

        else:
        
            health_text = "Critical"

        st.metric(
            "Budget Health Score",
            f"{health:.0f}/100"
        )

        st.caption(
            f"Current Budget Health : {health_text}"
        )

        st.markdown("---")

        st.subheader("📌 Quick Summary")

        summary = [
            ("Monthly Budget", f"{budget:.0f} kg"),
            ("Estimated Usage", f"{monthly_emission:.1f} kg"),
            ("Remaining Budget", f"{max(0, remaining_budget):.1f} kg"),
            ("Budget Utilization", f"{used_percent:.1f}%"),
            ("Eco Score", f"{eco_score}/100")
        ]

        for title, value in summary:
        
            col1, col2 = st.columns([2,1])

            with col1:
                st.write(title)

            with col2:
                st.write(f"**{value}**")

        st.info(
            "Your Carbon Budget Manager helps monitor monthly emissions and encourages sustainable decisions by comparing estimated emissions with your chosen budget."
        )
                            # ============================================================
        # 📊 Carbon Budget Analytics
        # ============================================================

        import pandas as pd
        import plotly.graph_objects as go
        from datetime import datetime

        st.markdown(
            "<div class='section-header'>📊 Carbon Budget Analytics</div>",
            unsafe_allow_html=True
        )

        # ----------------------------
        # Session History
        # ----------------------------
        if "budget_history" not in st.session_state:
            st.session_state.budget_history = []

        history = st.session_state.budget_history

        history.append({
            "date": datetime.now().strftime("%d %b %Y"),
            "budget": budget,
            "usage": round(monthly_emission,2),
            "remaining": round(max(0,remaining_budget),2),
            "eco_score": eco_score
        })

        # Keep only latest 12 entries
        if len(history) > 12:
            history.pop(0)

        df = pd.DataFrame(history)

        st.subheader("📅 Budget History")

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")

        # ----------------------------
        # Trend Chart
        # ----------------------------

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["budget"],
                mode="lines+markers",
                name="Budget"
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["usage"],
                mode="lines+markers",
                name="Usage"
            )
        )

        fig.update_layout(
            height=400,
            title="Monthly Carbon Budget Trend",
            xaxis_title="Assessment",
            yaxis_title="kg CO₂"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.markdown("---")

        # ----------------------------
        # Budget Achievement
        # ----------------------------

        st.subheader("🏆 Budget Achievement")

        if used_percent <= 25:
        
            badge = "🥇 Carbon Saver"

        elif used_percent <= 50:
        
            badge = "🥈 Eco Performer"

        elif used_percent <= 75:
        
            badge = "🥉 Budget Keeper"

        elif used_percent <= 100:
        
            badge = "⚠ Budget Watch"

        else:
        
            badge = "🚨 Budget Exceeded"

        st.metric(
            "Current Achievement",
            badge
        )

        st.markdown("---")

        # ----------------------------
        # Budget Forecast
        # ----------------------------

        st.subheader("📈 Budget Forecast")

        days_in_month = 30

        daily_average = monthly_emission / days_in_month

        forecast = daily_average * days_in_month

        st.metric(
            "Projected Monthly Emission",
            f"{forecast:.1f} kg"
        )

        if forecast <= budget:
        
            st.success(
                "Based on current estimates, you are likely to stay within your budget."
            )

        else:
        
            st.error(
                "Current trend suggests your budget may be exceeded this month."
            )

        st.markdown("---")

        # ----------------------------
        # Budget Alerts
        # ----------------------------

        st.subheader("🚨 Budget Alerts")

        alerts = []

        if transport == "Car":
            alerts.append("Transportation contributes significantly to your budget usage.")

        if electricity > 250:
            alerts.append("Electricity consumption is above the recommended range.")

        if flights > 3:
            alerts.append("Frequent air travel greatly increases emissions.")

        if eco_score < 60:
            alerts.append("Your Eco Score indicates room for improvement.")

        if remaining_budget <= 50:
            alerts.append("Remaining monthly budget is critically low.")

        if len(alerts) == 0:
        
            st.success(
                "No active budget alerts."
            )

        else:
        
            for alert in alerts:
            
                st.warning(alert)

        st.markdown("---")

        # ----------------------------
        # Budget Insights
        # ----------------------------

        st.subheader("💡 Budget Insights")

        highest = max(contributors,key=contributors.get)

        lowest = min(contributors,key=contributors.get)

        st.info(
        f"""
        Highest Contributor

        **{highest}**

        Lowest Contributor

        **{lowest}**
        """
        )

        if highest == "Transportation":
        
            st.write("🚲 Switching transportation habits would have the biggest impact.")

        elif highest == "Electricity":
        
            st.write("⚡ Reducing electricity consumption offers the greatest savings.")

        elif highest == "Diet":
        
            st.write("🥗 Dietary changes can noticeably reduce emissions.")

        elif highest == "Flights":
        
            st.write("✈ Reducing flights will significantly improve your budget.")

        st.markdown("---")

        # ----------------------------
        # Monthly Recommendation
        # ----------------------------

        st.subheader("🎯 Monthly Recommendation")

        if used_percent < 50:
        
            st.success(
                "Excellent progress. Maintain your current lifestyle."
            )

        elif used_percent < 80:
        
            st.info(
                "Minor lifestyle improvements can further reduce emissions."
            )

        else:
        
            st.error(
                "Focus on high-impact emission sources to remain within budget."
            )

        st.caption(
                    "Carbon Budget Analytics provides a historical view of your budget usage and helps forecast future emission trends."
                )
                                                            # ============================================================
        # 💾 Carbon Budget Records
        # ============================================================

        st.markdown(
            "<div class='section-header'>💾 Budget Records</div>",
            unsafe_allow_html=True
        )

        if "saved_budgets" not in st.session_state:
            st.session_state.saved_budgets = []

        save_col, reset_col = st.columns(2)

        with save_col:
        
            if st.button("💾 Save Current Budget"):
            
                record = {
                    "Date": datetime.now().strftime("%d %b %Y %H:%M"),
                    "Budget": budget,
                    "Usage": round(monthly_emission,2),
                    "Remaining": round(max(0,remaining_budget),2),
                    "Eco Score": eco_score,
                    "Health": health_text
                }

                st.session_state.saved_budgets.append(record)

                st.success("Budget snapshot saved successfully.")

        with reset_col:
        
            if st.button("🔄 Reset Budget History"):
            
                st.session_state.saved_budgets.clear()

                st.success("Budget history cleared.")

        st.markdown("---")

        records = st.session_state.saved_budgets

        if len(records) == 0:
        
            st.info("No saved budget records available.")

        else:
        
            history_df = pd.DataFrame(records)

            st.subheader("📋 Saved Budget History")

            search = st.text_input(
                "Search by Date",
                placeholder="Search..."
            )

            if search:
            
                history_df = history_df[
                    history_df["Date"].str.contains(
                        search,
                        case=False
                    )
                ]

            st.dataframe(
                history_df,
                use_container_width=True,
                hide_index=True
            )

        st.markdown("---")

        # ============================================================
        # Budget Statistics
        # ============================================================

        if len(records) > 0:
        
            stats_df = pd.DataFrame(records)

            st.subheader("📊 Budget Statistics")

            c1,c2,c3,c4 = st.columns(4)

            with c1:
            
                st.metric(
                    "Saved Records",
                    len(stats_df)
                )

            with c2:
            
                st.metric(
                    "Average Usage",
                    f"{stats_df['Usage'].mean():.1f} kg"
                )

            with c3:
            
                st.metric(
                    "Highest Usage",
                    f"{stats_df['Usage'].max():.1f} kg"
                )

            with c4:
            
                st.metric(
                    "Lowest Usage",
                    f"{stats_df['Usage'].min():.1f} kg"
                )

        st.markdown("---")

        # ============================================================
        # Delete Individual Record
        # ============================================================

        if len(records) > 0:
        
            st.subheader("🗑 Delete Record")

            options = [
                f"{i+1}. {r['Date']}"
                for i,r in enumerate(records)
            ]

            selected = st.selectbox(
                "Select Record",
                options
            )

            delete_index = options.index(selected)

            if st.button("Delete Selected Record"):
            
                st.session_state.saved_budgets.pop(delete_index)

                st.success("Record deleted.")

                st.rerun()

        st.markdown("---")

        # ============================================================
        # Budget Summary
        # ============================================================

        st.subheader("📌 Budget Summary")

        if len(records)==0:
        
            st.info(
                "Save budget snapshots to build your monthly history."
            )

        else:
        
            latest = records[-1]

            st.markdown(f"""
        **Latest Budget**

        • Budget : **{latest['Budget']} kg**

        • Usage : **{latest['Usage']} kg**

        • Remaining : **{latest['Remaining']} kg**

        • Eco Score : **{latest['Eco Score']}**

        • Budget Health : **{latest['Health']}**
        """)

        st.caption(
            "Saved budget snapshots allow you to compare your sustainability progress over time."
        )
        # ============================================================
        # 📤 Carbon Budget Reports & Analytics
        # ============================================================

        import io
        import pandas as pd

        st.markdown(
            "<div class='section-header'>📤 Budget Reports & Analytics</div>",
            unsafe_allow_html=True
        )

        records = st.session_state.get("saved_budgets", [])

        # ------------------------------------------------------------
        # Export CSV
        # ------------------------------------------------------------

        if records:
        
            export_df = pd.DataFrame(records)

            csv = export_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                "📥 Export Budget History (CSV)",
                data=csv,
                file_name="carbon_budget_history.csv",
                mime="text/csv",
                use_container_width=True
            )

        else:
        
            st.info("Save at least one budget snapshot to enable export.")

        st.markdown("---")

        # ------------------------------------------------------------
        # Annual Projection
        # ------------------------------------------------------------

        st.subheader("📅 Annual Carbon Projection")

        annual_projection = monthly_emission * 12

        goal_projection = budget * 12

        col1, col2 = st.columns(2)

        with col1:
        
            st.metric(
                "Projected Annual Emissions",
                f"{annual_projection:.1f} kg"
            )

        with col2:
        
            st.metric(
                "Annual Carbon Budget",
                f"{goal_projection:.1f} kg"
            )

        difference = goal_projection - annual_projection

        if difference >= 0:
        
            st.success(
                f"You are projected to remain within your annual budget by {difference:.1f} kg CO₂."
            )

        else:
        
            st.error(
                f"You may exceed your annual budget by {abs(difference):.1f} kg CO₂."
            )

        st.markdown("---")

        # ------------------------------------------------------------
        # Carbon Savings Calculator
        # ------------------------------------------------------------

        st.subheader("💰 Carbon Savings Calculator")

        saving_options = {
            "Cycle instead of driving twice a week":80,
            "Reduce electricity by 10%":120,
            "Replace 3 meat meals weekly":90,
            "Skip one domestic flight":250,
            "Work from home one day/week":70,
            "Install LED lighting":40
        }

        selected = st.multiselect(
            "Select sustainability actions",
            list(saving_options.keys())
        )

        estimated_savings = sum(
            saving_options[item]
            for item in selected
        )

        new_emission = max(
            0,
            annual_projection-estimated_savings
        )

        st.metric(
            "Estimated Annual Savings",
            f"{estimated_savings} kg CO₂"
        )

        st.metric(
            "Projected New Annual Emission",
            f"{new_emission:.1f} kg CO₂"
        )

        st.markdown("---")

        # ------------------------------------------------------------
        # Smart Notifications
        # ------------------------------------------------------------

        st.subheader("🔔 Budget Notifications")

        notifications = []

        if used_percent > 90:
            notifications.append(
                "🚨 You are very close to exceeding your monthly carbon budget."
            )

        if eco_score < 60:
            notifications.append(
                "⚠ Your Eco Score is below the recommended level."
            )

        if transport == "Car":
            notifications.append(
                "🚗 Transportation is a major contributor to your emissions."
            )

        if electricity > 250:
            notifications.append(
                "⚡ Electricity usage is relatively high this month."
            )

        if flights > 2:
            notifications.append(
                "✈ Air travel significantly impacts your carbon budget."
            )

        if not notifications:
        
            st.success(
                "No important notifications at the moment."
            )

        else:
        
            for note in notifications:
            
                st.warning(note)

        st.markdown("---")

        # ------------------------------------------------------------
        # AI Budget Advisor
        # ------------------------------------------------------------

        st.subheader("🤖 AI Budget Advisor")

        advice = []

        if transport == "Car":
            advice.append(
                "Switching to public transport a few days each week could noticeably reduce your monthly emissions."
            )

        if electricity > 200:
            advice.append(
                "Consider replacing older appliances with energy-efficient alternatives."
            )

        if diet == "Non-Vegetarian":
            advice.append(
                "Increasing plant-based meals can reduce food-related emissions."
            )

        if flights > 2:
            advice.append(
                "Reducing unnecessary flights will have one of the largest impacts on your carbon footprint."
            )

        if eco_score >= 90:
            advice.append(
                "Excellent progress! Maintain your current habits and inspire others."
            )

        if not advice:
        
            st.success(
                "Your lifestyle is already highly sustainable. Keep up the great work!"
            )

        else:
        
            for index, item in enumerate(advice, start=1):
            
                st.info(f"{index}. {item}")

        st.markdown("---")

        # ------------------------------------------------------------
        # Goal Completion
        # ------------------------------------------------------------

        st.subheader("🎯 Budget Goal Completion")

        goal = budget

        completion = min(
            monthly_emission / goal,
            1.0
        )

        st.progress(completion)

        if completion < 0.5:
        
            st.success("Excellent progress toward your monthly budget goal.")

        elif completion < 0.75:
        
            st.info("You are comfortably within your budget.")

        elif completion < 1:
        
            st.warning("Approaching your monthly budget limit.")

        else:
        
            st.error("Monthly budget exceeded.")

        st.markdown("---")

        # ------------------------------------------------------------
        # Sustainability Scorecard
        # ------------------------------------------------------------

        st.subheader("🏅 Sustainability Scorecard")

        scorecard = {
            "Eco Score": eco_score,
            "Budget Health": round(health),
            "Budget Usage": round(100-used_percent),
            "Carbon Efficiency": round(max(0,100-(monthly_emission/budget*100)))
        }

        score_df = pd.DataFrame(
            scorecard.items(),
            columns=["Metric","Score"]
        )

        st.dataframe(
            score_df,
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "The Carbon Budget Manager combines budget tracking, analytics, projections, exports, and personalized guidance to help users monitor and improve their sustainability performance over time."
        )        
        render_sustainability_hub()
        render_eco_tip()
        # -------------------------
        # HISTORY & TRACKING
        # -------------------------
        st.markdown("---")
        with st.expander("🕒 Assessment Timeline", expanded=False):
            st.markdown("<div class='section-header'>📈 Your Eco Journey</div>", unsafe_allow_html=True)

        history = get_assessments(user_id)

        # ----------------------------------
        # Eco Action Streak Risk Detector
        # ----------------------------------

        if history and len(history) >= 3:
            recent_scores = [row[-1] for row in history[:3]]

            score_drop = recent_scores[2] - recent_scores[0]

            if score_drop >= 20:
                risk = "🔴 High Risk"
                color = "#ff4d4d"
            elif score_drop >= 10:
                risk = "🟠 Medium Risk"
                color = "#ff9800"
            else:
                risk = "🟢 Low Risk"
                color = "#4caf50"

            st.markdown(
                f"""
                <div style="
                    padding:14px;
                    border-radius:12px;
                    background:#111827;
                    border-left:6px solid {color};
                    margin-bottom:12px;">
                    <h4>{risk}</h4>
                    <p>Your recent assessments were analyzed automatically.</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            if recent_scores[0] < recent_scores[1] < recent_scores[2]:
                st.warning("⚠️ Eco Action Streak at Risk!")

                st.write(
                    "Your Eco Score has declined over your last three assessments. "
                    "Take action now to protect your sustainability streak."
                )

                st.info(
                    """
            ### 🌱 Suggested Recovery Actions

            - 🚶 Walk, cycle, or use public transport.
            - 💡 Reduce unnecessary electricity consumption.
            - 🥗 Choose more sustainable food options.
            - ✈️ Avoid non-essential flights whenever possible.
                        """
                )
            else:
                st.success("✅ Great! Your sustainability streak is stable.")

            import pandas as pd
            import plotly.express as px

            trend_df = pd.DataFrame({
                "Assessment": ["Oldest", "Previous", "Latest"],
                "Eco Score": [
                    recent_scores[2],
                    recent_scores[1],
                    recent_scores[0]
                ]
            })

            fig = px.line(
                trend_df,
                x="Assessment",
                y="Eco Score",
                markers=True,
                title="Eco Score Trend"
            )

            st.plotly_chart(fig, use_container_width=True)

            recovery = max(0, 100 - score_drop * 5)

            st.markdown("### 🔋 Recovery Readiness")

            st.progress(recovery / 100)

            st.caption(f"Recovery Score: {recovery}%")

            st.markdown("### 🌱 Personalized Recovery Plan")

            tips = []

            if score_drop >= 20:
                tips.extend([
                    "🚶 Walk or cycle instead of using a car.",
                    "💡 Reduce unnecessary electricity usage.",
                    "🥗 Eat more plant-based meals.",
                    "✈️ Avoid non-essential flights."
                ])
            elif score_drop >= 10:
                tips.extend([
                    "🚌 Use public transport whenever possible.",
                    "🔌 Switch off appliances when not in use.",
                    "♻️ Recycle household waste regularly."
                ])
            else:
                tips.append("🌿 Great work! Continue your sustainable habits.")

            for tip in tips:
                st.write(f"✅ {tip}")

            days = max(3, score_drop // 2)

            st.info(
                f"📅 Estimated time to recover your sustainability streak: **{days} days**"
            )

            st.markdown("### 📊 Streak Health Summary")

            status = "Healthy"
            message = "Keep maintaining your current sustainable habits."

            if score_drop >= 20:
                status = "Critical"
                message = "Immediate improvements are recommended to avoid losing your streak."
            elif score_drop >= 10:
                status = "Needs Attention"
                message = "Small lifestyle changes can quickly improve your progress."

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Streak Status", status)

            with col2:
                st.metric("Recent Score Drop", f"{score_drop} pts")

            st.caption(message)

                    

        if history:
            import pandas as pd
            import plotly.graph_objects as go
            df = pd.DataFrame(
                history,
                columns=[
                    "id",
                    "date",
                    "Created At",
                    "transport",
                    "distance",
                    "electricity",
                    "diet",
                    "flights",
                    "footprint",
                    "eco_score",
                ],
            )

            # -----------------------------
            # Eco Impact Streak Calendar
            # -----------------------------
            st.markdown("---")
            st.subheader("📅 Eco Impact Streak Calendar")

            calendar_df = df.copy()
            calendar_df["date"] = pd.to_datetime(calendar_df["date"]).dt.date

            today = pd.Timestamp.today().date()
            last_30_days = pd.date_range(end=today, periods=30)

            activity = []

            for day in last_30_days:
                if day.date() in calendar_df["date"].values:
                    activity.append("🟩")
                else:
                    activity.append("⬜")

            calendar_html = ""

            for i, box in enumerate(activity):
                calendar_html += f"<span style='font-size:20px'>{box}</span>"
                if (i + 1) % 10 == 0:
                    calendar_html += "<br>"

            st.markdown(calendar_html, unsafe_allow_html=True)

            active_days = len(calendar_df)

            st.metric(
                "🌱 Active Eco Days",
                active_days
            )

            st.caption("🟩 Assessment completed   ⬜ No assessment")



            # ---------------------------------------------------------------
            # Format the automatically generated creation timestamps before
            # displaying them in the Assessment History table.
            #
            # The database stores timestamps in the default SQLite format
            # (YYYY-MM-DD HH:MM:SS), which is suitable for storage and sorting
            # but not very user-friendly.
            #
            # This formatting step converts the raw timestamp into a more
            # readable format (e.g., "01 Aug 2026 03:45 PM"), improving the
            # overall user experience while preserving the original data in
            # the database.
            #
            # If a timestamp is missing or unavailable, a placeholder ("-")
            # is displayed instead of causing formatting errors.
            # ---------------------------------------------------------------
            df["Created At"] = df["Created At"].apply(format_timestamp)
            latest = history[0]
            stat1, stat2, stat3, stat4 = st.columns(4)

            with stat1:
                st.metric("Latest Footprint", f"{latest[7]:.0f} kg CO₂")

            with stat2:
                st.metric("Latest Score", f"{latest[8]}/100")

            if len(history) >= 2:
                previous_footprint = history[1][7]
                change = (
                    ((previous_footprint - latest[7]) / previous_footprint) * 100
                    if previous_footprint
                    else 0
                )
                with stat3:
                    st.metric(
                        "Change",
                        f"{abs(change):.1f}%",
                        delta=f"{change:.1f}% reduction",
                    )
            else:
                with stat3:
                    st.metric("Change", "N/A")

            with stat4:
                st.metric("Total Records", len(history))

            st.markdown("### 📉 Carbon Footprint Trend")
            trend_df = df[["date", "footprint"]].iloc[::-1].reset_index(drop=True)
            trend_df["date"] = pd.to_datetime(trend_df["date"])

            trend_fig = go.Figure()
            trend_fig.add_trace(
                go.Scatter(
                    x=trend_df["date"],
                    y=trend_df["footprint"],
                    mode="lines+markers",
                    name="Carbon Footprint",
                    line=dict(color="#4ade80", width=3),
                    marker=dict(size=8, color="#4ade80"),
                    fill="tozeroy",
                    fillcolor="rgba(74, 222, 128, 0.2)",
                    hovertemplate="<b>%{x|%b %d}</b><br>%{y:.0f} kg CO₂<extra></extra>",
                )
            )
            trend_fig.update_layout(
                height=320,
                margin=dict(l=40, r=20, t=20, b=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(55, 65, 81, 0.2)",
                showlegend=False,
                hovermode="x unified",
            )
            st.plotly_chart(trend_fig, use_container_width=True)

            st.markdown("### 📋 Assessment History")
            display_df = df[
                ["date", "transport", "electricity", "footprint", "eco_score"]
            ].copy()
            display_df.columns = [
                "📅 Date",
                "🚗 Transport",
                "⚡ Electricity (kWh)",
                "🌍 Footprint (kg CO₂)",
                "⭐ Eco Score",
            ]
            display_df = display_df.iloc[::-1].reset_index(drop=True)

            MAX_SEARCH = 100

            search_text = st.text_input(
                "🔍 Search by Date",
                placeholder="Enter date...",
                key="assessment_history_search",
                max_chars=MAX_SEARCH,
            )

            st.caption(f"🔎 {len(search_text)}/{MAX_SEARCH} characters")
            min_score, max_score = st.slider(
    "🌱 Eco Score Range",
    0,
    100,
    (0, 100),
    key="assessment_history_score_range",
    help="Adjust the minimum and maximum Eco Score to filter assessment history and display records within the selected range."
)

            if search_text:
                display_df = display_df[
                    display_df["📅 Date"]
                    .astype(str)
                    .str.contains(search_text, case=False, na=False)
                ]

            display_df = display_df[
                (display_df["⭐ Eco Score"] >= min_score)
                & (display_df["⭐ Eco Score"] <= max_score)
            ]

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            avg_footprint = df["footprint"].mean()
            avg_score = df["eco_score"].mean()
            min_footprint = df["footprint"].min()
            max_footprint = df["footprint"].max()

            stats_col1, stats_col2, stats_col3 = st.columns(3)
            stats_col1.metric("Average Footprint", f"{avg_footprint:.0f} kg CO₂")
            stats_col2.metric("Average Score", f"{avg_score:.0f}/100")
            stats_col3.metric(
                "Footprint Range",
                f"{min_footprint:.0f}–{max_footprint:.0f} kg CO₂",
            )
        else:
            st.info(
                "No assessment history yet. Complete an assessment to start tracking your progress."
            )

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
            MAX_APP = 50

            app_name = st.text_input(
                "Appliance Name",
                max_chars=MAX_APP,
                help="Enter your appliance name."
            )
            
            st.caption(f"🔌 {len(app_name)}/{MAX_APP} characters")
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
            del_id = st.selectbox(
    "Select appliance to remove",
    options=[(a['id'], a['name']) for a in appliances],
    format_func=lambda x: x[1],
    label_visibility="collapsed",
    help="Select the appliance you want to remove from your energy inventory."
)
        with del_cols[1]:
            if st.button(
                "🗑️ Remove",
                key="del_app",
                help="Remove the selected appliance."
            ):
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
        st.plotly_chart(fig_hr, use_container_width=True)

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
    
    # Header: Level, XP, Streak, Freeze Tokens
    total_xp = gf.get_total_xp(user_id)
    level = gf.calculate_level(total_xp)
    progress = gf.calculate_level_progress(total_xp)
    history = get_assessments(user_id)
    activities_dates = [row[1] for row in history] if history else []
    streak = gf.get_user_streak(user_id)
    token_balance = gf.get_freeze_token_balance(user_id)
    
    g_col1, g_col2, g_col3, g_col4 = st.columns(4)
    g_col1.metric("Current Level", f"Lvl {level}")
    g_col2.metric("Total XP", f"{total_xp} XP")
    g_col3.metric("Current Streak", f"{streak} Days 🔥")
    g_col4.metric("🧊 Freeze Tokens", f"{token_balance}")
    
    st.progress(progress, text=f"Progress to Level {level+1}")
    
    st.markdown("### 🧊 Green Streak Insurance")
    with st.expander("About Freeze Tokens"):
        st.write(
            "Freeze tokens protect your sustainability streak when you miss a day. "
            "Earn tokens by maintaining long streaks, then redeem them to keep your streak alive!"
        )
        st.markdown("**Milestone rewards:**")
        for threshold, tokens, _, label in gf.FREEZE_TOKEN_MILESTONES:
            st.write(f"- {label}: **{tokens}** token{'s' if tokens > 1 else ''}")
        total_earned = get_total_freeze_tokens_earned(user_id)
        st.write(f"*You've earned {total_earned} freeze token{'s' if total_earned != 1 else ''} total.*")
    
    if token_balance > 0:
        if st.button("🧊 Protect My Streak", type="primary", use_container_width=True):
            success, msg = gf.protect_streak_with_freeze(user_id)
            if success:
                st.success(msg)
            else:
                st.warning(msg)
            st.rerun()
    else:
        st.info("Keep your streak going to earn freeze tokens!")
    
    st.markdown("---")
    st.markdown("### 🏆 Weekly Challenges")
    
    user_challenges = gf.get_user_challenges(user_id)
    # Optimize primary evaluation loop by pre-computing challenge states
    challenge_states = {}
    for c in user_challenges:
        if c['status'] != 'expired':
            challenge_states[c['challenge_id']] = c
            
    for ch_id, ch_data in gf.CHALLENGES.items():
        with st.expander(f"🏆 {ch_data['title']} ({ch_data['xp']} XP) - {ch_data['category']}"):
            st.write(f"Target: {ch_data['target']} {ch_data['unit']}")
            if ch_id in challenge_states:
                state = challenge_states[ch_id]
                status = state['status']
                if status == 'completed':
                    st.success("🎉 Challenge Completed! Keep up the great work!")
                    st.balloons()
                    st.toast("🏆 Great job! Challenge completed successfully.")
                    st.info("🌍 Every completed challenge contributes to a greener lifestyle.")
                else:
                    current_prog = state['progress_value']
                    progress = min(current_prog / ch_data["target"], 1.0)
                    st.progress(progress)
                    percentage = int((current_prog / ch_data["target"]) * 100)
                    st.write(f"📊 Progress: {current_prog}/{ch_data['target']} ({percentage}%)")
                    
                    prog_val = st.number_input(f"Update Progress for {ch_id}", min_value=0.0, step=1.0, key=f"prog_{ch_id}")
                    if st.button("Update", key=f"btn_prog_{ch_id}"):
                        gf.update_challenge_progress(...)
                        gf.validate_challenge_progress(...)
                        st.toast("📈 Progress updated successfully!")
                        st.rerun()
            else:
                if st.button("Enroll", key=f"enroll_{ch_id}"):
                    gf.enroll_challenge(user_id, ch_id)
                    st.success("🎯 You have joined the challenge!")
                    st.toast("🌱 Best of luck! Complete it to earn rewards.")
                    st.toast("🌱 Successfully enrolled in the challenge!")
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
            freq = st.selectbox(
    "Trip Frequency",
    [
        "One-time",
        "Weekly Commute (10 trips/week)",
        "Daily (14 trips/week)"
    ],
    help="Choose how often you make this trip to estimate its long-term carbon impact."
)
            calc_btn = st.form_submit_button("Compare Emissions")
            
        if calc_btn:
            try:
                comparisons = compare_transit_modes(dist_val, pass_val)
                st.write(f"**Estimated Emissions for a {dist_val}km trip:**")
                
                # Chart
                import pandas as pd
                import plotly.express as px
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
                st.plotly_chart(fig, use_container_width=True)
                
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
            import pandas as pd
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

with tab6:
    import plotly.graph_objects as go

    st.markdown("<div class='section-header'>🔮 Future Self Sustainability Report</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>See the long-term consequences of today's habits — projected 1, 5, and 10 years into the future.</div>", unsafe_allow_html=True)

    report = generate_future_self_report(user_id)

    if report is None:
        st.markdown("""
        <div style='text-align:center; padding:60px 24px; border:1px dashed rgba(134,239,172,0.3); border-radius:16px; background:rgba(15,23,42,0.5);'>
            <div style='font-size:64px; margin-bottom:16px;'>🔮</div>
            <div style='font-size:22px; font-weight:700; color:#e5e7eb; margin-bottom:12px;'>No Assessment History Yet</div>
            <div style='font-size:15px; color:#94a3b8; max-width:500px; margin:0 auto; line-height:1.8;'>
                Complete your first carbon footprint assessment in the
                <b>🌍 Carbon Footprint</b> tab to unlock your Future Self report.
                <br><br>
                Once you have at least one assessment recorded, this dashboard will
                project your environmental impact 1, 5, and 10 years from now.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        scenario_labels = {1: "1 Year", 5: "5 Years", 10: "10 Years"}

        metrics_cols = st.columns(4)
        metrics_cols[0].metric("Current Footprint", f"{report.current_footprint:.0f} kg")
        metrics_cols[1].metric("Current Eco Score", f"{report.current_eco_score}/100")
        metrics_cols[2].metric("Assessments Logged", str(report.num_assessments))
        trend_str = f"{abs(report.trend_slope):.1f} kg/assessment"
        if report.trend_slope < 0:
            trend_str = f"↓ {trend_str}"
        elif report.trend_slope > 0:
            trend_str = f"↑ {trend_str}"
        else:
            trend_str = "→ Stable"
        metrics_cols[3].metric("Trend", trend_str)

        st.markdown("---")

        st.markdown("<div class='section-header'>📊 Impact Projections</div>", unsafe_allow_html=True)

        scenario_rows = []
        for year in (1, 5, 10):
            s = report.scenarios[year]
            scenario_rows.append({
                "Horizon": scenario_labels[year],
                "Annual Footprint (kg)": f"{s.annual_footprint:.0f}",
                "Cumulative (kg)": f"{s.cumulative_emissions:.0f}",
                "Eco Score": f"{s.eco_score}/100",
            })

        st.dataframe(
            pd.DataFrame(scenario_rows),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")

        st.markdown("<div class='section-header'>📈 Historical & Projected Trend</div>", unsafe_allow_html=True)

        timeline_df = build_projection_timeline(report)

        timeline_fig = go.Figure()

        hist = timeline_df[timeline_df["type"] == "Historical"]
        proj = timeline_df[timeline_df["type"] == "Projected"]

        if not hist.empty:
            timeline_fig.add_trace(go.Scatter(
                x=hist["label"],
                y=hist["value"],
                mode="lines+markers",
                name="Historical",
                line=dict(color="#4ade80", width=3),
                marker=dict(size=8, color="#4ade80"),
                hovertemplate="<b>%{x}</b><br>%{y:.0f} kg CO₂<extra></extra>",
            ))

        if not proj.empty:
            timeline_fig.add_trace(go.Scatter(
                x=proj["label"],
                y=proj["value"],
                mode="markers+lines",
                name="Projected",
                line=dict(color="#fbbf24", width=3, dash="dash"),
                marker=dict(size=12, color="#fbbf24", symbol="diamond"),
                hovertemplate="<b>%{x}</b><br>%{y:.0f} kg CO₂<extra></extra>",
            ))

        timeline_fig.update_layout(
            height=380,
            margin=dict(l=40, r=20, t=20, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(55, 65, 81, 0.2)",
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color="#e5e7eb"),
            ),
            xaxis=dict(showgrid=False, zeroline=False, color="#94a3b8"),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(74, 222, 128, 0.1)",
                zeroline=False,
                color="#94a3b8",
                title=dict(text="kg CO₂ / year"),
            ),
        )

        st.plotly_chart(timeline_fig, use_container_width=True, config={"displayModeBar": False})

        st.markdown("---")

        st.markdown("<div class='section-header'>📊 Contributors Over Time</div>", unsafe_allow_html=True)

        cat_fig = go.Figure()
        categories = list(report.current_contributors.keys())
        colors = {"Transport": "#4ade80", "Electricity": "#60a5fa", "Diet": "#fbbf24", "Flights": "#f87171"}

        x_labels = ["Current"] + [scenario_labels[y] for y in (1, 5, 10)]

        for cat in categories:
            values = [report.current_contributors.get(cat, 0)]
            for year in (1, 5, 10):
                values.append(report.scenarios[year].contributors.get(cat, 0))
            cat_fig.add_trace(go.Bar(
                name=cat,
                x=x_labels,
                y=values,
                marker_color=colors.get(cat, "#94a3b8"),
                hovertemplate="<b>%{x}</b><br>%{y:.0f} kg CO₂<extra></extra>",
            ))

        cat_fig.update_layout(
            barmode="group",
            height=380,
            margin=dict(l=40, r=20, t=20, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(55, 65, 81, 0.2)",
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color="#e5e7eb"),
            ),
            xaxis=dict(showgrid=False, zeroline=False, color="#94a3b8"),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(74, 222, 128, 0.1)",
                zeroline=False,
                color="#94a3b8",
                title=dict(text="kg CO₂ / year"),
            ),
        )

        st.plotly_chart(cat_fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("""
<style>
#scrollTopBtn {
    display: none;
    position: fixed;
    bottom: 25px;
    right: 25px;
    z-index: 9999;
    border: none;
    outline: none;
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: white;
    cursor: pointer;
    width: 55px;
    height: 55px;
    border-radius: 50%;
    font-size: 24px;
    font-weight: bold;
    box-shadow: 0 6px 18px rgba(0,0,0,0.3);
    transition: all 0.3s ease;
}

#scrollTopBtn:hover {
    transform: translateY(-4px) scale(1.08);
    box-shadow: 0 10px 24px rgba(0,0,0,0.4);
    background: linear-gradient(135deg, #16a34a, #15803d);
}
</style>

<button onclick="scrollToTop()" id="scrollTopBtn" title="Go to top">
⬆
</button>

<script>
let scrollButton = document.getElementById("scrollTopBtn");

window.onscroll = function () {
    if (
        document.body.scrollTop > 300 ||
        document.documentElement.scrollTop > 300
    ) {
        scrollButton.style.display = "block";
    } else {
        scrollButton.style.display = "none";
    }
};

function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}
</script>
""", unsafe_allow_html=True)

        st.markdown("""
<style>
#scrollTopBtn {
    display: none;
    position: fixed;
    bottom: 25px;
    right: 25px;
    z-index: 9999;
    border: none;
    outline: none;
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: white;
    cursor: pointer;
    width: 55px;
    height: 55px;
    border-radius: 50%;
    font-size: 24px;
    font-weight: bold;
    box-shadow: 0 6px 18px rgba(0,0,0,0.3);
    transition: all 0.3s ease;
}

#scrollTopBtn:hover {
    transform: translateY(-4px) scale(1.08);
    box-shadow: 0 10px 24px rgba(0,0,0,0.4);
    background: linear-gradient(135deg, #16a34a, #15803d);
}
</style>

<button onclick="scrollToTop()" id="scrollTopBtn" title="Go to top">
⬆
</button>

<script>
let scrollButton = document.getElementById("scrollTopBtn");

window.onscroll = function () {
    if (
        document.body.scrollTop > 300 ||
        document.documentElement.scrollTop > 300
    ) {
        scrollButton.style.display = "block";
    } else {
        scrollButton.style.display = "none";
    }
};

function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}
</script>
""", unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("<div class='section-header'>🌍 What This Means</div>", unsafe_allow_html=True)

        ten_yr = report.scenarios[10]
        avg_person_annual = 4700
        trees_per_kg = 0.0005
        offset_trees_10yr = int(ten_yr.cumulative_emissions * trees_per_kg)

        col_n1, col_n2 = st.columns(2)

        with col_n1:
            st.markdown(f"""
            <div class='card-highlight' style='padding:24px;'>
                <div style='font-size:18px; font-weight:700; color:#4ade80; margin-bottom:12px;'>📈 If Habits Continue</div>
                <div style='color:#374151; font-size:15px; line-height:1.9;'>
                    In <b>10 years</b>, your annual carbon footprint could be
                    <b style='color:#f87171;'>{ten_yr.annual_footprint:.0f} kg CO₂</b>
                    — that's a cumulative total of
                    <b style='color:#fbbf24;'>{ten_yr.cumulative_emissions:,.0f} kg</b>
                    over the decade.
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_n2:
            st.markdown(f"""
            <div class='card-highlight' style='padding:24px;'>
                <div style='font-size:18px; font-weight:700; color:#4ade80; margin-bottom:12px;'>🌱 The Cost of Inaction</div>
                <div style='color:#374151; font-size:15px; line-height:1.9;'>
                    To offset your 10-year projected emissions, you would need to plant
                    <b style='color:#4ade80;'>~{offset_trees_10yr:,} trees</b>
                    that each absorb ~48 lbs of CO₂ per year.
                    <br><br>
                    Your current footprint is
                    <b>{'above' if report.current_footprint > avg_person_annual else 'below'}</b>
                    the global average of {avg_person_annual:,} kg CO₂/year.
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("<div class='section-header'>📋 Scenario Details</div>", unsafe_allow_html=True)

        for year in (1, 5, 10):
            s = report.scenarios[year]
            direction = "increasing" if s.annual_footprint > report.current_footprint else "decreasing" if s.annual_footprint < report.current_footprint else "stable"
            emoji = "📈" if direction == "increasing" else "📉" if direction == "decreasing" else "➡️"
            score_change = s.eco_score - report.current_eco_score
            score_dir = "improving" if score_change > 0 else "declining" if score_change < 0 else "stable"
            score_emoji = "✅" if score_change > 0 else "⚠️" if score_change < 0 else "➡️"

            top_category = max(s.contributors, key=s.contributors.get)
            best_category = min(s.contributors, key=s.contributors.get)

            border_color = "#f87171" if direction == "increasing" else "#4ade80"
            st.markdown(f"""
            <div class='card' style='border-left: 4px solid {border_color};'>
                <div style='display:flex; align-items:center; gap:16px;'>
                    <div style='font-size:40px;'>{emoji}</div>
                    <div style='flex:1;'>
                        <div style='font-size:18px; font-weight:700; color:#4ade80;'>{scenario_labels[year]} Projection</div>
                        <div style='font-size:14px; color:#374151; margin-top:6px; line-height:1.7;'>
                            Annual footprint of <b>{s.annual_footprint:.0f} kg CO₂</b> | 
                            Eco Score <b>{s.eco_score}/100</b> ({score_emoji} {score_dir})
                            <br>
                            Biggest contributor: <b>{top_category}</b> | 
                            Best category: <b>{best_category}</b>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("<div class='section-header'>💡 Change Your Trajectory</div>", unsafe_allow_html=True)

        st.markdown("""
        <div class='card-highlight' style='padding:24px;'>
            <div style='font-size:15px; color:#374151; line-height:1.9;'>
                Your Future Self report is a <b>simulation based on your current habits</b>.
                Every small change you make today can bend the curve.
                Check the <b>💡 Personalized Recommendations</b> section in the
                Carbon Footprint tab for actionable steps to reduce your impact.
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
