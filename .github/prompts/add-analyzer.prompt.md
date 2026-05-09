---
description: "Scaffold a new Analyzer module for AnalizerAI. Use when adding a new analysis type such as legal, sentiment, ESG, or custom domain analysis."
argument-hint: "Name of the new analyzer, e.g. 'SentimentAnalyzer' or 'ESGAnalyzer'"
agent: agent
tools: [read, edit, search]
---

You are scaffolding a new Analyzer for the AnalizerAI project.

## Step 1 — Read the protocol

Read [app/analyzers/base.py](../../app/analyzers/base.py) to understand the `AbstractAnalyzer` protocol you must implement.
Also read [app/analyzers/summary.py](../../app/analyzers/summary.py) as a reference implementation.

## Step 2 — Determine the name

The user wants to add: **${input}**

Derive:
- `class_name`: PascalCase + "Analyzer" suffix (e.g. `SentimentAnalyzer`)
- `file_name`: snake_case (e.g. `sentiment.py`)
- `analysis_type_value`: lowercase snake_case (e.g. `sentiment`) — this will be added to the `AnalysisType` enum

## Step 3 — Create the analyzer file

Create `app/analyzers/<file_name>.py` with:
- Correct `AbstractAnalyzer` protocol implementation
- `analyze()` method that:
  - Emits a start `AuditEvent`
  - Calls LLM only for narrative/text (never for arithmetic)
  - If numbers are needed, calls `app/financial/calculator.py` first
  - Returns a fully populated `AnalysisResult`
  - Emits a completion `AuditEvent`
- Follow [analyzers.instructions.md](../.github/instructions/analyzers.instructions.md) exactly

## Step 4 — Register in the router

Edit [app/routing/router.py](../../app/routing/router.py):
- Add the new `AnalysisType` enum value
- Add keyword matching rules for the new type
- Wire the new analyzer class into the dispatch map

## Step 5 — Add prompt templates

Edit [app/llm/prompt_templates.py](../../app/llm/prompt_templates.py):
- Add `system_prompt` and `user_prompt_template` for the new analysis type

## Step 6 — Create the test stub

Create `tests/unit/test_<file_name>.py` with:
- At least one success-path test (mock the LLM provider)
- At least one test verifying no LLM call is made if `LOCAL_ONLY_MODE=true`
- Follow [tests.instructions.md](../.github/instructions/tests.instructions.md)

## Step 7 — Confirm

List every file created or modified with a one-line summary of the change.
