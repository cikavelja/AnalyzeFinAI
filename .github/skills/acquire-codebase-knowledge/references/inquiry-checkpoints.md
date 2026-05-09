# Inquiry Checkpoints

Per-template investigation questions for Phase 2 of the acquire-codebase-knowledge workflow.
For each template area, look for answers in the scan output first, then read source files to fill gaps.

---

## 1. STACK.md — Tech Stack

- What is the primary language and exact version? (check `pyproject.toml`, Docker `FROM` line)
- What package manager is used? (`pip`, `uv`, `poetry`)
- What are the core runtime frameworks? (web server, ORM, DI container)
- What do `dependencies` (production) vs dev dependencies contain?
- Is there a Docker image and what base image does it use?
- What are the key scripts in `Makefile` / `pyproject.toml`?

---

## 2. STRUCTURE.md — Directory Layout

- Where does source code live?
- What are the entry points? (check `app/main.py`, `app/ui/chainlit_app.py`, `app/ui/devui_app.py`)
- What is the stated purpose of each top-level directory?
- Are there non-obvious directories?
- What naming conventions do directories follow?

---

## 3. ARCHITECTURE.md — Patterns

- Is the code organized by layer or by feature?
- What is the primary data flow? Trace one request from entry to report output.
- Are there singletons, dependency injection patterns, or explicit initialization order requirements?
- Are there background workers, queues, or event-driven components?
- What design patterns appear repeatedly? (Protocol/DI, Pipeline, Factory)
- How do MAF agents interact with the pipeline?

---

## 4. CONVENTIONS.md — Coding Standards

- What is the file naming convention?
- What is the function and variable naming convention?
- What linter and formatter are configured? (check `pyproject.toml` for `ruff`, `mypy`)
- How are errors handled at each layer? (typed exceptions from `app/exceptions.py`)
- What logging library is used and what is the log message format? (`structlog`)
- How are imports organized?

---

## 5. INTEGRATIONS.md — External Services

- What external APIs are called? (OpenAI, HuggingFace, MarkItDown MCP)
- How are credentials stored and accessed? (`.env`, `pydantic-settings`, `app/config.py`)
- What databases are connected? (filesystem, SQLite)
- What monitoring or observability tools are used? (OpenTelemetry via MAF DevUI)
- How is the MCP server launched and connected?

---

## 6. TESTING.md — Test Setup

- What test runner is configured? (check `pyproject.toml` for pytest settings)
- Where are test files located? (`tests/unit/`, `tests/integration/`, `tests/fixtures/`)
- What assertion library is used? (`pytest` assert)
- How are external dependencies mocked? (`pytest-mock`, `respx`)
- Are there integration tests that hit real services vs. unit tests with mocks?
- Is there a coverage threshold enforced?

---

## 7. CONCERNS.md — Known Issues

- How many TODOs/FIXMEs/HACKs are in production code? (see scan output)
- Which files have the highest git churn in the last 90 days? (see scan output)
- Are there any files over 300 lines that mix multiple responsibilities?
- Are there stub analyzers (`NotImplementedError`) that need implementation?
- What security risks exist? (file upload validation, API key handling, MCP config)
- Are there performance patterns that don't scale? (sequential processing in Phase 1)
