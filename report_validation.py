"""Validation helpers for EcoBuddy PDF report generation."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping


MAX_REASONABLE_FOOTPRINT_KG = 1_000_000.0
MAX_INSIGHT_LENGTH = 10_000


@dataclass(frozen=True)
class ReportValidationResult:
    """Result returned after validating report-generation inputs."""

    is_valid: bool
    errors: tuple[str, ...]
    cleaned_data: Mapping[str, Any]


def _as_finite_number(
    value: Any,
    field_label: str,
) -> tuple[float | None, str | None]:
    """Convert a value to a finite float or return a user-facing error."""
    if value is None or isinstance(value, bool):
        return None, f"{field_label} is required."

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None, f"{field_label} must be a valid number."

    if not math.isfinite(number):
        return None, f"{field_label} must be a finite number."

    return number, None


def validate_report_data(
    total: Any,
    eco_score: Any,
    insight: Any,
) -> ReportValidationResult:
    """Validate and normalise the values required by the PDF report."""
    errors: list[str] = []
    cleaned: dict[str, Any] = {}

    footprint, footprint_error = _as_finite_number(
        total,
        "Carbon footprint",
    )
    if footprint_error:
        errors.append(footprint_error)
    elif footprint is not None:
        if footprint < 0:
            errors.append("Carbon footprint cannot be negative.")
        elif footprint > MAX_REASONABLE_FOOTPRINT_KG:
            errors.append(
                "Carbon footprint is outside the supported reporting range."
            )
        else:
            cleaned["total"] = footprint

    score, score_error = _as_finite_number(
        eco_score,
        "Eco score",
    )
    if score_error:
        errors.append(score_error)
    elif score is not None:
        if score < 0 or score > 100:
            errors.append("Eco score must be between 0 and 100.")
        else:
            cleaned["eco_score"] = round(score, 2)

    if insight is None:
        errors.append("Key insight is required.")
    elif not isinstance(insight, str):
        errors.append("Key insight must be text.")
    else:
        cleaned_insight = " ".join(insight.split())
        if not cleaned_insight:
            errors.append("Key insight cannot be empty.")
        elif len(cleaned_insight) > MAX_INSIGHT_LENGTH:
            errors.append(
                f"Key insight must be {MAX_INSIGHT_LENGTH:,} characters or fewer."
            )
        else:
            cleaned["insight"] = cleaned_insight

    return ReportValidationResult(
        is_valid=not errors,
        errors=tuple(errors),
        cleaned_data=cleaned if not errors else {},
    )
