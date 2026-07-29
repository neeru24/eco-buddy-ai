"""
Tests for ocr_utils.py - OCR and text parsing utilities.

Tests:
1. extract_text_from_file - PDF and image text extraction
2. parse_energy_consumption - Energy value extraction from text
3. Edge cases and error handling
"""

import pytest
from unittest.mock import patch, MagicMock
import io
from ocr_utils import extract_text_from_file, parse_energy_consumption


class TestExtractTextFromFile:
    """Tests for the extract_text_from_file function."""

    def test_extract_text_from_pdf(self):
        """Test extracting text from a PDF file."""
        # Create a mock PDF-like uploaded file
        mock_pdf = MagicMock()
        mock_pdf.type = "application/pdf"
        
        # Mock pdfplumber behavior
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Energy Consumption: 450 kWh\nTotal Usage: 400"
        
        with patch('ocr_utils.pdfplumber.open') as mock_open:
            mock_pdf_obj = MagicMock()
            mock_pdf_obj.__enter__ = MagicMock(return_value=mock_pdf_obj)
            mock_pdf_obj.__exit__ = MagicMock(return_value=False)
            mock_pdf_obj.pages = [mock_page]
            mock_open.return_value = mock_pdf_obj
            
            result = extract_text_from_file(mock_pdf)
            
            assert "Energy Consumption" in result
            assert "450" in result

    def test_extract_text_from_image(self):
        """Test extracting text from an image file."""
        # Create a mock image uploaded file
        mock_image = MagicMock()
        mock_image.type = "image/png"
        
        # Mock PIL behavior
        with patch('ocr_utils.Image.open') as mock_open:
            mock_img = MagicMock()
            mock_open.return_value = mock_img
            
            with patch('ocr_utils.pytesseract.image_to_string') as mock_ocr:
                mock_ocr.return_value = "Total Energy Usage: 350 kWh"
                
                result = extract_text_from_file(mock_image)
                
                assert "Energy" in result
                assert "350" in result

    def test_extract_text_from_empty_pdf(self):
        """Test extracting text from PDF with no content."""
        mock_pdf = MagicMock()
        mock_pdf.type = "application/pdf"
        
        with patch('ocr_utils.pdfplumber.open') as mock_open:
            mock_pdf_obj = MagicMock()
            mock_pdf_obj.__enter__ = MagicMock(return_value=mock_pdf_obj)
            mock_pdf_obj.__exit__ = MagicMock(return_value=False)
            mock_pdf_obj.pages = []
            mock_open.return_value = mock_pdf_obj
            
            result = extract_text_from_file(mock_pdf)
            
            assert result == ""

    def test_extract_text_handles_exception(self):
        """Test that exceptions are handled gracefully."""
        mock_file = MagicMock()
        mock_file.type = "application/pdf"
        
        with patch('ocr_utils.pdfplumber.open') as mock_open:
            mock_open.side_effect = Exception("PDF Error")
            
            result = extract_text_from_file(mock_file)
            
            # Should return empty string on error
            assert result == ""

    def test_extract_text_with_unknown_file_type(self):
        """Test extracting text from unknown file type."""
        mock_file = MagicMock()
        mock_file.type = "application/unknown"
        
        result = extract_text_from_file(mock_file)
        
        assert result == ""


class TestParseEnergyConsumption:
    """Tests for the parse_energy_consumption function."""

    def test_parse_simple_kwh_value(self):
        """Test parsing simple kWh value."""
        text = "350 kWh"
        result = parse_energy_consumption(text)
        
        assert result == 350.0

    def test_parse_with_comma_separator(self):
        """Test parsing value with comma separator."""
        text = "Total Consumption: 1,200.5 kWh"
        result = parse_energy_consumption(text)
        
        assert result == 1200.5

    def test_parse_multiple_kwh_patterns(self):
        """Test parsing multiple kWh values (returns first match)."""
        text = "Usage: 300 kWh, Previous: 450 kWh"
        result = parse_energy_consumption(text)
        
        assert result == 300.0

    def test_parse_case_insensitive(self):
        """Test that parsing is case-insensitive for kWh."""
        text = "Total: 450 kwh"
        result = parse_energy_consumption(text)
        
        assert result == 450.0

    def test_parse_total_consumption_pattern(self):
        """Test parsing 'Total Consumption' pattern."""
        text = "Total Consumption: 400 kWh"
        result = parse_energy_consumption(text)
        
        assert result == 400.0

    def test_parse_usage_pattern(self):
        """Test parsing 'Usage' pattern."""
        text = "Electricity Usage: 350"
        result = parse_energy_consumption(text)
        
        assert result == 350.0

    def test_parse_no_match_returns_none(self):
        """Test that None is returned when no pattern matches."""
        text = "No energy values here"
        result = parse_energy_consumption(text)
        
        assert result is None

    def test_parse_empty_text(self):
        """Test parsing empty text."""
        result = parse_energy_consumption("")
        
        assert result is None

    def test_parse_none_text(self):
        """Test parsing None text."""
        result = parse_energy_consumption(None)
        
        assert result is None

    def test_parse_decimal_value(self):
        """Test parsing decimal values."""
        text = "Energy: 450.5 kWh"
        result = parse_energy_consumption(text)
        
        assert result == 450.5

    def test_parse_without_unit(self):
        """Test parsing value without kWh unit."""
        text = "Total: 400"
        result = parse_energy_consumption(text)
        
        assert result == 400.0

    def test_parse_value_with_extra_spaces(self):
        """Test parsing value with extra spaces."""
        text = "Usage:   450   kWh"
        result = parse_energy_consumption(text)
        
        assert result == 450.0


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_parse_negative_values(self):
        """Test handling of negative values (should parse them)."""
        text = "Usage: -100 kWh"
        result = parse_energy_consumption(text)
        
        # Regex should capture negative values
        assert result == -100.0

    def test_parse_very_large_value(self):
        """Test parsing very large values."""
        text = "Total: 1000000 kWh"
        result = parse_energy_consumption(text)
        
        assert result == 1000000.0

    def test_parse_multiple_matches_returns_first(self):
        """Test that multiple matches return the first one."""
        text = "Usage: 100 kWh\nPrevious: 200 kWh\nTotal: 300 kWh"
        result = parse_energy_consumption(text)
        
        assert result == 100.0

    def test_parse_with_units(self):
        """Test parsing with various energy units."""
        text = "Energy: 450 KWH"
        result = parse_energy_consumption(text)
        
        assert result == 450.0

    def test_parse_with_special_characters(self):
        """Test parsing with special characters in text."""
        text = "Energy@Consumption: 450 kWh!"
        result = parse_energy_consumption(text)
        
        assert result == 450.0
