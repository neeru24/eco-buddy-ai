"""Global search for EcoBuddy AI dashboard sections and activities."""

from pathlib import Path
from typing import Any

import streamlit as st

from database import get_assessments


# Main dashboard sections available in app.py
DASHBOARD_SECTIONS = [
    {
        "title": "Carbon Footprint",
        "description": "Calculate and analyze your carbon footprint.",
        "icon": "🌍",
        "target": "Carbon Footprint",
    },
    {
        "title": "Home Energy Audit",
        "description": "Analyze household energy consumption.",
        "icon": "⚡",
        "target": "Home Energy Audit",
    },
    {
        "title": "Gamification",
        "description": "Track challenges, XP, badges, and progress.",
        "icon": "🎮",
        "target": "Gamification",
    },
    {
        "title": "Route Planning & Offsets",
        "description": "Compare greener travel options and offsets.",
        "icon": "🗺️",
        "target": "Route Planning & Offsets",
    },
    {
        "title": "Community Leaderboard",
        "description": "View sustainability rankings and progress.",
        "icon": "🏆",
        "target": "Community Leaderboard",
    },
    {
        "title": "Future Self",
        "description": "Explore projected environmental impact.",
        "icon": "🔮",
        "target": "Future Self",
    },
]


def get_page_results() -> list[dict[str, Any]]:
    """Build searchable results from the Streamlit pages directory."""
    pages_dir = Path(__file__).parent / "pages"

    if not pages_dir.exists():
        return []

    results = []

    for page in sorted(pages_dir.glob("*.py")):
        if page.name.startswith("_"):
            continue

        title = page.stem.replace("_", " ")

        results.append(
            {
                "title": title,
                "description": f"Open the {title} section.",
                "icon": "📄",
                "target": str(page),
            }
        )

    return results


def get_activity_results(user_id: int) -> list[dict[str, Any]]:
    """Return recent assessment activity as searchable results."""
    try:
        assessments = get_assessments(user_id)
    except Exception:
        return []

    results = []

    for assessment in assessments[:10]:
        if isinstance(assessment, dict):
            assessment_id = assessment.get("id")
            date = assessment.get("date", assessment.get("created_at", ""))
            footprint = assessment.get("footprint")
            eco_score = assessment.get("eco_score")
        else:
            assessment_id = assessment[0] if len(assessment) > 0 else None
            date = assessment[2] if len(assessment) > 2 else ""
            footprint = assessment[9] if len(assessment) > 9 else None
            eco_score = assessment[10] if len(assessment) > 10 else None

        results.append(
            {
                "title": f"Assessment {date}".strip(),
                "description": (
                    f"Carbon footprint: {footprint} kg CO₂"
                    f" • Eco Score: {eco_score}"
                ),
                "icon": "📊",
                "target": "Assessment_History.py",
                "id": assessment_id,
            }
        )

    return results


def search_results(
    query: str,
    user_id: int | None = None,
) -> list[dict[str, Any]]:
    """Search dashboard sections, pages, and saved activities."""
    query = query.strip().lower()

    if not query:
        return []

    all_results = []

    for item in DASHBOARD_SECTIONS:
        searchable = (
            f"{item['title']} "
            f"{item['description']} "
            f"{item['target']}"
        ).lower()

        if query in searchable:
            all_results.append({**item, "type": "Dashboard"})

    for item in get_page_results():
        searchable = (
            f"{item['title']} "
            f"{item['description']} "
            f"{item['target']}"
        ).lower()

        if query in searchable:
            all_results.append({**item, "type": "Page"})

    if user_id:
        for item in get_activity_results(user_id):
            searchable = (
                f"{item['title']} "
                f"{item['description']}"
            ).lower()

            if query in searchable:
                all_results.append({**item, "type": "Activity"})

    return all_results[:8]


def render_global_search(user_id: int | None = None) -> None:
    """Render the global search bar with live suggestions."""

    st.markdown(
    """
    <div style="
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    ">
        🔍 Global Search
    </div>
    """,
    unsafe_allow_html=True,
)

    query = st.text_input(
        "Search",
        placeholder="Search dashboard sections, reports, or activities...",
        label_visibility="collapsed",
        key="global_search_query",
    )

    if not query.strip():
        return

    results = search_results(query, user_id)

    if not results:
        st.info(f'No results found for "{query}".')
        return

    st.caption(f"Search results for **{query}**")

    for index, result in enumerate(results):
        label = (
            f"{result['icon']} {result['title']} "
            f"— {result['type']}"
        )

        if st.button(
            label,
            key=f"global_search_result_{index}",
            use_container_width=True,
        ):
            target = result["target"]

            if target.endswith(".py"):
                st.switch_page(f"pages/{Path(target).name}")
            else:
                st.info(
                    f"'{result['title']}' is available in the main dashboard."
                )