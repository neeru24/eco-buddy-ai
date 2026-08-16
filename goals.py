"""
Reduction Goal & Pathway Engine.

Turns EcoBuddy AI from a passive tracker into an accountability tool: a user
commits to a target annual footprint by a target date, and this module answers
the only question that matters afterwards — *am I reducing fast enough?*

The module is deliberately free of any Streamlit import so that every function
here is directly unit-testable and reusable from the PDF report, the dashboard
and the page layer.

Vocabulary
----------
baseline_kg   The footprint the user starts from (usually their latest assessment).
target_kg     The footprint they are committing to reach.
pathway       The month-by-month ideal trajectory from baseline to target.
observed pace The reduction actually achieved so far, in kg CO2 per month.
variance      actual minus expected. Negative means ahead of schedule.
"""

import datetime
import math
from typing import Any

from config import CATEGORY_WEIGHTS

# --- Status constants -------------------------------------------------------
# Ordered from best to worst so a UI can colour-code them directly.
STATUS_ACHIEVED = "ACHIEVED"
STATUS_AHEAD = "AHEAD"
STATUS_ON_TRACK = "ON_TRACK"
STATUS_AT_RISK = "AT_RISK"
STATUS_OFF_TRACK = "OFF_TRACK"

STATUS_ORDER = [
    STATUS_ACHIEVED,
    STATUS_AHEAD,
    STATUS_ON_TRACK,
    STATUS_AT_RISK,
    STATUS_OFF_TRACK,
]

# Human-facing copy for each status, kept next to the constants so the page
# layer never has to invent its own wording.
STATUS_LABELS = {
    STATUS_ACHIEVED: "Goal achieved",
    STATUS_AHEAD: "Ahead of schedule",
    STATUS_ON_TRACK: "On track",
    STATUS_AT_RISK: "At risk",
    STATUS_OFF_TRACK: "Off track",
}

STATUS_COLORS = {
    STATUS_ACHIEVED: "#0cb93d",
    STATUS_AHEAD: "#2e9e5b",
    STATUS_ON_TRACK: "#4caf50",
    STATUS_AT_RISK: "#f5a524",
    STATUS_OFF_TRACK: "#e5484d",
}

# Variance thresholds, expressed as a fraction of the total reduction the goal
# asks for. Using a relative threshold keeps the classification meaningful for
# both a 200 kg goal and a 4000 kg goal.
AHEAD_THRESHOLD = -0.05
ON_TRACK_THRESHOLD = 0.05
AT_RISK_THRESHOLD = 0.20

DAYS_PER_MONTH = 30.4375  # 365.25 / 12, so month maths stays leap-year honest

# The share of a category that can realistically be eliminated. Diet and
# electricity have a hard floor (everybody eats, everybody needs some power),
# whereas discretionary flying can in principle go to zero.
REDUCTION_CEILINGS = {
    "Transport": 0.80,
    "Electricity": 0.60,
    "Diet": 0.45,
    "Flights": 1.00,
}

DEFAULT_REDUCTION_CEILING = 0.50

# Goal lifecycle states persisted alongside the goal row.
GOAL_ACTIVE = "active"
GOAL_ARCHIVED = "archived"
GOAL_COMPLETED = "completed"


class GoalValidationError(ValueError):
    """Raised when a goal cannot be constructed from the supplied values."""


# --- Date helpers -----------------------------------------------------------

def _coerce_date(value: str | datetime.date, field_name: str) -> datetime.date:
    """
    Accept a date, a datetime, or an ISO-8601 string and return a plain date.

    The database hands back strings, the UI hands back date objects and the
    tests hand back both, so normalising once here keeps every other function
    free of isinstance checks.
    """
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise GoalValidationError(f"{field_name} must not be empty")
        # Tolerate the "2026-07-30 12:00:00" form SQLite produces.
        text = text.replace(" ", "T")
        try:
            return datetime.datetime.fromisoformat(text).date()
        except ValueError:
            try:
                return datetime.datetime.strptime(text[:10], "%Y-%m-%d").date()
            except ValueError:
                raise GoalValidationError(
                    f"{field_name} must be an ISO-8601 date, got {value!r}"
                )
    raise GoalValidationError(f"{field_name} must be a date, got {type(value).__name__}")


