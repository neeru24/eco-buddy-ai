"""Boundary reconciliation: counting each kilogram once, and only once.

The app has a large number of modules that each compute a footprint or project a
saving, and each of them is correct on its own terms. Nothing checks what
happens when a user runs several of them and adds the results up. In several
combinations the same physical kilogram is counted twice, and in at least one
the same kilowatt-hour is saved twice.

Cases that are reachable today
------------------------------
*   ``digital_footprint.py`` estimates the electricity used by a household's
    devices. ``household.py`` computes emissions from the electricity bill. The
    device electricity is *inside* the bill.
*   ``device_lifecycle.py`` amortises embodied manufacturing carbon.
    ``shopping_assistant.py`` scores the purchase. Buy a laptop and the
    embodied carbon can appear in both.
*   ``grid_scheduler.py`` projects a saving from shifting flexible load.
    ``smart_home.py`` projects a saving from automation that shifts the same
    load. A user with both sees two savings from one dishwasher.
*   ``financed_emissions.py`` attributes emissions from investments. That is a
    production-side attribution, and adding it to a consumption footprint is
    mixing two frames rather than summing within one.

The naive fix does not work
---------------------------
Deduplicating by module name fails, because the overlap is not between modules.
It is between the **activity, carrier, frame and time window** a claim covers,
and one module can produce claims that do and do not overlap with another's.

So activities are dotted paths and containment is a prefix relation:
``home.electricity`` contains ``home.electricity.devices`` and is disjoint from
``home.gas``. Time windows are compared as dates, and a claim that only partly
overlaps is prorated rather than dropped whole.

The failure to avoid is over-correction
----------------------------------------
Two claims on the same activity are not automatically duplicates. Insulating a
loft and installing a heat pump both act on space-heating gas, but they act
*sequentially* on it. The correct treatment is interaction - each measure
applied against the remaining base - not deletion. A reconciliation that cannot
tell overlap from interaction will silently delete real savings, which is a
worse failure than the one it is fixing. Footprints deduplicate; savings
compose.

What it will not do
-------------------
It will not add a consumption-frame total to a production-frame one, and it will
not pick a winner where its own rules do not resolve cleanly. Both cases are
reported as conflicts, because silently choosing is how the current problem
would be reproduced one level up.

Self-contained: standard library only, SQLite tables created lazily, no shared
files modified.
"""

import os
import json
import sqlite3
import logging
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

# ---------------------------------------------------------------------------
# Vocabulary
#
# Frames are not summable with each other. A consumption footprint counts the
# emissions caused by what a household uses; a production frame attributes the
# emissions of an activity to whoever owns it; a financed frame attributes the
# emissions of companies to whoever funds them. The same tonne can legitimately
# appear in all three, held by three different people, and adding them together
# means nothing at all.
# ---------------------------------------------------------------------------
FRAMES = {
    "consumption": {
        "label": "Consumption",
        "note": "What the household used, wherever it was produced. The frame "
                "most of this app works in.",
    },
    "production": {
        "label": "Production",
        "note": "Emissions attributed to whoever operates the activity. "
                "Overlaps consumption on purpose and must not be added to it.",
    },
    "financed": {
        "label": "Financed",
        "note": "Emissions of companies attributed to the people funding "
                "them. A third view of some of the same tonnes.",
    },
}

DEFAULT_FRAME = "consumption"

# Confidence, which decides precedence when two claims cover the same ground.
# Measured beats modelled: a meter reading and an estimate of the same thing are
# not two facts.
CONFIDENCE_ORDER = {"measured": 3, "estimated": 2, "modelled": 1}
DEFAULT_CONFIDENCE = "modelled"

