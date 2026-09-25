import fitz

from app.services.pdf_parser import extract_pages


def test_extract_pages_preserves_one_based_page_numbers(tmp_path):
    pdf_path = tmp_path / "two-pages.pdf"
    with fitz.open() as pdf:
        first = pdf.new_page()
        first.insert_text((72, 72), "RBI circular page one")
        second = pdf.new_page()
        second.insert_text((72, 72), "SEBI notice page two")
        pdf.save(pdf_path)

    assert extract_pages(pdf_path) == [
        (1, "RBI circular page one"),
        (2, "SEBI notice page two"),
    ]