def _coerce_positive_number(value: Any, field_name: str, allow_zero: bool = True) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise GoalValidationError(f"{field_name} must be a number, got {value!r}")
    if math.isnan(number) or math.isinf(number):
        raise GoalValidationError(f"{field_name} must be a finite number")
    if number < 0 or (number == 0 and not allow_zero):
        raise GoalValidationError(f"{field_name} must be greater than zero")
    return number


def months_between(start: str | datetime.date, end: str | datetime.date) -> float:
    """Fractional months between two dates. Negative if end precedes start."""
    start = _coerce_date(start, "start")
    end = _coerce_date(end, "end")
    return (end - start).days / DAYS_PER_MONTH


# --- Goal construction ------------------------------------------------------

def create_goal(baseline_kg: float, target_kg: float, start_date: str | datetime.date,
                target_date: str | datetime.date, goal_id: int | None = None,
                user_id: int | None = None, status: str = GOAL_ACTIVE) -> dict[str, Any]:
    """
    Build and validate a goal record.

    Returns a plain dict rather than a class so it round-trips through JSON,
    SQLite and st.session_state without any serialisation glue.
    """
    baseline = _coerce_positive_number(baseline_kg, "baseline_kg", allow_zero=False)
    target = _coerce_positive_number(target_kg, "target_kg")
    start = _coerce_date(start_date, "start_date")
    end = _coerce_date(target_date, "target_date")

    goal = {
        "id": goal_id,
        "user_id": user_id,
        "baseline_kg": baseline,
        "target_kg": target,
        "start_date": start,
        "target_date": end,
        "status": status,
    }
    validate_goal(goal)
    return goal


def validate_goal(goal: dict[str, Any]) -> bool:
    """Raise GoalValidationError if the goal is internally inconsistent."""
    baseline = goal["baseline_kg"]
    target = goal["target_kg"]
    start = _coerce_date(goal["start_date"], "start_date")
    end = _coerce_date(goal["target_date"], "target_date")

    if target >= baseline:
        raise GoalValidationError(
            f"target_kg ({target:.1f}) must be below baseline_kg ({baseline:.1f}) "
            "— a reduction goal has to actually reduce something"
        )
    if end <= start:
        raise GoalValidationError("target_date must be after start_date")
    if months_between(start, end) < 1:
        raise GoalValidationError("a goal window shorter than one month cannot be tracked")
    return True


def total_reduction_required(goal: dict[str, Any]) -> float:
    """Absolute kg CO2 that must come off between baseline and target."""
    return goal["baseline_kg"] - goal["target_kg"]


def reduction_percentage(goal: dict[str, Any]) -> float:
    """The goal expressed as a percentage cut from baseline."""
    baseline = goal["baseline_kg"]
    if baseline <= 0:
        return 0.0
    return (total_reduction_required(goal) / baseline) * 100.0


def required_monthly_reduction(goal: dict[str, Any]) -> float:
    """kg CO2 that must come off every month to land exactly on target."""
    window = months_between(goal["start_date"], goal["target_date"])
    if window <= 0:
        return 0.0
    return total_reduction_required(goal) / window


def required_daily_reduction(goal: dict[str, Any]) -> float:
    """The same pace expressed per day, useful for short-window goals."""
    return required_monthly_reduction(goal) / DAYS_PER_MONTH


# --- Ideal pathway ----------------------------------------------------------

def build_pathway(goal: dict[str, Any], points: int | None = None) -> list[dict[str, Any]]:
    """
    The ideal month-by-month trajectory from baseline to target.

    Returns a list of dicts with the date, the footprint the user should be at
    on that date, and how far through the goal window that milestone sits. The
    final point always lands exactly on the target date and target value, so a
    chart drawn from this never stops short of the goal marker.
    """
    start = _coerce_date(goal["start_date"], "start_date")
    end = _coerce_date(goal["target_date"], "target_date")
    window = months_between(start, end)

    if points is None:
        points = max(2, int(round(window)) + 1)
    points = max(2, int(points))

    baseline = goal["baseline_kg"]
    reduction = total_reduction_required(goal)
    total_days = (end - start).days

    pathway = []
    for index in range(points):
        fraction = index / (points - 1)
        milestone_date = start + datetime.timedelta(days=round(total_days * fraction))
        pathway.append({
            "date": milestone_date,
            "target_kg": round(baseline - reduction * fraction, 2),
            "fraction_elapsed": round(fraction, 4),
        })
    # Guard against rounding drift on the final milestone.
    pathway[-1]["date"] = end
    pathway[-1]["target_kg"] = round(goal["target_kg"], 2)
    return pathway


