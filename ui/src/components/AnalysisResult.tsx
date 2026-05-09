import type { AnalyzeResponse } from '../types/analysis'

interface Props {
  result: AnalyzeResponse
}

function Badge({ label }: { label: string }) {
  return (
    <span className="inline-block rounded-full bg-indigo-100 text-indigo-800 text-xs font-medium px-3 py-0.5">
      {label}
    </span>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">{title}</h3>
      {children}
    </div>
  )
}

export function AnalysisResult({ result }: Props) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-gray-800">Analysis Result</h2>
        <Badge label={result.analysis_type} />
      </div>

      {result.summary && (
        <Section title="Summary">
          <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">
            {result.summary}
          </p>
        </Section>
      )}

      {result.key_findings.length > 0 && (
        <Section title="Key Findings">
          <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
            {result.key_findings.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        </Section>
      )}

      {result.recommendations.length > 0 && (
        <Section title="Recommendations">
          <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
            {result.recommendations.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </Section>
      )}

      {Object.keys(result.metrics).length > 0 && (
        <Section title="Metrics">
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(result.metrics).map(([key, value]) => (
              <div key={key} className="rounded-lg bg-gray-50 px-3 py-2">
                <p className="text-xs text-gray-500">{key}</p>
                <p className="text-sm font-semibold text-gray-800">{value}</p>
              </div>
            ))}
          </div>
        </Section>
      )}

      {result.warnings.length > 0 && (
        <Section title="Warnings">
          <ul className="space-y-1">
            {result.warnings.map((w, i) => (
              <li
                key={i}
                className="flex gap-2 items-start rounded-lg bg-yellow-50 border border-yellow-200 px-3 py-2 text-sm text-yellow-800"
              >
                <span className="shrink-0">⚠️</span>
                <span>{w}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}

      <p className="text-xs text-gray-400">
        Request ID: {result.request_id}
        {result.model_used && ` · Model: ${result.model_used}`}
      </p>
    </div>
  )
}
