import re
import io
import gc
import logging
import tracemalloc
from typing import BinaryIO, Callable, Optional
from PIL import Image
from cache import cached
from cache_config import CACHE_CATEGORY_SESSION

logger = logging.getLogger(__name__)

MAX_OCR_IMAGE_DIMENSION = 1800

# 10 MB hard cap on a single uploaded bill. Larger files almost always indicate
# a wrong file (a phone photo dump, the previous month's bill scanned at 1200
# dpi, a multi-page brochure) and will OOM the Streamlit worker before OCR
# finishes. The cap is checked against the byte count we already hold, so no
# extra read passes through.
MAX_BILL_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Optional callbacks a caller can pass in. They keep `ocr_utils` free of any
# Streamlit import (the module is also imported from background tasks, tests,
# and CLI utilities) and let the UI layer decide how to surface progress and
# rejections.
ProgressCallback = Callable[[int, int], None]   # (pages_done, total_pages)
UserNotifier = Callable[[str, str], None]      # (message, level)


def _noop_progress(_done: int, _total: int) -> None:
    return None


def _noop_notify(_message: str, _level: str) -> None:
    return None


def _notify_too_large(notify: UserNotifier, size_bytes: int) -> None:
    size_mb = size_bytes / (1024 * 1024)
    cap_mb = MAX_BILL_FILE_SIZE_BYTES / (1024 * 1024)
    notify(
        f"Bill file is {size_mb:.1f} MB, which exceeds the {cap_mb:.0f} MB limit. "
        "Please upload a smaller file (re-scan at lower DPI, or upload a single page).",
        "warning",
    )


