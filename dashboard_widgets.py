from collections import OrderedDict
from typing import Iterable, Mapping, List, Optional
import streamlit as st
from database import (
    get_assessments,
    get_dashboard_widget_preferences,
    save_dashboard_widget_preferences,
)


WIDGETS = OrderedDict([
    ("summary", "Latest impact summary"),
    ("eco_score", "Eco score"),
    ("trend", "Footprint trend"),
    ("activity", "Latest activity"),
    ("quick_tips", "Quick eco tips"),
])

WIDGETS = OrderedDict(
    [
        ("summary", "🌍 Latest impact summary"),
        ("eco_score", "🏆 Eco score"),
        ("trend", "📈 Footprint trend"),
        ("activity", "🧭 Latest activity"),
        ("quick_tips", "💡 Quick eco tips"),
        ("insights", "🔎 Personal insights"),
    ]
)

DEFAULT_WIDGETS = tuple(WIDGETS.keys())
SESSION_KEY = "dashboard_widget_preferences"

def normalize_widget_preferences(widget_ids: Iterable[str] | None) -> List[str]:
    """Normalize widget preferences to a valid list of widget IDs"""
    if widget_ids is None:
        return list(DEFAULT_WIDGETS)

    
    valid_widgets = list(WIDGETS.keys())
    normalized = []
    
    for widget_id in widget_ids:
        if widget_id in valid_widgets and widget_id not in normalized:
            normalized.append(widget_id)
    
    # Ensure all default widgets are present
    for widget in DEFAULT_WIDGETS:
        if widget not in normalized:
            normalized.append(widget)
    
    return normalized

def get_user_widgets(user_id: str) -> List[str]:
    """Get user's widget preferences from database or session"""
    # Check session first
    if SESSION_KEY in st.session_state:
        return st.session_state[SESSION_KEY]
    
    # Get from database
    preferences = get_dashboard_widget_preferences(user_id)
    if preferences:
        normalized = normalize_widget_preferences(preferences)
        st.session_state[SESSION_KEY] = normalized
        return normalized
    
    # Return defaults
    default = list(DEFAULT_WIDGETS)
    st.session_state[SESSION_KEY] = default
    return default

def save_user_widgets(user_id: str, widget_ids: List[str]) -> bool:
    """Save user's widget preferences"""
    normalized = normalize_widget_preferences(widget_ids)
    result = save_dashboard_widget_preferences(user_id, normalized)
    if result:
        st.session_state[SESSION_KEY] = normalized
    return result

def render_widget(widget_id: str, user_id: str = None):
    """Render a single widget based on its ID"""
    if widget_id == "summary":
        st.subheader("📊 Latest Impact Summary")
        assessments = get_assessments(user_id)
        if assessments:
            latest = assessments[-1] if assessments else None

    return normalize_widget_preferences(saved)


def render_widget_customizer(user_id: int) -> list[str]:
    """Render the sidebar widget picker and persist explicit saves."""
    if SESSION_KEY not in st.session_state:
        st.session_state[SESSION_KEY] = get_user_widgets(user_id)

    with st.sidebar.expander("🧩 Dashboard widgets", expanded=False):
        st.caption("Choose which cards appear on your personal dashboard.")
        with st.form("dashboard_widget_preferences_form"):
            selected_labels = st.multiselect(
                "Visible widgets",
                options=list(WIDGETS.values()),
                default=[
                    WIDGETS[widget_id]
                    for widget_id in st.session_state[SESSION_KEY]
                    if widget_id in WIDGETS
                ],
                help="Your selection is restored the next time you sign in.",
            )
            save_clicked = st.form_submit_button(
                "Save dashboard",
                use_container_width=True,
            )

        if save_clicked:
            label_to_id = {label: widget_id for widget_id, label in WIDGETS.items()}
            selected_ids = normalize_widget_preferences(
                label_to_id[label] for label in selected_labels
            )
            if save_dashboard_widget_preferences(user_id, selected_ids):
                st.session_state[SESSION_KEY] = selected_ids
                st.success("Dashboard preferences saved.")
                st.rerun()
            else:
                st.error("Could not save dashboard preferences. Please try again.")

        if not st.session_state[SESSION_KEY]:
            st.info("No widgets selected. Use the picker above to add dashboard cards.")

    return list(st.session_state[SESSION_KEY])


