"""Rebound effect: what is left of a saving after take-back.

Every saving the app projects is a gross saving. It assumes the user does
exactly as much of the activity afterwards as before, and that the money
saved evaporates. Neither is true.

Direct rebound
--------------
When an energy service gets cheaper to deliver, people consume more of it.
Insulate a cold house and the occupants do not bank the whole saving - a good
part goes into a warmer house. That is a real welfare gain and a real
reduction in the projected saving, and it is largest exactly where the app's
advice is strongest.

It is not a flat percentage. The take-back depends on how far the household
is from satiation for that service: heating a cold home has high rebound,
heating an already-comfortable home has very little. Same measure, different
households, different answers - which is why this module models an elasticity
against a satiation level rather than applying a haircut.

Indirect rebound
----------------
Money not spent on gas does not disappear. It is spent on something else, and
that something else has a carbon intensity. Save 400 currency units a year on
heating and spend it on a flight and the net effect can be **negative**: the
efficiency measure increased the footprint. The app cannot represent that
today, so it reports the gross saving with full confidence.

Where this bites in code that is already merged
-----------------------------------------------
*   ``carbon_payback.py`` divides embodied carbon by an annual saving. Overstate
    the saving by 20% and the payback period is understated by the same
    proportion - and payback periods decide whether a purchase happens.
*   ``lifestyle_optimizer.py`` ranks actions by projected saving. Rebound
    differs by a factor of three between action types, so the *ranking*
    changes, not just the magnitudes.
*   ``goals.py`` sets targets against gross projections, which makes them
    quietly unachievable and makes the user look like the reason.

The correction has a direction
------------------------------
Actions with high rebound are the ones the app currently ranks highest,
because gross savings look biggest there. Correcting for it promotes avoided
consumption - a flight not taken has almost no direct take-back - over
efficiency measures that quietly give a third of it back.

One asymmetry worth keeping
---------------------------
For a household that was under-consuming an energy service (under-heating for
cost reasons), the rebound is not a loss. It is the improvement in living
conditions the measure was supposed to deliver. Reporting it as a shortfall
would be wrong, so it is labelled as a benefit taken in comfort rather than
in carbon.

Self-contained: standard library only, SQLite tables created lazily, no
shared files modified.
"""

import os
import json
import sqlite3
import logging
from typing import Any

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

