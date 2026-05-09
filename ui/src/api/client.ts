import type { AnalyzeRequest, AnalyzeResponse, UploadResponse } from '../types/analysis'

const BASE_URL = import.meta.env.VITE_API_URL ?? ''

export async function analyze(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  const response = await fetch(`${BASE_URL}/api/v1/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`API error ${response.status}: ${detail}`)
  }

  return response.json() as Promise<AnalyzeResponse>
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${BASE_URL}/api/v1/documents/upload`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`Upload error ${response.status}: ${detail}`)
  }

  return response.json() as Promise<UploadResponse>
}
