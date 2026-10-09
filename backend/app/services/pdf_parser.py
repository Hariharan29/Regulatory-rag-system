"""Page-preserving text extraction for regulatory PDFs."""

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import pymupdf


def _ocr_page(page: pymupdf.Page) -> str:
    """OCR one scanned page using the Tesseract executable installed in the backend image."""
    with TemporaryDirectory(prefix="finance-rag-ocr-") as temporary_directory:
        image_path = Path(temporary_directory) / "page.png"
        page.get_pixmap(dpi=250, colorspace=pymupdf.csGRAY, alpha=False).save(image_path)
        result = subprocess.run(
            ["tesseract", str(image_path), "stdout", "--psm", "3"],
            check=True,
            capture_output=True,
            text=True,
        )
    return result.stdout.strip()


def extract_pages(pdf_path: str | Path) -> list[tuple[int, str]]:
    """Return page text, OCRing pages that contain no extractable text."""
    pages = []
    with pymupdf.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()
            if not text:
                text = _ocr_page(page)
            pages.append((page_number, text))
    return pages
