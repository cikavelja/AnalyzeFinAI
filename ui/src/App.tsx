import { useState } from 'react'
import { analyze } from './api/client'
import type { AnalyzeResponse } from './types/analysis'
import { Header } from './components/Header'
import { AnalysisForm } from './components/AnalysisForm'
import { AnalysisResult } from './components/AnalysisResult'
import { LoadingSpinner } from './components/LoadingSpinner'

export default function App() {
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  async function handleSubmit(prompt: string, documentIds: string[], provider: 'openai' | 'local', modelId: string) {
    setIsLoading(true)
    setError(null)
    setResult(null)

    try {
      const data = await analyze({
        prompt,
        document_ids: documentIds.length ? documentIds : undefined,
        provider,
        model_id: modelId || undefined,
      })
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unexpected error')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />
      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-8 space-y-6">
        <div className="rounded-xl border border-gray-200 bg-white shadow-sm p-6">
          <AnalysisForm onSubmit={handleSubmit} isLoading={isLoading} />
        </div>

        {isLoading && <LoadingSpinner />}

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            <strong>Error:</strong> {error}
          </div>
        )}

        {result && <AnalysisResult result={result} />}
      </main>
    </div>
  )
}
