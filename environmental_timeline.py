"""Environmental impact timeline utilities and Streamlit renderer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Iterable, Mapping, Sequence

import streamlit as st

from database import (
    get_assessments,
    get_environmental_milestones,
    record_environmental_milestone,
    get_historical_events,
    add_historical_event,
)

EVENT_CATEGORIES = [
    "All Categories",
    "Policy & Treaties",
    "Climate Movements",
    "Scientific Discoveries",
]


@dataclass(frozen=True)
class MilestoneDefinition:
    """An extensible rule used to recognize one sustainability achievement."""

    milestone_type: str
    title: str
    description: str
    icon: str
    predicate: Callable[[Sequence[tuple]], bool]
    metadata_factory: Callable[[Sequence[tuple]], Mapping[str, object]]


def _assessment_count(rows: Sequence[tuple]) -> int:
    return len(rows)


def _best_eco_score(rows: Sequence[tuple]) -> int:
    scores = [int(row[8]) for row in rows if len(row) > 8 and row[8] is not None]
    return max(scores, default=0)


def _lowest_footprint(rows: Sequence[tuple]) -> float | None:
    values = [float(row[7]) for row in rows if len(row) > 7 and row[7] is not None]
    return min(values) if values else None


MILESTONE_DEFINITIONS: tuple[MilestoneDefinition, ...] = (
    MilestoneDefinition(
        "first_assessment",
        "Journey Started",
        "Completed the first environmental footprint assessment.",
        "🌱",
        lambda rows: _assessment_count(rows) >= 1,
        lambda rows: {"assessment_count": _assessment_count(rows)},
    ),
    MilestoneDefinition(
        "five_assessments",
        "Consistency Builder",
        "Completed five environmental footprint assessments.",
        "🗓️",
        lambda rows: _assessment_count(rows) >= 5,
        lambda rows: {"assessment_count": _assessment_count(rows)},
    ),
    MilestoneDefinition(
        "eco_score_70",
        "Eco Score: 70",
        "Reached an eco score of at least 70.",
        "⭐",
        lambda rows: _best_eco_score(rows) >= 70,
        lambda rows: {"best_eco_score": _best_eco_score(rows)},
    ),
    MilestoneDefinition(
        "eco_score_85",
        "Eco Champion",
        "Reached an eco score of at least 85.",
        "🏆",
        lambda rows: _best_eco_score(rows) >= 85,
        lambda rows: {"best_eco_score": _best_eco_score(rows)},
    ),
    MilestoneDefinition(
        "footprint_under_5",
        "Low-Impact Day",
        "Recorded a carbon footprint below 5 kg CO₂e.",
        "🍃",
        lambda rows: (
            _lowest_footprint(rows) is not None
            and _lowest_footprint(rows) < 5
        ),
        lambda rows: {"lowest_footprint": _lowest_footprint(rows)},
    ),
)


def evaluate_milestones(
    assessments: Sequence[tuple],
    definitions: Iterable[MilestoneDefinition] = MILESTONE_DEFINITIONS,
) -> list[dict]:
    """Return milestone payloads whose predicates are satisfied."""
    achieved: list[dict] = []
    for definition in definitions:
        if definition.predicate(assessments):
            achieved.append(
                {
                    "milestone_type": definition.milestone_type,
                    "title": definition.title,
                    "description": definition.description,
                    "icon": definition.icon,
                    "metadata": dict(definition.metadata_factory(assessments)),
                }
            )
    return achieved


def sync_environmental_milestones(user_id: int) -> int:
    """Evaluate assessment history and persist newly reached milestones."""
    assessments = get_assessments(user_id)
    inserted = 0
    for milestone in evaluate_milestones(assessments):
        inserted += int(
            record_environmental_milestone(
                user_id=user_id,
                milestone_type=milestone["milestone_type"],
                title=milestone["title"],
                description=milestone["description"],
                icon=milestone["icon"],
                metadata=milestone["metadata"],
            )
        )
    return inserted


def _format_date(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).strftime(
            "%d %b %Y"
        )
    except ValueError:
        return text[:10]


def render_environmental_timeline(user_id: int) -> None:
    """Render the Environmental Timeline interface."""
    st.title("📜 Environmental Timeline & Milestones")
    st.markdown(
        "Explore major global environmental events and historical climate milestones, "
        "or track your personal sustainability journey."
    )

    tab1, tab2, tab3 = st.tabs(
        ["🌎 Global Climate History", "🏆 My Personal Milestones", "➕ Add Historical Event"]
    )

    # TAB 1: HISTORICAL CLIMATE EVENTS
    with tab1:
        col1, col2 = st.columns([1, 2])
        with col1:
            selected_cat = st.selectbox(
                "Filter Category",
                options=EVENT_CATEGORIES,
                key="timeline_category_select",
            )
        with col2:
            search_query = st.text_input(
                "Search History by Keyword or Year",
                placeholder="e.g. Paris, 1970, Ozone, IPCC...",
                key="timeline_search_input",
            )

        events = get_historical_events(
            category=selected_cat,
            search_query=search_query.strip() if search_query else None,
        )

        st.markdown(f"### Found {len(events)} Climate Milestone(s)")

        if not events:
            st.info("No historical climate events matched your search.")
        else:
            for event in events:
                _render_event_timeline_node(event)

    # TAB 2: PERSONAL SUSTAINABILITY MILESTONES
    with tab2:
        sync_environmental_milestones(user_id)
        milestones = get_environmental_milestones(user_id)

        st.markdown("### Your Personal Achievement Timeline")
        st.caption(
            "Your sustainability milestones are recorded automatically as your assessment history grows."
        )

        if not milestones:
            st.info(
                "Complete your first footprint assessment to unlock the first timeline milestone."
            )
        else:
            for index, milestone in enumerate(milestones):
                date_label = _format_date(milestone.get("achieved_at"))
                highlight = index == 0
                border = "#22c55e" if highlight else "#94a3b8"
                badge = "LATEST ACHIEVEMENT" if highlight else "MILESTONE"

                st.markdown(
                    f"""
                    <div style="
                        position: relative;
                        margin: 0 0 14px 18px;
                        padding: 16px 18px;
                        border-left: 4px solid {border};
                        border-radius: 0 14px 14px 0;
                        background: rgba(34, 197, 94, 0.08);
                    ">
                        <div style="
                            position: absolute;
                            left: -15px;
                            top: 17px;
                            width: 26px;
                            height: 26px;
                            border-radius: 50%;
                            display: grid;
                            place-items: center;
                            background: white;
                            border: 3px solid {border};
                        ">{milestone.get("icon", "🌱")}</div>
                        <div style="
                            font-size: 11px;
                            font-weight: 800;
                            letter-spacing: .08em;
                            color: {border};
                        ">{badge}</div>
                        <div style="font-size: 18px; font-weight: 800;">
                            {milestone.get("title", "Achievement")}
                        </div>
                        <div style="opacity: .78; margin-top: 4px;">
                            {milestone.get("description", "")}
                        </div>
                        <div style="font-size: 12px; opacity: .58; margin-top: 8px;">
                            {date_label}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # TAB 3: ADD HISTORICAL EVENT
    with tab3:
        st.markdown("### Add a Major Environmental Event")
        with st.form("add_event_form", clear_on_submit=True):
            year = st.number_input("Year", min_value=1800, max_value=2100, value=2024)
            title = st.text_input("Event Title", placeholder="e.g. Global Plastics Treaty High-Level Summit")
            category = st.selectbox("Category", options=[c for c in EVENT_CATEGORIES if c != "All Categories"])
            description = st.text_area("Event Description")
            impact_summary = st.text_area("Environmental Impact Summary")
            educational_resources = st.text_input("Educational Resources / Readings")
            source_url = st.text_input("Reference Source URL")

            submit = st.form_submit_button("Add Event 🚀")

            if submit:
                if not title or not description or not impact_summary:
                    st.error("Please fill in all required fields (Title, Description, Impact Summary).")
                else:
                    success = add_historical_event(
                        year=int(year),
                        title=title,
                        category=category,
                        description=description,
                        impact_summary=impact_summary,
                        educational_resources=educational_resources,
                        source_url=source_url,
                    )
                    if success:
                        st.success(f"Historical event '{title}' added!")
                        st.rerun()
                    else:
                        st.error("Failed to add event. Title may already exist.")


