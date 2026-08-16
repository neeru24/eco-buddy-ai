"""
Assessment Data Quality & Anomaly Detection.

EcoBuddy AI stores every assessment it is given and then trusts all of it
equally — for charts, trends, the ARIMA forecast, the leaderboard and the eco
score. Nothing checks that the stored history is *sane*.

`calculate_footprint()` clamps a **single** calculation to MAX_DISTANCE /
MAX_ELECTRICITY / MAX_FLIGHTS, but nothing ever looks at the history as a
*series*. That gap lets several classes of defect through:

    outliers        one 40,000 kg row wrecks every chart axis and the trend
    duplicates      double-clicking "Analyze" writes two near-identical rows
    jumps           5,000 -> 500 -> 5,000 kg is data entry, not behaviour
    drift           a stored footprint that its own inputs no longer produce
    timestamps      future dates and out-of-order rows break the forecast
    missing fields  imported NULL/zero rows counted as real in averages
    staleness       a "current" footprint that is actually 14 months old

Every detector here is an independent pure function with no Streamlit import,
so each is directly testable and the set is easy to extend.

Design note on outlier detection
--------------------------------
This module uses a **modified Z-score built on the median absolute deviation**,
not mean and standard deviation. At the sample sizes this app actually has —
often fewer than ten assessments — a single extreme value inflates the standard
deviation enough to mask itself, so a mean/stdev test reliably fails to flag
the exact row it exists to catch. The median and MAD are resistant to that.
"""

import datetime
import math
import statistics
from typing import Any

# --- Severities -------------------------------------------------------------

SEVERITY_INFO = "INFO"
SEVERITY_WARNING = "WARNING"
SEVERITY_CRITICAL = "CRITICAL"

SEVERITY_ORDER = [SEVERITY_CRITICAL, SEVERITY_WARNING, SEVERITY_INFO]

# How many confidence points each issue of a given severity costs.
SEVERITY_PENALTY = {
    SEVERITY_CRITICAL: 25.0,
    SEVERITY_WARNING: 10.0,
    SEVERITY_INFO: 3.0,
}

# --- Issue codes ------------------------------------------------------------

CODE_OUTLIER = "outlier"
CODE_DUPLICATE = "duplicate"
CODE_IMPLAUSIBLE_JUMP = "implausible_jump"
CODE_CALCULATION_DRIFT = "calculation_drift"
CODE_FUTURE_DATE = "future_date"
CODE_OUT_OF_ORDER = "out_of_order"
CODE_DUPLICATE_TIMESTAMP = "duplicate_timestamp"
CODE_MISSING_FIELD = "missing_field"
CODE_ZERO_FOOTPRINT = "zero_footprint"
CODE_STALE_DATA = "stale_data"
CODE_SMALL_SAMPLE = "small_sample"

# --- Thresholds -------------------------------------------------------------

# 3.5 is the conventional cutoff for a modified Z-score.
DEFAULT_Z_THRESHOLD = 3.5

# Two submissions within this window with near-identical inputs are one event.
DEFAULT_DUPLICATE_WINDOW_MINUTES = 10
DEFAULT_DUPLICATE_TOLERANCE = 0.01

# A consecutive footprint changing by more than this multiple is data entry.
DEFAULT_MAX_JUMP_RATIO = 5.0

# Tolerance when re-deriving a stored footprint from its own inputs.
DEFAULT_DRIFT_TOLERANCE_PERCENT = 5.0

DEFAULT_MAX_AGE_DAYS = 180

# Below this many records the statistics are not meaningful on their own.
MIN_MEANINGFUL_SAMPLE = 5

# Required fields on an assessment record, and what counts as absent.
REQUIRED_FIELDS = ("date", "transport", "diet", "footprint")

GRADE_BANDS = [
    (90.0, "A"),
    (80.0, "B"),
    (70.0, "C"),
    (60.0, "D"),
    (0.0, "F"),
]


# --- Record normalisation ---------------------------------------------------

