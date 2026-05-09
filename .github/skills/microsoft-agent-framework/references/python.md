# Microsoft Agent Framework for Python

Use this reference when the target project is written in Python.

## Authoritative sources

- Repository: <https://github.com/microsoft/agent-framework/tree/main/python>
- Samples: <https://github.com/microsoft/agent-framework/tree/main/python/samples>

## Installation

For new projects, install the package with:

```bash
pip install agent-framework
```

For the Developer UI (dev-only, never in production):

```bash
pip install agent-framework-devui --pre
```

## Python-specific guidance

- Use modern async patterns throughout agent and workflow operations.
- Add type hints and keep APIs explicit even in dynamic code.
- Follow standard Python packaging and environment practices for dependencies and tooling.
- Use middleware, context providers, and orchestration patterns in ways that fit the Python application structure.
- Check the latest Python samples before introducing new APIs or workflow patterns.

## Agent Construction

```python
from agent_framework import Agent
from agent_framework.clients import OpenAIChatClient  # or HuggingFaceChatClient

analyst_agent = Agent(
    name="AnalystAgent",
    client=OpenAIChatClient(model="gpt-4o"),
    instructions="You are a financial document analyst...",
    tools=[analyze_document_tool, extract_metrics_tool],
)
```

## Tool Registration

Tools are plain `async def` functions — the docstring is used as the tool description:

```python
async def analyze_document_tool(document_id: str, analysis_type: str) -> str:
    """Analyze a document and return structured findings as JSON.

    Args:
        document_id: The unique identifier of the document to analyze.
        analysis_type: The type of analysis to perform (financial, summary, etc.)

    Returns:
        JSON string with analysis results or an error description.
    """
    try:
        result = await run_analysis(document_id, analysis_type)
        return result.model_dump_json()
    except AnalysisError as e:
        return json.dumps({"error": str(e), "document_id": document_id})
```

## Workflow Patterns

```python
from agent_framework import sequential, concurrent, handoff

# Sequential — each step uses the previous output
pipeline = sequential([ingest_step, convert_step, analyze_step, report_step])

# Concurrent — steps run in parallel
parallel_analysis = concurrent([financial_agent, summary_agent, legal_agent])

# Handoff — orchestrator delegates to specialist
orchestrator = handoff(orchestrator_agent, [analyst_agent, reviewer_agent])
```

## DevUI Launch (dev-only)

```python
from agent_framework.devui import serve

if __name__ == "__main__":
    serve(
        entities=[orchestrator_agent, analyst_agent, reviewer_agent],
        auto_open=True,
    )
```

Or from CLI:

```bash
devui ./app/agents --port 8080 --tracing
```

**Never expose DevUI in production Docker images.**
