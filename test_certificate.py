"""Tests for sustainability milestone certificate generation."""

import os
from pathlib import Path
from unittest.mock import patch

from certificate import generate_certificate


def test_generate_certificate_success():
    """Test generating a certificate with valid data produces a non-empty PDF."""
    path = generate_certificate(
        username="Test User",
        achievement_title="Eco Legend",
        achievement_description="Completed 10 challenges",
        eco_score=95.0,
        date_achieved="January 1, 2026"
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


def test_generate_certificate_long_text():
    """Test generating a certificate with excessively long strings doesn't fail."""
    path = generate_certificate(
        username="A" * 100,
        achievement_title="B" * 100,
        achievement_description="C" * 500,
        eco_score=100.0,
        date_achieved="January 1, 2026"
    )
    
    assert path is not None
    pdf_path = Path(path)
    try:
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 100
    finally:
        if pdf_path.exists():
            pdf_path.unlink()


def test_generate_certificate_unicode():
    """Test generating a certificate with unicode characters."""
    path = generate_certificate(
        username="ユーザー",
        achievement_title="🏆 Champion",
        achievement_description="Save the 🌍",
        eco_score=88.5,
        date_achieved="January 1, 2026"
    )
    
    assert path is not None
    pdf_path = Path(path)
    try:
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 100
    finally:
        if pdf_path.exists():
            pdf_path.unlink()


def test_generate_certificate_no_score():
    """Test generating a certificate when eco score is missing."""
    path = generate_certificate(
        username="Test",
        achievement_title="Test",
        achievement_description="Test",
        eco_score=None,
        date_achieved="Jan 1"
    )
    
    assert path is not None
    pdf_path = Path(path)
    try:
        assert pdf_path.exists()
    finally:
        if pdf_path.exists():
            pdf_path.unlink()


@patch("certificate.os.path.exists")
def test_generate_certificate_missing_font(mock_exists):
    """Test certificate generation successfully falls back when font is missing."""
    mock_exists.return_value = False  # Simulate font missing
    
    path = generate_certificate(
        username="Test User",
        achievement_title="Missing Font Test",
        achievement_description="Testing fallback to Helvetica",
        eco_score=50.0,
        date_achieved="January 1, 2026"
    )
    
    assert path is not None
    pdf_path = Path(path)
    try:
        assert pdf_path.exists()
    finally:
        if pdf_path.exists():
            pdf_path.unlink()
