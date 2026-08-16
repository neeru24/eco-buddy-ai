from achievement_showcase import (
    ShowcaseStats,
    _challenge_progress,
    build_showcase_stats,
)


def test_showcase_statistics_group_completion():
    stats = build_showcase_stats(
        unlocked_badges=[
            {"badge_id": "b1"},
            {"badge_id": "b2"},
            {"badge_id": "unknown"},
        ],
        user_challenges=[
            {"challenge_id": "c1", "status": "completed"},
            {"challenge_id": "c2", "status": "enrolled"},
            {"challenge_id": "unknown", "status": "completed"},
        ],
        milestones=[{"id": 1}, {"id": 2}],
        total_xp=225,
    )

    assert stats == ShowcaseStats(
        earned_badges=2,
        total_badges=4,
        completed_challenges=1,
        total_challenges=5,
        milestones=2,
        total_xp=225,
        level=2,
        overall_completion=0.35,
    )


def test_duplicate_records_are_not_double_counted():
    stats = build_showcase_stats(
        unlocked_badges=[{"badge_id": "b1"}, {"badge_id": "b1"}],
        user_challenges=[
            {"challenge_id": "c1", "status": "completed"},
            {"challenge_id": "c1", "status": "completed"},
        ],
        milestones=[],
        total_xp=0,
    )

    assert stats.earned_badges == 1
    assert stats.completed_challenges == 1


def test_unknown_achievement_ids_are_ignored():
    stats = build_showcase_stats(
        unlocked_badges=[{"badge_id": "does-not-exist"}],
        user_challenges=[
            {"challenge_id": "does-not-exist", "status": "completed"}
        ],
        milestones=[],
        total_xp=-50,
    )

    assert stats.earned_badges == 0
    assert stats.completed_challenges == 0
    assert stats.total_xp == 0
    assert stats.level == 1
    assert stats.overall_completion == 0


def test_challenge_progress_is_bounded_and_handles_states():
    assert _challenge_progress(None, 10) == 0
    assert (
        _challenge_progress(
            {"status": "enrolled", "progress_value": 5},
            10,
        )
        == 0.5
    )
    assert (
        _challenge_progress(
            {"status": "enrolled", "progress_value": 50},
            10,
        )
        == 1.0
    )
    assert (
        _challenge_progress(
            {"status": "completed", "progress_value": 0},
            10,
        )
        == 1.0
    )
