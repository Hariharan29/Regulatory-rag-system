"""Page-preserving text extraction for regulatory PDFs."""

from pathlib import Path

import fitz


def extract_pages(pdf_path: str | Path) -> list[tuple[int, str]]:
    """Return (1-based page number, extracted text) pairs for a PDF."""
    with fitz.open(pdf_path) as pdf:
        return [
            (page_number, page.get_text("text").strip())
            for page_number, page in enumerate(pdf, start=1)
        ]
