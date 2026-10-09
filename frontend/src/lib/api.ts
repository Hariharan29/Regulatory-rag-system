export type DocumentSource = "RBI" | "SEBI"

export type DocumentType =
  | "circular"
  | "master_direction"
  | "notification"
  | "other"

export interface QueryRequest {
  question: string
  filters: {
    source?: DocumentSource
  }
}

export interface QueryCitation {
  chunk_id: number
  document_id: number
  document_title: string
  page_number: number
  excerpt: string
}

export interface RetrievedChunk {
  chunk_id: number
  document_id: number
  document_title: string
  source: DocumentSource
  page_number: number
  excerpt: string
  score: number
}

export interface QueryResponse {
  answer: string
  citations: QueryCitation[]
  chunks_used: RetrievedChunk[]
  low_confidence: boolean
  audit_id: number
}

export interface DocumentRecord {
  id: number
  title: string
  source: DocumentSource
  doc_type: DocumentType
  issue_date: string | null
  file_path: string
  created_at: string
}

export interface DocumentListResponse {
  total: number
  items: DocumentRecord[]
}

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

const API_BASE_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(
  /\/+$/,
  "",
)

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init)
  } catch {
    throw new ApiError("The service could not be reached.", 0)
  }

  const payload: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    const detail =
      typeof payload === "object" && payload !== null && "detail" in payload
        ? payload.detail
        : null
    const message = typeof detail === "string" ? detail : "The request could not be completed."
    throw new ApiError(message, response.status)
  }

  if (payload === null) {
    throw new ApiError("The service returned an unreadable response.", response.status)
  }

  return payload as T
}

export function askQuestion(request: QueryRequest): Promise<QueryResponse> {
  return requestJson<QueryResponse>("/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  })
}

export function getDocuments(): Promise<DocumentListResponse> {
  return requestJson<DocumentListResponse>("/documents")
}