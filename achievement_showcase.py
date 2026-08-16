"""Achievement showcase data helpers and Streamlit renderer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import streamlit as st

from database import (
    get_environmental_milestones,
    get_total_xp,
    get_unlocked_badges,
    get_user_challenges,
)
from gamification import BADGES, CHALLENGES, calculate_level, calculate_level_progress


BADGE_ICONS: Mapping[str, str] = {
    "b1": "🌱",
    "b2": "🔥",
    "b3": "🏆",
    "b4": "🥗",
}

CHALLENGE_ICONS: Mapping[str, str] = {
    "Transport": "🚲",
    "Diet": "🥗",
    "Energy": "⚡",
    "General": "🌍",
}


@dataclass(frozen=True)
class ShowcaseStats:
    """Aggregated completion statistics for the showcase header."""

    earned_badges: int
    total_badges: int
    completed_challenges: int
    total_challenges: int
    milestones: int
    total_xp: int
    level: int
    overall_completion: float


def _clamp_progress(value: float) -> float:
    return max(0.0, min(1.0, value))


def build_showcase_stats(
    unlocked_badges: Sequence[Mapping[str, object]],
    user_challenges: Sequence[Mapping[str, object]],
    milestones: Sequence[Mapping[str, object]],
    total_xp: int,
) -> ShowcaseStats:
    """Build deterministic completion statistics from achievement records."""
    unlocked_ids = {
        str(item.get("badge_id"))
        for item in unlocked_badges
        if item.get("badge_id") in BADGES
    }
    completed_ids = {
        str(item.get("challenge_id"))
        for item in user_challenges
        if item.get("challenge_id") in CHALLENGES
        and item.get("status") == "completed"
    }

    badge_ratio = len(unlocked_ids) / len(BADGES) if BADGES else 1.0
    challenge_ratio = (
        len(completed_ids) / len(CHALLENGES) if CHALLENGES else 1.0
    )
    overall = _clamp_progress((badge_ratio + challenge_ratio) / 2)

    return ShowcaseStats(
        earned_badges=len(unlocked_ids),
        total_badges=len(BADGES),
        completed_challenges=len(completed_ids),
        total_challenges=len(CHALLENGES),
        milestones=len(milestones),
        total_xp=max(0, int(total_xp or 0)),
        level=calculate_level(max(0, int(total_xp or 0))),
        overall_completion=overall,
    )


def _challenge_progress(
    challenge: Mapping[str, object] | None,
    target: float,
) -> float:
    if not challenge:
        return 0.0
    if challenge.get("status") == "completed":
        return 1.0
    try:
        current = float(challenge.get("progress_value", 0) or 0)
    except (TypeError, ValueError):
        current = 0.0
    return _clamp_progress(current / target if target > 0 else 0.0)


def _safe_date(value: object) -> str:
    text = str(value or "")
    return text[:10] if text else "Not recorded"


def _render_header(stats: ShowcaseStats) -> None:
    st.markdown(
        """
        <div style="
            border-radius: 24px;
            padding: 28px;
            margin-bottom: 18px;
            background:
              radial-gradient(circle at top right, rgba(250,204,21,.28), transparent 38%),
              linear-gradient(135deg, rgba(22,163,74,.18), rgba(14,165,233,.12));
            border: 1px solid rgba(34,197,94,.25);
        ">
          <div style="font-size: 13px; font-weight: 800; letter-spacing: .12em;
                      color: #15803d;">SUSTAINABILITY ACHIEVEMENTS</div>
          <div style="font-size: 34px; font-weight: 900; margin-top: 4px;">
            Your impact deserves a spotlight
          </div>
          <div style="opacity: .72; margin-top: 6px;">
            Explore earned badges, completed challenges, milestone history,
            and progress towards your next achievement.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    first, second, third, fourth = st.columns(4)
    first.metric("Badges earned", f"{stats.earned_badges}/{stats.total_badges}")
    second.metric(
        "Challenges completed",
        f"{stats.completed_challenges}/{stats.total_challenges}",
    )
    third.metric("Impact milestones", stats.milestones)
    fourth.metric("Total XP", stats.total_xp)

    st.markdown(
        f"**Overall showcase completion — {stats.overall_completion * 100:.0f}%**"
    )
    st.progress(stats.overall_completion)

    level_progress = _clamp_progress(calculate_level_progress(stats.total_xp))
    st.caption(
        f"Level {stats.level} progress · {level_progress * 100:.0f}% towards "
        f"Level {stats.level + 1}"
    )
    st.progress(level_progress)


