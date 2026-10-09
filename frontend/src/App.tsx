import { useState } from 'react'

import AnswerView from '@/components/AnswerView'
import QueryForm from '@/components/QueryForm'
import type { QueryResponse } from '@/lib/api'

function App() {
  const [response, setResponse] = useState<QueryResponse | null>(null)

  return (
    <div className="min-h-svh bg-background text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto flex min-h-16 max-w-6xl items-center px-5 sm:px-8">
          <a className="text-sm font-semibold text-foreground" href="/">
            Regulatory Research
          </a>
        </div>
      </header>
      <main className="mx-auto w-full max-w-[720px] px-5 py-12 sm:px-8 sm:py-16">
        <QueryForm onResponse={setResponse} />
        {response && (
          <div className="mt-12 border-t border-border pt-8">
            <AnswerView response={response} />
          </div>
        )}
      </main>
    </div>
  )
}

export default App
