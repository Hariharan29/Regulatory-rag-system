import pymupdf

from app.services import pdf_parser


def test_extract_pages_preserves_one_based_page_numbers(tmp_path):
    pdf_path = tmp_path / "two-pages.pdf"
    with pymupdf.open() as pdf:
        first = pdf.new_page()
        first.insert_text((72, 72), "RBI circular page one")
        second = pdf.new_page()
        second.insert_text((72, 72), "SEBI notice page two")
        pdf.save(pdf_path)

    assert pdf_parser.extract_pages(pdf_path) == [
        (1, "RBI circular page one"),
        (2, "SEBI notice page two"),
    ]


def test_extract_pages_uses_ocr_for_image_only_pages(monkeypatch, tmp_path):
    pdf_path = tmp_path / "scanned.pdf"
    with pymupdf.open() as pdf:
        pdf.new_page()
        pdf.save(pdf_path)

    monkeypatch.setattr(pdf_parser, "_ocr_page", lambda page: "Scanned regulatory text")

    assert pdf_parser.extract_pages(pdf_path) == [(1, "Scanned regulatory text")]
