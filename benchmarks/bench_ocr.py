"""Benchmarks for ocr_utils.py – text parsing and file extraction."""
import os, sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from benchmarks.base_benchmark import BaseBenchmark
from benchmarks._st_mock import install_streamlit_mock, remove_streamlit_mock

_BILL = "Total Usage: 350 kWh\nRate: $0.14/kWh\nTotal Due: $54.88"
_PAGES = [_BILL, "350 kWh", "Total Consumption: 412 kWh", "1,234.5 kWh", "No value here"] * 10


class OcrBenchmark(BaseBenchmark):
    SUITE_NAME = "OCR Processing"

    def setup(self):
        install_streamlit_mock()
        import importlib, ocr_utils
        importlib.reload(ocr_utils)
        self._ocr = ocr_utils

    def teardown(self):
        remove_streamlit_mock()

    def _run_benchmarks(self):
        p = self._ocr.parse_energy_consumption
        self.measure("parse_energy_consumption – simple kWh",     p, "350 kWh")
        self.measure("parse_energy_consumption – labelled",       p, "Total Consumption: 412 kWh")
        self.measure("parse_energy_consumption – comma number",   p, "1,234.5 kWh")
        self.measure("parse_energy_consumption – multi-line bill",p, _BILL)
        self.measure("parse_energy_consumption – no match",       p, "Account: 99887766")
        self.measure("parse_energy_consumption – empty",          p, "")
        self.measure("parse_energy_consumption – None",           p, None)
        self.measure("parse_energy_consumption – batch 50 pages", lambda: [p(pg) for pg in _PAGES])

        def _pdf():
            f = MagicMock(); f.type = "application/pdf"
            pg = MagicMock(); pg.extract_text.return_value = _BILL
            ctx = MagicMock(); ctx.__enter__ = MagicMock(return_value=ctx)
            ctx.__exit__ = MagicMock(return_value=False); ctx.pages = [pg]
            with patch("pdfplumber.open", return_value=ctx):
                return self._ocr.extract_text_from_file(f)

        def _img():
            from PIL import Image
            img = Image.new("RGB", (100, 30), (255, 255, 255))
            f = MagicMock(); f.type = "image/png"
            with patch("PIL.Image.open", return_value=img), \
                 patch("pytesseract.image_to_string", return_value="350 kWh"):
                return self._ocr.extract_text_from_file(f)

        self.measure("extract_text_from_file – PDF (mocked)",   _pdf)
        self.measure("extract_text_from_file – image (mocked)", _img)