# Action types, with the elasticity of demand for the underlying service and
# the range the literature reports. `elasticity` is the share of a cost
# reduction taken back as extra consumption by a household at the reference
# satiation level; `low` and `high` bound the sensitivity analysis.
#
# The variation between these rows is the useful signal. A flat average
# across them would give roughly the right total and completely wrong
# rankings, which is the opposite of what this module is for.
ACTION_TYPES = {
    "space_heating": {
        "elasticity": 0.25, "low": 0.10, "high": 0.45,
        "satiation_sensitive": True,
        "label": "Space heating",
        "note": "The classic case, and the largest direct rebound in "
                "domestic energy. A colder home before the measure means "
                "more of the saving is taken as warmth.",
    },
    "water_heating": {
        "elasticity": 0.15, "low": 0.05, "high": 0.30,
        "satiation_sensitive": True,
        "label": "Water heating",
        "note": "Longer showers, more hot washes. Real but smaller than "
                "space heating.",
    },
    "lighting": {
        "elasticity": 0.10, "low": 0.02, "high": 0.20,
        "satiation_sensitive": False,
        "label": "Lighting",
        "note": "People do not want much more light than they already have, "
                "so most of an LED saving stays saved.",
    },
    "appliances": {
        "elasticity": 0.08, "low": 0.02, "high": 0.15,
        "satiation_sensitive": False,
        "label": "Appliances",
        "note": "A more efficient fridge does not get opened more often.",
    },
    "car_efficiency": {
        "elasticity": 0.20, "low": 0.10, "high": 0.30,
        "satiation_sensitive": False,
        "label": "Vehicle efficiency",
        "note": "Cheaper miles mean more miles. Consistently observed and "
                "consistently ignored in efficiency claims.",
    },
    "ev_switch": {
        "elasticity": 0.25, "low": 0.15, "high": 0.40,
        "satiation_sensitive": False,
        "label": "Switch to an EV",
        "note": "Running costs fall furthest here, so the mileage increase "
                "is larger than for a more efficient petrol car.",
    },
    "avoided_flight": {
        "elasticity": 0.02, "low": 0.00, "high": 0.05,
        "satiation_sensitive": False,
        "label": "Flight not taken",
        "note": "Almost no direct take-back - not flying does not make you "
                "want to fly more. Only the re-spending matters, which is "
                "why this class of action is systematically under-ranked "
                "by gross-saving tools.",
    },
    "diet_change": {
        "elasticity": 0.05, "low": 0.00, "high": 0.12,
        "satiation_sensitive": False,
        "label": "Dietary change",
        "note": "Food demand is close to satiated by definition. The "
                "take-back is almost entirely re-spending.",
    },
    "reduced_consumption": {
        "elasticity": 0.03, "low": 0.00, "high": 0.10,
        "satiation_sensitive": False,
        "label": "Buying less",
        "note": "Nothing gets cheaper to use, so there is no service to "
                "consume more of. The money is the only channel.",
    },
    "insulation": {
        "elasticity": 0.28, "low": 0.10, "high": 0.50,
        "satiation_sensitive": True,
        "label": "Insulation",
        "note": "Same service as space heating with a larger effect, "
                "because insulation changes comfort at every setting.",
    },
    "heat_pump": {
        "elasticity": 0.22, "low": 0.10, "high": 0.40,
        "satiation_sensitive": True,
        "label": "Heat pump",
        "note": "Cheaper warmth per degree, so the thermostat drifts up.",
    },
    "solar_pv": {
        "elasticity": 0.18, "low": 0.05, "high": 0.35,
        "satiation_sensitive": False,
        "label": "Rooftop solar",
        "note": "Self-generated electricity feels free at the margin, and "
                "gets used accordingly.",
    },
}

# How the household's starting comfort level changes direct rebound for the
# satiation-sensitive actions. A household that was under-heating takes far
# more of the saving as warmth - and that is the measure working, not
# failing.
SATIATION_LEVELS = {
    "under_consuming": {
        "multiplier": 2.0,
        "label": "Under-heating (cutting back on cost grounds)",
        "welfare_gain": True,
        "note": "Most of the saving will be taken as comfort. That is the "
                "point of the measure, not a failure of it, and reporting "
                "it as a shortfall would be wrong.",
    },
    "typical": {
        "multiplier": 1.0,
        "label": "Typical",
        "welfare_gain": False,
        "note": "The reference case the published elasticities describe.",
    },
    "satiated": {
        "multiplier": 0.35,
        "label": "Already comfortable",
        "welfare_gain": False,
        "note": "Little room to consume more of the service, so most of the "
                "saving stays saved.",
    },
}

DEFAULT_SATIATION = "typical"

# Where the money goes, and what it costs in carbon. Values are kg CO2e per
# currency unit of spending - the standard monetary intensity approach.
# The spread between these is enormous, which is why choosing one silently
# would be the whole error again in a different place.
RESPENDING_PROFILES = {
    "saved": {
        "intensity": 0.02,
        "label": "Saved or invested",
        "note": "Not zero. Invested money finances production somewhere, "
                "and claiming zero here would be the same wishful "
                "accounting this module exists to correct.",
    },
    "same_basket": {
        "intensity": 0.35,
        "label": "Spent on the same mix as before",
        "note": "The default assumption in most rebound studies: the money "
                "goes back into an average consumption basket.",
    },
    "services": {
        "intensity": 0.18,
        "label": "Services (haircuts, classes, care)",
        "note": "Labour-intensive spending is much lower carbon than "
                "goods, and this is the single most useful thing a user "
                "can do with a saving they intend to spend.",
    },
    "goods": {
        "intensity": 0.55,
        "label": "Physical goods",
        "note": "Manufacturing and freight. Higher than the average basket.",
    },
    "travel": {
        "intensity": 1.10,
        "label": "Travel and holidays",
        "note": "The category that produces backfire. A heating saving "
                "spent on flights can leave the household worse off than "
                "before the measure.",
    },
    "home_energy": {
        "intensity": 0.45,
        "label": "More home energy",
        "note": "Directly undoes the measure. Included because it happens.",
    },
}