def expected_footprint_at(goal: dict[str, Any], on_date: str | datetime.date) -> float:
    """
    Where the pathway says the user should be on a given date.

    Clamped at both ends: before the goal starts the expectation is the
    baseline, after it ends the expectation is the target.
    """
    start = _coerce_date(goal["start_date"], "start_date")
    end = _coerce_date(goal["target_date"], "target_date")
    when = _coerce_date(on_date, "on_date")

    if when <= start:
        return goal["baseline_kg"]
    if when >= end:
        return goal["target_kg"]

    elapsed = (when - start).days
    total = (end - start).days
    fraction = elapsed / total
    return goal["baseline_kg"] - total_reduction_required(goal) * fraction


# --- Observed progress ------------------------------------------------------

def _normalize_records(assessments: list[dict[str, Any]] | list[tuple[Any, ...]]) -> list[dict[str, Any]]:
    """
    Accept either the raw tuples get_assessments() returns or a list of dicts,
    and produce a clean, chronologically sorted list of {date, footprint}.

    get_assessments() returns rows shaped
        (id, date, transport, distance, electricity, diet, flights, footprint, eco_score)
    so index 1 is the date and index 7 is the footprint.
    """
    records = []
    for row in assessments or []:
        if isinstance(row, dict):
            raw_date = row.get("date")
            raw_footprint = row.get("footprint")
        elif isinstance(row, (list, tuple)):
            if len(row) < 8:
                continue
            raw_date = row[1]
            raw_footprint = row[7]
        else:
            continue

        if raw_date is None or raw_footprint is None:
            continue
        try:
            record_date = _coerce_date(raw_date, "date")
            footprint = float(raw_footprint)
        except (GoalValidationError, TypeError, ValueError):
            continue
        if math.isnan(footprint) or math.isinf(footprint):
            continue
        records.append({"date": record_date, "footprint": footprint})

    records.sort(key=lambda item: item["date"])
    return records


def latest_footprint(assessments: list[dict[str, Any]] | list[tuple[Any, ...]]) -> float | None:
    """The most recent recorded footprint, or None if there is no usable data."""
    records = _normalize_records(assessments)
    if not records:
        return None
    return records[-1]["footprint"]


def observed_pace(assessments: list[dict[str, Any]] | list[tuple[Any, ...]]) -> float:
    """
    Reduction actually achieved, in kg CO2 per month, via least-squares slope.

    A positive return value means the footprint is falling (good). Returns 0.0
    when there is too little data, or when every record shares one date and the
    slope is therefore undefined.
    """
    records = _normalize_records(assessments)
    if len(records) < 2:
        return 0.0

    origin = records[0]["date"]
    xs = [(record["date"] - origin).days / DAYS_PER_MONTH for record in records]
    ys = [record["footprint"] for record in records]

    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    denominator = sum((x - mean_x) ** 2 for x in xs)
    if denominator == 0:
        return 0.0
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    slope = numerator / denominator
    # slope is change per month; a falling footprint is a negative slope, and we
    # report reduction as a positive number because that reads better in the UI.
    return -slope


def project_final_footprint(goal: dict[str, Any],
                            assessments: list[dict[str, Any]] | list[tuple[Any, ...]],
                            as_of: str | datetime.date | None = None) -> float:
    """
    Linear projection of where the user lands on the target date if the pace
    observed so far continues unchanged.
    """
    as_of = _coerce_date(as_of or datetime.date.today(), "as_of")
    current = latest_footprint(assessments)
    if current is None:
        current = goal["baseline_kg"]

    end = _coerce_date(goal["target_date"], "target_date")
    remaining_months = months_between(as_of, end)
    if remaining_months <= 0:
        return current

    pace = observed_pace(assessments)
    projected = current - pace * remaining_months
    # A projection below zero is physically meaningless.
    return max(0.0, projected)


def classify_status(goal: dict[str, Any], variance_kg: float, current_kg: float) -> str:
    """
    Map a variance into one of the five status constants.

    variance_kg is actual minus expected, so negative is ahead of schedule.
    """
    if current_kg <= goal["target_kg"]:
        return STATUS_ACHIEVED

    required = total_reduction_required(goal)
    if required <= 0:
        return STATUS_ON_TRACK

    ratio = variance_kg / required
    if ratio <= AHEAD_THRESHOLD:
        return STATUS_AHEAD
    if ratio <= ON_TRACK_THRESHOLD:
        return STATUS_ON_TRACK
    if ratio <= AT_RISK_THRESHOLD:
        return STATUS_AT_RISK
    return STATUS_OFF_TRACK


