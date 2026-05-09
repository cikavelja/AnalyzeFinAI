---
name: ruff-recursive-fix
description: Run Ruff checks with optional scope and rule overrides, apply safe and unsafe autofixes iteratively, review each change, and resolve remaining findings with targeted edits or user decisions.
---

# Ruff Recursive Fix

## Overview

Use this skill to enforce code quality with Ruff in a controlled, iterative workflow.
It supports:

- Optional scope limitation to a specific folder.
- Default project settings from `pyproject.toml`.
- Flexible Ruff invocation (`uv`, direct `ruff`, `python -m ruff`, or equivalent).
- Optional per-run rule overrides (`--select`, `--ignore`, `--extend-select`, `--extend-ignore`).
- Automatic safe then unsafe autofixes.
- Diff review after each fix pass.
- Recursive repetition until findings are resolved or require a decision.
- Judicious use of inline `# noqa` only when suppression is justified.

## Inputs

Collect these inputs before running:

- `target_path` (optional): folder or file to check. Empty means whole repository.
- `ruff_runner` (optional): explicit Ruff command prefix (e.g. `uv run`, `ruff`, `python -m ruff`).
- `rules_select` (optional): comma-separated rule codes to enforce.
- `rules_ignore` (optional): comma-separated rule codes to ignore.
- `extend_select` (optional): extra rules to add without replacing configured defaults.
- `extend_ignore` (optional): extra ignored rules without replacing configured defaults.
- `allow_unsafe_fixes` (default: true): whether to run Ruff unsafe fixes.
- `ask_on_ambiguity` (default: true): always ask the user when multiple valid choices exist.

## Command Construction

### 0. Resolve Ruff Runner

Resolution order:
1. If `ruff_runner` is provided, use it as-is.
2. Else if `uv` is available and Ruff is managed through `uv`, use `uv run ruff`.
3. Else if `ruff` is available on `PATH`, use `ruff`.
4. Else if Python is available, use `python -m ruff`.

Base commands:
```bash
<ruff_cmd> check [target_path] [--select <codes>] [--ignore <codes>]
<ruff_cmd> format [target_path]
```

Examples:
```bash
# Full project with defaults from pyproject.toml
ruff check

# One folder with defaults
python -m ruff check app/financial

# Enforce specific rules only
uv run ruff check app/ --select F,E9,I

# Skip doc rules for this run
ruff check app/ --extend-ignore D,TD
```

## Workflow

### 1. Baseline Analysis
1. Run `<ruff_cmd> check` with the selected scope and options.
2. Classify findings: autofixable-safe / autofixable-unsafe / not-autofixable.
3. If no findings, stop.

### 2. Safe Autofix Pass
1. Run Ruff with `--fix`.
2. Review resulting diff for semantic correctness.
3. Run `<ruff_cmd> format` on the same scope.
4. Re-run `<ruff_cmd> check`.

### 3. Unsafe Autofix Pass
Run only if findings remain and `allow_unsafe_fixes=true`.
1. Run Ruff with `--fix --unsafe-fixes`.
2. Review diff carefully, prioritizing behavior-sensitive edits.
3. Run `<ruff_cmd> format`.
4. Re-run `<ruff_cmd> check`.

### 4. Manual Remediation Pass
For remaining findings:
1. Fix directly in code when there is a clear, safe correction.
2. Keep edits minimal and local.
3. Run `<ruff_cmd> format`.
4. Re-run `<ruff_cmd> check`.

### 5. Ambiguity Policy
If there are multiple valid solutions at any step, always ask the user before proceeding.

### 6. Suppression Decision (`# noqa`)
Use suppression only when ALL conditions are true:
- The rule conflicts with required behavior, public API, or framework conventions.
- Refactoring would be disproportionate to the value of the rule.
- The suppression is narrow (single line, explicit code: `# noqa: E501`).

### 7. Recursive Loop
Repeat steps 2–6 until:
- `<ruff_cmd> check` returns clean.
- Remaining findings require architectural decisions.
- Remaining findings are intentionally suppressed with rationale.
- Repeated loop makes no progress.

## Output Contract

At the end, report:
- Scope and Ruff options used.
- Number of iterations performed.
- Summary of fixed findings by rule code.
- List of manual fixes made.
- List of suppressions with rationale.
- Remaining findings requiring user decisions.

## Suggested Prompt Starters

- "Run ruff-recursive-fix on the whole repo with default config."
- "Run ruff-recursive-fix only on app/financial, ignore DOC rules."
- "Run ruff-recursive-fix on tests with select F,E9,I and no unsafe fixes."
