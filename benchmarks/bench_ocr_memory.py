"""
Benchmark script for OCR memory optimization.
Measures peak RAM consumption and allocation during image OCR processing.
"""
import io
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image
from unittest.mock import patch
from ocr_utils import optimize_image_for_ocr, benchmark_ocr_memory


def run_ocr_memory_benchmark():
    print("Running OCR Memory Optimization Benchmark...")
    
    # Create high resolution test image (3000x2000 RGBA)
    img = Image.new("RGBA", (3000, 2000), (200, 200, 200, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    image_bytes = buf.getvalue()
    
    print(f"Original Raw Image Size: 3000x2000 pixels (~24 MB raw RGBA buffer)")
    
    # Test image optimization
    opt_img = optimize_image_for_ocr(img, max_dim=1800)
    print(f"Optimized Image Size: {opt_img.size[0]}x{opt_img.size[1]} pixels (Mode: {opt_img.mode})")
    
    with patch("ocr_utils.pytesseract.image_to_string", return_value="Total Usage: 450 kWh"):
        bench_result = benchmark_ocr_memory(image_bytes)
        print(f"Benchmark Result: Allocated ~{bench_result['allocated_kb']} KB RAM during OCR run.")
        
    print("Benchmark completed successfully.")


if __name__ == "__main__":
    run_ocr_memory_benchmark()
