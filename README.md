# AnalizerAI

> AI-powered document analysis platform integrating Microsoft Agent Framework (MAF),
> Chainlit, and a deterministic financial calculation engine.

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
- [Known Limitations (Phase 1)](#known-limitations-phase-1)

---

## Overview

AnalizerAI analyses financial, legal, audit, and general documents using:

- **MAF Agents** (`OrchestratorAgent`, `AnalystAgent`, `ReviewerAgent`) for orchestrated,
  multi-step reasoning.
- **Deterministic financial engine** (`app/financial/calculator.py`) — no LLM arithmetic.
- **Chainlit UI** for production chat-based interaction.
- **MAF DevUI** for development-time agent inspection and workflow tracing.
- **Append-only audit log** (JSONL) for every pipeline step.

---

## Architecture

```
User ──► Chainlit UI ──► OrchestratorAgent
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
         AnalystAgent    ReviewerAgent   AnalysisWorkflow
              │
     ┌────────┴────────┐
     ▼                 ▼
 calculator.py    SummaryAnalyzer
 (deterministic)  (LLM narrative)
```

**Layer responsibilities:**

| Layer | Path | Responsibility |
|-------|------|----------------|
| Ingestion | `app/ingestion/` | File validation, type detection, metadata creation |
| Conversion | `app/conversion/` | Text/Markdown extraction (local or MCP) |
| Chunking | `app/chunking/` | Split text into overlapping DocumentChunks |
| Routing | `app/routing/` | Keyword-based AnalysisType detection |
| Analyzers | `app/analyzers/` | LLM narrative generation per analysis type |
| Financial | `app/financial/` | Deterministic pandas/numpy calculations |
| Agents | `app/agents/` | MAF agent instances with tool functions |
| Workflows | `app/workflows/` | MAF sequential pipeline orchestration |
| Audit | `app/audit/` | Append-only JSONL audit logger |
| UI | `app/ui/` | Chainlit (prod) + DevUI (dev only) |

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
| `OPENAI_MODEL` | `gpt-4o` | Model to use |
| `CONVERSION_MODE` | `local` | `local` or `mcp` |
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

### Production (Chainlit)

```bash
make run-ui
# → http://localhost:8000
```

### Development (MAF DevUI) — dev only

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

# The Chainlit UI is available at http://localhost:8000
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
├── ui/              # Chainlit (prod) + DevUI (dev)
├── validation/      # Result validator
└── workflows/       # MAF workflow orchestration
tests/
├── unit/            # Unit tests (no real APIs)
└── fixtures/        # Sample documents
docker/
├── Dockerfile
└── docker-compose.yml
```

---

## Known Limitations (Phase 1)

- Only `SummaryAnalyzer` is fully implemented. `FinancialAnalyzer`, `ComparisonAnalyzer`,
  `LegalAnalyzer`, `AuditAnalyzer`, and `CustomAnalyzer` are Phase 1 stubs.
- `LocalConverter` only does plain-text pass-through. PDF/DOCX binary parsing requires
  additional libraries (Phase 2).
- `MCPConverter` requires a running MarkItDown MCP server at `localhost:3001`.
- The `agent_framework` package (`agent-framework>=0.1.0`) must be available in the
  Python environment. If not installed, agents and workflows will fail to import.
- Financial calculator uses a stub DataFrame in `AnalystAgent.run_financial_calculation`.
  Full document-to-DataFrame extraction is a Phase 2 task.
