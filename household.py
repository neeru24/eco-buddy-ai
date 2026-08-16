"""Household carbon sharing and per-capita emission allocation.

Every calculator in EcoBuddy AI is single-user, so someone sharing a flat is
charged for the whole home's electricity, water and waste. This module lets a
user define a household, add its members, and split shared emissions fairly
so each person sees an honest per-capita footprint.

Three allocation methods are supported:

``equal``     every member carries the same share
``weighted``  shares follow an occupancy weight (days at home, room size, ...)
``usage``     shares follow per-member usage readings, with any unmeasured
              remainder split equally

All three conserve mass: the allocated shares always sum back to the input
total, with any rounding remainder assigned deterministically to the largest
share.

The module is self-contained: its SQLite tables are created lazily and no
shared files are modified.
"""

import os
import sqlite3
import hashlib
import logging
from typing import Any

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

# Categories that genuinely belong to the whole home and therefore get split.
SHARED_CATEGORIES = {
    "electricity": {"label": "Electricity", "icon": "⚡"},
    "heating": {"label": "Heating & gas", "icon": "🔥"},
    "water": {"label": "Water", "icon": "💧"},
    "waste": {"label": "Waste", "icon": "🗑️"},
    "shared_transport": {"label": "Shared vehicle", "icon": "🚗"},
}

# Categories that stay with the individual who caused them.
PERSONAL_CATEGORIES = {
    "commute": {"label": "Commute", "icon": "🚌"},
    "flights": {"label": "Flights", "icon": "✈️"},
    "diet": {"label": "Diet", "icon": "🍽️"},
    "shopping": {"label": "Shopping", "icon": "🛍️"},
}

ALLOCATION_METHODS = {
    "equal": "Split evenly between everyone",
    "weighted": "Split by occupancy weight",
    "usage": "Split by measured per-member usage",
}

DEFAULT_METHOD = "equal"

MEMBER_ROLES = ["Adult", "Child", "Flatmate", "Guest"]

MIN_WEIGHT = 0.1
MAX_WEIGHT = 10.0
DEFAULT_WEIGHT = 1.0

MAX_MEMBERS = 20

JOIN_CODE_LENGTH = 6
JOIN_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

# Annual per-capita household-related emissions in kg CO2, used to give a
# household context rather than an absolute verdict.
REGIONAL_PER_CAPITA_KG = {
    "Global": 4700.0,
    "US": 14500.0,
    "UK": 5200.0,
    "EU": 6300.0,
    "India": 1900.0,
}


def generate_join_code(seed: Any) -> str:
    """Derive a short, stable, human-friendly join code from a seed value."""
    digest = hashlib.sha256(str(seed).encode("utf-8")).hexdigest()
    number = int(digest[:16], 16)
    code = []
    for _ in range(JOIN_CODE_LENGTH):
        number, index = divmod(number, len(JOIN_CODE_ALPHABET))
        code.append(JOIN_CODE_ALPHABET[index])
    return "".join(code)


def normalize_join_code(code: str) -> str:
    """Normalise user-typed join codes (case, spaces, punctuation)."""
    if not code:
        return ""
    cleaned = "".join(
        char for char in str(code).upper() if char in JOIN_CODE_ALPHABET
    )
    return cleaned[:JOIN_CODE_LENGTH]


def _clean_weight(weight: float) -> float:
    """Clamp an occupancy weight into the allowed range."""
    try:
        value = float(weight)
    except (TypeError, ValueError):
        return DEFAULT_WEIGHT
    if value != value or value in (float("inf"), float("-inf")):
        return DEFAULT_WEIGHT
    return max(MIN_WEIGHT, min(value, MAX_WEIGHT))