def _parse_timestamp(value: datetime.datetime | datetime.date | str) -> datetime.datetime | None:
    """Parse the several date shapes the database and importers produce."""
    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, datetime.date):
        return datetime.datetime.combine(value, datetime.time.min)
    if isinstance(value, str):
        text = value.strip().replace(" ", "T")
        if not text:
            return None
        try:
            return datetime.datetime.fromisoformat(text)
        except ValueError:
            for pattern in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
                try:
                    return datetime.datetime.strptime(value.strip()[:10], pattern)
                except ValueError:
                    continue
    return None


def _to_float(value: Any) -> float | None:
    """Coerce to float, returning None rather than raising on bad input."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def normalize_records(
    assessments: list[dict[str, Any]] | list[tuple[Any, ...]],
) -> list[dict[str, Any]]:
    """
    Turn raw rows into dicts the detectors can work with.

    Accepts the nine-column tuple `get_assessments()` returns:
        (id, date, transport, distance, electricity, diet, flights,
         footprint, eco_score)
    as well as dicts. Unparseable rows are kept with None fields rather than
    dropped, because a row that cannot be parsed is itself a finding.
    """
    records = []
    for index, row in enumerate(assessments or []):
        if isinstance(row, dict):
            raw = {
                "id": row.get("id", index),
                "date": row.get("date"),
                "transport": row.get("transport"),
                "distance": row.get("distance"),
                "electricity": row.get("electricity"),
                "diet": row.get("diet"),
                "flights": row.get("flights"),
                "footprint": row.get("footprint"),
                "eco_score": row.get("eco_score"),
            }
        elif isinstance(row, (list, tuple)) and len(row) >= 9:
            raw = {
                "id": row[0],
                "date": row[1],
                "transport": row[2],
                "distance": row[3],
                "electricity": row[4],
                "diet": row[5],
                "flights": row[6],
                "footprint": row[7],
                "eco_score": row[8],
            }
        else:
            continue

        records.append({
            "id": raw["id"],
            "raw_date": raw["date"],
            "timestamp": _parse_timestamp(raw["date"]),
            "transport": raw["transport"],
            "distance": _to_float(raw["distance"]),
            "electricity": _to_float(raw["electricity"]),
            "diet": raw["diet"],
            "flights": _to_float(raw["flights"]),
            "footprint": _to_float(raw["footprint"]),
            "eco_score": _to_float(raw["eco_score"]),
        })
    return records


def make_issue(
    code: str,
    severity: str,
    message: str,
    record_ids: list[Any] | None = None,
    suggested_action: str = "",
) -> dict[str, Any]:
    """One detected defect."""
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "record_ids": list(record_ids or []),
        "suggested_action": suggested_action,
    }


# --- Detectors --------------------------------------------------------------

def modified_z_scores(values: list[float | None]) -> list[float]:
    """
    Modified Z-scores based on the median absolute deviation.

    Returns an empty list for fewer than three values — a Z-score over two
    points is meaningless. When the MAD is zero (more than half the values are
    identical) it falls back to the mean absolute deviation, which still
    separates a lone outlier from a block of identical readings.
    """
    numbers = [value for value in values if value is not None]
    if len(numbers) < 3:
        return []

    median = statistics.median(numbers)
    deviations = [abs(number - median) for number in numbers]
    mad = statistics.median(deviations)

    if mad == 0:
        mean_deviation = sum(deviations) / len(deviations)
        if mean_deviation == 0:
            return [0.0] * len(numbers)
        return [0.7979 * (number - median) / mean_deviation for number in numbers]

    return [0.6745 * (number - median) / mad for number in numbers]


def detect_outliers(
    records: list[dict[str, Any]],
    z_threshold: float = DEFAULT_Z_THRESHOLD,
) -> list[dict[str, Any]]:
    """Flag footprints that sit far from the median of the series."""
    usable = [record for record in records if record["footprint"] is not None]
    if len(usable) < 3:
        return []

    scores = modified_z_scores([record["footprint"] for record in usable])
    if not scores:
        return []

    issues = []
    for record, score in zip(usable, scores):
        if abs(score) > z_threshold:
            direction = "far above" if score > 0 else "far below"
            issues.append(make_issue(
                CODE_OUTLIER,
                SEVERITY_WARNING,
                (
                    f"Assessment {record['id']} ({record['footprint']:,.0f} kg CO2) is "
                    f"{direction} the rest of your history "
                    f"(modified Z-score {score:.1f})."
                ),
                [record["id"]],
                "Check the inputs for this assessment; a single mistyped value "
                "distorts every chart and trend built from this history.",
            ))
    return issues


def detect_duplicates(
    records: list[dict[str, Any]],
    time_window_minutes: float = DEFAULT_DUPLICATE_WINDOW_MINUTES,
    tolerance: float = DEFAULT_DUPLICATE_TOLERANCE,
) -> list[dict[str, Any]]:
    """
    Flag near-identical assessments submitted within a short window.

    The unique index on `assessments.trip_id` only protects rows that *have* a
    trip_id. The normal assessment path passes `trip_id=None`, so a double
    click on "Analyze" writes two rows and nothing stops it.
    """
    usable = sorted(
        [record for record in records if record["timestamp"] is not None],
        key=lambda record: record["timestamp"],
    )
    if len(usable) < 2:
        return []

    window = datetime.timedelta(minutes=time_window_minutes)
    issues = []

    for previous, current in zip(usable, usable[1:]):
        if current["timestamp"] - previous["timestamp"] > window:
            continue
        if not _inputs_match(previous, current, tolerance):
            continue
        gap_seconds = (current["timestamp"] - previous["timestamp"]).total_seconds()
        issues.append(make_issue(
            CODE_DUPLICATE,
            SEVERITY_WARNING,
            (
                f"Assessments {previous['id']} and {current['id']} have near-identical "
                f"inputs and were saved {gap_seconds:.0f} seconds apart."
            ),
            [previous["id"], current["id"]],
            "Likely a double submission. Remove one so it is not counted twice "
            "in averages and streaks.",
        ))
    return issues


def _inputs_match(left: dict[str, Any], right: dict[str, Any], tolerance: float) -> bool:
    """True when two records describe the same lifestyle inputs."""
    if left["transport"] != right["transport"] or left["diet"] != right["diet"]:
        return False

    for field in ("distance", "electricity", "flights", "footprint"):
        a = left[field]
        b = right[field]
        if a is None or b is None:
            if a is not b:
                return False
            continue
        scale = max(abs(a), abs(b), 1.0)
        if abs(a - b) / scale > tolerance:
            return False
    return True


def detect_implausible_jumps(
    records: list[dict[str, Any]],
    max_ratio: float = DEFAULT_MAX_JUMP_RATIO,
) -> list[dict[str, Any]]:
    """
    Flag consecutive footprints that change by an implausible multiple.

    Checked in both directions: a sudden collapse is as suspicious as a sudden
    spike, and both distort a trend line identically.
    """
    usable = sorted(
        [
            record for record in records
            if record["timestamp"] is not None
            and record["footprint"] is not None
            and record["footprint"] > 0
        ],
        key=lambda record: record["timestamp"],
    )
    if len(usable) < 2:
        return []

    issues = []
    for previous, current in zip(usable, usable[1:]):
        ratio = current["footprint"] / previous["footprint"]
        if ratio > max_ratio or ratio < (1.0 / max_ratio):
            direction = "increased" if ratio > 1 else "dropped"
            factor = ratio if ratio > 1 else 1.0 / ratio
            issues.append(make_issue(
                CODE_IMPLAUSIBLE_JUMP,
                SEVERITY_WARNING,
                (
                    f"Footprint {direction} {factor:.1f}x between assessments "
                    f"{previous['id']} ({previous['footprint']:,.0f} kg) and "
                    f"{current['id']} ({current['footprint']:,.0f} kg)."
                ),
                [previous["id"], current["id"]],
                "A change this large over one step is usually a data-entry error "
                "rather than a real lifestyle change. Verify both entries.",
            ))
    return issues


def detect_calculation_drift(
    records: list[dict[str, Any]],
    tolerance_percent: float = DEFAULT_DRIFT_TOLERANCE_PERCENT,
) -> list[dict[str, Any]]:
    """
    Flag rows whose stored footprint no longer matches their own inputs.

    Happens after an emission factor change or a hand-edited import. Imported
    from `emissions` lazily so this module stays importable without the API
    layer, and so a failure to recompute degrades to "no finding" rather than
    breaking the whole audit.
    """
    try:
        from emissions import calculate_footprint
    except ImportError:
        return []

    issues = []
    for record in records:
        if record["footprint"] is None or record["footprint"] <= 0:
            continue
        if record["transport"] is None or record["diet"] is None:
            continue
        if record["distance"] is None or record["electricity"] is None:
            continue

        try:
            expected, _ = calculate_footprint(
                record["transport"],
                record["distance"],
                record["electricity"],
                record["diet"],
                record["flights"] or 0,
            )
        except (ValueError, KeyError, TypeError):
            # Inputs this row cannot be recomputed from are reported by
            # detect_missing_fields, not here.
            continue

        if expected <= 0:
            continue
        drift_percent = abs(record["footprint"] - expected) / expected * 100.0
        if drift_percent > tolerance_percent:
            issues.append(make_issue(
                CODE_CALCULATION_DRIFT,
                SEVERITY_INFO,
                (
                    f"Assessment {record['id']} stores {record['footprint']:,.0f} kg but "
                    f"its own inputs now produce {expected:,.0f} kg "
                    f"({drift_percent:.0f}% apart)."
                ),
                [record["id"]],
                "The emission factors have changed since this was saved, or the "
                "row was edited outside the app. The stored value is kept as the "
                "historical record.",
            ))
    return issues


def detect_timestamp_issues(
    records: list[dict[str, Any]],
    now: datetime.datetime | None = None,
) -> list[dict[str, Any]]:
    """Flag future dates, unparseable dates and exact duplicate timestamps."""
    now = now or datetime.datetime.now()
    issues = []

    unparseable = [
        record["id"] for record in records
        if record["timestamp"] is None and record["raw_date"] is not None
    ]
    if unparseable:
        issues.append(make_issue(
            CODE_MISSING_FIELD,
            SEVERITY_CRITICAL,
            f"{len(unparseable)} assessment(s) have a date that cannot be read.",
            unparseable,
            "These rows are excluded from every time-based chart and forecast.",
        ))

    future = [
        record["id"] for record in records
        if record["timestamp"] is not None and record["timestamp"] > now
    ]
    if future:
        issues.append(make_issue(
            CODE_FUTURE_DATE,
            SEVERITY_CRITICAL,
            f"{len(future)} assessment(s) are dated in the future.",
            future,
            "Future-dated rows corrupt the forecast and the streak calculation. "
            "Correct the dates.",
        ))

    seen = {}
    duplicated = []
    for record in records:
        if record["timestamp"] is None:
            continue
        key = record["timestamp"]
        if key in seen:
            duplicated.extend([seen[key], record["id"]])
        else:
            seen[key] = record["id"]
    if duplicated:
        issues.append(make_issue(
            CODE_DUPLICATE_TIMESTAMP,
            SEVERITY_INFO,
            f"{len(set(duplicated))} assessment(s) share an identical timestamp.",
            sorted(set(duplicated), key=str),
            "Ordering between these rows is arbitrary, which can make a trend "
            "line appear to zig-zag.",
        ))

    return issues


def detect_out_of_order(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Flag a history that is not chronologically ordered as stored.

    `get_assessments()` orders by date DESC, so a reversed pair here means the
    dates themselves disagree with insertion order.
    """
    usable = [record for record in records if record["timestamp"] is not None]
    if len(usable) < 2:
        return []

    ascending = all(a["timestamp"] <= b["timestamp"] for a, b in zip(usable, usable[1:]))
    descending = all(a["timestamp"] >= b["timestamp"] for a, b in zip(usable, usable[1:]))

    if ascending or descending:
        return []

    return [make_issue(
        CODE_OUT_OF_ORDER,
        SEVERITY_INFO,
        "Assessment dates are not in a consistent chronological order.",
        [record["id"] for record in usable],
        "Charts sort before plotting, so this is cosmetic — but it usually "
        "indicates rows imported with inconsistent date formats.",
    )]