def evaluate_progress(goal: dict[str, Any],
                      assessments: list[dict[str, Any]] | list[tuple[Any, ...]],
                      as_of: str | datetime.date | None = None) -> dict[str, Any]:
    """
    The core entry point: everything the UI needs about a goal in one dict.

    Works with an empty assessment history — in that case the user is treated as
    sitting exactly on their baseline, which is the honest interpretation of
    "committed to a goal but has not logged anything yet".
    """
    validate_goal(goal)
    as_of = _coerce_date(as_of or datetime.date.today(), "as_of")

    current = latest_footprint(assessments)
    has_data = current is not None
    if not has_data:
        current = goal["baseline_kg"]

    required = total_reduction_required(goal)
    achieved = goal["baseline_kg"] - current
    percent_complete = (achieved / required * 100.0) if required > 0 else 100.0
    percent_complete = max(0.0, min(100.0, percent_complete))

    expected = expected_footprint_at(goal, as_of)
    variance = current - expected

    projected_final = project_final_footprint(goal, assessments, as_of=as_of)
    shortfall = max(0.0, projected_final - goal["target_kg"])

    end = _coerce_date(goal["target_date"], "target_date")
    days_remaining = max(0, (end - as_of).days)
    months_remaining = max(0.0, months_between(as_of, end))
    remaining_reduction = max(0.0, current - goal["target_kg"])
    pace_needed = (remaining_reduction / months_remaining) if months_remaining > 0 else 0.0

    status = classify_status(goal, variance, current)

    return {
        "status": status,
        "status_label": STATUS_LABELS[status],
        "status_color": STATUS_COLORS[status],
        "has_data": has_data,
        "as_of": as_of,
        "current_kg": round(current, 2),
        "baseline_kg": round(goal["baseline_kg"], 2),
        "target_kg": round(goal["target_kg"], 2),
        "achieved_kg": round(achieved, 2),
        "required_kg": round(required, 2),
        "remaining_kg": round(remaining_reduction, 2),
        "percent_complete": round(percent_complete, 1),
        "expected_footprint_now": round(expected, 2),
        "variance_kg": round(variance, 2),
        "observed_pace_kg_per_month": round(observed_pace(assessments), 2),
        "required_pace_kg_per_month": round(required_monthly_reduction(goal), 2),
        "pace_needed_from_now_kg_per_month": round(pace_needed, 2),
        "projected_final_kg": round(projected_final, 2),
        "projected_shortfall_kg": round(shortfall, 2),
        "days_remaining": days_remaining,
        "months_remaining": round(months_remaining, 2),
        "record_count": len(_normalize_records(assessments)),
    }


# --- Category allocation ----------------------------------------------------

def allocate_reduction(goal: dict[str, Any], contributors: dict[str, float]) -> dict[str, Any]:
    """
    Split the required reduction across emission categories.

    Two forces decide each category's share: how much it currently emits, and
    how much of it can realistically be cut. Charging a 40% cut to Diet is not
    actionable advice, so each category's contribution is weighted by its
    reducible headroom (current emission x its ceiling) rather than by its raw
    size alone. Any reduction that cannot be absorbed within the ceilings is
    reported as unallocated instead of being silently hidden.
    """
    required = total_reduction_required(goal)
    if not contributors or required <= 0:
        return {
            "allocations": {},
            "total_required_kg": round(max(0.0, required), 2),
            "total_allocated_kg": 0.0,
            "unallocated_kg": round(max(0.0, required), 2),
            "feasible": required <= 0,
        }

    headroom = {}
    for category, emission in contributors.items():
        try:
            value = max(0.0, float(emission))
        except (TypeError, ValueError):
            continue
        ceiling = REDUCTION_CEILINGS.get(category, DEFAULT_REDUCTION_CEILING)
        headroom[category] = value * ceiling

    total_headroom = sum(headroom.values())
    if total_headroom <= 0:
        return {
            "allocations": {},
            "total_required_kg": round(required, 2),
            "total_allocated_kg": 0.0,
            "unallocated_kg": round(required, 2),
            "feasible": False,
        }

    allocatable = min(required, total_headroom)
    allocations = {}
    for category, category_headroom in headroom.items():
        if category_headroom <= 0:
            continue
        share = category_headroom / total_headroom
        amount = allocatable * share
        current = max(0.0, float(contributors[category]))
        allocations[category] = {
            "current_kg": round(current, 2),
            "reduce_by_kg": round(amount, 2),
            "target_kg": round(max(0.0, current - amount), 2),
            "percent_of_total_reduction": round(share * 100.0, 1),
            "percent_cut_of_category": round((amount / current * 100.0) if current > 0 else 0.0, 1),
            "ceiling": REDUCTION_CEILINGS.get(category, DEFAULT_REDUCTION_CEILING),
            "weight": CATEGORY_WEIGHTS.get(category, 0.0),
        }

    total_allocated = sum(item["reduce_by_kg"] for item in allocations.values())
    return {
        "allocations": allocations,
        "total_required_kg": round(required, 2),
        "total_allocated_kg": round(total_allocated, 2),
        "unallocated_kg": round(max(0.0, required - allocatable), 2),
        "feasible": required <= total_headroom,
    }


