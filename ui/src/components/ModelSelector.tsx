import { useEffect, useRef, useState } from 'react'
import { deleteModel, downloadModel, getModelStatus, listModels } from '../api/client'
import type { ModelPreset, ModelStatus, ModelStatusResponse } from '../types/models'

export interface ModelSelection {
  provider: 'openai' | 'local'
  modelId: string
}

interface Props {
  selection: ModelSelection
  onChange: (selection: ModelSelection) => void
  disabled?: boolean
}

// Hardcoded fallback so cards always render even when the API is unreachable.
const FALLBACK_PRESETS: ModelPreset[] = [
  {
    model_id: 'microsoft/Phi-3.5-mini-instruct',
    name: 'Phi-3.5 Mini',
    family: 'phi',
    description: 'Microsoft Phi-3.5 Mini — 3.8 B params, instruction-tuned, runs on CPU',
    size_hint: '~7 GB',
    requires_token: false,
  },
  {
    model_id: 'meta-llama/Llama-3.2-1B-Instruct',
    name: 'Llama 3.2 1B',
    family: 'llama',
    description: 'Meta Llama 3.2 — 1 B params, instruction-tuned, very lightweight',
    size_hint: '~2.5 GB',
    requires_token: true,
  },
  {
    model_id: 'google/gemma-2-2b-it',
    name: 'Gemma 2 2B',
    family: 'gemma',
    description: 'Google Gemma 2 — 2 B params, instruction-tuned',
    size_hint: '~5 GB',
    requires_token: true,
  },
]

const FAMILY_EMOJI: Record<string, string> = {
  phi: '🔷',
  llama: '🦙',
  gemma: '💎',
  custom: '🔧',
}

const STATUS_LABELS: Record<ModelStatus, string> = {
  not_downloaded: 'Not downloaded',
  downloading: 'Downloading…',
  ready: '✓ Ready',
  error: 'Error',
}

const STATUS_COLORS: Record<ModelStatus, string> = {
  not_downloaded: 'text-gray-500',
  downloading: 'text-amber-600',
  ready: 'text-green-600',
  error: 'text-red-600',
}