def _render_badges(
    unlocked_badges: Sequence[Mapping[str, object]],
) -> None:
    st.subheader("🏅 Badge collection")
    unlocked_by_id = {
        str(item.get("badge_id")): item for item in unlocked_badges
    }

    columns = st.columns(2)
    for index, (badge_id, definition) in enumerate(BADGES.items()):
        unlocked = badge_id in unlocked_by_id
        record = unlocked_by_id.get(badge_id, {})
        icon = BADGE_ICONS.get(badge_id, "🏅")
        state = "UNLOCKED" if unlocked else "LOCKED"
        border = "#22c55e" if unlocked else "#94a3b8"
        background = (
            "rgba(34,197,94,.10)" if unlocked else "rgba(148,163,184,.08)"
        )
        date = (
            f"Unlocked {_safe_date(record.get('unlocked_at'))}"
            if unlocked
            else "Keep building sustainable habits"
        )

        with columns[index % 2]:
            st.markdown(
                f"""
                <div style="
                    min-height: 178px;
                    margin-bottom: 14px;
                    padding: 18px;
                    border-radius: 18px;
                    border: 1px solid {border};
                    background: {background};
                    opacity: {1 if unlocked else .68};
                ">
                  <div style="font-size: 34px;">{icon}</div>
                  <div style="font-size: 11px; font-weight: 900;
                              letter-spacing: .10em; color: {border};">
                    {state}
                  </div>
                  <div style="font-size: 19px; font-weight: 850; margin-top: 4px;">
                    {definition["name"]}
                  </div>
                  <div style="opacity: .72; margin-top: 4px;">
                    {definition["desc"]}
                  </div>
                  <div style="font-size: 12px; opacity: .58; margin-top: 10px;">
                    {date} · +{definition.get("xp", 0)} XP
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_challenges(
    user_challenges: Sequence[Mapping[str, object]],
) -> None:
    st.subheader("🎯 Challenge progress")
    records = {
        str(item.get("challenge_id")): item for item in user_challenges
    }

    for challenge_id, definition in CHALLENGES.items():
        record = records.get(challenge_id)
        progress = _challenge_progress(record, float(definition["target"]))
        status = str(record.get("status", "not started")) if record else "not started"
        icon = CHALLENGE_ICONS.get(definition["category"], "🌍")

        left, right = st.columns([4, 1])
        with left:
            st.markdown(
                f"**{icon} {definition['title']}**  \n"
                f"{definition['category']} · Target: {definition['target']} "
                f"{definition['unit']} · +{definition['xp']} XP"
            )
            st.progress(progress)
            st.caption(
                f"{progress * 100:.0f}% complete · Status: {status.title()}"
            )
        with right:
            if status == "completed":
                st.success("Completed")
            elif record:
                st.info("In progress")
            else:
                st.warning("Not started")


def _render_milestones(
    milestones: Sequence[Mapping[str, object]],
) -> None:
    st.subheader("🌍 Environmental milestones")

    if not milestones:
        st.info(
            "No environmental milestones yet. Complete a footprint assessment "
            "to begin your impact timeline."
        )
        return

    for index, milestone in enumerate(milestones):
        latest = index == 0
        accent = "#16a34a" if latest else "#64748b"
        label = "LATEST ACHIEVEMENT" if latest else "ACHIEVEMENT"

        st.markdown(
            f"""
            <div style="
                margin: 0 0 12px 14px;
                padding: 15px 18px;
                border-left: 4px solid {accent};
                border-radius: 0 14px 14px 0;
                background: rgba(34,197,94,.07);
            ">
              <div style="font-size: 11px; font-weight: 900;
                          letter-spacing: .09em; color: {accent};">
                {label}
              </div>
              <div style="font-size: 18px; font-weight: 850; margin-top: 3px;">
                {milestone.get("icon", "🌱")}
                {milestone.get("title", "Sustainability milestone")}
              </div>
              <div style="opacity: .72; margin-top: 3px;">
                {milestone.get("description", "")}
              </div>
              <div style="font-size: 12px; opacity: .56; margin-top: 8px;">
                {_safe_date(milestone.get("achieved_at"))}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_achievement_showcase(user_id: int) -> None:
    """Render the complete sustainability achievement dashboard."""
    unlocked_badges = get_unlocked_badges(user_id)
    user_challenges = get_user_challenges(user_id)
    milestones = get_environmental_milestones(user_id)
    total_xp = get_total_xp(user_id)

    stats = build_showcase_stats(
        unlocked_badges,
        user_challenges,
        milestones,
        total_xp,
    )
    _render_header(stats)

    badge_tab, challenge_tab, milestone_tab = st.tabs(
        ["Badges", "Challenges", "Milestones"]
    )
    with badge_tab:
        _render_badges(unlocked_badges)
    with challenge_tab:
        _render_challenges(user_challenges)
    with milestone_tab:
        _render_milestones(milestones)
