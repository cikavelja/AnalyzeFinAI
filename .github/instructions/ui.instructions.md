---
description: "Use when creating or editing UI code in app/ui/ or ui/. Covers React/Vite/Tailwind patterns, FastAPI integration, DevUI launch script, and what must not appear in production UI."
applyTo: "{app/ui/**/*.py,ui/src/**/*.{ts,tsx}}"
---
# UI Conventions — React (Production) + DevUI (Development)

## React Frontend (`ui/src/`)

The production UI is a Vite + React 18 + TypeScript + Tailwind CSS application in `ui/`.

### API Client (`ui/src/api/client.ts`)

All API calls go through the typed client — never call `fetch` directly in components:

```typescript
import { analyze } from '../api/client'
const result = await analyze({ prompt })
```

### Component Conventions

- Use functional components with typed props interfaces.
- Keep components under 150 lines — split by concern if larger.
- Tailwind classes only — no inline styles, no CSS modules.
- Async state: `isLoading`, `error`, `result` pattern in the page-level component (`App.tsx`).

### What Must NOT Be in React Code

- No business logic — only calls to `api/client.ts` functions.
- No hardcoded API base URLs — use `import.meta.env.VITE_API_URL ?? ''` (proxied via Vite in dev).
- No direct `fetch` outside `ui/src/api/client.ts`.

## DevUI — Development Launch Script (`devui_app.py`)

```python
# app/ui/devui_app.py
from agent_framework.devui import serve
from app.agents.orchestrator_agent import orchestrator_agent
from app.workflows.analysis_workflow import analysis_workflow

if __name__ == "__main__":
    serve(
        entities=[orchestrator_agent, analysis_workflow],
        auto_open=True,
        port=8080,
    )
```

- This file is **dev-only**. It must not be imported by any other module.
- Do not add `devui_app.py` to the production Docker image CMD.
- Use `--tracing` CLI flag for OpenTelemetry trace visualization.

## What Must NOT Be in UI Code

- No business logic — UI files only call pipeline/agent/workflow or API functions.
- No direct LLM calls from UI files — always go through the agent or API layer.
- No raw document content in log messages.
- No hardcoded API keys or model names — always read from environment / `app/config.py`.
