import json
import os
import streamlit as st

_PREF_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".theme_preference.json",
)

VALID_THEMES = ["light", "dark"]
DEFAULT_THEME = "dark"

LIGHT_CSS = """
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

    body,
    [data-testid="stAppViewContainer"] {
        color: var(--ink);
        background:
            linear-gradient(180deg, rgba(185, 215, 244, 0.74) 0%, rgba(244, 248, 240, 0.95) 48%, #f7faf3 100%),
            radial-gradient(circle at 14% 12%, rgba(255, 255, 255, 0.86), transparent 30%),
            linear-gradient(135deg, #d7ebff 0%, #f4f8e8 54%, #eaf5df 100%);
    }

    [data-testid="stHeader"] {
        background: transparent;
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

    .input-section,
    .card,
    .card-highlight,
    .metric-card {
        background: linear-gradient(145deg, var(--paper-strong), rgba(255, 255, 255, 0.64));
        border-color: var(--line);
        box-shadow: 0 18px 50px rgba(57, 86, 47, 0.12);
    }

    .card-highlight {
        background:
            linear-gradient(145deg, rgba(255, 255, 255, 0.94), rgba(232, 244, 216, 0.82)),
            linear-gradient(135deg, rgba(120, 169, 69, 0.12), transparent);
    }

    .metric-card::before,
    .card-highlight::before {
        background: linear-gradient(90deg, #030504, var(--leaf), #b6d274);
    }

    .progress-bar {
        background: rgba(8, 11, 10, 0.08);
    }

    .progress-fill {
        background: linear-gradient(90deg, #030504, var(--moss), var(--leaf));
    }

    .stTextInput > div > div > input,
    .stNumberInput input,
    .stSelectbox [data-baseweb="select"],
    .stTextArea textarea {
        background: rgba(255, 255, 255, 0.88) !important;
        border-color: rgba(8, 11, 10, 0.12) !important;
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
        background: #030504 !important;
        color: #fff !important;
        box-shadow: 0 16px 34px rgba(0, 0, 0, 0.2) !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        background: #101713 !important;
        box-shadow: 0 22px 44px rgba(0, 0, 0, 0.26) !important;
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
"""

DARK_CSS = """
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

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        background: rgba(3, 7, 18, 0.84);
        border-right: 1px solid var(--line);
        box-shadow: 18px 0 48px rgba(0, 0, 0, 0.26);
    }

    [data-testid="stSidebar"] * {
        color: var(--ink);
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
    [data-testid="stDataFrame"] [role="button"],
    [data-testid="stElementToolbar"] button {
        background: #0f172a !important;
        color: #f8fafc !important;
        border: 1px solid rgba(148, 163, 184, 0.28) !important;
    }

    [data-testid="stDataFrame"] button:hover,
    [data-testid="stDataFrame"] [role="button"]:hover,
    [data-testid="stElementToolbar"] button:hover {
        background: #1e293b !important;
        border-color: rgba(74, 222, 128, 0.5) !important;
    }

    [data-testid="stDataFrame"] svg,
    [data-testid="stElementToolbar"] svg {
        color: #f8fafc !important;
        fill: #f8fafc !important;
    }

    /* Dark mode tooltips, popovers, and toolbar menus */
    div[data-baseweb="popover"],
    div[role="tooltip"],
    div[data-baseweb="tooltip"],
    [data-testid="stTooltipContent"] {
        background-color: #0f172a !important;
        color: #ffffff !important;
        border: 1px solid rgba(134, 239, 172, 0.3) !important;
        border-radius: 12px !important;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.45) !important;
    }

    div[data-baseweb="popover"] *,
    div[role="tooltip"] *,
    div[data-baseweb="tooltip"] *,
    [data-testid="stTooltipContent"] * {
        color: #ffffff !important;
    }

    div[data-baseweb="popover"] li:hover,
    div[data-baseweb="popover"] [role="option"]:hover,
    div[data-baseweb="popover"] [role="menuitem"]:hover {
        background-color: rgba(34, 197, 94, 0.2) !important;
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
"""

THEMES = {
    "light": {"name": "Light", "icon": "☀️", "css": LIGHT_CSS},
    "dark": {"name": "Dark", "icon": "🌙", "css": DARK_CSS},
}


def _save_theme(name):
    try:
        with open(_PREF_PATH, "w") as f:
            json.dump({"theme": name}, f)
    except (OSError, IOError):
        pass


