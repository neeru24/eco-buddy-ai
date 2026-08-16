"""Climate Career Hub UI and core logic."""

from __future__ import annotations

import streamlit as st
from database import (
    get_career_opportunities,
    add_career_opportunity,
    toggle_career_bookmark,
    get_bookmarked_careers,
    is_career_bookmarked,
)

OPPORTUNITY_TYPES = [
    "All Types",
    "Internships",
    "Full-Time Jobs",
    "Fellowships",
    "Volunteer",
]

DOMAINS = [
    "All Domains",
    "Renewable Energy",
    "Carbon Capture",
    "Sustainable Agriculture",
    "Circular Economy",
    "Climate Policy",
    "Clean Mobility",
]

LOCATIONS = [
    "All Locations",
    "Remote",
    "Hybrid",
    "On-site",
]


def render_climate_careers() -> None:
    """Render the Climate Career Hub interface."""
    st.title("💼 Climate Career Hub")
    st.markdown(
        "Explore green career opportunities, climate-tech internships, fellowships, "
        "and volunteer roles shaping a sustainable future."
    )

    user_id = st.session_state.get("user_id") or 1

    tab1, tab2, tab3 = st.tabs(
        ["🔍 Browse Opportunities", "🔖 Bookmarked Listings", "➕ Post Opportunity"]
    )

    # TAB 1: BROWSE OPPORTUNITIES
    with tab1:
        c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
        with c1:
            sel_type = st.selectbox("Opportunity Type", options=OPPORTUNITY_TYPES, key="careers_type_sel")
        with c2:
            sel_domain = st.selectbox("Domain", options=DOMAINS, key="careers_domain_sel")
        with c3:
            sel_location = st.selectbox("Location", options=LOCATIONS, key="careers_loc_sel")
        with c4:
            search_q = st.text_input("Search Keyword", placeholder="e.g. Engineer, Solar, Policy...", key="careers_search_input")

        careers = get_career_opportunities(
            opportunity_type=sel_type,
            domain=sel_domain,
            location=sel_location,
            search_query=search_q.strip() if search_q else None,
        )

        st.markdown(f"### Found {len(careers)} Opportunity(ies)")

        if not careers:
            st.info("No career listings match your filter criteria.")
        else:
            for job in careers:
                _render_career_card(job, user_id=user_id)

    # TAB 2: BOOKMARKS
    with tab2:
        st.markdown("### 🔖 Your Bookmarked Listings")
        bookmarks = get_bookmarked_careers(user_id=user_id)
        if not bookmarks:
            st.info("You haven't bookmarked any opportunities yet. Click 'Bookmark' on any listing to save it here.")
        else:
            for job in bookmarks:
                _render_career_card(job, user_id=user_id, is_bookmarked_tab=True)

    # TAB 3: POST OPPORTUNITY
    with tab3:
        st.markdown("### Post a New Climate Opportunity")
        with st.form("post_career_form", clear_on_submit=True):
            title = st.text_input("Job Title / Role", placeholder="e.g. Clean Energy Data Analyst")
            company = st.text_input("Organization / Company", placeholder="e.g. EcoGrid Inc.")
            opp_type = st.selectbox("Opportunity Type", options=[t for t in OPPORTUNITY_TYPES if t != "All Types"])
            domain = st.selectbox("Domain", options=[d for d in DOMAINS if d != "All Domains"])
            location = st.text_input("Location", placeholder="e.g. Remote, or San Francisco, CA")
            apply_url = st.text_input("Application URL", placeholder="https://example.com/apply")
            description = st.text_area("Role Description & Responsibilities")

            submit = st.form_submit_button("Publish Opportunity 🚀")

            if submit:
                if not title or not company or not apply_url or not description:
                    st.error("Please complete all required fields.")
                else:
                    if not apply_url.startswith("http://") and not apply_url.startswith("https://"):
                        apply_url = "https://" + apply_url
                    success = add_career_opportunity(
                        title=title,
                        company=company,
                        opportunity_type=opp_type,
                        domain=domain,
                        location=location,
                        description=description,
                        apply_url=apply_url,
                    )
                    if success:
                        st.success("Opportunity posted successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to post opportunity. Please try again.")


def _render_career_card(job: dict, user_id: int, is_bookmarked_tab: bool = False) -> None:
    """Render an individual climate career card with bookmarking option."""
    card_id = job["id"]
    bookmarked = is_career_bookmarked(user_id=user_id, career_id=card_id)

    with st.container():
        cols = st.columns([3, 1])
        with cols[0]:
            st.markdown(f"#### {job['title']} @ **{job['company']}**")
            st.caption(
                f"🏷️ **Type:** {job['type']} | 🌐 **Domain:** {job['domain']} | 📍 **Location:** {job['location']}"
            )
            st.write(job["description"])

        with cols[1]:
            st.markdown("<br>", unsafe_allow_html=True)
            st.link_button("🚀 Apply Now", job["apply_url"])

            b_label = "📌 Bookmarked" if bookmarked else "🔖 Bookmark"
            if st.button(b_label, key=f"bm_btn_{card_id}_{'bm' if is_bookmarked_tab else 'main'}"):
                toggle_career_bookmark(user_id=user_id, career_id=card_id)
                st.rerun()

        st.divider()
