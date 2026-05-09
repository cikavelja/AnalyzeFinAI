export function Header() {
  return (
    <header className="bg-indigo-700 text-white shadow-md">
      <div className="max-w-4xl mx-auto px-4 py-4 flex items-center gap-3">
        <span className="text-2xl">🔍</span>
        <div>
          <h1 className="text-xl font-bold tracking-tight">AnalizerAI</h1>
          <p className="text-indigo-200 text-sm">AI-powered document analysis</p>
        </div>
      </div>
    </header>
  )
}
