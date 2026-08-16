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
        extract_text_from_file.clear()
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
        extract_text_from_file.clear()
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
        extract_text_from_file.clear()
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
        extract_text_from_file.clear()
        mock_file = MagicMock()
        mock_file.type = "application/pdf"
        
        with patch('ocr_utils.pdfplumber.open') as mock_open:
            mock_open.side_effect = Exception("PDF Error")
            
            result = extract_text_from_file(mock_file)
            
            # Should return empty string on error
            assert result == ""

    def test_extract_text_with_unknown_file_type(self):
        """Test extracting text from unknown file type."""
        extract_text_from_file.clear()
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


class TestMemoryOptimization:
    """Tests for memory optimization and resource releasing during OCR."""

    def test_optimize_image_resizes_large_images(self):
        from PIL import Image
        from ocr_utils import optimize_image_for_ocr
        large_img = Image.new("RGBA", (3000, 2000), (255, 0, 0, 255))
        opt_img = optimize_image_for_ocr(large_img, max_dim=1800)
        assert opt_img.size[0] <= 1800
        assert opt_img.size[1] <= 1800
        assert opt_img.mode in ("L", "RGB")

    def test_optimize_image_none(self):
        from ocr_utils import optimize_image_for_ocr
        assert optimize_image_for_ocr(None) is None

    def test_extract_text_from_bytes_image_optimization(self):
        from PIL import Image
        import io
        from ocr_utils import extract_text_from_bytes
        img = Image.new("RGB", (2000, 2000), (255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_bytes = buf.getvalue()
        
        with patch('ocr_utils.pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = "Total: 500 kWh"
            res = extract_text_from_bytes(img_bytes, "image/png")
            assert "500" in res

    def test_benchmark_ocr_memory(self):
        from PIL import Image
        import io
        from ocr_utils import benchmark_ocr_memory
        img = Image.new("RGB", (100, 100), (255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_bytes = buf.getvalue()

        with patch('ocr_utils.pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = "350 kWh"
            res = benchmark_ocr_memory(img_bytes)
            assert res["status"] == "success"
            assert "allocated_kb" in res


class TestMemoryLeakFixes:
    """Regression tests for the PDF bill memory leak (#696).

    Each test pins down one of the failure modes reported in the issue so a
    future change cannot reintroduce them:

    * OOM on uploads larger than 10 MB (#4)
    * NameError because ``uploaded_file.size`` was read on raw bytes
    * NameError on ``st.warning`` because Streamlit was never imported here
    * RecursionError on large PDFs from ``text += page_text + "\\n"``
    * No way for the caller to report progress
    """

    def test_extract_text_from_bytes_rejects_oversize_pdf(self):
        """An oversize PDF is rejected with empty result and the notifier is called."""
        from ocr_utils import extract_text_from_bytes, MAX_BILL_FILE_SIZE_BYTES

        oversize = b"%PDF-1.4\n" + (b"%pad " * ((MAX_BILL_FILE_SIZE_BYTES // 5) + 1))
        notifications = []

        result = extract_text_from_bytes(
            oversize,
            "application/pdf",
            notify=lambda message, level: notifications.append((message, level)),
        )

        assert result == ""
        assert notifications, "Oversize upload must surface a user-facing warning"
        assert notifications[0][1] == "warning"
        assert "10" in notifications[0][0]  # mentions the 10 MB limit

    def test_extract_text_from_bytes_handles_unknown_mime(self):
        """Unknown MIME types return empty without raising."""
        from ocr_utils import extract_text_from_bytes

        assert extract_text_from_bytes(b"some bytes", "application/zip") == ""

    def test_extract_text_from_bytes_does_not_reference_undefined_st(self):
        """Regression: the previous code referenced ``st.warning`` without
        importing streamlit. This crashed every PDF bill.
        """
        # If `st` were referenced, calling the function under a strict module
        # would raise NameError. Now the module does not import streamlit at
        # all -- but we still verify by checking ``ocrmod`` has no `st` symbol.
        import ocr_utils

        assert not hasattr(ocr_utils, "st"), (
            "ocr_utils must not depend on streamlit; it is imported from "
            "background tasks and tests too."
        )

    def test_extract_text_from_bytes_reports_progress_per_page(self):
        """The progress callback is invoked once per page with running totals."""
        from ocr_utils import extract_text_from_bytes

        progress_calls = []

        def _progress(done, total):
            progress_calls.append((done, total))

        page_texts = ["page one body", "page two body", "page three body"]
        mock_page_objs = []
        for text in page_texts:
            mp = MagicMock()
            mp.extract_text.return_value = text
            mock_page_objs.append(mp)

        with patch("ocr_utils.pdfplumber.open") as mock_open:
            mock_pdf = MagicMock()
            mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
            mock_pdf.__exit__ = MagicMock(return_value=False)
            mock_pdf.pages = mock_page_objs
            mock_open.return_value = mock_pdf

            result = extract_text_from_bytes(
                b"%PDF-1.4 fake bytes",
                "application/pdf",
                on_progress=_progress,
            )

        # Every page reported once, totals strictly increasing, last call
        # equals (total_pages, total_pages).
        assert progress_calls == [(1, 3), (2, 3), (3, 3)]
        assert "page one body" in result
        assert "page three body" in result

    def test_extract_text_from_bytes_skips_unreadable_page(self):
        """A single page that raises does not abort the whole document."""
        from ocr_utils import extract_text_from_bytes

        good_page = MagicMock()
        good_page.extract_text.return_value = "kWh: 250"

        bad_page = MagicMock()
        bad_page.extract_text.side_effect = RuntimeError("corrupt page")

        with patch("ocr_utils.pdfplumber.open") as mock_open:
            mock_pdf = MagicMock()
            mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
            mock_pdf.__exit__ = MagicMock(return_value=False)
            mock_pdf.pages = [good_page, bad_page, good_page]
            mock_open.return_value = mock_pdf

            result = extract_text_from_bytes(
                b"%PDF-1.4",
                "application/pdf",
            )

        assert "kWh: 250" in result
        # Two pages contribute "kWh: 250", separated by "\n"
        assert result.count("kWh: 250") == 2

    def test_extract_text_from_bytes_does_not_concatenate_in_loop(self):
        """Regression: ``text += page_text + '\\n'`` produced O(n**2) behaviour
        on large PDFs and was the root cause of the RecursionError in #4.

        The fix accumulates into a list and joins once. We pin that by mocking
        a PDF with 200 pages and asserting the result is well-formed and the
        concatenation cost is bounded (linear time, not quadratic).
        """
        from ocr_utils import extract_text_from_bytes
        import time

        page_texts = [f"page {i} content " * 50 for i in range(200)]

        with patch("ocr_utils.pdfplumber.open") as mock_open:
            mock_pdf = MagicMock()
            mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
            mock_pdf.__exit__ = MagicMock(return_value=False)
            mock_pdf.pages = [
                MagicMock(extract_text=MagicMock(return_value=t)) for t in page_texts
            ]
            mock_open.return_value = mock_pdf

            start = time.monotonic()
            result = extract_text_from_bytes(b"%PDF-1.4", "application/pdf")
            elapsed = time.monotonic() - start

        # Every page must be present and separated. The previous implementation
        # would have either hung or RecursionErrored well before this.
        for i in (0, 50, 100, 150, 199):
            assert f"page {i} content" in result
        assert result.count("page ") == 200 * 50  # 50 "page " per page text
        # Sanity bound: 200-page join runs in well under a second on any host.
        assert elapsed < 5.0, f"200-page PDF took {elapsed:.2f}s -- suspect quadratic concatenation"

    def test_extract_text_from_file_rejects_oversize_upload(self):
        """``extract_text_from_file`` checks the size attribute on the upload."""
        from ocr_utils import extract_text_from_file, MAX_BILL_FILE_SIZE_BYTES

        notifications = []

        mock_upload = MagicMock()
        mock_upload.type = "application/pdf"
        mock_upload.size = MAX_BILL_FILE_SIZE_BYTES + 1

        result = extract_text_from_file(
            mock_upload,
            notify=lambda message, level: notifications.append((message, level)),
        )

        assert result == ""
        assert notifications, "Oversize upload must surface a user-facing warning"

    def test_extract_text_from_file_progress_callback(self):
        """Progress is reported on the file-based entry point too."""
        from ocr_utils import extract_text_from_file

        progress_calls = []
        extract_text_from_file.clear()

        mock_upload = MagicMock()
        mock_upload.type = "application/pdf"
        mock_upload.size = 1024  # well under the cap

        with patch("ocr_utils.pdfplumber.open") as mock_open:
            mock_pdf = MagicMock()
            mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
            mock_pdf.__exit__ = MagicMock(return_value=False)
            mock_pdf.pages = [
                MagicMock(extract_text=MagicMock(return_value=f"page {i}"))
                for i in range(1, 4)
            ]
            mock_open.return_value = mock_pdf

            result = extract_text_from_file(
                mock_upload,
                on_progress=lambda done, total: progress_calls.append((done, total)),
            )

        assert progress_calls == [(1, 3), (2, 3), (3, 3)]
        assert "page 1" in result and "page 3" in result