DEFAULT_RESPENDING = "same_basket"

# Below this, the rebound is not worth reporting as a correction.
MATERIALITY_THRESHOLD = 0.05

DAYS_PER_YEAR = 365


class ReboundError(ValueError):
    """Raised when a request cannot be answered honestly."""


def _as_float(value: float, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if result != result:
        return default
    return result


def _non_negative(value: float, default: float = 0.0) -> float:
    return max(0.0, _as_float(value, default))


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------

def list_action_types() -> list[str]:
    """Action types with a rebound model."""
    return sorted(ACTION_TYPES)


def get_action_type(action_type: str) -> dict[str, Any]:
    """The elasticity, range and rationale for an action type."""
    if action_type not in ACTION_TYPES:
        raise ReboundError(
            f"No rebound model for '{action_type}'. Add one to ACTION_TYPES "
            "rather than applying an average - the variation between action "
            "types is the entire signal here, and an average would give "
            "roughly the right total with completely wrong rankings."
        )
    return dict(ACTION_TYPES[action_type])


def list_satiation_levels() -> list[str]:
    """Household starting positions that change direct rebound."""
    return list(SATIATION_LEVELS)


def get_satiation(level: str) -> dict[str, Any]:
    if level not in SATIATION_LEVELS:
        raise ReboundError(
            f"Unknown satiation level '{level}'. Pick one of: "
            + ", ".join(SATIATION_LEVELS)
        )
    return dict(SATIATION_LEVELS[level])


def list_respending_profiles() -> list[str]:
    """Where a saved pound might go."""
    return list(RESPENDING_PROFILES)


def get_respending(profile: str) -> dict[str, Any]:
    if profile not in RESPENDING_PROFILES:
        raise ReboundError(
            f"Unknown re-spending profile '{profile}'. Pick one of: "
            + ", ".join(RESPENDING_PROFILES)
        )
    return dict(RESPENDING_PROFILES[profile])


# ---------------------------------------------------------------------------
# Direct rebound
# ---------------------------------------------------------------------------

def direct_rebound(gross_saving_kg: float, action_type: str, satiation: str = DEFAULT_SATIATION,
                   elasticity: float | None = None) -> dict[str, Any]:
    """Take-back from consuming more of the service that got cheaper.

    Returns the carbon given back, and whether that give-back is a welfare
    gain rather than a loss - which it is for a household that was
    under-consuming the service to begin with.
    """
    gross = _non_negative(gross_saving_kg)
    action = get_action_type(action_type)
    level = get_satiation(satiation)

    rate = _non_negative(
        action["elasticity"] if elasticity is None else elasticity
    )
    if action["satiation_sensitive"]:
        rate *= level["multiplier"]
    rate = min(1.0, rate)

    taken_back = gross * rate
    welfare = bool(level["welfare_gain"] and action["satiation_sensitive"])

    return {
        "action_type": action_type,
        "gross_saving_kg": gross,
        "rate": rate,
        "taken_back_kg": taken_back,
        "remaining_kg": gross - taken_back,
        "is_welfare_gain": welfare,
        "satiation": satiation,
        "note": action["note"],
        "satiation_note": level["note"],
    }


# ---------------------------------------------------------------------------
# Indirect rebound
# ---------------------------------------------------------------------------

def indirect_rebound(money_saved: float, respending: str = DEFAULT_RESPENDING,
                     respent_fraction: float = 1.0, intensity: float | None = None) -> dict[str, Any]:
    """Carbon caused by spending the money the measure freed up.

    This is the term that can produce backfire, and the only one that can.
    """
    money = _non_negative(money_saved)
    profile = get_respending(respending)
    fraction = min(1.0, _non_negative(respent_fraction))

    rate = (
        profile["intensity"] if intensity is None else _non_negative(intensity)
    )
    respent = money * fraction
    caused = respent * rate

    return {
        "respending": respending,
        "money_saved": money,
        "respent": respent,
        "respent_fraction": fraction,
        "intensity": rate,
        "caused_kg": caused,
        "note": profile["note"],
    }


# ---------------------------------------------------------------------------
# Net effect
# ---------------------------------------------------------------------------

def net_saving(gross_saving_kg: float, action_type: str, money_saved: float = 0.0,
               satiation: str = DEFAULT_SATIATION, respending: str = DEFAULT_RESPENDING,
               respent_fraction: float = 1.0, elasticity: float | None = None) -> dict[str, Any]:
    """Gross saving, both take-back terms, and what is actually left.

    The decomposition is the deliverable. Handing a user a smaller number
    with no explanation of where the rest went is worse than the
    over-claim it replaces.
    """
    direct = direct_rebound(gross_saving_kg, action_type, satiation, elasticity)
    indirect = indirect_rebound(money_saved, respending, respent_fraction)

    gross = direct["gross_saving_kg"]
    net = gross - direct["taken_back_kg"] - indirect["caused_kg"]

    total_rebound = gross - net
    rebound_share = total_rebound / gross if gross > 0 else 0.0

    backfire = net < 0

    if backfire:
        reading = (
            "This measure **increases** your footprint once take-back and "
            "re-spending are counted. That is backfire, it is rare, and it "
            "is real - an efficiency tool that cannot detect it is not a "
            "reduction tool."
        )
    elif direct["is_welfare_gain"]:
        reading = (
            "A large share of this saving will be taken as comfort rather "
            "than carbon. For a household that has been under-heating, that "
            "is the measure working as intended - the benefit is real, it is "
            "just not a carbon benefit."
        )
    elif rebound_share >= 0.4:
        reading = (
            "Well under half of the projected saving survives. The gross "
            "figure is not wrong so much as answering a different question "
            "from the one a reduction target asks."
        )
    elif rebound_share >= MATERIALITY_THRESHOLD:
        reading = (
            "A meaningful share of the projected saving is taken back. Plan "
            "against the net figure, not the gross one."
        )
    else:
        reading = (
            "Very little take-back here. The projected saving is close to "
            "what you will actually get, which is a genuine advantage of "
            "this kind of action over an efficiency measure."
        )

    return {
        "action_type": action_type,
        "gross_saving_kg": gross,
        "direct_rebound_kg": direct["taken_back_kg"],
        "indirect_rebound_kg": indirect["caused_kg"],
        "total_rebound_kg": total_rebound,
        "net_saving_kg": net,
        "rebound_share": rebound_share,
        "backfire": backfire,
        "is_welfare_gain": direct["is_welfare_gain"],
        "direct": direct,
        "indirect": indirect,
        "reading": reading,
    }


def sensitivity(gross_saving_kg: float, action_type: str, money_saved: float = 0.0,
                satiation: str = DEFAULT_SATIATION, respending: str = DEFAULT_RESPENDING,
                respent_fraction: float = 1.0) -> dict[str, Any]:
    """Net saving across the published elasticity range.

    The elasticities carry real uncertainty. A range with a stated basis is
    more useful and more honest than a point estimate, and this module
    should not reproduce the false precision it exists to correct.
    """
    action = get_action_type(action_type)

    low = net_saving(
        gross_saving_kg, action_type, money_saved, satiation, respending,
        respent_fraction, elasticity=action["high"],
    )
    high = net_saving(
        gross_saving_kg, action_type, money_saved, satiation, respending,
        respent_fraction, elasticity=action["low"],
    )
    central = net_saving(
        gross_saving_kg, action_type, money_saved, satiation, respending,
        respent_fraction,
    )

    return {
        "action_type": action_type,
        "central_kg": central["net_saving_kg"],
        "low_kg": low["net_saving_kg"],
        "high_kg": high["net_saving_kg"],
        "spread_kg": high["net_saving_kg"] - low["net_saving_kg"],
        "elasticity_range": (action["low"], action["high"]),
        "could_backfire": low["net_saving_kg"] < 0,
    }


# ---------------------------------------------------------------------------
# Corrected payback
# ---------------------------------------------------------------------------

def corrected_payback_years(embodied_kg: float, gross_annual_saving_kg: float, action_type: str,
                            money_saved_per_year: float = 0.0,
                            satiation: str = DEFAULT_SATIATION,
                            respending: str = DEFAULT_RESPENDING) -> dict[str, Any]:
    """Payback period computed from net rather than gross saving.

    ``carbon_payback.py`` divides embodied carbon by a gross annual saving.
    Overstate the saving by 20% and the payback period is understated by the
    same proportion - and payback periods are what decide whether a purchase
    is worth making.

    A measure whose net saving is zero or negative never pays back. That is
    reported as ``None`` rather than as a very large number, because a large
    number invites someone to plot it.
    """
    embodied = _non_negative(embodied_kg)
    result = net_saving(
        gross_annual_saving_kg, action_type, money_saved_per_year,
        satiation, respending,
    )

    gross_annual = result["gross_saving_kg"]
    net_annual = result["net_saving_kg"]

    gross_years = embodied / gross_annual if gross_annual > 0 else None
    net_years = embodied / net_annual if net_annual > 0 else None

    return {
        "embodied_kg": embodied,
        "gross_annual_saving_kg": gross_annual,
        "net_annual_saving_kg": net_annual,
        "gross_payback_years": gross_years,
        "net_payback_years": net_years,
        "understated_by_years": (
            net_years - gross_years
            if (net_years is not None and gross_years is not None)
            else None
        ),
        "never_pays_back": net_years is None and embodied > 0,
        "backfire": result["backfire"],
    }


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------

def rank_actions(actions: list[dict[str, Any]] | None, satiation: str = DEFAULT_SATIATION,
                 respending: str = DEFAULT_RESPENDING) -> dict[str, Any]:
    """Rank options by gross and by net saving, and report the difference.

    Rebound differs by a factor of ten between action types, so this changes
    the order rather than just the magnitudes. The change has a direction:
    avoided consumption climbs, efficiency measures fall.
    """
    scored = []
    for action in actions or []:
        if not isinstance(action, dict):
            continue
        result = net_saving(
            action.get("gross_saving_kg", 0.0),
            action.get("action_type", "reduced_consumption"),
            action.get("money_saved", 0.0),
            satiation,
            respending,
        )
        result["label"] = action.get("label", action.get("action_type", ""))
        scored.append(result)

    by_gross = sorted(
        scored, key=lambda item: item["gross_saving_kg"], reverse=True
    )
    by_net = sorted(scored, key=lambda item: item["net_saving_kg"], reverse=True)

    gross_rank = {item["label"]: index for index, item in enumerate(by_gross)}
    net_rank = {item["label"]: index for index, item in enumerate(by_net)}

    changes = []
    for label, before in gross_rank.items():
        after = net_rank[label]
        if before == after:
            continue
        changes.append({
            "label": label,
            "gross_rank": before + 1,
            "net_rank": after + 1,
            "movement": before - after,
            "direction": "up" if after < before else "down",
        })
    changes.sort(key=lambda item: abs(item["movement"]), reverse=True)

    return {
        "by_gross": by_gross,
        "by_net": by_net,
        "ranking_changes": changes,
        "top_changed": bool(by_gross and by_net)
        and by_gross[0]["label"] != by_net[0]["label"],
        "backfiring": [item["label"] for item in scored if item["backfire"]],
    }


def get_rebound_insights(results: list[dict[str, Any]] | None) -> list[str]:
    """Plain-language guidance from a set of scored actions."""
    insights = []
    rows = [row for row in results or [] if isinstance(row, dict)]

    if not rows:
        return [
            "Add an action to see how much of its projected saving survives "
            "take-back."
        ]

    backfiring = [row for row in rows if row.get("backfire")]
    if backfiring:
        insights.append(
            "At least one of these measures **increases** your footprint "
            "once re-spending is counted. Backfire is rare and it is real, "
            "and it is invisible to any tool that reports gross savings."
        )

    welfare = [row for row in rows if row.get("is_welfare_gain")]
    if welfare:
        insights.append(
            "Some of the take-back here is comfort in a home that was "
            "under-heated. That is a benefit, not a shortfall - it is simply "
            "not a carbon benefit, and it should not be counted as one in "
            "either direction."
        )

    heavy = [row for row in rows if row.get("rebound_share", 0) >= 0.4]
    light = [row for row in rows if row.get("rebound_share", 0) < 0.1]
    if heavy and light:
        insights.append(
            "Take-back varies by more than a factor of four across these "
            "actions, which is why correcting for it changes the order and "
            "not just the numbers. Efficiency measures give more back; "
            "avoided consumption gives almost none."
        )

    indirect_heavy = [
        row for row in rows
        if row.get("indirect_rebound_kg", 0)
        > row.get("direct_rebound_kg", 0)
    ]
    if indirect_heavy:
        insights.append(
            "For some of these the re-spending matters more than the extra "
            "consumption. Where the money goes is then the decision, not the "
            "measure itself - and services are roughly a third of the carbon "
            "of travel per unit spent."
        )

    insights.append(
        "Set reduction targets against the net figures. A goal built on "
        "gross savings is quietly unachievable, and it will look like the "
        "user's fault rather than the projection's."
    )

    return insights


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_rebound_db() -> None:
    """Create the table if it does not exist yet."""
    conn = None
    try:
        conn = _connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rebound_scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                action_type TEXT NOT NULL,
                gross_saving_kg REAL NOT NULL,
                net_saving_kg REAL NOT NULL,
                rebound_share REAL NOT NULL,
                backfire INTEGER NOT NULL DEFAULT 0,
                detail_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Unable to initialise rebound table: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def save_scenario(user_id: int, name: str, result: dict[str, Any]) -> int | None:
    """Persist a scored scenario. Returns the row id or None."""
    init_rebound_db()
    conn = None
    try:
        conn = _connect()
        cursor = conn.execute(
            """
            INSERT INTO rebound_scenarios (
                user_id, name, action_type, gross_saving_kg, net_saving_kg,
                rebound_share, backfire, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                (name or "Scenario").strip() or "Scenario",
                result.get("action_type", ""),
                _as_float(result.get("gross_saving_kg")),
                _as_float(result.get("net_saving_kg")),
                _as_float(result.get("rebound_share")),
                1 if result.get("backfire") else 0,
                json.dumps(result, default=str),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as exc:
        logger.error("Unable to save rebound scenario: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def get_scenarios(user_id: int, limit: int = 25) -> list[dict[str, Any]]:
    """A user's saved scenarios, newest first."""
    init_rebound_db()
    conn = None
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, name, action_type, gross_saving_kg, net_saving_kg,
                   rebound_share, backfire, detail_json, created_at
            FROM rebound_scenarios
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT ?
            """,
            (user_id, int(limit)),
        ).fetchall()

        scenarios = []
        for row in rows:
            record = dict(row)
            try:
                record["detail"] = json.loads(record.pop("detail_json") or "{}")
            except (TypeError, ValueError):
                record["detail"] = {}
            record["backfire"] = bool(record.get("backfire"))
            scenarios.append(record)
        return scenarios
    except sqlite3.Error as exc:
        logger.error("Unable to load rebound scenarios: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def delete_scenario(scenario_id: int) -> bool:
    """Delete a saved scenario."""
    init_rebound_db()
    conn = None
    try:
        conn = _connect()
        cursor = conn.execute(
            "DELETE FROM rebound_scenarios WHERE id = ?", (scenario_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as exc:
        logger.error("Unable to delete rebound scenario: %s", exc)
        return False
    finally:
        if conn:
            conn.close()