def detect_missing_fields(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flag null, blank or degenerate required fields."""
    issues = []
    missing_by_field = {}

    for record in records:
        for field in REQUIRED_FIELDS:
            key = "raw_date" if field == "date" else field
            value = record[key]
            if value is None or (isinstance(value, str) and not value.strip()):
                missing_by_field.setdefault(field, []).append(record["id"])

    for field, ids in sorted(missing_by_field.items()):
        issues.append(make_issue(
            CODE_MISSING_FIELD,
            SEVERITY_CRITICAL,
            f"{len(ids)} assessment(s) are missing '{field}'.",
            ids,
            f"Rows without '{field}' cannot be analysed reliably and are usually "
            "the result of a partial import.",
        ))

    zero_footprints = [
        record["id"] for record in records
        if record["footprint"] is not None and record["footprint"] == 0
    ]
    if zero_footprints:
        issues.append(make_issue(
            CODE_ZERO_FOOTPRINT,
            SEVERITY_WARNING,
            f"{len(zero_footprints)} assessment(s) record a footprint of exactly zero.",
            zero_footprints,
            "A zero footprint is almost never real. These rows drag every average "
            "down while looking like genuine progress.",
        ))

    return issues


def detect_staleness(
    records: list[dict[str, Any]],
    max_age_days: float = DEFAULT_MAX_AGE_DAYS,
    now: datetime.datetime | None = None,
) -> list[dict[str, Any]]:
    """Flag a history whose most recent entry is too old to represent 'now'."""
    now = now or datetime.datetime.now()
    timestamps = [
        record["timestamp"] for record in records
        if record["timestamp"] is not None and record["timestamp"] <= now
    ]
    if not timestamps:
        return []

    age_days = (now - max(timestamps)).days
    if age_days <= max_age_days:
        return []

    return [make_issue(
        CODE_STALE_DATA,
        SEVERITY_INFO,
        f"Your most recent assessment is {age_days} days old.",
        [],
        "Your dashboard is describing your lifestyle as it was, not as it is. "
        "Run a fresh assessment.",
    )]


def detect_small_sample(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flag a history too short for its statistics to mean much."""
    usable = [record for record in records if record["footprint"] is not None]
    if len(usable) >= MIN_MEANINGFUL_SAMPLE:
        return []

    return [make_issue(
        CODE_SMALL_SAMPLE,
        SEVERITY_INFO,
        (
            f"Only {len(usable)} usable assessment(s) recorded — "
            f"{MIN_MEANINGFUL_SAMPLE} or more gives meaningful trends."
        ),
        [],
        "Trends, forecasts and outlier detection all need more data before they "
        "can be relied on.",
    )]


# --- Aggregation ------------------------------------------------------------

DETECTORS = (
    detect_missing_fields,
    detect_timestamp_issues,
    detect_out_of_order,
    detect_outliers,
    detect_duplicates,
    detect_implausible_jumps,
    detect_calculation_drift,
    detect_staleness,
    detect_small_sample,
)


def audit_assessments(
    assessments: list[dict[str, Any]] | list[tuple[Any, ...]],
    now: datetime.datetime | None = None,
    include_drift: bool = True,
) -> dict[str, Any]:
    """
    Run every detector and return a full quality report.

    `include_drift` exists because recomputing every row calls into
    `emissions`, which is the one detector with a non-trivial cost.
    """
    records = normalize_records(assessments)
    issues = []

    for detector in DETECTORS:
        if detector is detect_calculation_drift and not include_drift:
            continue
        try:
            if detector in (detect_timestamp_issues, detect_staleness):
                issues.extend(detector(records, now=now))
            else:
                issues.extend(detector(records))
        except Exception:
            # A single failing detector must never take down the whole audit.
            continue

    score = calculate_confidence_score(issues, len(records))
    return {
        "record_count": len(records),
        "issues": issues,
        "issue_count": len(issues),
        "confidence_score": score,
        "grade": quality_grade(score),
        "by_severity": group_issues_by_severity(issues),
        "flagged_record_ids": sorted(
            {record_id for issue in issues for record_id in issue["record_ids"]},
            key=str,
        ),
    }


def calculate_confidence_score(issues: list[dict[str, Any]], record_count: int) -> float:
    """
    A 0-100 confidence score for the dataset.

    Penalties are weighted by severity and scaled by how much of the history is
    affected, so one bad row in fifty costs far less than one bad row in three.
    A small-sample penalty is applied on top, because a two-record history with
    no detected issues is not actually trustworthy — there is simply not enough
    of it to find anything wrong with.
    """
    if record_count <= 0:
        return 0.0

    score = 100.0
    for issue in issues:
        penalty = SEVERITY_PENALTY.get(issue["severity"], 5.0)
        affected = len(issue["record_ids"]) or 1
        proportion = min(1.0, affected / record_count)
        # Half the penalty is fixed (the defect exists at all) and half scales
        # with how much of the history it touches.
        score -= penalty * (0.5 + 0.5 * proportion)

    if record_count < MIN_MEANINGFUL_SAMPLE:
        score -= (MIN_MEANINGFUL_SAMPLE - record_count) * 5.0

    return round(max(0.0, min(100.0, score)), 1)


def quality_grade(score: float) -> str:
    """Map a confidence score onto an A-F band."""
    for threshold, grade in GRADE_BANDS:
        if score >= threshold:
            return grade
    return "F"


def group_issues_by_severity(
    issues: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Bucket issues by severity, most severe first."""
    grouped = {severity: [] for severity in SEVERITY_ORDER}
    for issue in issues:
        grouped.setdefault(issue["severity"], []).append(issue)
    return grouped


def summarize_report(report: dict[str, Any]) -> str:
    """One-line human summary for a dashboard banner."""
    if report["record_count"] == 0:
        return "No assessments recorded yet — nothing to check."

    critical = len(report["by_severity"].get(SEVERITY_CRITICAL, []))
    warnings = len(report["by_severity"].get(SEVERITY_WARNING, []))

    if not report["issues"]:
        return (
            f"Grade {report['grade']} — no data quality issues found across "
            f"{report['record_count']} assessment(s)."
        )
    if critical:
        return (
            f"Grade {report['grade']} — {critical} critical issue(s) and "
            f"{warnings} warning(s) found. Some records cannot be analysed reliably."
        )
    if warnings:
        return (
            f"Grade {report['grade']} — {warnings} warning(s) found. Your history "
            "is usable but some records look suspicious."
        )
    return (
        f"Grade {report['grade']} — only minor observations across "
        f"{report['record_count']} assessment(s)."
    )


def filter_clean_records(
    assessments: list[dict[str, Any]] | list[tuple[Any, ...]],
    report: dict[str, Any] | None = None,
    severities: tuple[str, ...] = (SEVERITY_CRITICAL,),
) -> list[dict[str, Any]] | list[tuple[Any, ...]]:
    """
    Return the subset of rows safe to feed to forecasting and the leaderboard.

    Defaults to excluding only CRITICAL rows: a genuine high-emission month is
    an outlier worth keeping, and silently dropping every flagged row would
    hide exactly the behaviour the app exists to surface.
    """
    report = report or audit_assessments(assessments)

    excluded = {
        record_id
        for issue in report["issues"]
        if issue["severity"] in severities
        for record_id in issue["record_ids"]
    }
    if not excluded:
        return list(assessments or [])

    kept = []
    for row in assessments or []:
        if isinstance(row, dict):
            record_id = row.get("id")
        elif isinstance(row, (list, tuple)) and row:
            record_id = row[0]
        else:
            continue
        if record_id not in excluded:
            kept.append(row)
    return kept


def to_dict(report: dict[str, Any]) -> dict[str, Any]:
    """JSON-safe representation of a report, for export and logging."""
    return {
        "record_count": report["record_count"],
        "confidence_score": report["confidence_score"],
        "grade": report["grade"],
        "issue_count": report["issue_count"],
        "summary": summarize_report(report),
        "issues": [
            {
                "code": issue["code"],
                "severity": issue["severity"],
                "message": issue["message"],
                "record_ids": [str(record_id) for record_id in issue["record_ids"]],
                "suggested_action": issue["suggested_action"],
            }
            for issue in report["issues"]
        ],
    }