@st.cache_data(show_spinner=False)
def _assessment_rows_to_frame(rows: tuple) -> pd.DataFrame:
    import pandas as pd
    columns = [
        "id",
        "date",
        "transport",
        "distance",
        "electricity",
        "diet",
        "flights",
        "footprint",
        "eco_score",
    ]
    frame = pd.DataFrame(rows, columns=columns)
    if not frame.empty:
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
        frame["footprint"] = pd.to_numeric(frame["footprint"], errors="coerce")
        frame["eco_score"] = pd.to_numeric(frame["eco_score"], errors="coerce")
    return frame


def render_customizable_dashboard(user_id: int, selected_widgets: Iterable[str]) -> None:
    """Render the saved dashboard layout using the user's assessment history."""
    selected = normalize_widget_preferences(selected_widgets)
    if not selected:
        return

    # Breadcrumb navigation for the dashboard section
    st.markdown(
        """
        <nav class="breadcrumb" aria-label="Breadcrumb">
            <span class="breadcrumb-item">🏠 Home</span>
            <span class="breadcrumb-separator">›</span>
            <span class="breadcrumb-item active">📊 Dashboard</span>
        </nav>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='section-header'>📊 My Dashboard</div>", unsafe_allow_html=True)
    st.caption("Personalized widgets based on your saved dashboard preferences.")

    frame = _assessment_rows_to_frame(tuple(get_assessments(user_id)))
    latest: Mapping[str, object] | None = None
    if not frame.empty:
        latest = frame.iloc[0].to_dict()

    if "summary" in selected:
        with st.container(border=True):
            st.subheader("🌍 Latest impact summary")

            if latest:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Carbon Footprint", f"{latest.get('carbon_footprint', 0):.2f} kg")
                with col2:
                    st.metric("Energy Used", f"{latest.get('energy_used', 0):.1f} kWh")
                with col3:
                    st.metric("Waste Generated", f"{latest.get('waste_generated', 0):.1f} kg")
            else:
                st.info("No assessments found. Start tracking your impact!")
    
    elif widget_id == "eco_score":
        st.subheader("🌱 Eco Score")
        assessments = get_assessments(user_id)
        if assessments:
            latest = assessments[-1] if assessments else None
            if latest:
                score = latest.get('eco_score', 0)
                st.progress(score / 100)
                st.metric("Score", f"{score}/100")
                if score >= 80:
                    st.success("Excellent! Keep it up! 🌟")
                elif score >= 60:
                    st.info("Good! Room for improvement!")
                else:
                    st.warning("Needs attention! Let's improve! 💪")
        else:
            st.info("Complete an assessment to see your Eco Score")
    
    elif widget_id == "trend":
        st.subheader("📈 Footprint Trend")
        assessments = get_assessments(user_id)
        if assessments and len(assessments) > 1:
            import pandas as pd
            data = pd.DataFrame(assessments)
            if 'date' in data.columns and 'carbon_footprint' in data.columns:
                st.line_chart(data.set_index('date')['carbon_footprint'])
            else:
                st.info("Insufficient data for trend analysis")
        else:
            st.info("Need at least 2 assessments to show trend")
    
    elif widget_id == "activity":
        st.subheader("🕐 Latest Activity")
        assessments = get_assessments(user_id)
        if assessments:
            for assessment in assessments[-3:]:
                date = assessment.get('date', 'Unknown date')
                carbon = assessment.get('carbon_footprint', 'N/A')
                st.text(f"📅 {date}: {carbon} kg CO2")
        else:
            st.info("No recent activity")
    
    elif widget_id == "quick_tips":
        st.subheader("💡 Quick Eco Tips")
        tips = [
            "🚲 Use bicycle for short distances",
            "💡 Switch to LED bulbs",
            "♻️ Recycle paper, plastic, and glass",
            "🌿 Plant a tree every month",
            "🔌 Unplug devices when not in use",
            "🚿 Take shorter showers",
            "🥗 Eat more plant-based meals",
            "📦 Reduce plastic usage"
        ]
        import random
        for tip in random.sample(tips, min(3, len(tips))):
            st.info(tip)

def render_dashboard(user_id: str):
    """Render the full dashboard with user's preferred widgets"""
    st.title("🌍 EcoBuddy Dashboard")
    
    # Get user's widget preferences
    widgets = get_user_widgets(user_id)
    
    # Show widget management
    with st.expander("⚙️ Manage Dashboard Widgets", expanded=False):
        st.write("Select widgets to display on your dashboard:")
        selected = []
        cols = st.columns(2)
        for idx, (widget_id, widget_name) in enumerate(WIDGETS.items()):
            col_idx = idx % 2
            is_checked = widget_id in widgets
            checked = cols[col_idx].checkbox(
                widget_name,
                value=is_checked,
                key=f"widget_{widget_id}"
            )
            if checked:
                selected.append(widget_id)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("💾 Save Preferences", use_container_width=True):
                if save_user_widgets(user_id, selected):
                    st.success("✅ Widget preferences saved!")
                    st.rerun()
                else:
                    st.error("❌ Failed to save preferences")
        with col2:
            if st.button("🔄 Reset to Default", use_container_width=True):
                save_user_widgets(user_id, list(DEFAULT_WIDGETS))
                st.success("✅ Reset to default widgets!")
                st.rerun()
    
    st.divider()
    
    # Render widgets in 2-column layout
    if not widgets:
        st.warning("No widgets selected. Please add widgets from the settings above.")
        return
    
    cols = st.columns(2)
    for idx, widget_id in enumerate(widgets):
        if widget_id not in WIDGETS:
            continue
        col_idx = idx % 2
        with cols[col_idx]:
            with st.container(border=True):
                render_widget(widget_id, user_id)
    
    # Add refresh button at bottom
    st.divider()
    if st.button("🔄 Refresh Dashboard", use_container_width=True):
        st.rerun()

def main():
    """Main dashboard function"""
    st.set_page_config(
        page_title="EcoBuddy Dashboard",
        page_icon="🌍",
        layout="wide"
    )
    
    # Initialize session state
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = "default_user"
    
    # Get user ID
    user_id = st.session_state.get("user_id", "default_user")
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50?text=EcoBuddy+AI", use_container_width=True)
        st.markdown("---")
        st.markdown("### 👤 User Profile")
        user_id_input = st.text_input("User ID", value=user_id)
        if user_id_input != user_id:
            st.session_state["user_id"] = user_id_input
            st.rerun()
        st.markdown("---")
        st.markdown("### 📊 Stats")
        assessments = get_assessments(user_id)
        if assessments:
            st.metric("Total Assessments", len(assessments))
            latest = assessments[-1] if assessments else None
            if latest:
                st.metric("Latest Eco Score", f"{latest.get('eco_score', 0)}/100")
    
    # Render dashboard
    render_dashboard(user_id)


if __name__ == "__main__":
    main()

    if "quick_tips" in selected:
        with st.container(border=True):
            st.subheader("💡 Quick eco tips")
            tips = [
                "Walk, cycle, or use public transport for short journeys.",
                "Turn off standby appliances and unnecessary lights.",
                "Plan meals to reduce food waste.",
            ]
            if latest and str(latest.get("transport")) == "Car":
                tips.insert(0, "Combine car trips or car-share to reduce transport emissions.")
            for tip in tips[:3]:
                st.markdown(f"- {tip}")
    if "insights" in selected:
        with st.container(border=True):
            st.subheader("🔎 Personal insights")

            if latest:
                footprint = float(latest["footprint"])
                score = int(latest["eco_score"])
                transport = str(latest["transport"])
                electricity = float(latest["electricity"])
                flights = int(latest["flights"])

                insights = []

                if score >= 85:
                    insights.append(
                        "🌱 Your eco score is excellent. Keep maintaining your current habits."
                    )
                elif score >= 70:
                    insights.append(
                        "🌿 Your sustainability habits are strong, with room for further improvement."
                    )
                elif score >= 50:
                    insights.append(
                        "💡 Your score shows progress. Focus on one high-impact lifestyle change at a time."
                    )
                else:
                    insights.append(
                        "⚡ Your footprint has significant improvement potential. Start with your largest emission source."
                    )

                if transport.lower() in {"car", "taxi"}:
                    insights.append(
                        "🚗 Transport is an important area to improve. Consider public transport, walking, cycling, or car-sharing."
                    )

                if electricity >= 300:
                    insights.append(
                        "🔌 Your electricity usage is relatively high. Reducing unnecessary appliance use could help."
                    )
                elif electricity >= 150:
                    insights.append(
                        "💡 Look for small electricity savings by switching off unused lights and appliances."
                    )

                if flights > 0:
                    insights.append(
                        "✈️ Air travel contributes to your footprint. Consider alternatives when practical."
                    )

                st.metric("Current footprint", f"{footprint:,.0f} kg CO₂/year")

                for insight in insights[:4]:
                    st.markdown(f"- {insight}")

            else:
                st.info(
                    "Complete a carbon assessment to receive personalized sustainability insights."
                )

