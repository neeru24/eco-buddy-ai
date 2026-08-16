from collections import OrderedDict
from typing import Iterable, Mapping, List, Optional
import streamlit as st
from database import (
    get_assessments,
    get_dashboard_widget_preferences,
    save_dashboard_widget_preferences,
)


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
    """Return unique, known widget IDs in the canonical display order."""
    requested = set(widget_ids or [])
    return [widget_id for widget_id in WIDGETS if widget_id in requested]


def load_widget_preferences(user_id: int) -> List[str]:
    """Load a user's saved widgets, falling back to all dashboard widgets."""
    saved = get_dashboard_widget_preferences(user_id)
    if saved is None:
        return list(DEFAULT_WIDGETS)
    return normalize_widget_preferences(saved)


def get_user_widgets(user_id: str) -> List[str]:
    """Get user's widget preferences from database or session."""
    if SESSION_KEY in st.session_state:
        return st.session_state[SESSION_KEY]

    preferences = get_dashboard_widget_preferences(user_id)
    if preferences:
        normalized = normalize_widget_preferences(preferences)
        st.session_state[SESSION_KEY] = normalized
        return normalized

    default = list(DEFAULT_WIDGETS)
    st.session_state[SESSION_KEY] = default
    return default


def save_user_widgets(user_id: str, widget_ids: List[str]) -> bool:
    """Save user's widget preferences."""
    normalized = normalize_widget_preferences(widget_ids)
    result = save_dashboard_widget_preferences(user_id, normalized)
    if result:
        st.session_state[SESSION_KEY] = normalized
    return result


def render_widget_customizer(user_id: int) -> list[str]:
    """Render the sidebar widget picker and persist explicit saves."""
    if SESSION_KEY not in st.session_state:
        st.session_state[SESSION_KEY] = load_widget_preferences(user_id)

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
def _assessment_rows_to_frame(rows: tuple):
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


def _has_value(value) -> bool:
    """Return False for None and NaN so missing values fall back to empty states."""
    if value is None:
        return False
    try:
        import pandas as pd

        return not bool(pd.isna(value))
    except (TypeError, ValueError):
        return True


def _latest_has_assessment(latest: Mapping[str, object] | None) -> bool:
    """Check that the latest assessment row carries usable footprint data."""
    return latest is not None and _has_value(latest.get("footprint"))


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

    # Data existence check: every widget below degrades to a friendly empty
    # state when no assessment data exists yet.
    frame = _assessment_rows_to_frame(tuple(get_assessments(user_id)))
    latest: Mapping[str, object] | None = None
    if not frame.empty:
        latest = frame.iloc[0].to_dict()

    if "summary" in selected:
        with st.container(border=True):
            st.subheader("🌍 Latest impact summary")
            if _latest_has_assessment(latest):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Annual footprint",
                        f"{float(latest['footprint']):,.0f} kg CO₂",
                    )
                with col2:
                    score = latest.get("eco_score")
                    st.metric(
                        "Eco score",
                        f"{int(score)}/100" if _has_value(score) else "N/A",
                    )
                with col3:
                    transport = latest.get("transport")
                    st.metric("Primary transport", str(transport) if _has_value(transport) else "N/A")
            else:
                st.info("No assessments found yet. Start tracking your impact!")

    if "eco_score" in selected:
        with st.container(border=True):
            st.subheader("🏆 Eco score")
            score_value = latest.get("eco_score") if latest else None
            if _has_value(score_value):
                score = max(0, min(100, int(score_value)))
                st.progress(score / 100, text=f"Current score: {score}/100")
                if score >= 85:
                    st.success("Eco Champion — excellent sustainable habits.")
                elif score >= 70:
                    st.info("Green Guardian — you are performing well.")
                elif score >= 50:
                    st.warning("Eco Learner — small changes can raise your score.")
                else:
                    st.error("High impact — focus on your largest emission source first.")
            else:
                st.info("Your eco score will appear after an assessment.")

    if "trend" in selected:
        with st.container(border=True):
            st.subheader("📈 Footprint trend")
            trend = frame.dropna(subset=["date", "footprint"]).sort_values("date")
            if len(trend) >= 2:
                # Data existence check before generating the Plotly figure.
                import plotly.express as px

                figure = px.line(
                    trend,
                    x="date",
                    y="footprint",
                    markers=True,
                    labels={"date": "Assessment date", "footprint": "kg CO₂/year"},
                    title="Carbon footprint over time",
                )
                figure.update_traces(
                    hovertemplate="<b>%{x|%b %d, %Y}</b><br>%{y:,.0f} kg CO₂/year<extra></extra>",
                    line=dict(color="#4ade80", width=3),
                    marker=dict(size=8, color="#4ade80"),
                )
                figure.update_layout(
                    margin=dict(l=10, r=10, t=30, b=10),
                    xaxis_title="Assessment date",
                    yaxis_title="kg CO₂ / year",
                )
                st.plotly_chart(figure, use_container_width=True)
            elif len(trend) == 1:
                st.info("Complete one more assessment to unlock your trend chart.")
            else:
                st.info("Assessment history is not available yet.")

    if "activity" in selected:
        with st.container(border=True):
            st.subheader("🧭 Latest activity")
            if _latest_has_assessment(latest):
                import pandas as pd

                def _fmt(key: str, unit: str) -> str:
                    value = latest.get(key)
                    if not _has_value(value):
                        return "N/A"
                    return f"{float(value):g} {unit}"

                activity = pd.DataFrame(
                    {
                        "Category": ["Transport", "Distance", "Electricity", "Diet", "Flights"],
                        "Value": [
                            str(latest.get("transport")) if _has_value(latest.get("transport")) else "N/A",
                            _fmt("distance", "km/day"),
                            _fmt("electricity", "kWh/month"),
                            str(latest.get("diet")) if _has_value(latest.get("diet")) else "N/A",
                            _fmt("flights", ""),
                        ],
                    }
                )
                st.dataframe(activity, hide_index=True, use_container_width=True)
            else:
                st.info("Your latest lifestyle inputs will appear here.")

    if "quick_tips" in selected:
        with st.container(border=True):
            st.subheader("💡 Quick eco tips")
            tips = [
                "Walk, cycle, or use public transport for short journeys.",
                "Turn off standby appliances and unnecessary lights.",
                "Plan meals to reduce food waste.",
            ]
            if latest and str(latest.get("transport", "")) == "Car":
                tips.insert(0, "Combine car trips or car-share to reduce transport emissions.")
            for tip in tips[:3]:
                st.markdown(f"- {tip}")

    if "insights" in selected:
        with st.container(border=True):
            st.subheader("🔎 Personal insights")
            if _latest_has_assessment(latest):
                footprint = float(latest["footprint"])
                score = int(latest["eco_score"]) if _has_value(latest.get("eco_score")) else 0
                transport = str(latest.get("transport")) if _has_value(latest.get("transport")) else ""
                electricity = float(latest["electricity"]) if _has_value(latest.get("electricity")) else 0.0
                flights = int(latest["flights"]) if _has_value(latest.get("flights")) else 0

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