# The shared activity vocabulary. Paths are dotted and containment is a prefix
# relation, which is what lets a broad claim and a detailed one be compared
# without either module knowing about the other.
ACTIVITIES = {
    "home": "Everything at home",
    "home.electricity": "Household electricity",
    "home.electricity.devices": "Devices, screens and streaming",
    "home.electricity.flexible": "Shiftable appliance load",
    "home.electricity.heating": "Electric heating and hot water",
    "home.gas": "Household gas",
    "home.gas.space_heating": "Space heating",
    "home.gas.water_heating": "Water heating",
    "travel": "All travel",
    "travel.car": "Car travel",
    "travel.flight": "Flights",
    "travel.public": "Public transport",
    "food": "All food",
    "food.meat": "Meat and dairy",
    "food.other": "Other food",
    "goods": "Goods and services",
    "goods.electronics": "Electronics",
    "goods.electronics.embodied": "Manufacturing carbon in electronics",
    "goods.clothing": "Clothing and textiles",
    "investments": "Investments and pensions",
}

# Which module is expected to claim what. Not enforced - a claim carries its own
# boundary - but recorded here so that the overlaps this module was written for
# are visible in one place rather than rediscovered.
MODULE_CLAIMS = {
    "household": {"activity": "home.electricity", "frame": "consumption",
                  "confidence": "measured"},
    "digital_footprint": {"activity": "home.electricity.devices",
                          "frame": "consumption", "confidence": "modelled"},
    "grid_scheduler": {"activity": "home.electricity.flexible",
                       "frame": "consumption", "confidence": "modelled"},
    "smart_home": {"activity": "home.electricity.flexible",
                   "frame": "consumption", "confidence": "modelled"},
    "degree_days": {"activity": "home.gas.space_heating", "frame": "consumption",
                    "confidence": "measured"},
    "device_lifecycle": {"activity": "goods.electronics.embodied",
                         "frame": "consumption", "confidence": "modelled"},
    "shopping_assistant": {"activity": "goods.electronics",
                           "frame": "consumption", "confidence": "estimated"},
    "financed_emissions": {"activity": "investments", "frame": "financed",
                           "confidence": "modelled"},
}

REQUIRED_FIELDS = ("source", "activity", "frame", "kg")


class ReconciliationError(ValueError):
    """Raised for a claim that cannot be interpreted."""


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if result != result or result in (float("inf"), float("-inf")):
        return default
    return result


def _parse_date(value: Any, default: date) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return default


def list_frames() -> list[str]:
    return list(FRAMES)


def get_frame(name: str) -> dict[str, Any]:
    if name not in FRAMES:
        raise ReconciliationError(
            f"Unknown frame '{name}'. Known frames: {', '.join(sorted(FRAMES))}."
        )
    return dict(FRAMES[name])


def list_activities() -> list[str]:
    return list(ACTIVITIES)


def activity_label(path: str) -> str:
    """A readable name, falling back to the path itself for unknown activities.

    Unknown paths are allowed on purpose: a module should be able to declare a
    narrower boundary than this vocabulary anticipated, and the prefix relation
    still works. Refusing them would push modules back towards declaring
    nothing, which is the situation this replaces.
    """
    return ACTIVITIES.get(path, path)


# ---------------------------------------------------------------------------
# Claims
# ---------------------------------------------------------------------------

def make_claim(
    source: str,
    activity: str,
    kg: float,
    frame: str = DEFAULT_FRAME,
    kind: str = "footprint",
    confidence: str = DEFAULT_CONFIDENCE,
    carrier: str | None = None,
    period_start: str | None = None,
    period_end: str | None = None,
    base_kg: float | None = None,
    exclusive_group: str | None = None,
    label: str | None = None,
    claim_id: str | None = None,
) -> dict[str, Any]:
    """Build a claim with its boundary declared.

    ``base_kg`` is required for savings: a saving of 200 kg means nothing for
    interaction purposes without knowing what it is 200 kg *out of*. Two
    measures that each cut heating by a third do not cut it by two thirds.
    """
    if kind not in ("footprint", "saving"):
        raise ReconciliationError(
            f"Unknown claim kind '{kind}'. Expected 'footprint' or 'saving'."
        )
    if confidence not in CONFIDENCE_ORDER:
        raise ReconciliationError(
            f"Unknown confidence '{confidence}'. Expected one of "
            f"{', '.join(CONFIDENCE_ORDER)}."
        )
    get_frame(frame)

    if not str(activity or "").strip():
        raise ReconciliationError(
            "A claim with no activity cannot be reconciled against anything. "
            "Declare the boundary or submit it as unreconcilable."
        )

    start = _parse_date(period_start, date(2000, 1, 1))
    end = _parse_date(period_end, date(2100, 1, 1))
    if end < start:
        raise ReconciliationError(
            "A claim's period ends before it starts, which makes its overlap "
            "with anything else undefined."
        )

    claim = {
        "id": claim_id or f"{source}:{activity}:{kind}",
        "source": str(source),
        "label": label or f"{source} - {activity_label(activity)}",
        "activity": str(activity).strip(),
        "frame": frame,
        "kind": kind,
        "confidence": confidence,
        "carrier": carrier,
        "kg": _as_float(kg),
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "exclusive_group": exclusive_group,
    }
    if kind == "saving":
        base = _as_float(base_kg)
        if base <= 0:
            raise ReconciliationError(
                "A saving needs the base it was taken from. Without it, two "
                "measures on the same activity cannot be composed and would "
                "have to be either added (overstating) or deleted "
                "(understating)."
            )
        claim["base_kg"] = base
    return claim