export function ModelSelector({ selection, onChange, disabled }: Props) {
  const [presets, setPresets] = useState<ModelPreset[]>(FALLBACK_PRESETS)
  const [statuses, setStatuses] = useState<Record<string, ModelStatusResponse>>({})
  const [customModelId, setCustomModelId] = useState('')
  const [hfToken, setHfToken] = useState('')
  const [showToken, setShowToken] = useState(false)
  const [downloadError, setDownloadError] = useState<string | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    listModels()
      .then(({ presets: p, statuses: s }) => {
        setPresets(p)
        setStatuses(s)
      })
      .catch(() => {
        // API unreachable — presets already set to FALLBACK_PRESETS; statuses stay empty (not_downloaded)
      })
  }, [])

  // Poll status for any model currently downloading
  useEffect(() => {
    const downloading = Object.values(statuses).filter(s => s.status === 'downloading')
    if (downloading.length === 0) {
      if (pollingRef.current) clearInterval(pollingRef.current)
      return
    }
    if (pollingRef.current) return // already polling

    pollingRef.current = setInterval(async () => {
      const updates = await Promise.allSettled(
        downloading.map(s => getModelStatus(s.model_id))
      )
      setStatuses(prev => {
        const next = { ...prev }
        updates.forEach(r => {
          if (r.status === 'fulfilled') next[r.value.model_id] = r.value
        })
        return next
      })
      // Stop polling when nothing is downloading any more
      const stillDownloading = updates.some(
        r => r.status === 'fulfilled' && r.value.status === 'downloading'
      )
      if (!stillDownloading && pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }, 3000)

    return () => {
      if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null }
    }
  }, [statuses])

  async function handleDownload(modelId: string) {
    setDownloadError(null)
    const preset = presets.find(p => p.model_id === modelId)
    const token = hfToken || undefined
    if (preset?.requires_token && !token) {
      setShowToken(true)
      setDownloadError('This model requires a HuggingFace token. Enter it above and retry.')
      return
    }
    try {
      const status = await downloadModel({ model_id: modelId, hf_token: token })
      setStatuses(prev => ({ ...prev, [modelId]: status }))
    } catch (err) {
      setDownloadError(err instanceof Error ? err.message : 'Download failed')
    }
  }

  async function handleDelete(modelId: string) {
    setDeleteError(null)
    try {
      const status = await deleteModel(modelId)
      setStatuses(prev => ({ ...prev, [modelId]: status }))
      // If the deleted model was selected, deselect it
      if (selection.provider === 'local' && selection.modelId === modelId) {
        onChange({ provider: 'local', modelId: '' })
      }
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Delete failed')
    }
  }

  function selectLocalModel(modelId: string) {
    onChange({ provider: 'local', modelId })
  }

  const effectiveLocalId = selection.provider === 'local' ? selection.modelId : ''

  return (
    <div className="space-y-4">
      {/* Provider tabs */}
      <div className="flex gap-2">
        {(['openai', 'local'] as const).map(p => (
          <button
            key={p}
            type="button"
            disabled={disabled}
            onClick={() =>
              onChange({
                provider: p,
                modelId: p === 'openai' ? '' : (effectiveLocalId || presets[0]?.model_id || ''),
              })
            }
            className={`flex-1 rounded-lg border py-2 text-sm font-medium transition-colors
              ${selection.provider === p
                ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                : 'border-gray-300 bg-white text-gray-600 hover:bg-gray-50'}
              disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {p === 'openai' ? '☁️ OpenAI' : '🖥️ Local (HuggingFace)'}
          </button>
        ))}
      </div>

      {/* Local model options */}
      {selection.provider === 'local' && (
        <div className="space-y-3">
          {/* HF Token (collapsed by default) */}
          <div>
            <button
              type="button"
              className="text-xs text-indigo-600 hover:underline"
              onClick={() => setShowToken(v => !v)}
            >
              {showToken ? '▾ Hide' : '▸ Set'} HuggingFace token (for gated models)
            </button>
            {showToken && (
              <input
                type="password"
                value={hfToken}
                onChange={e => setHfToken(e.target.value)}
                placeholder="hf_…"
                className="mt-1 w-full rounded border border-gray-300 px-3 py-1.5 text-xs
                           focus:border-indigo-400 focus:outline-none focus:ring-1 focus:ring-indigo-300"
              />
            )}
          </div>

          {/* Preset model cards */}
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            {presets.map(preset => {
              const status: ModelStatusResponse = statuses[preset.model_id] ?? {
                model_id: preset.model_id,
                status: 'not_downloaded',
                progress_pct: 0,
                error: null,
              }
              const isSelected = effectiveLocalId === preset.model_id
              const isReady = status.status === 'ready'
              const isDownloading = status.status === 'downloading'

              return (
                <div
                  key={preset.model_id}
                  className={`rounded-lg border p-3 space-y-2 cursor-pointer transition-colors
                    ${isSelected ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 bg-white hover:border-indigo-300'}
                    ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                  onClick={() => !disabled && isReady && selectLocalModel(preset.model_id)}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{FAMILY_EMOJI[preset.family]}</span>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-gray-800 truncate">{preset.name}</p>
                      <p className="text-xs text-gray-500">{preset.size_hint}</p>
                    </div>
                  </div>
                  <p className="text-xs text-gray-600">{preset.description}</p>
                  {preset.requires_token && (
                    <span className="inline-block text-xs bg-amber-100 text-amber-700 rounded px-1.5 py-0.5">
                      🔑 Token required
                    </span>
                  )}
                  <div className="flex items-center justify-between gap-1">
                    <span className={`text-xs font-medium ${STATUS_COLORS[status.status]}`}>
                      {STATUS_LABELS[status.status]}
                      {status.status === 'error' && status.error && (
                        <span className="block text-red-500 text-xs truncate" title={status.error}>
                          {status.error.slice(0, 40)}
                        </span>
                      )}
                    </span>
                    <div className="flex items-center gap-1">
                      {!isReady && !isDownloading && (
                        <button
                          type="button"
                          disabled={disabled}
                          onClick={e => { e.stopPropagation(); handleDownload(preset.model_id) }}
                          className="rounded bg-indigo-600 px-2 py-0.5 text-xs text-white
                                     hover:bg-indigo-700 disabled:opacity-50"
                        >
                          Download
                        </button>
                      )}
                      {isDownloading && (
                        <span className="text-xs text-amber-600 animate-pulse">⏳</span>
                      )}
                      {isReady && isSelected && (
                        <span className="text-xs text-indigo-600 font-semibold">Selected</span>
                      )}
                      {isReady && !isSelected && (
                        <button
                          type="button"
                          disabled={disabled}
                          onClick={e => { e.stopPropagation(); selectLocalModel(preset.model_id) }}
                          className="rounded border border-indigo-400 px-2 py-0.5 text-xs text-indigo-700
                                     hover:bg-indigo-50 disabled:opacity-50"
                        >
                          Use
                        </button>
                      )}
                      {isReady && (
                        <button
                          type="button"
                          disabled={disabled}
                          title="Delete model from disk"
                          onClick={e => {
                            e.stopPropagation()
                            if (window.confirm(`Delete "${preset.name}" from disk? You can re-download it later.`)) {
                              handleDelete(preset.model_id)
                            }
                          }}
                          className="rounded border border-red-300 px-2 py-0.5 text-xs text-red-600
                                     hover:bg-red-50 disabled:opacity-50"
                        >
                          🗑
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Custom model ID */}
          <div className="rounded-lg border border-dashed border-gray-300 p-3 space-y-2">
            <p className="text-xs font-medium text-gray-700">🔧 Custom model ID</p>
            <div className="flex gap-2">
              <input
                type="text"
                value={customModelId}
                onChange={e => setCustomModelId(e.target.value)}
                placeholder="e.g. mistralai/Mistral-7B-Instruct-v0.3"
                disabled={disabled}
                className="flex-1 rounded border border-gray-300 px-3 py-1.5 text-xs
                           focus:border-indigo-400 focus:outline-none focus:ring-1 focus:ring-indigo-300
                           disabled:opacity-50"
              />
              <button
                type="button"
                disabled={disabled || !customModelId.trim()}
                onClick={() => {
                  const id = customModelId.trim()
                  if (id) { handleDownload(id); selectLocalModel(id) }
                }}
                className="rounded bg-gray-700 px-3 py-1.5 text-xs text-white
                           hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Download & Use
              </button>
            </div>
            {effectiveLocalId && !presets.find(p => p.model_id === effectiveLocalId) && (
              <p className="text-xs text-indigo-600">
                Using custom model: <span className="font-mono">{effectiveLocalId}</span>
              </p>
            )}
          </div>

          {downloadError && (
            <p className="text-xs text-red-600">{downloadError}</p>
          )}
          {deleteError && (
            <p className="text-xs text-red-600">{deleteError}</p>
          )}
        </div>
      )}

      {/* Summary badge */}
      <div className="flex items-center gap-1.5 text-xs text-gray-500">
        <span>Active LLM:</span>
        <span className="font-mono bg-gray-100 rounded px-1.5 py-0.5">
          {selection.provider === 'openai' ? '☁️ OpenAI' : `🖥️ ${selection.modelId || 'local'}`}
        </span>
      </div>

      {/* CPU speed warning */}
      {selection.provider === 'local' && selection.modelId && (
        <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1.5">
          ⚠️ <strong>CPU inference is slow</strong> — expect 2–5 min per analysis. For faster results use OpenAI or set <code>LOCAL_MAX_NEW_TOKENS=256</code> in your <code>.env</code>.
        </p>
      )}
    </div>
  )
}