def validate_member_weights(members: list[dict[str, Any]]) -> tuple[bool, str]:
    """Validate a member list before it is used for allocation.

    Returns ``(is_valid, message)``.
    """
    if not members:
        return False, "A household needs at least one member."
    if len(members) > MAX_MEMBERS:
        return False, f"A household can hold at most {MAX_MEMBERS} members."

    names = [str(member.get("name", "")).strip().lower() for member in members]
    if any(not name for name in names):
        return False, "Every member needs a name."
    if len(set(names)) != len(names):
        return False, "Member names must be unique within a household."

    for member in members:
        try:
            weight = float(member.get("weight", DEFAULT_WEIGHT))
        except (TypeError, ValueError):
            return False, f"{member.get('name')} has an invalid occupancy weight."
        if weight < MIN_WEIGHT or weight > MAX_WEIGHT:
            return False, (
                f"{member.get('name')}'s weight must be between "
                f"{MIN_WEIGHT} and {MAX_WEIGHT}."
            )

    return True, "Household members look good."


def _distribute(total: float, raw_shares: list[float]) -> list[float]:
    """Scale ``raw_shares`` so they sum exactly to ``total``.

    The rounding remainder is given to the largest share, which keeps the
    allocation deterministic and guarantees conservation of the total.
    """
    total = round(float(total), 2)
    weight_sum = sum(raw_shares)

    if weight_sum <= 0 or not raw_shares:
        even = round(total / len(raw_shares), 2) if raw_shares else 0.0
        shares = [even] * len(raw_shares)
    else:
        shares = [round(total * value / weight_sum, 2) for value in raw_shares]

    if shares:
        remainder = round(total - sum(shares), 2)
        if remainder:
            largest = max(range(len(shares)), key=lambda i: shares[i])
            shares[largest] = round(shares[largest] + remainder, 2)

    return shares


def allocate_shared_emissions(total_kg: float, members: list[dict[str, Any]], method: str = DEFAULT_METHOD, usage: dict[str, Any] | None = None) -> dict[str, float]:
    """Split a shared emission total between household members.

    ``usage`` maps member names to a measured usage value and is only read by
    the ``usage`` method. Members with no reading share the remaining total
    equally.
    """
    members = members or []
    if not members:
        return {}

    method = method if method in ALLOCATION_METHODS else DEFAULT_METHOD
    total_kg = max(0.0, float(total_kg or 0.0))

    if method == "equal":
        raw = [1.0] * len(members)
    elif method == "weighted":
        raw = [_clean_weight(member.get("weight", DEFAULT_WEIGHT)) for member in members]
    else:
        usage = usage or {}
        raw = []
        for member in members:
            try:
                value = float(usage.get(member.get("name"), 0.0))
            except (TypeError, ValueError):
                value = 0.0
            raw.append(max(0.0, value))
        if sum(raw) <= 0:
            raw = [1.0] * len(members)

    shares = _distribute(total_kg, raw)
    return {member["name"]: shares[index] for index, member in enumerate(members)}


