import type { AnalyzeRequest, AnalyzeResponse, UploadResponse } from '../types/analysis'
import type { DownloadRequest, ModelStatusResponse, ModelsListResponse } from '../types/models'

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

export async function listModels(): Promise<ModelsListResponse> {
  const response = await fetch(`${BASE_URL}/api/v1/models`)
  if (!response.ok) throw new Error(`Models API error ${response.status}`)
  return response.json() as Promise<ModelsListResponse>
}

export async function downloadModel(request: DownloadRequest): Promise<ModelStatusResponse> {
  const response = await fetch(`${BASE_URL}/api/v1/models/download`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`Download error ${response.status}: ${detail}`)
  }
  return response.json() as Promise<ModelStatusResponse>
}

export async function getModelStatus(modelId: string): Promise<ModelStatusResponse> {
  const encodedId = modelId.replace(/\//g, '--')
  const response = await fetch(`${BASE_URL}/api/v1/models/${encodedId}/status`)
  if (!response.ok) throw new Error(`Status API error ${response.status}`)
  return response.json() as Promise<ModelStatusResponse>
}

export async function deleteModel(modelId: string): Promise<ModelStatusResponse> {
  const encodedId = modelId.replace(/\//g, '--')
  const response = await fetch(`${BASE_URL}/api/v1/models/${encodedId}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`Delete error ${response.status}: ${detail}`)
  }
  return response.json() as Promise<ModelStatusResponse>
}