def validate_claim(claim: dict[str, Any] | None) -> tuple[bool, str]:
    """Whether a claim declares enough boundary to be reconciled."""
    if not isinstance(claim, dict):
        return False, "Not a claim."
    for field in REQUIRED_FIELDS:
        if claim.get(field) in (None, ""):
            return False, f"No {field} declared."
    if claim.get("frame") not in FRAMES:
        return False, f"Unknown frame '{claim.get('frame')}'."
    if claim.get("kind") == "saving" and _as_float(claim.get("base_kg")) <= 0:
        return False, "A saving without a base cannot be composed."
    return True, ""


# ---------------------------------------------------------------------------
# Boundary comparison
# ---------------------------------------------------------------------------

def activity_relation(first: str, second: str) -> str:
    """How two activity paths relate: same, contains, contained or disjoint.

    Containment is a prefix relation on dotted segments, compared segment by
    segment rather than as raw strings - otherwise ``home.gas`` would appear to
    contain ``home.gasoline``.
    """
    left = [part for part in str(first).split(".") if part]
    right = [part for part in str(second).split(".") if part]
    if left == right:
        return "same"
    if len(left) < len(right) and right[:len(left)] == left:
        return "contains"
    if len(right) < len(left) and left[:len(right)] == right:
        return "contained"
    return "disjoint"


