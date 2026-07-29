import re
import io
import logging
import pdfplumber
import pytesseract
from PIL import Image
from cache import cached
from cache_config import CACHE_CATEGORY_SESSION

logger = logging.getLogger(__name__)

def extract_text_from_bytes(file_bytes: bytes, file_type: str) -> str:
    """
    Extracts text from raw file bytes (PDF or Image).
    Pure, thread-safe function suitable for background processing.
    """
    if not file_bytes:
        return ""
    text = ""
    file_type_lower = (file_type or "").lower()

    if "pdf" in file_type_lower:
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.warning(f"Error reading PDF bytes: {e}")

    elif "image" in file_type_lower:
        try:
            image = Image.open(io.BytesIO(file_bytes))
            text = pytesseract.image_to_string(image)
        except Exception as e:
            logger.warning(f"Error reading image bytes: {e}")

    return text


@cached(category=CACHE_CATEGORY_SESSION)
def extract_text_from_file(uploaded_file):
    """
    Extracts text from a Streamlit UploadedFile object or file mock.
    Uses caching to avoid re-running OCR on identical files.
    """
    if uploaded_file is None:
        return ""

    text = ""
    file_type = getattr(uploaded_file, "type", "")

    if "pdf" in file_type:
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.warning(f"Error reading PDF: {e}")

    elif "image" in file_type:
        try:
            image = Image.open(uploaded_file)
            text = pytesseract.image_to_string(image)
        except Exception as e:
            logger.warning(f"Error reading image: {e}")

    return text


@cached(category=CACHE_CATEGORY_SESSION)
def parse_energy_consumption(text):
    """
    Parses energy consumption values from text.
    Looks for patterns like '350 kWh', 'Total Consumption: 400', etc.
    Returns the float value if found, else None.
    """
    if not text:
        return None

    # Common regex patterns for utility bills
    patterns = [
        # Match 'Number kWh' or 'Numberkwh' e.g. 350 kWh, 1,200.5 kWh, -100 kWh
        r'(-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)\s*(?:kWh|kwh|KWH)',
        # Match 'Total Consumption ... Number' or 'Total ... Number' or 'Usage ... Number'
        r'(?:total\s+consumption|total|usage|total\s+usage|electricity\s+usage).*?(-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)\s*(?:kWh|kwh)?'
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            val_str = matches[0].replace(',', '')
            try:
                return float(val_str)
            except ValueError:
                continue

    return None
