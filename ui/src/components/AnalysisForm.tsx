import { useState, type FormEvent } from 'react'
import { uploadDocument } from '../api/client'
import { FileUpload, type UploadedFile } from './FileUpload'
import { ModelSelector, type ModelSelection } from './ModelSelector'

interface Props {
  onSubmit: (prompt: string, documentIds: string[], provider: 'openai' | 'local', modelId: string) => void
  isLoading: boolean
}

export function AnalysisForm({ onSubmit, isLoading }: Props) {
  const [prompt, setPrompt] = useState('')
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [modelSelection, setModelSelection] = useState<ModelSelection>({
    provider: 'openai',
    modelId: '',
  })

  async function handleUpload(files: FileList) {
    setUploadError(null)
    setIsUploading(true)
    try {
      const results = await Promise.all(
        Array.from(files).map((f) => uploadDocument(f)),
      )
      setUploadedFiles((prev) => [
        ...prev,
        ...results.map((r) => ({ id: r.document_id, name: r.file_name, size: r.file_size })),
      ])
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  function handleRemove(id: string) {
    setUploadedFiles((prev) => prev.filter((f) => f.id !== id))
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const trimmed = prompt.trim()
    if (trimmed) {
      onSubmit(
        trimmed,
        uploadedFiles.map((f) => f.id),
        modelSelection.provider,
        modelSelection.modelId,
      )
    }
  }

  const busy = isLoading || isUploading

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <ModelSelector
        selection={modelSelection}
        onChange={setModelSelection}
        disabled={busy}
      />

      <FileUpload
        uploadedFiles={uploadedFiles}
        onUpload={handleUpload}
        onRemove={handleRemove}
        isLoading={busy}
      />

      {uploadError && (
        <p className="text-sm text-red-600">{uploadError}</p>
      )}

      <label htmlFor="prompt" className="block text-sm font-medium text-gray-700">
        Analysis prompt
      </label>
      <textarea
        id="prompt"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        rows={5}
        placeholder="e.g. Summarise the key financial metrics and revenue trends…"
        className="w-full rounded-lg border border-gray-300 px-4 py-3 text-sm shadow-sm
                   focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-300
                   resize-none disabled:opacity-50"
        disabled={busy}
      />
      <button
        type="submit"
        disabled={busy || !prompt.trim()}
        className="w-full rounded-lg bg-indigo-600 px-6 py-3 text-sm font-semibold text-white
                   shadow hover:bg-indigo-700 active:bg-indigo-800 transition-colors
                   disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isUploading ? 'Uploading…' : isLoading ? 'Analysing…' : 'Analyse'}
      </button>
    </form>
  )
}
