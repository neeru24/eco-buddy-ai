"""Community Eco-Teams & Group Footprint Challenges.

Social layer where users form eco-teams (family, workplace, classmates)
working toward shared emissions-reduction goals. Features:
  - Create/join teams with invite codes, role-based permissions (owner, member)
  - Aggregate individual assessments into team footprint with per-capita normalization
  - Team challenges with collective progress tracking
  - Team XP & badges distributed to contributing members
  - Team leaderboards + within-team contributions view
  - Integrates with existing gamification (personal streaks/missions count toward team)

Self-contained SQLite tables, no shared file modifications.
"""

import os
import json
import logging
import sqlite3
import secrets
import datetime
from typing import Any

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

TEAM_ROLES = {"owner": 2, "member": 1}
TEAM_CHALLENGE_TYPES = {
    "reduce_transport": {"title": "Cut Transport Emissions", "unit": "kg CO₂e", "icon": "🚌"},
    "reduce_energy": {"title": "Cut Home Energy", "unit": "kWh", "icon": "💡"},
    "increase_recycling": {"title": "Boost Recycling Rate", "unit": "%", "icon": "♻️"},
    "weekly_logging": {"title": "Weekly Logging Streak", "unit": "weeks", "icon": "📅"},
    "plant_based_days": {"title": "Plant-Based Days", "unit": "days", "icon": "🥗"},
}


