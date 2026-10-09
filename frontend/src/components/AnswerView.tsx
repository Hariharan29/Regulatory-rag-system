import type { QueryResponse } from "@/lib/api"

interface AnswerViewProps {
  response: QueryResponse
}

export default function AnswerView({ response }: AnswerViewProps) {
  return (
    <section aria-labelledby="answer-heading" className="space-y-4">
      <h2
        className="text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground"
        id="answer-heading"
      >
        Answer
      </h2>
      <div
        className={
          response.low_confidence
            ? "border-l-2 border-primary py-1 pl-4"
            : undefined
        }
        role={response.low_confidence ? "status" : undefined}
      >
        <p className="whitespace-pre-wrap font-serif text-[18px] leading-[1.6] text-foreground">
          {response.answer}
        </p>
      </div>
    </section>
  )
}