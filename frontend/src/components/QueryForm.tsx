import { useState, type FormEvent, type MouseEvent } from "react"

import { Button } from "@/components/ui/button"
import {
  ApiError,
  askQuestion,
  type DocumentSource,
  type QueryRequest,
  type QueryResponse,
} from "@/lib/api"

interface QueryFormProps {
  onResponse?: (response: QueryResponse) => void
}

const exampleQuestions = [
  "KYC requirements for NBFCs",
  "Reporting cyber security incidents",
  "Disclosure requirements for investment advisers",
]

const sourceOptions: Array<{ label: string; value: DocumentSource | "ALL" }> = [
  { label: "All", value: "ALL" },
  { label: "RBI", value: "RBI" },
  { label: "SEBI", value: "SEBI" },
]

export default function QueryForm({ onResponse }: QueryFormProps) {
  const [question, setQuestion] = useState("")
  const [source, setSource] = useState<DocumentSource | "ALL">("ALL")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastRequest, setLastRequest] = useState<QueryRequest | null>(null)
  const [responseReceived, setResponseReceived] = useState(false)

  async function submitRequest(request: QueryRequest) {
    setLastRequest(request)
    setError(null)
    setResponseReceived(false)
    setIsLoading(true)

    try {
      const response = await askQuestion(request)
      onResponse?.(response)
      setResponseReceived(true)
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : "The query could not be completed.",
      )
    } finally {
      setIsLoading(false)
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmedQuestion = question.trim()
    if (!trimmedQuestion || isLoading) return

    void submitRequest({
      question: trimmedQuestion,
      filters: source === "ALL" ? {} : { source },
    })
  }

  function handleExampleClick(event: MouseEvent<HTMLAnchorElement>, example: string) {
    event.preventDefault()
    setQuestion(example)
    document.getElementById("query-input")?.focus()
  }

  return (
    <section aria-labelledby="query-heading" className="w-full">
      <h1
        id="query-heading"
        className="mb-6 text-base font-medium text-foreground"
      >
        Ask a question
      </h1>

      <form className="space-y-5" onSubmit={handleSubmit}>
        <div className="space-y-2">
          <label className="text-sm text-muted-foreground" htmlFor="query-input">
            Regulatory question
          </label>
          <input
            autoComplete="off"
            className="h-12 w-full rounded-[4px] border border-border bg-white px-4 text-base text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-wait disabled:bg-muted"
            disabled={isLoading}
            id="query-input"
            onChange={(event) => {
              setQuestion(event.target.value)
              setError(null)
              setResponseReceived(false)
            }}
            placeholder="e.g. KYC requirements for NBFCs"
            type="text"
            value={question}
          />
        </div>

        <div className="flex flex-wrap items-end justify-between gap-4">
          <fieldset className="space-y-2" disabled={isLoading}>
            <legend className="text-sm text-muted-foreground">Filter by source</legend>
            <div
              aria-label="Regulator source"
              className="inline-flex gap-1 rounded-[4px] border border-border p-1"
              role="group"
            >
              {sourceOptions.map((option) => {
                const selected = source === option.value
                return (
                  <button
                    aria-pressed={selected}
                    className={`min-w-14 rounded-[3px] px-3 py-1.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-wait disabled:opacity-60 ${
                      selected
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                    disabled={isLoading}
                    key={option.value}
                    onClick={() => setSource(option.value)}
                    type="button"
                  >
                    {option.label}
                  </button>
                )
              })}
            </div>
          </fieldset>

          <Button
            className="h-10 rounded-[4px] px-5 shadow-none transition-none active:translate-y-0"
            disabled={isLoading}
            type="submit"
          >
            {isLoading ? "Searching..." : "Search"}
          </Button>
        </div>
      </form>

      {!question && !error && !responseReceived && (
        <div className="mt-8 space-y-3 text-sm">
          <p className="text-muted-foreground">
            Ask a specific question about an RBI or SEBI requirement.
          </p>
          <ul className="space-y-2">
            {exampleQuestions.map((example) => (
              <li key={example}>
                <a
                  className="text-primary underline decoration-border underline-offset-4 hover:decoration-primary focus-visible:rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  href="#query-input"
                  onClick={(event) => handleExampleClick(event, example)}
                >
                  {example}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {isLoading && (
        <p aria-live="polite" className="mt-5 text-sm text-muted-foreground" role="status">
          Searching indexed documents...
        </p>
      )}

      {responseReceived && (
        <p aria-live="polite" className="mt-5 text-sm text-muted-foreground" role="status">
          Response received.
        </p>
      )}

      {error && (
        <div
          className="mt-6 flex items-center gap-3 border-l-2 border-primary py-1 pl-4 text-sm text-muted-foreground"
          role="alert"
        >
          <p>{error}</p>
          {lastRequest && (
            <button
              className="shrink-0 text-primary underline underline-offset-4 focus-visible:rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              disabled={isLoading}
              onClick={() => void submitRequest(lastRequest)}
              type="button"
            >
              Retry
            </button>
          )}
        </div>
      )}
    </section>
  )
}