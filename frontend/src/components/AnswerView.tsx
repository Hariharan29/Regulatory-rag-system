import { useState } from "react"
import { ArrowDownRight, BookMarked, ChevronDown, ChevronUp } from "lucide-react"

import type { QueryResponse } from "@/lib/api"

interface AnswerViewProps {
  response: QueryResponse
}

export default function AnswerView({ response }: AnswerViewProps) {
  const [expandedSources, setExpandedSources] = useState<Set<number>>(
    () => new Set(),
  )
  const retrievedById = new Map(
    response.chunks_used.map((chunk) => [chunk.chunk_id, chunk]),
  )
  const sourceOrder = new Map(
    response.chunks_used.map((chunk, index) => [index + 1, chunk.chunk_id]),
  )
  const citationIds = new Set(response.citations.map((citation) => citation.chunk_id))

  function renderAnswer() {
    const parts = response.answer.split(/(\[SRC-\d+\])/gi)
    return parts.map((part, index) => {
      const match = /^\[SRC-(\d+)\]$/i.exec(part)
      const chunkId = match ? sourceOrder.get(Number(match[1])) : undefined
      if (!chunkId || !citationIds.has(chunkId)) {
        return <span key={`answer-${index}`}>{part}</span>
      }
      return (
        <a
          className="mx-0.5 inline-flex rounded-sm px-1 text-sm font-semibold text-primary underline decoration-primary/40 underline-offset-2 hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          href={`#source-${chunkId}`}
          key={`answer-${index}`}
          aria-label={`View source ${match?.[1]}`}
        >
          [{match?.[1]}]
        </a>
      )
    })
  }

  return (
    <section aria-labelledby="answer-heading" className="space-y-8">
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground">
              Research response
            </p>
            <h2 className="mt-1 text-xl font-medium tracking-tight" id="answer-heading">
              Answer
            </h2>
          </div>
          {response.low_confidence ? (
            <span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-900">
              Limited evidence
            </span>
          ) : (
            <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-900">
              Sources linked
            </span>
          )}
        </div>

        <div
          className={`rounded-lg border bg-card p-5 sm:p-6 ${
            response.low_confidence ? "border-amber-300" : "border-border"
          }`}
          role={response.low_confidence ? "status" : undefined}
        >
          <p className="whitespace-pre-wrap font-serif text-[18px] leading-[1.75] text-foreground">
            {renderAnswer()}
          </p>
        </div>
      </div>

      {response.citations.length > 0 && (
        <section aria-labelledby="sources-heading" className="space-y-4">
          <div className="flex items-center gap-2">
            <BookMarked aria-hidden="true" className="size-4 text-primary" />
            <h3 className="text-base font-medium text-foreground" id="sources-heading">
              Sources
            </h3>
            <span className="text-xs text-muted-foreground">
              {response.citations.length}
            </span>
          </div>

          <ol className="space-y-3">
            {response.citations.map((citation, index) => {
              const retrieved = retrievedById.get(citation.chunk_id)
              const sourceReference = response.chunks_used.findIndex(
                (chunk) => chunk.chunk_id === citation.chunk_id,
              ) + 1
              const isExpanded = expandedSources.has(citation.chunk_id)
              return (
                <li
                  className="scroll-mt-6 rounded-lg border border-border bg-card"
                  id={`source-${citation.chunk_id}`}
                  key={citation.chunk_id}
                >
                  <button
                    aria-expanded={isExpanded}
                    className="flex w-full items-start gap-3 p-4 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
                    onClick={() =>
                      setExpandedSources((current) => {
                        const next = new Set(current)
                        if (next.has(citation.chunk_id)) next.delete(citation.chunk_id)
                        else next.add(citation.chunk_id)
                        return next
                      })
                    }
                    type="button"
                  >
                    <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-secondary text-xs font-semibold text-primary">
                      {sourceReference || index + 1}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block text-sm font-medium text-foreground">
                        {citation.document_title}
                      </span>
                      <span className="mt-1 block text-xs text-muted-foreground">
                        [SRC-{sourceReference || index + 1}] ·{" "}
                        {retrieved?.source ?? "Regulator"} · Page {citation.page_number}
                      </span>
                      {!isExpanded && (
                        <span className="mt-2 block line-clamp-2 text-sm leading-6 text-muted-foreground">
                          {citation.excerpt}
                        </span>
                      )}
                    </span>
                    {isExpanded ? (
                      <ChevronUp aria-hidden="true" className="mt-1 size-4 shrink-0 text-muted-foreground" />
                    ) : (
                      <ChevronDown aria-hidden="true" className="mt-1 size-4 shrink-0 text-muted-foreground" />
                    )}
                  </button>
                  {isExpanded && (
                    <div className="border-t border-border px-4 pb-4 pt-3 sm:ml-10">
                      <p className="whitespace-pre-wrap text-sm leading-6 text-foreground">
                        {citation.excerpt}
                      </p>
                      <p className="mt-3 flex items-center gap-1 text-xs text-muted-foreground">
                        <ArrowDownRight aria-hidden="true" className="size-3.5" />
                        Indexed excerpt · source document page {citation.page_number}
                      </p>
                    </div>
                  )}
                </li>
              )
            })}
          </ol>
        </section>
      )}

      {response.citations.length === 0 && !response.low_confidence && (
        <p className="rounded-md border border-amber-300 bg-amber-50 p-4 text-sm text-amber-950" role="status">
          No source citations were returned for this answer. Treat it as unverified.
        </p>
      )}
    </section>
  )
}