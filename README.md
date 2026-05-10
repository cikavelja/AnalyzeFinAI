# AnalizerAI

> AI-powered document analysis platform integrating Microsoft Agent Framework (MAF),
> FastAPI, React, and a deterministic financial calculation engine.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quickstart](#quickstart)
- [Configuration](#configuration)
- [Development](#development)
- [Running the UI](#running-the-ui)
- [CLI Usage](#cli-usage)
- [Testing](#testing)
- [Docker](#docker)
- [Project Structure](#project-structure)
- [Known Limitations](#known-limitations)

---

## Overview

AnalizerAI analyses financial, legal, audit, and general documents using:

- **MAF Agents** (`OrchestratorAgent`, `AnalystAgent`, `ReviewerAgent`) for orchestrated,
  multi-step reasoning.
- **Deterministic financial engine** (`app/financial/calculator.py`) — no LLM arithmetic.
- **`UniversalAnalyzer`** for SUMMARY, COMPARISON, LEGAL, AUDIT, and CUSTOM analysis types
  (prompt-template-driven LLM narrative).
- **`FinancialAnalyzer`** combining deterministic metrics with LLM narrative generation.
- **React + TypeScript + Tailwind CSS** frontend for production interaction.
- **FastAPI** REST API (`GET /healthz`, `POST /api/v1/analyze`).
- **MAF DevUI** for development-time agent inspection and workflow tracing.
- **Append-only audit log** (JSONL) for every pipeline step.

---

## Architecture

```
Browser ►►► React UI (Vite + Tailwind, port 5173 dev / static in prod)
                 │  HTTP fetch
                 ▼
            FastAPI (port 8000)
            GET  /healthz
            POST /api/v1/analyze
                 │
        OrchestratorAgent
               │
   ┌──────────┼───────────┐
   ▼           ▼           ▼
AnalystAgent  ReviewerAgent  AnalysisWorkflow
   │
┌──┴──────────────────────┐
▼                          ▼
calculator.py         UniversalAnalyzer / FinancialAnalyzer
(deterministic)       (LLM narrative via prompt templates)
```

**Layer responsibilities:**

| Layer | Path | Responsibility |
|-------|------|----------------|
| API | `app/api/` | FastAPI REST endpoints, CORS, static file serving |
| Ingestion | `app/ingestion/` | File validation, type detection, metadata creation |
| Conversion | `app/conversion/` | Text/Markdown extraction (`local`, `markitdown`, or `mcp`) |
| Chunking | `app/chunking/` | Split text into overlapping DocumentChunks |
| Routing | `app/routing/` | Keyword-based AnalysisType detection |
| Analyzers | `app/analyzers/` | LLM narrative generation per analysis type |
| Financial | `app/financial/` | Deterministic pandas/numpy calculations |
| Agents | `app/agents/` | MAF agent instances with tool functions |
| Workflows | `app/workflows/` | MAF sequential pipeline orchestration |
| Audit | `app/audit/` | Append-only JSONL audit logger |
| UI (React) | `ui/` | React + TypeScript + Tailwind CSS frontend |
| UI (Dev) | `app/ui/` | MAF DevUI dev-only launcher |

---

## Quickstart

```bash
# 1. Clone the repo
git clone <repo-url>
cd AnalyzeFinAI

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dev dependencies
make install-dev

# 4. Copy and configure environment variables
cp .env.example .env
# Edit .env and set OPENAI_API_KEY

# 5. Run tests
make test
```

---

## Configuration

All settings are read from environment variables (or `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | _(required)_ | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o` | Model to use for OpenAI provider |
| `LLM_PROVIDER` | `openai` | `openai` \| `local` (HuggingFace on-device) |
| `LOCAL_MODEL_ID` | `microsoft/Phi-3.5-mini-instruct` | HuggingFace model ID (used when `LLM_PROVIDER=local`) |
| `HF_TOKEN` | _(empty)_ | HuggingFace access token for gated models |
| `HF_CACHE_DIR` | `data/models` | Directory for cached HuggingFace model weights |
| `CONVERSION_MODE` | `markitdown` | `local` \| `markitdown` \| `mcp` |
| `MCP_ENDPOINT` | `http://localhost:3001/convert` | MCP server endpoint (used when `CONVERSION_MODE=mcp`) |
| `LOG_LEVEL` | `INFO` | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` |
| `AUDIT_LOG_PATH` | `data/audit.jsonl` | Audit log file path |
| `LOCAL_ONLY_MODE` | `false` | Block all network calls when `true` |

---

## Development

```bash
make install-dev   # Install all deps including dev extras
make lint          # Run ruff + mypy
make fmt           # Auto-format with ruff
make test          # Run pytest
```

---

## Running the UI

### Production — FastAPI + React (built)

```bash
# 1. Build the React frontend
cd ui && npm run build && cd ..

# 2. Start the API server (serves React static files too)
make run-api
# → http://localhost:8000
```

### Development — API + React (hot-reload)

Run each in a separate terminal:

```bash
# Terminal 1 — FastAPI with auto-reload
make run-api
# → http://localhost:8000/api/v1/analyze

# Terminal 2 — Vite dev server with HMR
make run-react
# → http://localhost:5173
```

### Development — MAF DevUI (dev only)

```bash
make run-devui
# → http://localhost:8080
```

> ⚠️ DevUI is for development inspection only. Never use it in production.

---

## CLI Usage

```bash
# Validate a file
python -m app validate path/to/report.pdf

# Analyse a document
python -m app analyze "What is the revenue trend?" --file path/to/report.pdf

# Specify output path
python -m app analyze "Summarise this contract" -f contract.pdf -o data/summary.md
```

---

## Testing

```bash
make test        # Full suite
make test-unit   # Unit tests only
```

Tests are in `tests/unit/`. Each module has:
- At least one success-path test
- At least one failure/error-path test
- Edge-case coverage (empty, zero, None)

Sample documents for integration tests go in `tests/fixtures/sample_docs/`.

---

## Docker

```bash
# Build and run
cd docker
docker-compose up --build

# The React UI + FastAPI are available at http://localhost:8000
```

Environment variables are passed via `.env` or Docker Compose environment block.

---

## Project Structure

```
app/
├── agents/          # MAF agent instances
│   ├── orchestrator_agent.py
│   ├── analyst_agent.py
│   └── reviewer_agent.py
├── analyzers/       # Document analyzers (LLM narrative)
├── api/             # FastAPI app, routes, schemas
│   ├── main.py
│   ├── routes/      # health.py, analysis.py
│   └── schemas/     # Pydantic request/response schemas
├── audit/           # Append-only JSONL audit logger
├── chunking/        # Text chunker
├── config.py        # pydantic-settings singleton
├── conversion/      # Document → text/markdown converters
├── exceptions.py    # Typed exceptions
├── financial/       # Deterministic calculator (no LLM)
├── ingestion/       # File detector, validator, loader
├── llm/             # LLM provider abstractions
├── models/          # Pydantic data models
├── reporting/       # Report writer (Markdown + JSON)
├── routing/         # Keyword-based prompt router
├── storage/         # Filesystem storage backend
├── ui/              # MAF DevUI dev-only launcher
├── validation/      # Result validator
└── workflows/       # MAF workflow orchestration
ui/
├── src/             # React + TypeScript components and API client
└── dist/            # Built assets (generated, gitignored)
tests/
├── unit/            # Unit tests (no real APIs)
└── fixtures/        # Sample documents
docker/
├── Dockerfile
└── docker-compose.yml
```

---

## Known Limitations

- `LocalConverter` only does plain-text pass-through (UTF-8 decode). Use
  `CONVERSION_MODE=markitdown` for PDF, DOCX, XLSX, PPTX, HTML, and image support.
- `MCPConverter` requires a running MarkItDown MCP server at the configured
  `MCP_ENDPOINT` (default `localhost:3001`).
- The `agent_framework` package (`agent-framework>=1.0.0`) must be available in the
  Python environment. If not installed, agents and workflows will fail to import.
- Financial DataFrame extraction (`app/financial/extractor.py`) currently produces a
  stub empty DataFrame when no structured tabular data is detected. Full document-to-
  DataFrame extraction from arbitrary PDFs is a Phase 2 task.
