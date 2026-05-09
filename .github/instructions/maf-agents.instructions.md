---
description: "Use when creating or editing MAF agents or workflows in app/agents/ or app/workflows/. Covers agent_framework.Agent construction, tool registration, workflow patterns, DevUI launch, and MAF conventions."
applyTo: "{app/agents,app/workflows}/**/*.py"
---
# Microsoft Agent Framework (MAF) Conventions

## Agent Construction

Every agent must be an `agent_framework.Agent` instance with these required fields:

```python
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

orchestrator = Agent(
    name="OrchestratorAgent",         # PascalCase, matches variable name
    client=OpenAIChatClient(),         # or HuggingFaceChatClient()
    instructions="You are ...",        # System prompt — be specific about role and constraints
    tools=[tool_fn_1, tool_fn_2],      # Plain async functions with docstrings
)
```

## Tool Functions

Tools are plain `async def` functions. The docstring is what MAF shows the agent
as the tool description — make it precise:

```python
async def run_financial_calculation(document_id: str, calculation_type: str) -> str:
    """
    Run a deterministic financial calculation on a converted document.
    calculation_type: one of 'yoy', 'cagr', 'ratios', 'anomalies', 'trends'.
    Returns a JSON string of FinancialMetrics.
    """
    ...
```

- Always type-hint tool parameters and return type.
- Tools must be `async def` — no sync functions as MAF tools.
- Tool return values must be `str` or JSON-serializable. Return Pydantic `.model_dump_json()`.

## Workflow Patterns

Use `WorkflowBuilder` + `@executor` for graph-based workflows. This is **required** for
the DevUI diagram to render — `FunctionalWorkflow` (`@workflow` decorator) lacks the
`executors` attribute that DevUI uses to detect and visualize workflows.

```python
from agent_framework import WorkflowBuilder, WorkflowContext
from agent_framework._workflows._function_executor import executor
from typing import Never

# Intermediate step: receives dict, sends dict to next executor
@executor
async def ingest_step(context: dict, ctx: WorkflowContext[dict]) -> None:
    # ... do work ...
    await ctx.send_message(context)

# First step when DevUI sends a string: use input=str and coerce inside
@executor(input=str)
async def first_step(context, ctx: WorkflowContext[dict]) -> None:
    if not isinstance(context, dict):
        context = {"prompt": str(context), "document_ids": []}
    await ctx.send_message(context)

# Last step: yield output instead of sending to next executor
@executor(workflow_output=str)
async def report_step(context: dict, ctx: WorkflowContext[Never, str]) -> None:
    await ctx.yield_output("final result")

# Wire executors into a workflow
my_workflow = (
    WorkflowBuilder(name="MyWorkflow", description="...", start_executor=first_step)
    .add_edge(first_step, ingest_step)
    .add_edge(ingest_step, report_step)
    .build()
)
```

- Use `add_edge` for sequential dependencies.
- Use `add_fan_out_edges` for parallel broadcasting to multiple executors.
- Use `WorkflowBuilder` agents directly with `.add_edge(executor, agent)` for agent handoffs.

## DevUI Launch (Development Only)

```python
# app/ui/devui_app.py
from agent_framework.devui import serve
serve(entities=[orchestrator_agent, analysis_workflow], auto_open=True)
```

- `serve()` is dev-only. Never import `agent_framework.devui` in production code paths.
- DevUI port default: 8080. Use `--tracing` flag for OpenTelemetry traces.

## Agent Naming

- Agent `name` must be `PascalCase` matching the Python variable: `"OrchestratorAgent"`, `"AnalystAgent"`, `"ReviewerAgent"`.
- Workflow `name` must end in `"Workflow"`: `"AnalysisWorkflow"`.

## Error Handling in Tools

Tools must never raise unhandled exceptions — they would crash the MAF run loop.
Catch exceptions, log them, and return a structured error string:

```python
try:
    result = await do_work()
    return result.model_dump_json()
except ConversionError as e:
    logger.error("conversion_failed", error=str(e))
    return json.dumps({"error": str(e), "status": "failed"})
```