def suggest_feasible_target(baseline_kg: float, contributors: dict[str, float]) -> float:
    """
    The lowest target that is actually reachable given the reduction ceilings.

    Used by the goal form to stop a user committing to something arithmetically
    impossible, which is the fastest way to make them abandon the feature.
    """
    baseline = _coerce_positive_number(baseline_kg, "baseline_kg", allow_zero=False)
    if not contributors:
        return round(baseline * (1 - DEFAULT_REDUCTION_CEILING), 2)

    total_headroom = 0.0
    for category, emission in contributors.items():
        try:
            value = max(0.0, float(emission))
        except (TypeError, ValueError):
            continue
        total_headroom += value * REDUCTION_CEILINGS.get(category, DEFAULT_REDUCTION_CEILING)

    return round(max(0.0, baseline - total_headroom), 2)


# --- Presentation helpers ---------------------------------------------------

def summarize_goal(goal: dict[str, Any], progress: dict[str, Any]) -> str:
    """One-sentence summary for the dashboard banner and the PDF report."""
    status = progress["status"]
    target = progress["target_kg"]
    current = progress["current_kg"]
    days = progress["days_remaining"]

    if status == STATUS_ACHIEVED:
        return (
            f"Goal achieved — you are at {current:,.0f} kg CO2/year, "
            f"at or below your {target:,.0f} kg target."
        )
    if not progress["has_data"]:
        return (
            f"Goal set: reach {target:,.0f} kg CO2/year within {days} days. "
            "Log an assessment to start tracking progress."
        )
    if status == STATUS_AHEAD:
        return (
            f"Ahead of schedule — {progress['percent_complete']:.0f}% of the way to "
            f"{target:,.0f} kg with {days} days left."
        )
    if status == STATUS_ON_TRACK:
        return (
            f"On track — {progress['percent_complete']:.0f}% complete, "
            f"{progress['remaining_kg']:,.0f} kg still to cut in {days} days."
        )
    if status == STATUS_AT_RISK:
        return (
            f"At risk — you are {progress['variance_kg']:,.0f} kg above the pathway. "
            f"Cutting {progress['pace_needed_from_now_kg_per_month']:,.0f} kg/month "
            "from here still lands the goal."
        )
    return (
        f"Off track — projected to finish at {progress['projected_final_kg']:,.0f} kg, "
        f"{progress['projected_shortfall_kg']:,.0f} kg short of your target."
    )


def pathway_to_series(pathway: list[dict[str, Any]]) -> tuple[list[datetime.date], list[float]]:
    """Split a pathway into parallel date/value lists for charting."""
    return (
        [point["date"] for point in pathway],
        [point["target_kg"] for point in pathway],
    )


def goal_to_dict(goal: dict[str, Any]) -> dict[str, Any]:
    """JSON-safe representation, for export and for storing in session state."""
    return {
        "id": goal.get("id"),
        "user_id": goal.get("user_id"),
        "baseline_kg": goal["baseline_kg"],
        "target_kg": goal["target_kg"],
        "start_date": _coerce_date(goal["start_date"], "start_date").isoformat(),
        "target_date": _coerce_date(goal["target_date"], "target_date").isoformat(),
        "status": goal.get("status", GOAL_ACTIVE),
    }
