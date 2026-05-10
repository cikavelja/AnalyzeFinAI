.PHONY: install install-dev run-api run-react run-devui run-cli test lint fmt help

# ── Variables ──────────────────────────────────────────────────────────────
PYTHON   := python
PIP      := pip
PYTEST   := pytest
RUFF     := ruff
MYPY     := mypy

# ── Setup ──────────────────────────────────────────────────────────────────

## install: Install production dependencies only
install:
	$(PIP) install -e .

## install-dev: Install production + development dependencies (requires --pre for agent-framework-devui)
install-dev:
	$(PIP) install -e ".[dev]" --pre

# ── Run ────────────────────────────────────────────────────────────────────

## run-api: Start the FastAPI server (development, auto-reload)
run-api:
	uvicorn app.api.main:app --reload --reload-dir app --port 8000

## run-react: Start the React Vite dev server
run-react:
	cd ui && npm run dev

## run-devui: Launch the MAF DevUI (development only — never use in production)
run-devui:
	$(PYTHON) app/ui/devui_app.py

## run-cli: Show CLI help
run-cli:
	$(PYTHON) -m app --help

# ── Quality ────────────────────────────────────────────────────────────────

## lint: Run ruff linter + mypy type checker
lint:
	$(RUFF) check app tests
	$(MYPY) app

## fmt: Auto-format with ruff
fmt:
	$(RUFF) format app tests
	$(RUFF) check --fix app tests

## test: Run the full pytest suite
test:
	$(PYTEST) tests/ -v --tb=short

## test-unit: Run unit tests only
test-unit:
	$(PYTEST) tests/unit/ -v --tb=short

# ── Help ───────────────────────────────────────────────────────────────────

## help: Show this message
help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## /  /'