def _load_theme():
    try:
        with open(_PREF_PATH, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            name = data.get("theme", "")
            if name in VALID_THEMES:
                return name
    except (FileNotFoundError, json.JSONDecodeError, OSError, KeyError, AttributeError):
        pass
    return DEFAULT_THEME


from session_state_utils import ensure_session_state


def _ensure_theme_state():
    if "theme" not in st.session_state:
        st.session_state.theme = _load_theme()


def render_theme_selector():
    _ensure_theme_state()

    current = st.session_state.theme
    options = [f"{THEMES[k]['icon']} {THEMES[k]['name']}" for k in VALID_THEMES]
    labels_by_name = {f"{THEMES[k]['icon']} {THEMES[k]['name']}": k for k in VALID_THEMES}
    current_label = f"{THEMES[current]['icon']} {THEMES[current]['name']}"

    selected = st.sidebar.selectbox(
        "Theme",
        options,
        index=options.index(current_label) if current_label in options else 0,
        key="_theme_selector",
    )

    chosen = labels_by_name.get(selected, DEFAULT_THEME)
    if chosen != st.session_state.theme:
        st.session_state.theme = chosen
        _save_theme(chosen)
        st.rerun()


def apply_theme():
    _ensure_theme_state()

    theme_name = st.session_state.get("theme", DEFAULT_THEME)
    if theme_name not in THEMES:
        # Invalid or missing config: fall back to the default theme.
        theme_name = DEFAULT_THEME
        st.session_state.theme = DEFAULT_THEME

    css = THEMES[theme_name]["css"]

    try:
        _inject_theme_css(css)
    except Exception:
        # Graceful fallback: if the configured theme is invalid or cannot be
        # rendered, fall back to Streamlit's default theme instead of crashing
        # the app on startup.
        st.session_state.theme = DEFAULT_THEME


def _inject_theme_css(css):
    st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    * {{
        box-sizing: border-box;
    }}

    html {{
        scroll-behavior: smooth;
    }}

    .block-container {{
        max-width: 1280px;
        padding: 24px 32px 56px;
    }}

    .title {{
        margin: 8px 0 12px;
        color: var(--ink);
        font-size: clamp(46px, 6vw, 82px);
        line-height: 1;
        font-weight: 800;
        letter-spacing: 0;
        text-align: center;
        animation: fadeUp 700ms ease both;
    }}

    .subtitle {{
        max-width: 720px;
        margin: 0 auto 30px;
        color: var(--muted);
        font-size: 19px;
        line-height: 1.6;
        font-weight: 500;
        text-align: center;
        animation: fadeUp 800ms 80ms ease both;
    }}

    .section-header {{
        margin: 38px 0 18px;
        color: var(--ink);
        font-size: clamp(28px, 3vw, 42px);
        line-height: 1.08;
        font-weight: 800;
        letter-spacing: 0;
        animation: fadeUp 650ms ease both;
    }}

    .section-header::after {{
        content: '';
        display: block;
        width: 88px;
        height: 4px;
        margin-top: 14px;
        border-radius: 999px;
        background: linear-gradient(90deg, #030504, var(--leaf), rgba(120, 169, 69, 0));
    }}

    .input-section,
    .card,
    .card-highlight,
    .metric-card {{
        border: 1px solid var(--line);
        border-radius: var(--radius);
        box-shadow: 0 18px 50px rgba(57, 86, 47, 0.12);
        backdrop-filter: blur(18px);
        position: relative;
        overflow: hidden;
        animation: fadeUp 700ms ease both;
        transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
    }}

    .input-section {{
        padding: 34px;
        margin-bottom: 24px;
    }}

    .card,
    .card-highlight,
    .metric-card {{
        padding: 26px;
        margin-bottom: 16px;
    }}

    .metric-card::before,
    .card-highlight::before {{
        content: '';
        position: absolute;
        inset: 0 0 auto 0;
        height: 5px;
    }}

    .metric-card:hover,
    .card:hover,
    .card-highlight:hover {{
        transform: translateY(-6px);
        border-color: rgba(95, 143, 54, 0.28);
        box-shadow: 0 26px 64px rgba(57, 86, 47, 0.17);
    }}

    .badge {{
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
    }}

    .badge-champion {{
        background: linear-gradient(135deg, #f4c760, #d8831e);
        color: #2c1804;
    }}

    .badge-guardian {{
        background: linear-gradient(135deg, #acd66f, #5f8f36);
        color: #0d1c0f;
    }}

    .badge-learner {{
        background: linear-gradient(135deg, #b9d7f4, #6aa0cf);
        color: #071927;
    }}

    .badge-high {{
        background: linear-gradient(135deg, #ff8e70, #d84b35);
        color: #2e0904;
    }}

    .progress-bar {{
        width: 100%;
        height: 12px;
        margin-top: 12px;
        border-radius: 999px;
        overflow: hidden;
    }}

    .progress-fill {{
        height: 100%;
        border-radius: inherit;
        box-shadow: 0 0 20px rgba(95, 143, 54, 0.34);
        transition: width 600ms ease;
    }}

    hr {{
        height: 1px;
        margin: 32px 0;
        border: none;
        background: linear-gradient(90deg, transparent, rgba(8, 11, 10, 0.16), transparent);
    }}

    .stTextInput > div > div > input,
    .stNumberInput input,
    .stSelectbox [data-baseweb="select"],
    .stTextArea textarea {{
        min-height: 48px;
        border: 1px solid rgba(8, 11, 10, 0.12) !important;
        border-radius: 12px !important;
    }}

    .stButton > button,
    .stDownloadButton > button,
    [data-testid="stFormSubmitButton"] > button {{
        min-height: 52px;
        padding: 0 28px !important;
        border: none !important;
        border-radius: 12px !important;
        font-size: 15px !important;
        font-weight: 800 !important;
        letter-spacing: 0 !important;
        transition: transform 180ms ease, box-shadow 180ms ease, background 180ms ease !important;
    }}

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {{
        transform: translateY(-2px);
    }}

    .stInfo,
    .stWarning,
    .stSuccess,
    .stError {{
        border-radius: 14px !important;
        border: 1px solid var(--line) !important;
        box-shadow: 0 12px 30px rgba(57, 86, 47, 0.08);
    }}

    /* Hide spreadsheet editor options: Statistics and Format from dataframe toolbars and popovers */
    [data-testid="stDataFrameToolBar"] button[aria-label*="Statistics"],
    [data-testid="stDataFrameToolBar"] button[aria-label*="Format"],
    [data-testid="stElementToolbar"] button[aria-label*="Statistics"],
    [data-testid="stElementToolbar"] button[aria-label*="Format"],
    div[data-baseweb="popover"] [role="menuitem"]:has(*:contains("Statistics")),
    div[data-baseweb="popover"] [role="menuitem"]:has(*:contains("Format")),
    div[data-baseweb="popover"] li:has(*:contains("Statistics")),
    div[data-baseweb="popover"] li:has(*:contains("Format")),
    div[data-baseweb="popover"] button:has(*:contains("Statistics")),
    div[data-baseweb="popover"] button:has(*:contains("Format")) {{
        display: none !important;
    }}

    @keyframes fadeUp {{
        from {{
            opacity: 0;
            transform: translateY(18px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    @media (max-width: 760px) {{
        .block-container {{
            padding: 16px 14px 42px;
        }}

        /* Mobile-friendly typography */
        .title {{
            font-size: clamp(34px, 10vw, 52px);
            line-height: 1.05;
            margin-bottom: 10px;
        }}

        .subtitle {{
            font-size: 16px;
            line-height: 1.5;
            padding: 0 8px;
            margin-bottom: 22px;
        }}

        .section-header {{
            font-size: clamp(24px, 7vw, 34px);
            margin-top: 28px;
        }}

        /* Prevent cards from feeling cramped */
        .input-section,
        .card,
        .card-highlight,
        .metric-card {{
            padding: 18px;
            margin-bottom: 14px;
        }}

        /* Make buttons easier to tap on mobile */
        .stButton > button,
        .stDownloadButton > button,
        [data-testid="stFormSubmitButton"] > button {{
            width: 100%;
            min-height: 50px;
            font-size: 14px !important;
        }}

        /* Improve form controls on smaller screens */
        .stTextInput > div > div > input,
        .stNumberInput input,
        .stSelectbox [data-baseweb="select"],
        .stTextArea textarea {{
            min-height: 46px;
            font-size: 15px;
        }}

        /* Keep tables usable without breaking the page */
        .history-table-wrap {{
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }}

        .history-table {{
            min-width: 620px;
        }}

        /* Reduce hover movement on touch devices */
        .metric-card:hover,
        .card:hover,
        .card-highlight:hover {{
            transform: none;
        }}

        .stExpander {{
    border-radius: 14px;
    border: 1px solid rgba(74,222,128,.25);
    transition: all .3s ease;
}}

.stExpander:hover {{
    transform: translateY(-2px);
}}

        .input-section,
        .card,
        .card-highlight,
        .metric-card {{
            padding: 22px;
        }}
    }}

        /* Breadcrumb navigation */
    .breadcrumb {{
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        margin: 8px 0 24px;
        padding: 12px 16px;
        border: 1px solid var(--line);
        border-radius: 12px;
        background: var(--paper);
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.08);
        font-size: 14px;
        font-weight: 600;
    }}

    .breadcrumb-item {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        color: var(--muted);
        transition: color 180ms ease, transform 180ms ease;
    }}

    .breadcrumb-item:hover {{
        color: var(--leaf);
        transform: translateY(-1px);
    }}

    .breadcrumb-item.active {{
        color: var(--ink);
        font-weight: 800;
    }}

    .breadcrumb-separator {{
        color: var(--muted);
        opacity: 0.7;
        user-select: none;
    }}

    @media (max-width: 760px) {{
        .breadcrumb {{
            gap: 5px;
            margin-bottom: 18px;
            padding: 10px 12px;
            font-size: 13px;
        }}
    }}
{css}
</style>

""", unsafe_allow_html=True)


def render_empty_state(icon, title, message):
    st.markdown(
        f"""
        <div style='text-align:center; padding:48px 24px; border:1px dashed rgba(134,239,172,0.3); border-radius:16px; background:rgba(15,23,42,0.5);'>
            <div style='font-size:48px; margin-bottom:12px;'>{icon}</div>
            <div style='font-size:18px; font-weight:600; color:#e5e7eb; margin-bottom:8px;'>{title}</div>
            <div style='font-size:14px; color:#94a3b8;'>{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_info_card(message):
    st.markdown(
        f"""
        <div style='padding:18px 24px; border-radius:14px; background:linear-gradient(135deg, rgba(34,197,94,0.15), rgba(74,222,128,0.08)); border:1px solid rgba(74,222,128,0.3); margin-top:8px;'>
            <span style='font-size:18px;'>💡</span>
            <span style='color:#e5e7eb; font-size:15px;'>{message}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_appliance_table(table_rows):
    st.markdown(
        f"""
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
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Unit and currency preference selector
# ---------------------------------------------------------------------------

def render_unit_selector(user_id=None):
    """
    Sidebar selector for unit system and currency.

    Lives alongside render_theme_selector() so the preference is reachable from
    every page — it has to be global, or the PDF report and the dashboard end
    up disagreeing with the input forms.

    Returns the active preference dict so the caller can format with it
    immediately without a second lookup.
    """
    from units import (
        DEFAULT_PREFERENCE,
        SYSTEM_LABELS,
        UNIT_SYSTEMS,
        get_currency,
        list_currencies,
        make_preference,
    )

    if "unit_preference" not in st.session_state:
        loaded = DEFAULT_PREFERENCE
        if user_id is not None:
            try:
                from database import get_unit_preference
                loaded = get_unit_preference(user_id)
            except Exception:
                # A preference lookup must never stop a page from rendering.
                loaded = DEFAULT_PREFERENCE
        st.session_state.unit_preference = loaded

    current = st.session_state.unit_preference

    system_labels = [SYSTEM_LABELS[key] for key in UNIT_SYSTEMS]
    system_by_label = {SYSTEM_LABELS[key]: key for key in UNIT_SYSTEMS}
    current_system_label = SYSTEM_LABELS[current["system"]]

    selected_system_label = st.sidebar.selectbox(
        "Units",
        system_labels,
        index=system_labels.index(current_system_label),
        key="_unit_system_selector",
    )

    currency_codes = list_currencies()
    currency_labels = [
        f"{get_currency(code)['symbol']} {code}" for code in currency_codes
    ]
    currency_by_label = dict(zip(currency_labels, currency_codes))
    current_currency_label = (
        f"{get_currency(current['currency'])['symbol']} {current['currency']}"
    )

    selected_currency_label = st.sidebar.selectbox(
        "Currency",
        currency_labels,
        index=currency_labels.index(current_currency_label),
        key="_currency_selector",
    )

    chosen = make_preference(
        system_by_label.get(selected_system_label, current["system"]),
        currency_by_label.get(selected_currency_label, current["currency"]),
    )

    if chosen != current:
        st.session_state.unit_preference = chosen
        if user_id is not None:
            try:
                from database import save_unit_preference
                save_unit_preference(user_id, chosen["system"], chosen["currency"])
            except Exception:
                pass
        st.rerun()

    return chosen


def get_active_unit_preference(user_id=None):
    """
    The preference a page should format with, without rendering a selector.

    Pages that only display values call this; the sidebar selector is rendered
    once per page by whichever component owns the sidebar.
    """
    from units import DEFAULT_PREFERENCE

    if "unit_preference" in st.session_state:
        return st.session_state.unit_preference

    if user_id is not None:
        try:
            from database import get_unit_preference
            preference = get_unit_preference(user_id)
            st.session_state.unit_preference = preference
            return preference
        except Exception:
            pass

    return DEFAULT_PREFERENCE
