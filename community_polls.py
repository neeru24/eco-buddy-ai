"""Community Polls UI and core logic."""

from __future__ import annotations

import uuid
import streamlit as st
from database import (
    get_active_polls,
    get_archived_polls,
    create_poll,
    vote_poll,
    has_user_voted,
    archive_poll,
)


def _get_anonymous_user_token() -> str:
    """Retrieve or generate a session-scoped anonymous user token for voting."""
    if "user_id" in st.session_state and st.session_state["user_id"]:
        return f"user_{st.session_state['user_id']}"
    if "anon_poll_token" not in st.session_state:
        st.session_state["anon_poll_token"] = f"anon_{uuid.uuid4().hex[:12]}"
    return st.session_state["anon_poll_token"]


def render_community_polls() -> None:
    """Render the Community Polls module in Streamlit."""
    st.title("🗳️ Community Polls")
    st.markdown(
        "Vote anonymously on sustainability questions, view live community responses, "
        "and explore archived polls."
    )

    user_token = _get_anonymous_user_token()

    tab1, tab2, tab3 = st.tabs(
        ["📊 Active Polls", "➕ Create Poll", "📦 Poll Archive"]
    )

    # TAB 1: ACTIVE POLLS
    with tab1:
        active_polls = get_active_polls()
        st.markdown(f"### Active Polls ({len(active_polls)})")

        if not active_polls:
            st.info("No active polls right now. Be the first to create one!")
        else:
            for poll in active_polls:
                poll_id = poll["id"]
                st.subheader(f"❓ {poll['question']}")
                st.caption(
                    f"**Category:** {poll['category']} | **Created by:** {poll['created_by']} | "
                    f"**Total Votes:** {poll['total_votes']}"
                )

                already_voted = has_user_voted(poll_id, user_token)

                if already_voted:
                    st.success("✓ You have voted on this poll! Here are the live results:")
                    _render_poll_results(poll)
                else:
                    options = poll["options"]
                    option_labels = [opt["option_text"] for opt in options]
                    selected_opt_label = st.radio(
                        "Cast your vote:",
                        options=option_labels,
                        key=f"radio_poll_{poll_id}",
                    )

                    col_vote, col_archive = st.columns([1, 1])
                    with col_vote:
                        if st.button("Submit Vote 🗳️", key=f"btn_vote_{poll_id}"):
                            selected_opt = next(
                                opt for opt in options if opt["option_text"] == selected_opt_label
                            )
                            success = vote_poll(poll_id, selected_opt["id"], user_token)
                            if success:
                                st.success("Vote recorded successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to record vote or already voted.")

                    with col_archive:
                        if st.button("Archive Poll 📁", key=f"btn_archive_{poll_id}"):
                            if archive_poll(poll_id):
                                st.success("Poll archived.")
                                st.rerun()

                    with st.expander("View Live Results without Voting"):
                        _render_poll_results(poll)

                st.divider()

    # TAB 2: CREATE POLL
    with tab2:
        st.markdown("### Create a New Community Poll")
        with st.form("create_poll_form", clear_on_submit=True):
            question = st.text_input("Poll Question", placeholder="e.g. Should carbon labeling be mandatory on menus?")
            category = st.selectbox(
                "Category",
                options=["General", "Lifestyle", "Policy", "Technology", "Transport", "Energy"],
            )
            created_by = st.text_input(
                "Creator Name",
                value=st.session_state.get("username") or "Community Member",
            )

            st.markdown("#### Options (At least 2 required)")
            opt1 = st.text_input("Option 1", placeholder="Yes")
            opt2 = st.text_input("Option 2", placeholder="No")
            opt3 = st.text_input("Option 3 (Optional)", placeholder="Unsure / Neutral")
            opt4 = st.text_input("Option 4 (Optional)")

            submit = st.form_submit_button("Publish Poll 🚀")

            if submit:
                options = [o.strip() for o in [opt1, opt2, opt3, opt4] if o and o.strip()]
                if not question.strip():
                    st.error("Please enter a poll question.")
                elif len(options) < 2:
                    st.error("Please provide at least 2 valid options.")
                else:
                    new_id = create_poll(
                        question=question,
                        options=options,
                        category=category,
                        created_by=created_by,
                    )
                    if new_id:
                        st.success("Poll created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create poll. Please try again.")

    # TAB 3: ARCHIVE
    with tab3:
        archived_polls = get_archived_polls()
        st.markdown(f"### Archived Polls ({len(archived_polls)})")

        if not archived_polls:
            st.info("No archived polls found.")
        else:
            for poll in archived_polls:
                with st.expander(f"📁 {poll['question']} ({poll['total_votes']} votes)"):
                    st.caption(f"**Category:** {poll['category']} | **Created by:** {poll['created_by']}")
                    _render_poll_results(poll)


def _render_poll_results(poll: dict) -> None:
    """Render percentage bar results for a poll."""
    total_votes = poll["total_votes"]
    for opt in poll["options"]:
        count = opt["vote_count"]
        pct = (count / total_votes * 100) if total_votes > 0 else 0
        st.write(f"**{opt['option_text']}** — {count} vote(s) ({pct:.1f}%)")
        st.progress(pct / 100.0)
