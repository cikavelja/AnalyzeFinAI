---
description: "Use when creating or editing UI code in app/ui/. Covers Chainlit async patterns, step display, streaming, file upload validation, DevUI launch script, and what must not appear in production UI."
applyTo: "app/ui/**/*.py"
---
# UI Conventions — Chainlit (Production) + DevUI (Development)

## Chainlit — Production UI (`chainlit_app.py`)

### Decorator Pattern

```python
import chainlit as cl

@cl.on_chat_start
async def on_chat_start() -> None:
    """Initialize session state and display welcome."""
    ...

@cl.on_message
async def on_message(message: cl.Message) -> None:
    """Handle incoming chat messages and uploaded files."""
    ...
```

### Long Operations Must Use `cl.Step`

Never `await` a long operation directly in a message handler. Wrap it:

```python
async with cl.Step(name="Converting documents") as step:
    results = await convert_all_documents(documents)
    step.output = f"Converted {len(results)} documents"
```

Steps appear in the Chainlit UI as collapsible progress indicators with timing.

### Streaming LLM Output

Always stream — never buffer and return the full response at once:

```python
msg = cl.Message(content="")
await msg.send()
async for token in llm_provider.stream(...):
    await msg.stream_token(token)
await msg.update()
```

### File Upload Validation

Before passing uploaded files to the ingestion layer, validate in the UI:

```python
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".csv", ".pptx", ".txt",
                      ".html", ".json", ".xml", ".png", ".jpg", ".zip"}

for element in message.elements:
    if isinstance(element, cl.File):
        ext = Path(element.name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            await cl.Message(content=f"❌ Unsupported file type: {ext}").send()
            return
```

### Report Download

Send completed reports as file attachments:

```python
elements = [cl.File(name="report.md", path=str(report_path), display="inline")]
await cl.Message(content="✅ Analysis complete. Report attached.", elements=elements).send()
```

### Audit Log Display

Render audit events as collapsed steps, not raw JSON:

```python
for event in audit_events:
    async with cl.Step(name=f"{event.event_type} — {event.status}") as s:
        s.output = event.detail
```

## DevUI — Development Launch Script (`devui_app.py`)

```python
# app/ui/devui_app.py
from agent_framework.devui import serve
from app.agents.orchestrator_agent import orchestrator_agent
from app.workflows.analysis_workflow import analysis_workflow

if __name__ == "__main__":
    serve(
        entities=[orchestrator_agent, analysis_workflow],
        auto_open=True,
        port=8080,
    )
```

- This file is **dev-only**. It must not be imported by any other module.
- Do not add `devui_app.py` to the production Docker image CMD.
- Use `--tracing` CLI flag for OpenTelemetry trace visualization.

## What Must NOT Be in UI Code

- No business logic — UI files only call pipeline/agent/workflow functions.
- No direct LLM calls from UI files — always go through the agent or provider layer.
- No raw document content in log messages.
- No hardcoded API keys or model names — always read from `app/config.py`.