def _get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_teams_db() -> bool:
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS eco_teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                invite_code TEXT UNIQUE NOT NULL,
                owner_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS team_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(team_id, user_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS team_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                challenge_type TEXT NOT NULL,
                target_value REAL NOT NULL,
                current_value REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ends_at TIMESTAMP,
                completed_at TIMESTAMP,
                reward_xp INTEGER NOT NULL DEFAULT 50,
                FOREIGN KEY (team_id) REFERENCES eco_teams (id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS team_member_contributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                challenge_id INTEGER,
                metric_type TEXT NOT NULL,
                value REAL NOT NULL,
                xp_awarded INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (team_id) REFERENCES eco_teams (id),
                FOREIGN KEY (challenge_id) REFERENCES team_challenges (id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS team_badges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                badge_key TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (team_id) REFERENCES eco_teams (id)
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Teams init error: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def _generate_invite_code() -> str:
    return secrets.token_urlsafe(8)[:8].upper()


def create_team(owner_id: int, name: str, description: str = "") -> dict[str, Any] | None:
    init_teams_db()
    invite_code = _generate_invite_code()
    conn = None
    try:
        conn = _get_conn()
        cursor = conn.execute(
            "INSERT INTO eco_teams (name, description, invite_code, owner_id) "
            "VALUES (?, ?, ?, ?)",
            (name, description, invite_code, owner_id),
        )
        team_id = cursor.lastrowid
        conn.execute(
            "INSERT INTO team_members (team_id, user_id, role) VALUES (?, ?, 'owner')",
            (team_id, owner_id),
        )
        conn.commit()
        return {"id": team_id, "name": name, "invite_code": invite_code}
    except sqlite3.Error as exc:
        logger.error("Create team error: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def join_team(user_id: int, invite_code: str) -> tuple[bool, str]:
    init_teams_db()
    conn = None
    try:
        conn = _get_conn()
        team = conn.execute(
            "SELECT id, name FROM eco_teams WHERE invite_code = ?", (invite_code.upper(),)
        ).fetchone()
        if not team:
            return False, "Invalid invite code."
        team_id, name = team
        exists = conn.execute(
            "SELECT 1 FROM team_members WHERE team_id = ? AND user_id = ?",
            (team_id, user_id),
        ).fetchone()
        if exists:
            return False, "You're already a member of this team."
        conn.execute(
            "INSERT INTO team_members (team_id, user_id, role) VALUES (?, ?, 'member')",
            (team_id, user_id),
        )
        conn.commit()
        return True, f"Joined team '{name}'!"
    except sqlite3.Error as exc:
        logger.error("Join team error: %s", exc)
        return False, "Could not join team."
    finally:
        if conn:
            conn.close()


def leave_team(user_id: int, team_id: int) -> tuple[bool, str]:
    init_teams_db()
    conn = None
    try:
        conn = _get_conn()
        role = conn.execute(
            "SELECT role FROM team_members WHERE team_id = ? AND user_id = ?",
            (team_id, user_id),
        ).fetchone()
        if not role:
            return False, "Not a member of this team."
        if role[0] == "owner":
            # Owner must transfer ownership or delete team
            return False, "Owner cannot leave — transfer ownership or delete the team."
        conn.execute(
            "DELETE FROM team_members WHERE team_id = ? AND user_id = ?",
            (team_id, user_id),
        )
        conn.commit()
        return True, "Left the team."
    except sqlite3.Error as exc:
        logger.error("Leave team error: %s", exc)
        return False, "Could not leave team."
    finally:
        if conn:
            conn.close()


def get_user_teams(user_id: int) -> list[dict[str, Any]]:
    init_teams_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT t.id, t.name, t.description, t.invite_code, t.owner_id,
                   tm.role, t.created_at
            FROM eco_teams t
            JOIN team_members tm ON tm.team_id = t.id
            WHERE tm.user_id = ?
            ORDER BY t.created_at DESC
            """,
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        logger.error("Get user teams error: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def get_team_members(team_id: int) -> list[dict[str, Any]]:
    init_teams_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT tm.user_id, tm.role, tm.joined_at
            FROM team_members tm
            WHERE tm.team_id = ?
            ORDER BY tm.role DESC, tm.joined_at ASC
            """,
            (team_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        logger.error("Get team members error: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def get_team_info(team_id: int) -> dict[str, Any] | None:
    init_teams_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM eco_teams WHERE id = ?", (team_id,)
        ).fetchone()
        return dict(row) if row else None
    except sqlite3.Error as exc:
        logger.error("Get team info error: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def _get_user_latest_footprint(user_id: int) -> dict[str, Any] | None:
    """Get latest carbon footprint from assessments."""
    from database import get_assessments
    assessments = get_assessments(user_id, limit=1)
    if not assessments:
        return None
    a = assessments[0]
    return {
        "total_kg": float(a.get("total_footprint", a.get("footprint", 0))),
        "transport_kg": float(a.get("transport_footprint", 0)),
        "energy_kg": float(a.get("electricity_footprint", 0)),
        "date": a.get("created_at"),
    }


def _get_user_latest_waste(user_id: int) -> dict[str, Any] | None:
    from database import get_waste_assessments
    waste = get_waste_assessments(user_id)
    if not waste:
        return None
    w = waste[0]
    return {
        "weekly_kg": float(w.get("total_weekly_kg", 0)),
        "recyclable_pct": float(w.get("recyclable_pct", 0)),
        "annual_co2": float(w.get("annual_co2", 0)),
    }


def _get_user_water_logging(user_id: int) -> dict[str, Any] | None:
    from database import get_water_assessments
    water = get_water_assessments(user_id, limit=1)
    if not water:
        return None
    w = water[0]
    return {"weekly_liters": float(w.get("total_liters", 0)) * 7}


def get_team_footprint(team_id: int) -> dict[str, Any]:
    """Aggregate team footprint with per-capita normalization."""
    members = get_team_members(team_id)
    if not members:
        return {"members": 0, "total_footprint_kg": 0, "per_capita_kg": 0,
                "transport_kg": 0, "energy_kg": 0, "waste_kg": 0, "water_liters": 0}

    totals = {"total": 0.0, "transport": 0.0, "energy": 0.0, "waste": 0.0, "water": 0.0}
    count = 0

    for m in members:
        fp = _get_user_latest_footprint(m["user_id"])
        if fp:
            totals["total"] += fp["total_kg"]
            totals["transport"] += fp["transport_kg"]
            totals["energy"] += fp["energy_kg"]
            count += 1
        waste = _get_user_latest_waste(m["user_id"])
        if waste:
            totals["waste"] += waste["annual_co2"] / 52  # weekly CO2e from waste
        water = _get_user_water_logging(m["user_id"])
        if water:
            totals["water"] += water["weekly_liters"]

    n = max(count, 1)
    return {
        "members": len(members),
        "total_footprint_kg": round(totals["total"], 1),
        "per_capita_kg": round(totals["total"] / n, 1),
        "transport_kg": round(totals["transport"], 1),
        "energy_kg": round(totals["energy"], 1),
        "waste_kg": round(totals["waste"], 1),
        "water_liters": round(totals["water"], 1),
        "contributions": {
            m["user_id"]: {
                "footprint_kg": round(
                    (_get_user_latest_footprint(m["user_id"]) or {}).get("total_kg", 0), 1
                ),
                "waste_kg": round(
                    (_get_user_latest_waste(m["user_id"]) or {}).get("annual_co2", 0) / 52, 1
                ),
            }
            for m in members
        },
    }


def create_team_challenge(
    team_id: int,
    challenge_type: str,
    target_value: float,
    days: int = 7,
    reward_xp: int = 100,
) -> dict[str, Any] | None:
    init_teams_db()
    if challenge_type not in TEAM_CHALLENGE_TYPES:
        return None
    conn = None
    try:
        conn = _get_conn()
        ends_at = (datetime.datetime.now() + datetime.timedelta(days=days)).isoformat()
        cursor = conn.execute(
            """
            INSERT INTO team_challenges (team_id, challenge_type, target_value, ends_at, reward_xp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (team_id, challenge_type, target_value, ends_at, reward_xp),
        )
        challenge_id = cursor.lastrowid
        conn.commit()
        return {
            "id": challenge_id,
            "team_id": team_id,
            "type": challenge_type,
            "target": target_value,
            "ends_at": ends_at,
            "reward_xp": reward_xp,
        }
    except sqlite3.Error as exc:
        logger.error("Create team challenge error: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def get_team_challenges(team_id: int, status: str | None = None) -> list[dict[str, Any]]:
    init_teams_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        if status:
            rows = conn.execute(
                "SELECT * FROM team_challenges WHERE team_id = ? AND status = ? ORDER BY started_at DESC",
                (team_id, status),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM team_challenges WHERE team_id = ? ORDER BY started_at DESC",
                (team_id,),
            ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        logger.error("Get team challenges error: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def update_challenge_progress(team_id: int, challenge_id: int, user_id: int, value: float) -> bool:
    """Record a member's contribution and update challenge progress."""
    init_teams_db()
    conn = None
    try:
        conn = _get_conn()
        # Record individual contribution
        conn.execute(
            """
            INSERT INTO team_member_contributions (team_id, user_id, challenge_id, metric_type, value)
            VALUES (?, ?, ?, ?, ?)
            """,
            (team_id, user_id, challenge_id, "progress", value),
        )
        # Sum all contributions for this challenge
        total = conn.execute(
            "SELECT SUM(value) FROM team_member_contributions WHERE challenge_id = ?",
            (challenge_id,),
        ).fetchone()[0] or 0.0

        # Get challenge target
        challenge = conn.execute(
            "SELECT target_value, reward_xp, status FROM team_challenges WHERE id = ?",
            (challenge_id,),
        ).fetchone()
        if not challenge:
            return False
        target, reward_xp, status = challenge
        if status != "active":
            return False

        new_status = "active"
        completed_at = None
        if total >= target:
            new_status = "completed"
            completed_at = datetime.datetime.now().isoformat()

        conn.execute(
            "UPDATE team_challenges SET current_value = ?, status = ?, completed_at = ? WHERE id = ?",
            (total, new_status, completed_at, challenge_id),
        )

        if new_status == "completed":
            # Award XP to all contributors
            contributors = conn.execute(
                "SELECT DISTINCT user_id FROM team_member_contributions WHERE challenge_id = ?",
                (challenge_id,),
            ).fetchall()
            for (uid,) in contributors:
                from database import award_xp
                award_xp(uid, "team_challenge", str(challenge_id), reward_xp,
                         f"Team challenge completed: {total:.1f}/{target:.1f}")
                # Record XP awarded
                conn.execute(
                    "UPDATE team_member_contributions SET xp_awarded = ? "
                    "WHERE challenge_id = ? AND user_id = ?",
                    (reward_xp, challenge_id, uid),
                )
            # Award team badge
            from ai_waste_sorter import WASTE_CATEGORIES  # import to avoid circular
            conn.execute(
                "INSERT INTO team_badges (team_id, badge_key, name, description) "
                "VALUES (?, ?, ?, ?)",
                (team_id, f"challenge_{challenge_id}",
                 f"Completed {TEAM_CHALLENGE_TYPES.get(challenge[2], {}).get('title', 'Challenge')}",
                 f"Team reached {total:.1f}/{target:.1f} {TEAM_CHALLENGE_TYPES.get(challenge[2], {}).get('unit', '')}"),
            )

        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Update challenge progress error: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def get_team_leaderboard() -> list[dict[str, Any]]:
    """Global team leaderboard by per-capita footprint (lower is better)."""
    init_teams_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, name, invite_code, owner_id, created_at FROM eco_teams ORDER BY id ASC"
        ).fetchall()
        teams = []
        for row in rows:
            fp = get_team_footprint(row["id"])
            if fp["members"] > 0:
                teams.append({
                    "id": row["id"],
                    "name": row["name"],
                    "members": fp["members"],
                    "per_capita_kg": fp["per_capita_kg"],
                    "total_footprint_kg": fp["total_footprint_kg"],
                })
        teams.sort(key=lambda t: t["per_capita_kg"])
        return teams
    except sqlite3.Error as exc:
        logger.error("Get team leaderboard error: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def get_within_team_contributions(team_id: int) -> list[dict[str, Any]]:
    """Individual contributions ranked within the team."""
    fp = get_team_footprint(team_id)
    contribs = fp.get("contributions", {})
    members = get_team_members(team_id)
    result = []
    for m in members:
        c = contribs.get(m["user_id"], {"footprint_kg": 0, "waste_kg": 0})
        result.append({
            "user_id": m["user_id"],
            "role": m["role"],
            "footprint_kg": c["footprint_kg"],
            "waste_kg": c["waste_kg"],
            "total_contribution_kg": round(c["footprint_kg"] + c["waste_kg"], 1),
        })
    result.sort(key=lambda x: x["total_contribution_kg"])
    return result


def get_team_badges(team_id: int) -> list[dict[str, Any]]:
    init_teams_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM team_badges WHERE team_id = ? ORDER BY earned_at DESC",
            (team_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        logger.error("Get team badges error: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def transfer_ownership(team_id: int, current_owner_id: int, new_owner_id: int) -> tuple[bool, str]:
    init_teams_db()
    conn = None
    try:
        conn = _get_conn()
        role = conn.execute(
            "SELECT role FROM team_members WHERE team_id = ? AND user_id = ?",
            (team_id, current_owner_id),
        ).fetchone()
        if not role or role[0] != "owner":
            return False, "Only the owner can transfer ownership."
        is_member = conn.execute(
            "SELECT 1 FROM team_members WHERE team_id = ? AND user_id = ?",
            (team_id, new_owner_id),
        ).fetchone()
        if not is_member:
            return False, "New owner must be a current member."
        conn.execute(
            "UPDATE eco_teams SET owner_id = ? WHERE id = ?",
            (new_owner_id, team_id),
        )
        conn.execute(
            "UPDATE team_members SET role = 'owner' WHERE team_id = ? AND user_id = ?",
            (team_id, new_owner_id),
        )
        conn.execute(
            "UPDATE team_members SET role = 'member' WHERE team_id = ? AND user_id = ?",
            (team_id, current_owner_id),
        )
        conn.commit()
        return True, "Ownership transferred."
    except sqlite3.Error as exc:
        logger.error("Transfer ownership error: %s", exc)
        return False, "Could not transfer ownership."
    finally:
        if conn:
            conn.close()