def _render_event_timeline_node(event: dict) -> None:
    """Render a single historical event card node."""
    cat_colors = {
        "Policy & Treaties": "#3b82f6",
        "Climate Movements": "#22c55e",
        "Scientific Discoveries": "#a855f7",
    }
    color = cat_colors.get(event["category"], "#eab308")

    st.markdown(
        f"""
        <div style="
            position: relative;
            margin: 0 0 16px 12px;
            padding: 16px 20px;
            border-left: 5px solid {color};
            border-radius: 0 12px 12px 0;
            background: rgba(15, 23, 42, 0.03);
        ">
            <div style="font-size: 13px; font-weight: bold; color: {color};">
                📅 YEAR {event['year']} — <span style="text-transform: uppercase;">{event['category']}</span>
            </div>
            <div style="font-size: 20px; font-weight: 800; margin-top: 4px;">
                {event['title']}
            </div>
            <div style="margin-top: 8px; font-size: 15px; line-height: 1.5;">
                {event['description']}
            </div>
            <div style="margin-top: 10px; padding: 10px 14px; background: rgba(34, 197, 94, 0.08); border-radius: 8px; font-size: 14px;">
                🌱 <strong>Impact Summary:</strong> {event['impact_summary']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if event.get("educational_resources") or event.get("source_url"):
        with st.expander(f"📚 Educational Resources & References ({event['title']})"):
            if event.get("educational_resources"):
                st.markdown(f"**Learning Resources:** {event['educational_resources']}")
            if event.get("source_url"):
                st.link_button("🌐 Learn More / Read Source", event["source_url"])

    st.divider()



@dataclass(frozen=True)
class MilestoneDefinition:
    """An extensible rule used to recognize one sustainability achievement."""

    milestone_type: str
    title: str
    description: str
    icon: str
    predicate: Callable[[Sequence[tuple]], bool]
    metadata_factory: Callable[[Sequence[tuple]], Mapping[str, object]]


def _assessment_count(rows: Sequence[tuple]) -> int:
    return len(rows)


def _best_eco_score(rows: Sequence[tuple]) -> int:
    scores = [int(row[8]) for row in rows if len(row) > 8 and row[8] is not None]
    return max(scores, default=0)


def _lowest_footprint(rows: Sequence[tuple]) -> float | None:
    values = [float(row[7]) for row in rows if len(row) > 7 and row[7] is not None]
    return min(values) if values else None


MILESTONE_DEFINITIONS: tuple[MilestoneDefinition, ...] = (
    MilestoneDefinition(
        "first_assessment",
        "Journey Started",
        "Completed the first environmental footprint assessment.",
        "🌱",
        lambda rows: _assessment_count(rows) >= 1,
        lambda rows: {"assessment_count": _assessment_count(rows)},
    ),
    MilestoneDefinition(
        "five_assessments",
        "Consistency Builder",
        "Completed five environmental footprint assessments.",
        "🗓️",
        lambda rows: _assessment_count(rows) >= 5,
        lambda rows: {"assessment_count": _assessment_count(rows)},
    ),
    MilestoneDefinition(
        "eco_score_70",
        "Eco Score: 70",
        "Reached an eco score of at least 70.",
        "⭐",
        lambda rows: _best_eco_score(rows) >= 70,
        lambda rows: {"best_eco_score": _best_eco_score(rows)},
    ),
    MilestoneDefinition(
        "eco_score_85",
        "Eco Champion",
        "Reached an eco score of at least 85.",
        "🏆",
        lambda rows: _best_eco_score(rows) >= 85,
        lambda rows: {"best_eco_score": _best_eco_score(rows)},
    ),
    MilestoneDefinition(
        "footprint_under_5",
        "Low-Impact Day",
        "Recorded a carbon footprint below 5 kg CO₂e.",
        "🍃",
        lambda rows: (
            _lowest_footprint(rows) is not None
            and _lowest_footprint(rows) < 5
        ),
        lambda rows: {"lowest_footprint": _lowest_footprint(rows)},
    ),
)


def evaluate_milestones(
    assessments: Sequence[tuple],
    definitions: Iterable[MilestoneDefinition] = MILESTONE_DEFINITIONS,
) -> list[dict]:
    """Return milestone payloads whose predicates are satisfied."""
    achieved: list[dict] = []
    for definition in definitions:
        if definition.predicate(assessments):
            achieved.append(
                {
                    "milestone_type": definition.milestone_type,
                    "title": definition.title,
                    "description": definition.description,
                    "icon": definition.icon,
                    "metadata": dict(definition.metadata_factory(assessments)),
                }
            )
    return achieved


def sync_environmental_milestones(user_id: int) -> int:
    """Evaluate assessment history and persist newly reached milestones."""
    assessments = get_assessments(user_id)
    inserted = 0
    for milestone in evaluate_milestones(assessments):
        inserted += int(
            record_environmental_milestone(
                user_id=user_id,
                milestone_type=milestone["milestone_type"],
                title=milestone["title"],
                description=milestone["description"],
                icon=milestone["icon"],
                metadata=milestone["metadata"],
            )
        )
    return inserted


def _format_date(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).strftime(
            "%d %b %Y"
        )
    except ValueError:
        return text[:10]


def render_environmental_timeline(user_id: int) -> None:
    """Render a visual milestone timeline for the active user."""
    sync_environmental_milestones(user_id)
    milestones = get_environmental_milestones(user_id)

    st.markdown("## 🌍 Environmental Impact Timeline")
    st.caption(
        "Your sustainability milestones are recorded automatically as your "
        "assessment history grows."
    )

    if not milestones:
        st.info(
            "Complete your first footprint assessment to unlock the first "
            "timeline milestone."
        )
        return

    for index, milestone in enumerate(milestones):
        date_label = _format_date(milestone.get("achieved_at"))
        highlight = index == 0
        border = "#22c55e" if highlight else "#94a3b8"
        badge = "LATEST ACHIEVEMENT" if highlight else "MILESTONE"

        st.markdown(
            f"""
            <div style="
                position: relative;
                margin: 0 0 14px 18px;
                padding: 16px 18px;
                border-left: 4px solid {border};
                border-radius: 0 14px 14px 0;
                background: rgba(34, 197, 94, 0.08);
            ">
                <div style="
                    position: absolute;
                    left: -15px;
                    top: 17px;
                    width: 26px;
                    height: 26px;
                    border-radius: 50%;
                    display: grid;
                    place-items: center;
                    background: white;
                    border: 3px solid {border};
                ">{milestone.get("icon", "🌱")}</div>
                <div style="
                    font-size: 11px;
                    font-weight: 800;
                    letter-spacing: .08em;
                    color: {border};
                ">{badge}</div>
                <div style="font-size: 18px; font-weight: 800;">
                    {milestone.get("title", "Achievement")}
                </div>
                <div style="opacity: .78; margin-top: 4px;">
                    {milestone.get("description", "")}
                </div>
                <div style="font-size: 12px; opacity: .58; margin-top: 8px;">
                    {date_label}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
