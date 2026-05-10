export interface AnalyzeRequest {
  prompt: string
  document_ids?: string[]
  provider?: 'openai' | 'local'
  model_id?: string
}

export interface AnalyzeResponse {
  request_id: string
  analysis_type: string
  summary: string
  narrative: string
  key_findings: string[]
  recommendations: string[]
  warnings: string[]
  metrics: Record<string, number>
  model_used: string | null
}

export interface UploadResponse {
  document_id: string
  file_name: string
  file_size: number
}
