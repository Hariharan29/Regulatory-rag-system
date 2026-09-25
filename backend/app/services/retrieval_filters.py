"""Shared source and document-type filters for retrieval services."""

from sqlalchemy import Select

from app.models.document import Document, DocumentSource, DocumentType


def apply_document_filters(
    statement: Select,
    source: DocumentSource | str | None = None,
    doc_type: DocumentType | str | None = None,
) -> Select:
    if source is not None:
        normalized_source = (
            source if isinstance(source, DocumentSource) else DocumentSource(source.upper())
        )
        statement = statement.where(Document.source == normalized_source)
    if doc_type is not None:
        normalized_type = (
            doc_type if isinstance(doc_type, DocumentType) else DocumentType(doc_type.lower())
        )
        statement = statement.where(Document.doc_type == normalized_type)
    return statement


def matches_document_filters(
    actual_source: DocumentSource,
    actual_type: DocumentType,
    source: DocumentSource | str | None = None,
    doc_type: DocumentType | str | None = None,
) -> bool:
    normalized_source = (
        source if isinstance(source, DocumentSource) else DocumentSource(source.upper())
        if source is not None
        else None
    )
    normalized_type = (
        doc_type if isinstance(doc_type, DocumentType) else DocumentType(doc_type.lower())
        if doc_type is not None
        else None
    )
    return (normalized_source is None or actual_source == normalized_source) and (
        normalized_type is None or actual_type == normalized_type
    )
