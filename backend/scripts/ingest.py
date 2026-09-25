"""Ingest PDF files from the repository's data/raw_pdfs directory."""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PDF_DIRECTORY = PROJECT_ROOT / "data" / "raw_pdfs"
logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PdfMetadata:
    title: str
    source: str
    doc_type: str


def infer_metadata(pdf_path: Path) -> PdfMetadata | None:
    """Infer regulator and document type from the documented filename convention."""
    match = re.match(r"^(RBI|SEBI)_(.+)$", pdf_path.stem, flags=re.IGNORECASE)
    if match is None:
        return None

    source = match.group(1).upper()
    remainder = match.group(2)
    type_match = re.match(r"^(master_direction|circular|notification)(?:_|$)", remainder, re.I)
    doc_type = type_match.group(1).lower() if type_match else "other"
    title = re.sub(r"_+", " ", pdf_path.stem).strip().title()
    return PdfMetadata(title=title, source=source, doc_type=doc_type)


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    from app.core.database import create_session
    from app.models.document import DocumentSource, DocumentType
    from app.services.ingestion import ingest_pdf

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    pdf_paths = sorted(PDF_DIRECTORY.rglob("*.pdf"))
    if not pdf_paths:
        logger.warning("No PDFs found in %s", PDF_DIRECTORY)
        return 0

    db = create_session()
    failed = 0
    try:
        for pdf_path in pdf_paths:
            metadata = infer_metadata(pdf_path)
            if metadata is None:
                logger.warning("Skipping filename without RBI/SEBI prefix: %s", pdf_path.name)
                continue
            try:
                document = ingest_pdf(
                    db,
                    pdf_path,
                    title=metadata.title,
                    source=DocumentSource(metadata.source),
                    doc_type=DocumentType(metadata.doc_type),
                    stored_path=pdf_path.relative_to(PROJECT_ROOT).as_posix(),
                )
                if document is None:
                    logger.info("Already ingested: %s", pdf_path.name)
                else:
                    logger.info("Ingested: %s (%s chunks)", pdf_path.name, len(document.chunks))
            except Exception:
                failed += 1
                logger.exception("Failed to ingest %s", pdf_path)
    finally:
        db.close()

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
