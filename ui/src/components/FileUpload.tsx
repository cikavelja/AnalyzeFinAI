import { useRef, useState } from 'react'

export interface UploadedFile {
  id: string
  name: string
  size: number
}

interface Props {
  uploadedFiles: UploadedFile[]
  onUpload: (files: FileList) => void
  onRemove: (id: string) => void
  isLoading: boolean
}

const ACCEPTED = '.pdf,.docx,.xlsx,.csv,.pptx,.txt,.md,.html,.json,.xml,.png,.jpg,.jpeg,.zip'

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function FileUpload({ uploadedFiles, onUpload, onRemove, isLoading }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files.length > 0) onUpload(e.dataTransfer.files)
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files.length > 0) {
      onUpload(e.target.files)
      e.target.value = ''
    }
  }

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-gray-700">
        Documents <span className="text-gray-400 font-normal">(optional)</span>
      </label>

      <div
        onClick={() => !isLoading && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed
                    px-6 py-6 text-sm transition-colors cursor-pointer
                    ${isDragging ? 'border-indigo-400 bg-indigo-50' : 'border-gray-300 bg-gray-50 hover:border-indigo-300 hover:bg-indigo-50/40'}
                    ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <svg className="h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
        </svg>
        <span className="text-gray-600">
          <span className="font-medium text-indigo-600">Click to upload</span> or drag & drop
        </span>
        <span className="text-xs text-gray-400">PDF, DOCX, XLSX, CSV, TXT and more</span>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED}
          className="hidden"
          onChange={handleChange}
          disabled={isLoading}
        />
      </div>

      {uploadedFiles.length > 0 && (
        <ul className="space-y-2">
          {uploadedFiles.map((f) => (
            <li key={f.id} className="flex items-center justify-between rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm">
              <div className="flex items-center gap-2 min-w-0">
                <svg className="h-4 w-4 shrink-0 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span className="truncate text-gray-700">{f.name}</span>
                <span className="shrink-0 text-gray-400">{formatBytes(f.size)}</span>
              </div>
              <button
                type="button"
                onClick={() => onRemove(f.id)}
                disabled={isLoading}
                className="ml-2 shrink-0 text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50"
                aria-label={`Remove ${f.name}`}
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
