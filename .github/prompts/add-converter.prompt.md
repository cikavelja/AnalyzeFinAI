---
description: "Scaffold a new document Converter for AnalizerAI. Use when adding a new conversion backend such as a REST API converter, a local library converter, or a new MCP-based converter."
argument-hint: "Name and transport type, e.g. 'RestApiConverter' or 'TikaConverter (http)'"
agent: agent
tools: [read, edit, search]
---

You are scaffolding a new document Converter for the AnalizerAI project.

## Step 1 — Read the protocol

Read [app/conversion/base.py](../../app/conversion/base.py) to understand the `AbstractConverter` protocol.
Also read [app/conversion/local_converter.py](../../app/conversion/local_converter.py) as a reference implementation.

## Step 2 — Determine the name

The user wants to add: **${input}**

Derive:
- `class_name`: PascalCase + "Converter" suffix (e.g. `TikaConverter`)
- `file_name`: snake_case (e.g. `tika_converter.py`)
- `config_key`: what `CONVERSION_MODE` value will select this converter (e.g. `tika`)

## Step 3 — Create the converter file

Create `app/conversion/<file_name>.py` with:
- Correct `AbstractConverter` protocol implementation
- `convert(file_path: Path) -> ConversionResult` async method
- On failure: do not raise — return `ConversionResult(success=False, error=str(e))`
- Log conversion start and end via `structlog`
- Emit `AuditEvent` at start and end

## Step 4 — Register in config

Edit [app/config.py](../../app/config.py):
- Add the new `config_key` as a valid `CONVERSION_MODE` literal

Edit [app/orchestration/pipeline.py](../../app/orchestration/pipeline.py):
- Add the new converter to the DI selection block

## Step 5 — Add config documentation

Edit [.env.example](../../.env.example):
- Add the new `CONVERSION_MODE` option as a comment

## Step 6 — Create tests

Create `tests/unit/test_<file_name>.py` with:
- Success path: mock the external dependency, assert Markdown is returned
- Failure path: mock a failure, assert `ConversionResult(success=False)` is returned
- Never hit a real network or filesystem in unit tests

## Step 7 — Confirm

List every file created or modified with a one-line summary of the change.
