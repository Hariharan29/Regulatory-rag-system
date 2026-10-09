import { useState } from 'react'
import { ArrowUpRight, Landmark, ShieldCheck } from 'lucide-react'

import AnswerView from '@/components/AnswerView'
import DocumentLibrary from '@/components/DocumentLibrary'
import QueryForm from '@/components/QueryForm'
import { API_BASE_URL, type QueryResponse } from '@/lib/api'

function App() {
  const [response, setResponse] = useState<QueryResponse | null>(null)

  return (
    <div className="min-h-svh bg-background text-foreground">
      <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="mx-auto flex min-h-16 max-w-7xl items-center justify-between px-5 sm:px-8">
          <a aria-label="Regulatory Research home" className="flex items-center gap-3" href="/">
            <span className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Landmark aria-hidden="true" className="size-5" />
            </span>
            <span>
              <span className="block text-sm font-semibold text-foreground">
                Regulatory Research
              </span>
              <span className="block text-xs text-muted-foreground">
                RBI &amp; SEBI knowledge assistant
              </span>
            </span>
          </a>
          <a
            className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline focus-visible:rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            href={`${API_BASE_URL}/docs`}
            rel="noreferrer"
            target="_blank"
          >
            API docs
            <ArrowUpRight aria-hidden="true" className="size-3.5" />
          </a>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl flex-1 px-5 py-8 sm:px-8 sm:py-12">
        <section className="mb-9 max-w-3xl">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
            Regulatory intelligence, grounded in source documents
          </p>
          <h1 className="mt-3 text-3xl font-medium leading-tight tracking-tight text-foreground sm:text-4xl">
            Find the rule. Understand the requirement.
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base">
            Ask a question about indexed RBI and SEBI documents. Review the cited
            excerpts and page references alongside each response.
          </p>
        </section>

        <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(320px,0.82fr)] lg:gap-10">
          <div className="min-w-0 space-y-8">
            <section className="rounded-xl border border-border bg-card p-5 shadow-sm sm:p-7">
              <QueryForm onResponse={setResponse} />
            </section>
            {response ? (
              <div aria-live="polite" className="min-w-0">
                <AnswerView response={response} />
              </div>
            ) : (
              <div className="flex items-start gap-3 rounded-lg border border-border bg-secondary/50 p-4">
                <ShieldCheck aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-primary" />
                <p className="text-sm leading-6 text-muted-foreground">
                  Answers are generated from indexed documents and are not a
                  substitute for the regulator’s current official publications
                  or professional advice.
                </p>
              </div>
            )}
          </div>

          <aside className="min-w-0 rounded-xl border border-border bg-background p-5 sm:p-6">
            <DocumentLibrary />
            <p className="mt-5 border-t border-border pt-4 text-xs leading-5 text-muted-foreground">
              The library displays document metadata and indexed passage counts.
              Source PDFs remain in the configured document store.
            </p>
          </aside>
        </div>
      </main>

      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 px-5 py-5 text-xs text-muted-foreground sm:px-8">
          <span>Regulatory Research · RBI and SEBI documents</span>
          <span>Verify important requirements against the official source.</span>
        </div>
      </footer>
    </div>
  )
}

export default App
