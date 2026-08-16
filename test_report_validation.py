"""Tests for report data validation and PDF blocking."""

from pathlib import Path

import pytest

from report import generate_pdf
from report_validation import validate_report_data


@pytest.mark.parametrize(
    ("total", "eco_score", "insight", "expected_error"),
    [
        (None, 50, "Insight", "Carbon footprint is required."),
        (10, None, "Insight", "Eco score is required."),
        (10, 50, None, "Key insight is required."),
        (
            "not-a-number",
            50,
            "Insight",
            "Carbon footprint must be a valid number.",
        ),
        (10, "bad", "Insight", "Eco score must be a valid number."),
        (-1, 50, "Insight", "Carbon footprint cannot be negative."),
        (10, -1, "Insight", "Eco score must be between 0 and 100."),
        (10, 101, "Insight", "Eco score must be between 0 and 100."),
        (
            float("nan"),
            50,
            "Insight",
            "Carbon footprint must be a finite number.",
        ),
        (
            10,
            float("inf"),
            "Insight",
            "Eco score must be a finite number.",
        ),
        (10, 50, "   ", "Key insight cannot be empty."),
    ],
)
def test_invalid_report_values_are_rejected(
    total,
    eco_score,
    insight,
    expected_error,
):
    result = validate_report_data(total, eco_score, insight)

    assert result.is_valid is False
    assert expected_error in result.errors
    assert result.cleaned_data == {}


def test_valid_report_values_are_normalised():
    result = validate_report_data(
        "12.5",
        "87",
        "  Use   public transport.  ",
    )

    assert result.is_valid is True
    assert result.errors == ()
    assert result.cleaned_data == {
        "total": 12.5,
        "eco_score": 87.0,
        "insight": "Use public transport.",
    }


def test_pdf_generation_is_blocked_for_invalid_data():
    assert generate_pdf(None, 50, "Insight") is None
    assert generate_pdf(10, 101, "Insight") is None
    assert generate_pdf(10, 50, "") is None


def test_valid_data_generates_a_non_empty_pdf():
    path = generate_pdf(
        12.5,
        87,
        "Use public transport more often.",
    )

    assert path is not None
    pdf_path = Path(path)
    try:
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 100
        assert pdf_path.read_bytes().startswith(b"%PDF")
    finally:
        if pdf_path.exists():
            pdf_path.unlink()
