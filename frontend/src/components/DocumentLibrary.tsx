import { useEffect, useRef, useState } from "react"
import { ArrowLeft, ArrowRight, BookOpen, FileText, RefreshCw } from "lucide-react"

import {
  ApiError,
  getDocument,
  getDocuments,
  type DocumentDetail,
  type DocumentRecord,
  type DocumentSource,
  type DocumentType,
} from "@/lib/api"

const PAGE_SIZE = 8

const documentTypes: Array<{ label: string; value: DocumentType | "ALL" }> = [
  { label: "All types", value: "ALL" },
  { label: "Circulars", value: "circular" },
  { label: "Master directions", value: "master_direction" },
  { label: "Notifications", value: "notification" },
  { label: "Other", value: "other" },
]

function documentTypeLabel(value: DocumentType): string {
  return value.replaceAll("_", " ")
}

function formatDate(value: string | null): string {
  if (!value) return "Date not listed"
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(
    new Date(`${value}T00:00:00`),
  )
}

interface DocumentLibraryProps {
  refreshKey?: number
}

export default function DocumentLibrary({ refreshKey = 0 }: DocumentLibraryProps) {
  const [source, setSource] = useState<DocumentSource | "ALL">("ALL")
  const [docType, setDocType] = useState<DocumentType | "ALL">("ALL")
  const [offset, setOffset] = useState(0)
  const [documents, setDocuments] = useState<DocumentRecord[]>([])
  const [total, setTotal] = useState(0)
  const [selectedDocument, setSelectedDocument] = useState<DocumentDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isDetailLoading, setIsDetailLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [detailError, setDetailError] = useState<string | null>(null)
  const [retryKey, setRetryKey] = useState(0)
  const detailRequestId = useRef(0)

  useEffect(() => {
    let isCurrent = true
    setIsLoading(true)
    setError(null)

    void getDocuments({
      source: source === "ALL" ? undefined : source,
      doc_type: docType === "ALL" ? undefined : docType,
      offset,
      limit: PAGE_SIZE,
    })
      .then((result) => {
        if (!isCurrent) return
        setDocuments(result.items)
        setTotal(result.total)
      })
      .catch((requestError: unknown) => {
        if (!isCurrent) return
        setError(
          requestError instanceof ApiError
            ? requestError.message
            : "The document library could not be loaded.",
        )
      })
      .finally(() => {
        if (isCurrent) setIsLoading(false)
      })

    return () => {
      isCurrent = false
    }
  }, [docType, offset, refreshKey, retryKey, source])

  async function openDocument(document: DocumentRecord) {
    const requestId = ++detailRequestId.current
    setSelectedDocument(null)
    setDetailError(null)
    setIsDetailLoading(true)
    try {
      const details = await getDocument(document.id)
      if (requestId === detailRequestId.current) setSelectedDocument(details)
    } catch (requestError) {
      if (requestId === detailRequestId.current) {
        setDetailError(
          requestError instanceof ApiError
            ? requestError.message
            : "Document details could not be loaded.",
        )
      }
    } finally {
      if (requestId === detailRequestId.current) setIsDetailLoading(false)
    }
  }

  function changeSource(value: DocumentSource | "ALL") {
    setSource(value)
    setOffset(0)
    detailRequestId.current += 1
    setSelectedDocument(null)
    setIsDetailLoading(false)
  }

  function changeDocumentType(value: DocumentType | "ALL") {
    setDocType(value)
    setOffset(0)
    detailRequestId.current += 1
    setSelectedDocument(null)
    setIsDetailLoading(false)
  }

  const pageNumber = Math.floor(offset / PAGE_SIZE) + 1
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <section aria-labelledby="library-heading" className="space-y-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground">
            Reference collection
          </p>
          <h2 className="mt-1 text-xl font-medium tracking-tight" id="library-heading">
            Document library
          </h2>
        </div>
        <span className="rounded-full bg-secondary px-3 py-1 text-xs text-secondary-foreground">
          {total} {total === 1 ? "document" : "documents"}
        </span>
      </div>

      <div className="flex flex-wrap gap-2" aria-label="Filter documents by regulator">
        {(["ALL", "RBI", "SEBI"] as const).map((value) => {
          const selected = source === value
          return (
            <button
              aria-pressed={selected}
              className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                selected
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border bg-card text-muted-foreground hover:text-foreground"
              }`}
              key={value}
              onClick={() => changeSource(value)}
              type="button"
            >
              {value === "ALL" ? "All regulators" : value}
            </button>
          )
        })}
      </div>

      <label className="sr-only" htmlFor="document-type-filter">
        Filter documents by type
      </label>
      <select
        className="h-10 w-full rounded-md border border-border bg-card px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        id="document-type-filter"
        onChange={(event) =>
          changeDocumentType(event.target.value as DocumentType | "ALL")
        }
        value={docType}
      >
        {documentTypes.map((type) => (
          <option key={type.value} value={type.value}>
            {type.label}
          </option>
        ))}
      </select>

      {isLoading && (
        <p aria-live="polite" className="rounded-lg border border-border bg-card p-4 text-sm text-muted-foreground" role="status">
          Loading indexed documents…
        </p>
      )}

      {!isLoading && error && (
        <div className="rounded-lg border border-destructive/30 bg-card p-4" role="alert">
          <p className="text-sm text-foreground">{error}</p>
          <button
            className="mt-3 inline-flex items-center gap-2 text-sm font-medium text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            onClick={() => setRetryKey((value) => value + 1)}
            type="button"
          >
            <RefreshCw aria-hidden="true" className="size-4" />
            Retry
          </button>
        </div>
      )}

      {!isLoading && !error && total === 0 && (
        <div className="rounded-lg border border-dashed border-border bg-card px-5 py-8 text-center">
          <BookOpen aria-hidden="true" className="mx-auto size-6 text-muted-foreground" />
          <p className="mt-3 text-sm font-medium text-foreground">No documents found</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Ingest regulatory PDFs to make them available for browsing and questions.
          </p>
        </div>
      )}

      {!isLoading && !error && documents.length > 0 && (
        <>
          <ul className="divide-y divide-border overflow-hidden rounded-lg border border-border bg-card">
            {documents.map((document) => (
              <li key={document.id}>
                <button
                  className="flex w-full items-start gap-3 px-4 py-4 text-left transition-colors hover:bg-secondary/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
                  onClick={() => void openDocument(document)}
                  type="button"
                >
                  <span className="mt-0.5 rounded-md bg-secondary p-2 text-primary">
                    <FileText aria-hidden="true" className="size-4" />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm font-medium leading-5 text-foreground">
                      {document.title}
                    </span>
                    <span className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs capitalize text-muted-foreground">
                      <span>{document.source}</span>
                      <span aria-hidden="true">·</span>
                      <span>{documentTypeLabel(document.doc_type)}</span>
                      <span aria-hidden="true">·</span>
                      <span>{formatDate(document.issue_date)}</span>
                    </span>
                  </span>
                  <ArrowRight aria-hidden="true" className="mt-1 size-4 shrink-0 text-muted-foreground" />
                </button>
              </li>
            ))}
          </ul>

          <div className="flex items-center justify-between gap-3">
            <p className="text-xs text-muted-foreground">
              Page {pageNumber} of {pageCount}
            </p>
            <div className="flex gap-2">
              <button
                aria-label="Previous page"
                className="inline-flex size-9 items-center justify-center rounded-md border border-border bg-card text-foreground disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                disabled={offset === 0 || isLoading}
                onClick={() => setOffset((value) => Math.max(0, value - PAGE_SIZE))}
                type="button"
              >
                <ArrowLeft aria-hidden="true" className="size-4" />
              </button>
              <button
                aria-label="Next page"
                className="inline-flex size-9 items-center justify-center rounded-md border border-border bg-card text-foreground disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                disabled={offset + PAGE_SIZE >= total || isLoading}
                onClick={() => setOffset((value) => value + PAGE_SIZE)}
                type="button"
              >
                <ArrowRight aria-hidden="true" className="size-4" />
              </button>
            </div>
          </div>
        </>
      )}

      {isDetailLoading && (
        <p aria-live="polite" className="text-sm text-muted-foreground" role="status">
          Loading document details…
        </p>
      )}

      {detailError && (
        <p className="rounded-md border border-destructive/30 bg-card p-3 text-sm text-foreground" role="alert">
          {detailError}
        </p>
      )}

      {selectedDocument && (
        <section
          aria-labelledby="document-detail-heading"
          className="rounded-lg border border-border bg-secondary/50 p-4"
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground">
                Document details
              </p>
              <h3 className="mt-1 text-base font-medium text-foreground" id="document-detail-heading">
                {selectedDocument.title}
              </h3>
            </div>
            <button
              aria-label="Close document details"
              className="rounded px-2 py-1 text-sm text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              onClick={() => {
                detailRequestId.current += 1
                setSelectedDocument(null)
                setIsDetailLoading(false)
              }}
              type="button"
            >
              Close
            </button>
          </div>
          <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-xs text-muted-foreground">Regulator</dt>
              <dd className="mt-1 font-medium text-foreground">{selectedDocument.source}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Document type</dt>
              <dd className="mt-1 font-medium capitalize text-foreground">
                {documentTypeLabel(selectedDocument.doc_type)}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Issued</dt>
              <dd className="mt-1 font-medium text-foreground">
                {formatDate(selectedDocument.issue_date)}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Indexed passages</dt>
              <dd className="mt-1 font-medium text-foreground">
                {selectedDocument.chunk_count}
              </dd>
            </div>
          </dl>
        </section>
      )}
    </section>
  )
}