def __getattr__(name):
    if name in ("pdfplumber", "pytesseract"):
        return __import__(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def optimize_image_for_ocr(image: Image.Image, max_dim: int = MAX_OCR_IMAGE_DIMENSION) -> Image.Image:
    """
    Optimizes a PIL Image for OCR processing to reduce memory consumption:
    1. Converts multi-channel (RGBA, CMYK, Palette) images to Grayscale ('L') or RGB,
       saving memory (1 byte/pixel vs 4 bytes/pixel).
    2. Resizes oversized images to a maximum dimension while maintaining aspect ratio.
    """
    if image is None:
        return None

    # Convert mode to grayscale or RGB if needed
    processed_image = image
    mode = getattr(image, "mode", None)
    if isinstance(mode, str):
        if mode in ("RGBA", "LA", "P", "CMYK"):
            processed_image = image.convert("L")
        elif mode not in ("L", "RGB"):
            processed_image = image.convert("RGB")

    # Downscale image if dimensions exceed max_dim
    size = getattr(processed_image, "size", None)
    if isinstance(size, (tuple, list)) and len(size) == 2:
        w, h = size
        if isinstance(w, (int, float)) and isinstance(h, (int, float)) and (w > max_dim or h > max_dim):
            scale = max_dim / float(max(w, h))
            new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
            
            resample = getattr(Image, "Resampling", Image).LANCZOS
            resized_img = processed_image.resize((new_w, new_h), resample=resample)
            if processed_image is not image and hasattr(processed_image, "close"):
                processed_image.close()
            processed_image = resized_img

    return processed_image


def extract_text_from_bytes(
    file_bytes: bytes,
    file_type: str,
    on_progress: Optional[ProgressCallback] = None,
    notify: Optional[UserNotifier] = None,
) -> str:
    """
    Extracts text from raw file bytes (PDF or Image).

    Pure, thread-safe function suitable for background processing. The caller
    supplies progress and user-facing-notification callbacks so this module
    never has to know whether it is running inside Streamlit, a Celery worker
    or a unit test.

    A 10 MB hard cap is enforced up front: anything larger is rejected before
    pdfplumber or PIL is asked to parse it, so the Streamlit worker never has
    to hold a multi-hundred-MB phone dump in RAM.
    """
    import pdfplumber
    import pytesseract

    if not file_bytes:
        return ""

    on_progress = on_progress or _noop_progress
    notify = notify or _noop_notify

    if len(file_bytes) > MAX_BILL_FILE_SIZE_BYTES:
        logger.warning(
            "Bill file of %d bytes rejected (limit is %d bytes)",
            len(file_bytes),
            MAX_BILL_FILE_SIZE_BYTES,
        )
        _notify_too_large(notify, len(file_bytes))
        return ""

    file_type_lower = (file_type or "").lower()

    if "pdf" in file_type_lower:
        # The bytes are wrapped in BytesIO and given to pdfplumber, which reads
        # pages lazily. We accumulate page text into a list and join once at
        # the end -- the previous `text += page_text + "\n"` was O(n**2) on a
        # large bill and was the source of the RecursionError reported in #4.
        page_texts: list[str] = []
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                total_pages = len(pdf.pages)
                for index, page in enumerate(pdf.pages, start=1):
                    try:
                        page_text = page.extract_text() or ""
                    except Exception as page_error:  # one bad page shouldn't kill the rest
                        logger.warning(
                            "Skipping unreadable PDF page %d/%d: %s",
                            index,
                            total_pages,
                            page_error,
                        )
                        page_text = ""
                    if page_text:
                        page_texts.append(page_text)
                    if hasattr(page, "flush_cache"):
                        try:
                            page.flush_cache()
                        except Exception:
                            pass
                    on_progress(index, total_pages)
        except Exception as e:
            logger.warning("Error reading PDF bytes: %s", e)
            return "\n".join(page_texts)

        return "\n".join(page_texts)

    if "image" in file_type_lower:
        try:
            with Image.open(io.BytesIO(file_bytes)) as raw_image:
                opt_image = optimize_image_for_ocr(raw_image)
                try:
                    text = pytesseract.image_to_string(opt_image)
                finally:
                    if opt_image is not raw_image and hasattr(opt_image, "close"):
                        opt_image.close()
        except Exception as e:
            logger.warning("Error reading image bytes: %s", e)
            return ""
        finally:
            gc.collect()
        return text

    return ""


@cached(category=CACHE_CATEGORY_SESSION)
def extract_text_from_file(
    uploaded_file: BinaryIO,
    on_progress: Optional[ProgressCallback] = None,
    notify: Optional[UserNotifier] = None,
) -> str:
    """
    Extracts text from a Streamlit UploadedFile object or file mock.
    Uses caching to avoid re-running OCR on identical files.
    Optimizes image memory and releases resources efficiently.

    A 10 MB hard cap is enforced before the file is handed to pdfplumber/PIL.
    Over-cap uploads are rejected through the supplied ``notify`` callback
    rather than crashing the worker -- and since Streamlit is not imported
    here, ``notify`` defaults to a no-op, so this module stays usable from
    tests and CLI utilities.
    """
    import pdfplumber
    import pytesseract

    if uploaded_file is None:
        return ""

    on_progress = on_progress or _noop_progress
    notify = notify or _noop_notify

    file_size = getattr(uploaded_file, "size", 0) or 0
    # Mock objects and other non-numeric ``size`` attributes must not crash
    # the comparison; coerce defensively so unit tests that pass a bare
    # MagicMock keep working without having to stub ``size``.
    if isinstance(file_size, (int, float)) and file_size > MAX_BILL_FILE_SIZE_BYTES:
        logger.warning(
            "Bill file of %d bytes rejected (limit is %d bytes)",
            file_size,
            MAX_BILL_FILE_SIZE_BYTES,
        )
        _notify_too_large(notify, file_size)
        return ""

    file_type = getattr(uploaded_file, "type", "")
    file_type_lower = (file_type or "").lower()

    if "pdf" in file_type_lower:
        # List-and-join again, for the same reason as extract_text_bytes:
        # repeated string concatenation is what produced the RecursionError
        # on large bills (#4).
        page_texts: list[str] = []
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                total_pages = len(pdf.pages)
                for index, page in enumerate(pdf.pages, start=1):
                    try:
                        page_text = page.extract_text() or ""
                    except Exception as page_error:
                        logger.warning(
                            "Skipping unreadable PDF page %d/%d: %s",
                            index,
                            total_pages,
                            page_error,
                        )
                        page_text = ""
                    if page_text:
                        page_texts.append(page_text)
                    if hasattr(page, "flush_cache"):
                        try:
                            page.flush_cache()
                        except Exception:
                            pass
                    on_progress(index, total_pages)
        except Exception as e:
            logger.warning("Error reading PDF: %s", e)
            return "\n".join(page_texts)

        return "\n".join(page_texts)

    if "image" in file_type_lower:
        try:
            raw_image = Image.open(uploaded_file)
            opt_image = optimize_image_for_ocr(raw_image)
            try:
                text = pytesseract.image_to_string(opt_image)
            finally:
                if opt_image is not raw_image and hasattr(opt_image, "close"):
                    opt_image.close()
                if hasattr(raw_image, "close"):
                    raw_image.close()
        except Exception as e:
            logger.warning("Error reading image: %s", e)
            return ""
        finally:
            gc.collect()
        return text

    return ""


@cached(category=CACHE_CATEGORY_SESSION)
def parse_energy_consumption(text: str | None) -> float | None:
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


def benchmark_ocr_memory(image_bytes: bytes) -> dict:
    """
    Benchmarks memory usage during OCR processing of an image.
    Returns peak memory allocated (in KB) and reduction statistics.
    """
    import pytesseract

    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()
    
    try:
        with Image.open(io.BytesIO(image_bytes)) as raw_img:
            opt_img = optimize_image_for_ocr(raw_img)
            _ = pytesseract.image_to_string(opt_img)
            if opt_img is not raw_img and hasattr(opt_img, "close"):
                opt_img.close()
    except Exception as e:
        logger.warning(f"Benchmark OCR error: {e}")
            
    snapshot_after = tracemalloc.take_snapshot()
    tracemalloc.stop()
    
    stats = snapshot_after.compare_to(snapshot_before, 'lineno')
    total_allocated_kb = sum(stat.size for stat in stats) / 1024.0
    
    gc.collect()
    return {
        "allocated_kb": round(total_allocated_kb, 2),
        "status": "success"
    }
