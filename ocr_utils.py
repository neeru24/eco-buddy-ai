import re
import pdfplumber
import pytesseract
from PIL import Image
import io

def extract_text_from_file(uploaded_file):
    """Extracts text from a Streamlit UploadedFile object."""
    text = ""
    file_type = uploaded_file.type

    if "pdf" in file_type:
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Error reading PDF: {e}")
            
    elif "image" in file_type:
        try:
            image = Image.open(uploaded_file)
            text = pytesseract.image_to_string(image)
        except Exception as e:
            print(f"Error reading image: {e}")

    return text

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
        # Match 'Number kWh' or 'Numberkwh' e.g. 350 kWh, 1,200.5 kWh
        r'((?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)\s*(?:kWh|kwh|KWH)',
        # Match 'Total Consumption ... Number' or 'Usage ... Number'
        r'(?:total\s+consumption|usage|total\s+usage|electricity\s+usage).*?((?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)\s*(?:kWh|kwh)?'
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Take the first match
            val_str = matches[0].replace(',', '')
            try:
                return float(val_str)
            except ValueError:
                continue

    return None
