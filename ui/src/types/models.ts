export interface ModelPreset {
  model_id: string
  name: string
  family: 'phi' | 'llama' | 'gemma' | 'custom'
  description: string
  size_hint: string
  requires_token: boolean
}

export type ModelStatus = 'not_downloaded' | 'downloading' | 'ready' | 'error'

export interface ModelStatusResponse {
  model_id: string
  status: ModelStatus
  progress_pct: number
  error: string | null
}

export interface ModelsListResponse {
  presets: ModelPreset[]
  statuses: Record<string, ModelStatusResponse>
}

export interface DownloadRequest {
  model_id: string
  hf_token?: string
}
