---
description: "Keep README.md up to date whenever new functionality is added or changed. Apply to all app/ source files and key config files."
applyTo: "{app/**/*.py,pyproject.toml,docker-compose.yml,Dockerfile,Makefile}"
---
# README Maintenance Rules

## When to Update README.md

Update `README.md` whenever any of the following change:

| Change | README section(s) to update |
|--------|----------------------------|
| New layer or module added to `app/` | Architecture table, Layer Summary table, Project Structure |
| New `AnalysisType` supported | Pipeline Stages → Routing, Analysis |
| New CLI command or flag | Usage → CLI |
| New configuration key | Getting Started → Configuration |
| New supported file format | End-User UI (Chainlit) supported formats list |
| New LLM provider implementation | Key Design Principles → LLM Abstraction; Architecture table |
| New storage backend | Architecture table; Configuration |
| New converter backend | Architecture table; Configuration |
| New MAF agent or workflow pattern | Architecture → MAF Agent Orchestration |
| New financial metric or formula | Pipeline Stages → Financial Calculation |
| `make` target added or renamed | Development → commands |
| Python version requirement change | Development → Code Conventions |
| New dependency (pydantic, typer, etc.) | Prerequisites or Code Conventions |
| Docker or deployment change | Usage → Docker |

## How to Update

1. Edit only the relevant section(s) — do not rewrite the entire README.
2. Keep the same formatting and heading hierarchy.
3. Add new rows to tables rather than replacing existing rows.
4. If a feature is removed, remove or strike-through the corresponding entry.
5. Do not add version numbers or dates unless the user requests it.
6. Do not add "Changed in this PR" callout boxes — the README describes current state only.

## What NOT to Put in README.md

- Internal implementation details (class internals, private methods).
- Full API reference — that belongs in docstrings.
- Changelog entries — use CHANGELOG.md or git history.
- Raw audit log output examples beyond the minimal snippet already present.
- Secrets, API keys, or credentials of any kind.
