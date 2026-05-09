---
description: "Run an end-to-end AnalizerAI analysis and summarize the result. Use when you want to test the pipeline against real documents or verify a change didn't break the output."
argument-hint: "Input folder path and prompt, e.g. './documents -- Financial analysis for 2024'"
agent: agent
tools: [read, execute, search]
---

You are running an end-to-end analysis using the AnalizerAI pipeline.

## Step 1 — Parse the input

The user provided: **${input}**

Split on ` -- ` to extract:
- `input_folder`: path to the documents folder (left side)
- `user_prompt`: the analysis prompt (right side)

If either is missing, ask the user to provide both separated by ` -- `.

## Step 2 — Validate the environment

Run:
```bash
python -m app validate --input <input_folder>
```

Report any rejected files (unsupported extension, too large, corrupted).
Stop here if zero valid files are found.

## Step 3 — Choose launch mode

Ask the user which UI/mode to use:
- **CLI** (default): `python -m app analyze`
- **React UI** (production): `make run-api` (serves built `ui/dist/`)
- **DevUI** (dev/debug): `python app/ui/devui_app.py`

## Step 4 — Run the analysis (CLI mode)

```bash
python -m app analyze \
  --input <input_folder> \
  --prompt "<user_prompt>" \
  --output ./reports/report.md \
  --verbose
```

Capture stdout and stderr. If the command fails, show the full error and suggest fixes.

## Step 5 — Summarize the report

Read `./reports/report.md` and provide:
- **Executive Summary** (from the report)
- **Key Findings** (bullet list, top 5)
- **Warnings / Limitations** (if any)
- **Audit trail** — show the count of `AuditEvent`s from `./data/audit.jsonl`

## Step 6 — Offer next steps

Suggest:
- Which analysis type was detected and whether it was correct
- Whether to re-run with a different prompt or analysis type
- Whether to open the React UI for a richer view: run `make run-api` and visit http://localhost:8000