def compute_household_footprint(
    members: list[dict[str, Any]],
    shared_inputs: dict[str, Any],
    personal_by_member: dict[str, Any] | None = None,
    method: str = DEFAULT_METHOD,
    usage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the full household breakdown.

    ``shared_inputs`` maps shared category keys to annual kg CO2 for the whole
    home. ``personal_by_member`` maps a member name to that member's own
    personal categories.
    """
    members = members or []
    shared_inputs = shared_inputs or {}
    personal_by_member = personal_by_member or {}

    if not members:
        return {
            "members": [],
            "household_total_kg": 0.0,
            "shared_total_kg": 0.0,
            "personal_total_kg": 0.0,
            "per_capita_kg": 0.0,
            "method": method,
            "shared_by_category": {},
        }

    shared_by_category = {}
    allocations = {member["name"]: {} for member in members}

    for category, amount in shared_inputs.items():
        if category not in SHARED_CATEGORIES:
            continue
        amount = max(0.0, float(amount or 0.0))
        shared_by_category[category] = round(amount, 2)
        split = allocate_shared_emissions(amount, members, method, usage)
        for name, value in split.items():
            allocations[name][category] = value

    member_rows = []
    for member in members:
        name = member["name"]
        shared_total = round(sum(allocations[name].values()), 2)

        personal = {
            key: max(0.0, float(value or 0.0))
            for key, value in (personal_by_member.get(name) or {}).items()
            if key in PERSONAL_CATEGORIES
        }
        personal_total = round(sum(personal.values()), 2)

        member_rows.append(
            {
                "name": name,
                "role": member.get("role", "Adult"),
                "weight": _clean_weight(member.get("weight", DEFAULT_WEIGHT)),
                "shared_kg": shared_total,
                "shared_by_category": allocations[name],
                "personal_kg": personal_total,
                "personal_by_category": personal,
                "total_kg": round(shared_total + personal_total, 2),
            }
        )

    shared_total_kg = round(sum(shared_by_category.values()), 2)
    personal_total_kg = round(sum(row["personal_kg"] for row in member_rows), 2)
    household_total = round(shared_total_kg + personal_total_kg, 2)

    member_rows.sort(key=lambda row: row["total_kg"], reverse=True)

    for row in member_rows:
        row["share_pct"] = (
            round(row["total_kg"] / household_total * 100, 1)
            if household_total > 0
            else 0.0
        )

    return {
        "members": member_rows,
        "member_count": len(member_rows),
        "household_total_kg": household_total,
        "shared_total_kg": shared_total_kg,
        "personal_total_kg": personal_total_kg,
        "per_capita_kg": round(household_total / len(member_rows), 2),
        "shared_pct": (
            round(shared_total_kg / household_total * 100, 1)
            if household_total > 0
            else 0.0
        ),
        "method": method if method in ALLOCATION_METHODS else DEFAULT_METHOD,
        "shared_by_category": shared_by_category,
    }


def rank_members(breakdown: dict[str, Any]) -> list[dict[str, Any]]:
    """Rank members against the household average."""
    members = breakdown.get("members", [])
    if not members:
        return []

    average = breakdown.get("per_capita_kg", 0.0)
    ranked = []
    for position, member in enumerate(
        sorted(members, key=lambda row: row["total_kg"], reverse=True), start=1
    ):
        gap = round(member["total_kg"] - average, 2)
        ranked.append(
            {
                "position": position,
                "name": member["name"],
                "total_kg": member["total_kg"],
                "gap_kg": gap,
                "gap_pct": round(gap / average * 100, 1) if average > 0 else 0.0,
                "above_average": gap > 0,
            }
        )
    return ranked


def household_insights(breakdown: dict[str, Any], limit: int = 4) -> list[str]:
    """Generate plain-language observations about a household breakdown."""
    if not breakdown.get("members"):
        return ["Add household members to see how your emissions split."]

    insights = []
    shared_by_category = breakdown.get("shared_by_category", {})

    if shared_by_category and breakdown["household_total_kg"] > 0:
        top_key = max(shared_by_category, key=shared_by_category.get)
        top_value = shared_by_category[top_key]
        share = top_value / breakdown["household_total_kg"] * 100
        label = SHARED_CATEGORIES[top_key]["label"]
        insights.append(
            f"Shared {label.lower()} is {share:.0f}% of the household total - "
            f"a change here helps everyone at once."
        )

    if breakdown["shared_pct"] >= 50:
        insights.append(
            f"{breakdown['shared_pct']}% of your household's footprint is shared, "
            f"so household-level decisions matter more than individual ones."
        )
    elif breakdown["household_total_kg"] > 0:
        insights.append(
            f"Only {breakdown['shared_pct']}% of the total is shared - most of the "
            f"footprint comes from individual habits."
        )

    ranked = rank_members(breakdown)
    if len(ranked) >= 2 and ranked[0]["gap_kg"] > 0:
        insights.append(
            f"{ranked[0]['name']} is {ranked[0]['gap_kg']:.0f} kg above the household "
            f"average of {breakdown['per_capita_kg']:.0f} kg."
        )

    if breakdown["member_count"] > 1:
        solo = breakdown["household_total_kg"]
        insights.append(
            f"Sharing a home cuts each person's footprint from {solo:,.0f} kg to "
            f"{breakdown['per_capita_kg']:,.0f} kg - that saving is real, not an accounting trick."
        )

    return insights[: max(0, int(limit))]


def per_capita_vs_national(per_capita_kg: float, region: str = "Global") -> dict[str, Any]:
    """Compare a household's per-capita footprint to a regional average."""
    baseline = REGIONAL_PER_CAPITA_KG.get(region, REGIONAL_PER_CAPITA_KG["Global"])
    per_capita_kg = max(0.0, float(per_capita_kg or 0.0))
    difference = per_capita_kg - baseline

    return {
        "region": region if region in REGIONAL_PER_CAPITA_KG else "Global",
        "baseline_kg": baseline,
        "per_capita_kg": round(per_capita_kg, 2),
        "difference_kg": round(difference, 2),
        "difference_pct": round(difference / baseline * 100, 1) if baseline else 0.0,
        "below_average": difference < 0,
    }


def _get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_household_db() -> bool:
    """Create the household tables if they do not exist yet."""
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS households (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                owner_user_id INTEGER NOT NULL,
                join_code TEXT UNIQUE NOT NULL,
                allocation_method TEXT NOT NULL DEFAULT 'equal',
                region TEXT NOT NULL DEFAULT 'Global',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS household_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                household_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                user_id INTEGER,
                weight REAL NOT NULL DEFAULT 1.0,
                role TEXT NOT NULL DEFAULT 'Adult',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(household_id, name)
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Household init error: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def create_household(name: str, owner_user_id: int, method: str = DEFAULT_METHOD, region: str = "Global") -> int | None:
    """Create a household owned by ``owner_user_id``. Returns the new row id."""
    init_household_db()
    conn = None
    try:
        conn = _get_conn()
        # A temporary unique placeholder keeps the UNIQUE constraint valid
        # until the real code can be derived from the new row id.
        cursor = conn.execute(
            """
            INSERT INTO households (name, owner_user_id, join_code, allocation_method, region)
            VALUES (?, ?, hex(randomblob(8)), ?, ?)
            """,
            (
                (name or "My household").strip(),
                owner_user_id,
                method if method in ALLOCATION_METHODS else DEFAULT_METHOD,
                region if region in REGIONAL_PER_CAPITA_KG else "Global",
            ),
        )
        household_id = cursor.lastrowid

        # The join code is derived from the row id so it is unique and stable.
        code = generate_join_code(f"{household_id}-{owner_user_id}")
        conn.execute(
            "UPDATE households SET join_code = ? WHERE id = ?", (code, household_id)
        )
        conn.commit()
        return household_id
    except sqlite3.Error as exc:
        logger.error("Unable to create household: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def get_household(household_id: int) -> dict[str, Any] | None:
    """Return a household row plus its members, or None."""
    init_household_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT id, name, owner_user_id, join_code, allocation_method,
                   region, created_at
            FROM households WHERE id = ?
            """,
            (household_id,),
        ).fetchone()
        if not row:
            return None
        household = dict(row)
        household["members"] = get_members(household_id)
        return household
    except sqlite3.Error as exc:
        logger.error("Unable to load household: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def get_household_by_code(code: str) -> dict[str, Any] | None:
    """Find a household by its join code, however the user typed it."""
    init_household_db()
    normalized = normalize_join_code(code)
    if len(normalized) != JOIN_CODE_LENGTH:
        return None

    conn = None
    try:
        conn = _get_conn()
        row = conn.execute(
            "SELECT id FROM households WHERE join_code = ?", (normalized,)
        ).fetchone()
        return get_household(row[0]) if row else None
    except sqlite3.Error as exc:
        logger.error("Unable to look up household by code: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def get_households_for_user(user_id: int) -> list[dict[str, Any]]:
    """Return every household a user owns or belongs to."""
    init_household_db()
    conn = None
    try:
        conn = _get_conn()
        rows = conn.execute(
            """
            SELECT DISTINCT h.id
            FROM households h
            LEFT JOIN household_members m ON m.household_id = h.id
            WHERE h.owner_user_id = ? OR m.user_id = ?
            ORDER BY h.id
            """,
            (user_id, user_id),
        ).fetchall()
        return [get_household(row[0]) for row in rows]
    except sqlite3.Error as exc:
        logger.error("Unable to list households: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def update_household(household_id: int, name: str | None = None, method: str | None = None, region: str | None = None) -> bool:
    """Update a household's name, allocation method or region."""
    init_household_db()
    updates = []
    params = []

    if name is not None and str(name).strip():
        updates.append("name = ?")
        params.append(str(name).strip())
    if method in ALLOCATION_METHODS:
        updates.append("allocation_method = ?")
        params.append(method)
    if region in REGIONAL_PER_CAPITA_KG:
        updates.append("region = ?")
        params.append(region)

    if not updates:
        return False

    conn = None
    try:
        conn = _get_conn()
        params.append(household_id)
        cursor = conn.execute(
            f"UPDATE households SET {', '.join(updates)} WHERE id = ?", params
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as exc:
        logger.error("Unable to update household: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def add_member(household_id: int, name: str, weight: float = DEFAULT_WEIGHT, role: str = "Adult", user_id: int | None = None) -> int | None:
    """Add a member to a household. Names are unique per household."""
    init_household_db()
    name = str(name or "").strip()
    if not name:
        return None
    if len(get_members(household_id)) >= MAX_MEMBERS:
        logger.warning("Household %s is already full", household_id)
        return None

    conn = None
    try:
        conn = _get_conn()
        cursor = conn.execute(
            """
            INSERT INTO household_members (household_id, name, user_id, weight, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                household_id,
                name,
                user_id,
                _clean_weight(weight),
                role if role in MEMBER_ROLES else "Adult",
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        logger.warning("Member %s already exists in household %s", name, household_id)
        return None
    except sqlite3.Error as exc:
        logger.error("Unable to add household member: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def get_members(household_id: int) -> list[dict[str, Any]]:
    """Return a household's members, ordered by name."""
    init_household_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, name, user_id, weight, role, created_at
            FROM household_members
            WHERE household_id = ?
            ORDER BY name
            """,
            (household_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        logger.error("Unable to load household members: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def update_member(member_id: int, weight: float | None = None, role: str | None = None) -> bool:
    """Update a member's occupancy weight or role."""
    init_household_db()
    updates = []
    params = []

    if weight is not None:
        updates.append("weight = ?")
        params.append(_clean_weight(weight))
    if role in MEMBER_ROLES:
        updates.append("role = ?")
        params.append(role)

    if not updates:
        return False

    conn = None
    try:
        conn = _get_conn()
        params.append(member_id)
        cursor = conn.execute(
            f"UPDATE household_members SET {', '.join(updates)} WHERE id = ?", params
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as exc:
        logger.error("Unable to update household member: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def remove_member(member_id: int) -> bool:
    """Remove a single member from a household."""
    init_household_db()
    conn = None
    try:
        conn = _get_conn()
        cursor = conn.execute(
            "DELETE FROM household_members WHERE id = ?", (member_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as exc:
        logger.error("Unable to remove household member: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def join_household(code: str, user_id: int, display_name: str) -> tuple[bool, str]:
    """Join an existing household by code. Returns ``(success, message)``."""
    household = get_household_by_code(code)
    if not household:
        return False, "No household found with that code."

    display_name = str(display_name or "").strip()
    if not display_name:
        return False, "Please provide a display name."

    for member in household["members"]:
        if member["user_id"] == user_id:
            return False, "You are already part of this household."
        if member["name"].lower() == display_name.lower():
            return False, "That name is already taken in this household."

    if add_member(household["id"], display_name, user_id=user_id) is None:
        return False, "Could not join this household."

    return True, f"You joined {household['name']}."


def delete_household(household_id: int) -> bool:
    """Delete a household and all of its members."""
    init_household_db()
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            "DELETE FROM household_members WHERE household_id = ?", (household_id,)
        )
        cursor = conn.execute("DELETE FROM households WHERE id = ?", (household_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as exc:
        logger.error("Unable to delete household: %s", exc)
        return False
    finally:
        if conn:
            conn.close()
