---
name: acquire-codebase-knowledge
description: 'Use this skill when the user explicitly asks to map, document, or onboard into an existing codebase. Trigger for prompts like "map this codebase", "document this architecture", "onboard me to this repo", or "create codebase docs". Do not trigger for routine feature implementation, bug fixes, or narrow code edits unless the user asks for repository-level discovery.'
license: MIT
compatibility: 'Cross-platform. Requires Python 3.8+ and git. Run scripts/scan.py from the target project root.'
metadata:
  version: "1.3"
argument-hint: 'Optional: specific area to focus on, e.g. "architecture only", "testing and concerns"'
---

# Acquire Codebase Knowledge

Produces seven populated documents in `docs/codebase/` covering everything needed to work
effectively on the project. Only document what is verifiable from files or terminal output —
never infer or assume.

## Workflow

Copy and track this checklist:

```
- [ ] Phase 1: Run scan, read intent documents
- [ ] Phase 2: Investigate each documentation area
- [ ] Phase 3: Populate all seven docs in docs/codebase/
- [ ] Phase 4: Validate docs, present findings, resolve all [ASK USER] items
```

## Output Contract (Required)

Before finishing, all of the following must be true:

1. Exactly these files exist in `docs/codebase/`: `STACK.md`, `STRUCTURE.md`,
   `ARCHITECTURE.md`, `CONVENTIONS.md`, `INTEGRATIONS.md`, `TESTING.md`, `CONCERNS.md`.
2. Every claim is traceable to source files, config, or terminal output.
3. Unknowns are marked as `[TODO]`; intent-dependent decisions are marked `[ASK USER]`.
4. Every document includes a short "evidence" list with concrete file paths.
5. Final response includes numbered `[ASK USER]` questions and intent-vs-reality divergences.

---

### Phase 1: Scan and Read Intent

1. Run the scan script from the project root:
   ```bash
   python3 .github/skills/acquire-codebase-knowledge/scripts/scan.py --output docs/codebase/.codebase-scan.txt
   ```
2. Search for `PRD`, `TRD`, `README`, `ROADMAP`, `SPEC`, `DESIGN` files and read them.
3. Summarise the stated project intent before reading any source code.

### Phase 2: Investigate

Use the scan output to answer questions for each of the seven templates.
Load [`references/inquiry-checkpoints.md`](references/inquiry-checkpoints.md) for the full
per-template question list.

### Phase 3: Populate Templates

Fill in this order:
1. `STACK.md` — language, runtime, frameworks, all dependencies
2. `STRUCTURE.md` — directory layout, entry points, key files
3. `ARCHITECTURE.md` — layers, patterns, data flow
4. `CONVENTIONS.md` — naming, formatting, error handling, imports
5. `INTEGRATIONS.md` — external APIs, databases, auth, monitoring
6. `TESTING.md` — frameworks, file organization, mocking strategy
7. `CONCERNS.md` — tech debt, bugs, security risks, perf bottlenecks

Use `[TODO]` for anything that cannot be determined from code.
Use `[ASK USER]` where the right answer requires team intent.

### Phase 4: Validate, Repair, Verify

1. Validate each doc against `references/inquiry-checkpoints.md`.
2. For each non-trivial claim, confirm at least one evidence reference exists.
3. Fix and re-validate until all seven docs pass.
4. Present a summary, list every `[ASK USER]` item as a numbered question,
   and highlight any Intent vs. Reality divergences from Phase 1.

Validation pass criteria:
- No unsupported claims.
- No empty required sections.
- Unknowns use `[TODO]` rather than assumptions.
- Team-intent gaps are explicitly marked `[ASK USER]`.

---

## Focus Area Mode

If the user supplies a focus area (e.g. "architecture only"):
1. Always run Phase 1 in full.
2. Fully complete focus-area documents first.
3. For non-focus documents, keep required sections present and mark unknowns as `[TODO]`.
4. Still run the Phase 4 validation loop on all seven documents.

---

## Gotchas

**Outdated README:** Cross-reference with actual file structure before treating any README
claim as fact.

**Generated/compiled output:** Never document patterns from `dist/`, `build/`, `generated/`,
`__pycache__/`. Document source conventions only.

**`.env.example` reveals required config:** Read `.env.example` to discover required
environment variables.

**`devDependencies` ≠ production stack:** Document linters, formatters, and test frameworks
separately as dev tooling.

**Test TODOs ≠ production debt:** TODOs inside `tests/` are coverage gaps, not production
technical debt. Separate them in `CONCERNS.md`.

---

## Bundled Assets

| Asset | When to load |
|-------|-------------|
| [`scripts/scan.py`](scripts/scan.py) | Phase 1 — run first, before reading any code |
| [`references/inquiry-checkpoints.md`](references/inquiry-checkpoints.md) | Phase 2 — per-template investigation questions |
