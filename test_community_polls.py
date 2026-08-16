"""Unit tests for Community Polls functionality."""

from database import (
    init_community_polls_db,
    seed_community_polls,
    get_active_polls,
    get_archived_polls,
    create_poll,
    vote_poll,
    has_user_voted,
    archive_poll,
)


def test_init_and_seed_polls():
    """Verify initialization and seeding of community polls."""
    assert init_community_polls_db() is True
    seed_community_polls()

    active = get_active_polls()
    archived = get_archived_polls()

    assert len(active) >= 2
    assert len(archived) >= 1


def test_create_and_vote_poll():
    """Verify creating a new poll and voting anonymously."""
    poll_id = create_poll(
        question="Should cities ban gas-powered leaf blowers?",
        options=["Yes, ban them", "No, keep them", "Undecided"],
        category="Policy",
        created_by="UnitTester",
    )
    assert poll_id is not None

    user_token = "tester_user_999"
    assert has_user_voted(poll_id, user_token) is False

    active_polls = get_active_polls()
    target_poll = next(p for p in active_polls if p["id"] == poll_id)
    opt_id = target_poll["options"][0]["id"]

    voted = vote_poll(poll_id, opt_id, user_token)
    assert voted is True
    assert has_user_voted(poll_id, user_token) is True

    # Duplicate vote attempt should fail
    duplicate_vote = vote_poll(poll_id, opt_id, user_token)
    assert duplicate_vote is False


def test_archive_poll():
    """Verify archiving an active poll."""
    poll_id = create_poll(
        question="Temporary test poll for archiving",
        options=["Option A", "Option B"],
        category="General",
    )
    assert poll_id is not None

    archived = archive_poll(poll_id)
    assert archived is True

    archived_polls = get_archived_polls()
    archived_ids = [p["id"] for p in archived_polls]
    assert poll_id in archived_ids