def period_overlap(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    """Shared days between two claims, and what share of each they are."""
    start_a = _parse_date(first.get("period_start"), date(2000, 1, 1))
    end_a = _parse_date(first.get("period_end"), date(2100, 1, 1))
    start_b = _parse_date(second.get("period_start"), date(2000, 1, 1))
    end_b = _parse_date(second.get("period_end"), date(2100, 1, 1))

    start = max(start_a, start_b)
    end = min(end_a, end_b)
    shared = max(0, (end - start).days + 1) if end >= start else 0

    days_a = (end_a - start_a).days + 1
    days_b = (end_b - start_b).days + 1
    return {
        "shared_days": shared,
        "share_of_first": shared / days_a if days_a > 0 else 0.0,
        "share_of_second": shared / days_b if days_b > 0 else 0.0,
    }


def claims_overlap(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    """Whether two claims cover any of the same ground, and how much.

    ``degree`` distinguishes full containment from partial intersection, because
    the treatment differs: a fully contained claim is removed, a partly
    overlapping one is prorated.
    """
    relation = activity_relation(first.get("activity", ""), second.get("activity", ""))
    frames_match = first.get("frame") == second.get("frame")

    carrier_a = first.get("carrier")
    carrier_b = second.get("carrier")
    carriers_match = not (carrier_a and carrier_b and carrier_a != carrier_b)

    overlap = period_overlap(first, second)
    time_share = overlap["share_of_second"]

    overlapping = (
        relation in ("same", "contains", "contained")
        and frames_match
        and carriers_match
        and time_share > 0
    )
    if not overlapping:
        degree = "none"
    elif time_share >= 0.999:
        degree = "full"
    else:
        degree = "partial"

    return {
        "relation": relation,
        "frames_match": frames_match,
        "carriers_match": carriers_match,
        "shared_days": overlap["shared_days"],
        "time_share": time_share,
        "overlapping": overlapping,
        "degree": degree,
    }


def _confidence_rank(claim: dict[str, Any]) -> int:
    return CONFIDENCE_ORDER.get(claim.get("confidence"), 0)


# ---------------------------------------------------------------------------
# Footprint reconciliation
# ---------------------------------------------------------------------------

def reconcile_footprints(claims: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Sum footprint claims once each, with an audit trail of what was removed.

    Broader claims are considered first, so a total is in place before the
    detail that sits inside it is examined. Where the detail is only partly
    inside - a monthly claim against a quarterly total - only the overlapping
    share is removed and the remainder is kept.
    """
    accepted = []
    unreconcilable = []
    for claim in claims or []:
        valid, reason = validate_claim(claim)
        if not valid or claim.get("kind") != "footprint":
            if claim is not None and claim.get("kind") != "saving":
                unreconcilable.append({"claim": claim, "reason": reason or "Not a footprint."})
            continue
        accepted.append(dict(claim))

    frames: dict[str, dict[str, Any]] = {}
    audit: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []

    for frame_name in FRAMES:
        in_frame = [claim for claim in accepted if claim["frame"] == frame_name]
        if not in_frame:
            continue

        # Broadest first: a total should exist before its detail is examined.
        in_frame.sort(key=lambda claim: (
            len(claim["activity"].split(".")), -_confidence_rank(claim), -claim["kg"]
        ))

        kept: list[dict[str, Any]] = []
        for claim in in_frame:
            retained = claim["kg"]
            removals = []

            for other in kept:
                comparison = claims_overlap(other, claim)
                if not comparison["overlapping"]:
                    continue

                relation = comparison["relation"]
                share = comparison["time_share"]

                if relation == "same":
                    if _confidence_rank(other) > _confidence_rank(claim):
                        removed = retained * share
                        retained -= removed
                        removals.append({
                            "against": other["id"],
                            "rule": "same boundary, lower confidence removed",
                            "removed_kg": removed,
                            "detail": (
                                f"{claim['source']} covers the same boundary as "
                                f"{other['source']}, which is {other['confidence']} "
                                f"rather than {claim['confidence']}. A measurement "
                                f"and an estimate of the same thing are not two facts."
                            ),
                        })
                    elif _confidence_rank(other) == _confidence_rank(claim):
                        conflicts.append({
                            "claims": [other["id"], claim["id"]],
                            "reason": (
                                f"{other['source']} and {claim['source']} claim the "
                                f"same boundary at the same confidence "
                                f"({claim['confidence']}), and differ by "
                                f"{abs(other['kg'] - claim['kg']):,.0f} kg. Picking "
                                f"one silently would reproduce the problem this "
                                f"module exists to fix."
                            ),
                            "kept": other["id"],
                        })
                        removed = retained * share
                        retained -= removed
                        removals.append({
                            "against": other["id"],
                            "rule": "same boundary, unresolved - larger kept, conflict raised",
                            "removed_kg": removed,
                            "detail": "Counted once, with the disagreement reported.",
                        })
                elif relation == "contains":
                    removed = retained * share
                    if claim["kg"] > other["kg"] and share >= 0.999:
                        conflicts.append({
                            "claims": [other["id"], claim["id"]],
                            "reason": (
                                f"{claim['source']} claims {claim['kg']:,.0f} kg for "
                                f"{activity_label(claim['activity'])}, which sits "
                                f"inside {other['source']}'s "
                                f"{other['kg']:,.0f} kg for "
                                f"{activity_label(other['activity'])}. A part cannot "
                                f"be larger than the whole; one of the two is wrong."
                            ),
                            "kept": other["id"],
                        })
                    retained -= removed
                    removals.append({
                        "against": other["id"],
                        "rule": "contained in a broader claim",
                        "removed_kg": removed,
                        "detail": (
                            f"{activity_label(claim['activity'])} is inside "
                            f"{activity_label(other['activity'])}, which "
                            f"{other['source']} has already counted."
                        ),
                    })

                if retained <= 0:
                    retained = 0.0
                    break

            record = dict(claim)
            record["retained_kg"] = max(0.0, retained)
            record["removed_kg"] = claim["kg"] - record["retained_kg"]
            record["removals"] = removals
            kept.append(record)
            for removal in removals:
                audit.append(dict(removal, claim=claim["id"], source=claim["source"]))

        frames[frame_name] = {
            "frame": frame_name,
            "label": FRAMES[frame_name]["label"],
            "note": FRAMES[frame_name]["note"],
            "claims": kept,
            "naive_total_kg": sum(claim["kg"] for claim in kept),
            "reconciled_total_kg": sum(claim["retained_kg"] for claim in kept),
            "removed_kg": sum(claim["removed_kg"] for claim in kept),
        }

    return {
        "frames": frames,
        "audit": audit,
        "conflicts": conflicts,
        "unreconcilable": unreconcilable,
        "naive_total_kg": sum(frame["naive_total_kg"] for frame in frames.values()),
        "reconciled_total_kg": sum(frame["reconciled_total_kg"] for frame in frames.values()),
        "removed_kg": sum(frame["removed_kg"] for frame in frames.values()),
    }


# ---------------------------------------------------------------------------
# Saving reconciliation
# ---------------------------------------------------------------------------

def compose_savings(savings: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Apply savings sequentially against the remaining base, not the original.

    Two measures that each cut heating by a third do not cut it by two thirds.
    The second acts on what the first left behind, so the total is always less
    than the naive sum and never zero unless the measures are.

    The order is reported because it matters: applied largest-first and
    smallest-first the total is identical, but the credit attributed to each
    individual measure is not, and anything that ranks measures needs to know
    that.
    """
    entries = [dict(saving) for saving in savings or [] if _as_float(saving.get("base_kg")) > 0]
    if not entries:
        return {
            "applied": [], "naive_total_kg": 0.0, "composed_total_kg": 0.0,
            "interaction_loss_kg": 0.0, "base_kg": 0.0,
        }

    # The broadest declared base wins: a measure declared against the whole
    # heating load and one declared against a subset are both acting on the
    # larger quantity.
    base = max(entry["base_kg"] for entry in entries)
    entries.sort(key=lambda entry: entry["kg"], reverse=True)

    remaining = base
    applied = []
    for entry in entries:
        fraction = min(1.0, max(0.0, entry["kg"] / entry["base_kg"]))
        amount = remaining * fraction
        remaining -= amount
        applied.append(dict(
            entry,
            fraction=fraction,
            standalone_kg=entry["kg"],
            applied_kg=amount,
            interaction_kg=entry["kg"] - amount,
        ))

    naive = sum(entry["kg"] for entry in entries)
    composed = sum(entry["applied_kg"] for entry in applied)
    return {
        "applied": applied,
        "base_kg": base,
        "naive_total_kg": naive,
        "composed_total_kg": composed,
        "interaction_loss_kg": naive - composed,
        "remaining_kg": remaining,
    }


def reconcile_savings(claims: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Group savings by activity, resolve exclusive measures, then compose.

    Savings are never deduplicated the way footprints are. Two measures on the
    same activity are usually sequential rather than duplicated, and deleting one
    would understate as badly as adding both overstates. The exception is
    measures that genuinely cannot coexist - two different heating systems -
    which is why an exclusive group is declared rather than inferred.
    """
    accepted = []
    unreconcilable = []
    for claim in claims or []:
        if not isinstance(claim, dict) or claim.get("kind") != "saving":
            continue
        valid, reason = validate_claim(claim)
        if not valid:
            unreconcilable.append({"claim": claim, "reason": reason})
            continue
        accepted.append(dict(claim))

    dropped: list[dict[str, Any]] = []
    groups: dict[str, list[dict[str, Any]]] = {}
    for claim in accepted:
        groups.setdefault(claim["exclusive_group"] or f"__{claim['id']}", []).append(claim)

    survivors = []
    for name, members in groups.items():
        if name.startswith("__") or len(members) == 1:
            survivors.extend(members)
            continue
        members.sort(key=lambda claim: claim["kg"], reverse=True)
        survivors.append(members[0])
        for loser in members[1:]:
            dropped.append({
                "claim": loser["id"],
                "rule": "mutually exclusive measures",
                "removed_kg": loser["kg"],
                "detail": (
                    f"{loser['source']} and {members[0]['source']} cannot both "
                    f"happen - only one heating system gets installed - so the "
                    f"larger is kept rather than both being counted."
                ),
            })

    # Activities that contain one another are composed together: a measure on
    # space heating and a measure on all household gas act on overlapping
    # ground, so they interact even though their paths differ.
    buckets: list[dict[str, Any]] = []
    for claim in survivors:
        placed = False
        for bucket in buckets:
            if bucket["frame"] != claim["frame"]:
                continue
            if activity_relation(bucket["activity"], claim["activity"]) != "disjoint":
                bucket["claims"].append(claim)
                if len(claim["activity"].split(".")) < len(bucket["activity"].split(".")):
                    bucket["activity"] = claim["activity"]
                placed = True
                break
        if not placed:
            buckets.append({
                "activity": claim["activity"],
                "frame": claim["frame"],
                "claims": [claim],
            })

    results = []
    for bucket in buckets:
        composition = compose_savings(bucket["claims"])
        results.append({
            "activity": bucket["activity"],
            "label": activity_label(bucket["activity"]),
            "frame": bucket["frame"],
            "interacting": len(bucket["claims"]) > 1,
            **composition,
        })

    results.sort(key=lambda row: row["composed_total_kg"], reverse=True)
    return {
        "activities": results,
        "dropped": dropped,
        "unreconcilable": unreconcilable,
        "naive_total_kg": sum(row["naive_total_kg"] for row in results)
                          + sum(item["removed_kg"] for item in dropped),
        "composed_total_kg": sum(row["composed_total_kg"] for row in results),
        "interaction_loss_kg": sum(row["interaction_loss_kg"] for row in results),
    }


def reconcile(claims: list[dict[str, Any]] | None) -> dict[str, Any]:
    """The whole report: footprints deduplicated, savings composed.

    The two totals are returned separately and are never added together. A
    footprint is a quantity that exists; a saving is a change against a
    counterfactual. Summing them would produce a number with no referent.
    """
    footprints = reconcile_footprints(claims)
    savings = reconcile_savings(claims)

    overstatement = footprints["removed_kg"] + savings["interaction_loss_kg"] + sum(
        item["removed_kg"] for item in savings["dropped"]
    )
    naive = footprints["naive_total_kg"] + savings["naive_total_kg"]

    return {
        "footprints": footprints,
        "savings": savings,
        "conflicts": footprints["conflicts"],
        "unreconcilable": footprints["unreconcilable"] + savings["unreconcilable"],
        "naive_total_kg": naive,
        "overstatement_kg": overstatement,
        "overstatement_pct": (100.0 * overstatement / naive) if naive > 0 else 0.0,
        "frames_reported_separately": [
            name for name, frame in footprints["frames"].items()
            if frame["reconciled_total_kg"] > 0
        ],
    }


def get_reconciliation_insights(report: dict[str, Any] | None) -> list[str]:
    """Plain statements about what was adjusted and why."""
    if not report:
        return ["Submit some claims to see whether they overlap."]

    insights: list[str] = []
    overstatement = _as_float(report.get("overstatement_kg"))
    percentage = _as_float(report.get("overstatement_pct"))

    if overstatement > 1.0:
        insights.append(
            f"Adding these claims up unadjusted overstates by "
            f"{overstatement:,.0f} kg, which is {percentage:.0f}% of the naive "
            f"total. None of the individual modules is wrong; the sum is."
        )
    else:
        insights.append(
            "These claims do not overlap. The naive sum and the reconciled "
            "total agree, which is worth knowing rather than assuming."
        )

    footprints = report.get("footprints") or {}
    removed = _as_float(footprints.get("removed_kg"))
    if removed > 1.0:
        insights.append(
            f"{removed:,.0f} kg was double counted between footprint claims - "
            f"detail sitting inside a total that already included it. Every "
            f"removal is in the audit trail with the rule that produced it."
        )

    savings = report.get("savings") or {}
    interaction = _as_float(savings.get("interaction_loss_kg"))
    if interaction > 1.0:
        insights.append(
            f"{interaction:,.0f} kg of the projected savings was interaction, "
            f"not duplication. Measures acting on the same activity apply to "
            f"what the previous one left behind, so they were composed rather "
            f"than deleted - deleting them would understate as badly as adding "
            f"them overstates."
        )

    frames = [name for name in (report.get("frames_reported_separately") or [])]
    if len(frames) > 1:
        labels = ", ".join(FRAMES[name]["label"].lower() for name in frames)
        insights.append(
            f"There are claims in more than one accounting frame here "
            f"({labels}). They are reported separately and deliberately not "
            f"added: the same tonne can appear in all of them, held by "
            f"different people."
        )

    conflicts = report.get("conflicts") or []
    if conflicts:
        insights.append(
            f"{len(conflicts)} conflict(s) could not be resolved by the rules "
            f"and are reported rather than decided. Silently picking a winner "
            f"is how this problem gets reproduced one level up."
        )

    unreconcilable = report.get("unreconcilable") or []
    if unreconcilable:
        insights.append(
            f"{len(unreconcilable)} claim(s) did not declare enough boundary to "
            f"be reconciled. They are excluded from the totals rather than "
            f"quietly trusted."
        )

    insights.append(
        "Footprint and saving totals are kept apart on purpose. A footprint is "
        "a quantity that exists; a saving is a change against a counterfactual, "
        "and adding them gives a number with no referent."
    )
    return insights


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_reconciliation_db() -> bool:
    """Create the table if it does not exist yet."""
    conn = None
    try:
        conn = _connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS boundary_reconciliations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                naive_total_kg REAL NOT NULL,
                overstatement_kg REAL NOT NULL,
                conflict_count INTEGER NOT NULL DEFAULT 0,
                detail_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Unable to initialise reconciliation table: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def save_reconciliation(user_id: int, name: str, report: dict[str, Any]) -> int | None:
    """Persist a report. Returns the row id or None."""
    init_reconciliation_db()
    conn = None
    try:
        conn = _connect()
        cursor = conn.execute(
            """
            INSERT INTO boundary_reconciliations (
                user_id, name, naive_total_kg, overstatement_kg,
                conflict_count, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                (name or "Reconciliation").strip() or "Reconciliation",
                _as_float(report.get("naive_total_kg")),
                _as_float(report.get("overstatement_kg")),
                len(report.get("conflicts") or []),
                json.dumps(report, default=str),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as exc:
        logger.error("Unable to save reconciliation: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def get_reconciliations(user_id: int, limit: int = 25) -> list[dict[str, Any]]:
    """A user's saved reports, newest first."""
    init_reconciliation_db()
    conn = None
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, name, naive_total_kg, overstatement_kg, conflict_count,
                   detail_json, created_at
            FROM boundary_reconciliations
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT ?
            """,
            (user_id, int(limit)),
        ).fetchall()

        reports = []
        for row in rows:
            record = dict(row)
            try:
                record["detail"] = json.loads(record.pop("detail_json") or "{}")
            except (TypeError, ValueError):
                record["detail"] = {}
            reports.append(record)
        return reports
    except sqlite3.Error as exc:
        logger.error("Unable to load reconciliations: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def delete_reconciliation(report_id: int) -> bool:
    """Delete a saved report."""
    init_reconciliation_db()
    conn = None
    try:
        conn = _connect()
        cursor = conn.execute(
            "DELETE FROM boundary_reconciliations WHERE id = ?", (report_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as exc:
        logger.error("Unable to delete reconciliation: %s", exc)
        return False
    finally:
        if conn:
            conn.close()
